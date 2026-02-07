"""Controller for lyric parsing rule management"""

import base64
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import LyricParsingRule
from schemas.lyric_parsing_rule_schemas import (
    LyricParsingRuleCreate,
    LyricParsingRuleListResponse,
    LyricParsingRuleReorderRequest,
    LyricParsingRuleResponse,
    LyricParsingRuleUpdate,
)


class LyricParsingRuleController:
    """Controller for lyric parsing rule operations"""

    @staticmethod
    def _decode_replacement(replacement: str) -> str:
        """Decode Base64-encoded replacement string"""
        try:
            return base64.b64decode(replacement.encode()).decode("utf-8")
        except Exception:
            # If decoding fails, return original (backward compatibility)
            return replacement

    @staticmethod
    def _encode_replacement(replacement: str) -> str:
        """Encode replacement string to Base64"""
        return base64.b64encode(replacement.encode("utf-8")).decode("ascii")

    @staticmethod
    def get_all_rules(
        db: Session, rule_type: str | None = None, active_only: bool = False
    ) -> tuple[dict[str, Any], int]:
        """Get all lyric parsing rules, optionally filtered by type and active status"""
        try:
            query = db.query(LyricParsingRule)

            if rule_type:
                query = query.filter(LyricParsingRule.rule_type == rule_type)

            if active_only:
                query = query.filter(LyricParsingRule.active)

            # Order by execution order
            rules = query.order_by(LyricParsingRule.order).all()

            # Decode Base64-encoded replacements before returning
            for rule in rules:
                rule.replacement = LyricParsingRuleController._decode_replacement(rule.replacement)

            rules_data = [LyricParsingRuleResponse.model_validate(rule) for rule in rules]
            response = LyricParsingRuleListResponse(rules=rules_data, total=len(rules_data))

            return response.model_dump(), 200

        except Exception as e:
            return {"error": f"Failed to retrieve rules: {str(e)}"}, 500

    @staticmethod
    def get_rule_by_id(db: Session, rule_id: int) -> tuple[dict[str, Any], int]:
        """Get a specific rule by ID"""
        try:
            rule = db.query(LyricParsingRule).filter(LyricParsingRule.id == rule_id).first()

            if not rule:
                return {"error": f"Rule with ID {rule_id} not found"}, 404

            # Decode Base64-encoded replacement before returning
            rule.replacement = LyricParsingRuleController._decode_replacement(rule.replacement)

            response = LyricParsingRuleResponse.model_validate(rule)
            return response.model_dump(), 200

        except Exception as e:
            return {"error": f"Failed to retrieve rule: {str(e)}"}, 500

    @staticmethod
    def create_rule(db: Session, rule_data: LyricParsingRuleCreate) -> tuple[dict[str, Any], int]:
        """Create a new lyric parsing rule"""
        try:
            # Encode replacement before storing in DB
            rule_dict = rule_data.model_dump()
            rule_dict["replacement"] = LyricParsingRuleController._encode_replacement(rule_dict["replacement"])

            # Create new rule
            new_rule = LyricParsingRule(**rule_dict)
            db.add(new_rule)
            db.commit()
            db.refresh(new_rule)

            # Decode replacement before returning
            new_rule.replacement = LyricParsingRuleController._decode_replacement(new_rule.replacement)

            response = LyricParsingRuleResponse.model_validate(new_rule)
            return response.model_dump(), 201

        except IntegrityError as e:
            db.rollback()
            return {"error": f"Database integrity error: {str(e)}"}, 409
        except Exception as e:
            db.rollback()
            return {"error": f"Failed to create rule: {str(e)}"}, 500

    @staticmethod
    def update_rule(db: Session, rule_id: int, update_data: LyricParsingRuleUpdate) -> tuple[dict[str, Any], int]:
        """Update an existing lyric parsing rule"""
        try:
            rule = db.query(LyricParsingRule).filter(LyricParsingRule.id == rule_id).first()

            if not rule:
                return {"error": f"Rule with ID {rule_id} not found"}, 404

            # Update only provided fields
            update_dict = update_data.model_dump(exclude_unset=True)

            # Encode replacement if present in update
            if "replacement" in update_dict:
                update_dict["replacement"] = LyricParsingRuleController._encode_replacement(update_dict["replacement"])

            for field, value in update_dict.items():
                setattr(rule, field, value)

            db.commit()
            db.refresh(rule)

            # Decode replacement before returning
            rule.replacement = LyricParsingRuleController._decode_replacement(rule.replacement)

            response = LyricParsingRuleResponse.model_validate(rule)
            return response.model_dump(), 200

        except Exception as e:
            db.rollback()
            return {"error": f"Failed to update rule: {str(e)}"}, 500

    @staticmethod
    def delete_rule(db: Session, rule_id: int) -> tuple[dict[str, Any], int]:
        """Hard delete a lyric parsing rule"""
        try:
            rule = db.query(LyricParsingRule).filter(LyricParsingRule.id == rule_id).first()

            if not rule:
                return {"error": f"Rule with ID {rule_id} not found"}, 404

            db.delete(rule)
            db.commit()

            return {"message": f"Rule with ID {rule_id} has been deleted"}, 200

        except Exception as e:
            db.rollback()
            return {"error": f"Failed to delete rule: {str(e)}"}, 500

    @staticmethod
    def reorder_rules(db: Session, reorder_data: LyricParsingRuleReorderRequest) -> tuple[dict[str, Any], int]:
        """Reorder rules based on provided ID list"""
        try:
            rule_ids = reorder_data.rule_ids

            # Verify all IDs exist
            existing_rules = db.query(LyricParsingRule).filter(LyricParsingRule.id.in_(rule_ids)).all()
            existing_ids = {rule.id for rule in existing_rules}

            if len(existing_ids) != len(rule_ids):
                missing_ids = set(rule_ids) - existing_ids
                return {"error": f"Rules not found: {missing_ids}"}, 404

            # Update order for each rule
            for index, rule_id in enumerate(rule_ids):
                rule = db.query(LyricParsingRule).filter(LyricParsingRule.id == rule_id).first()
                if rule:
                    rule.order = index

            db.commit()

            # Return all rules in their new order
            all_rules = db.query(LyricParsingRule).order_by(LyricParsingRule.order).all()
            rules_data = [LyricParsingRuleResponse.model_validate(rule) for rule in all_rules]
            response = LyricParsingRuleListResponse(rules=rules_data, total=len(rules_data))

            return response.model_dump(), 200

        except Exception as e:
            db.rollback()
            return {"error": f"Failed to reorder rules: {str(e)}"}, 500
