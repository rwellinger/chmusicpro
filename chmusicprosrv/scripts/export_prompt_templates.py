#!/usr/bin/env python3
"""
Export script for prompt templates from local database.
Reads all prompt templates from local db and generates init_prompt_templates.py

Usage:
    python scripts/export_prompt_templates.py
"""

import os
import sys
from datetime import datetime


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from sqlalchemy.orm import Session

from db.database import get_db
from db.models import PromptTemplate


def fetch_templates():
    """Fetch all active templates from local database"""
    print("Connecting to local database...")
    db: Session = next(get_db())

    try:
        templates = db.query(PromptTemplate).order_by(PromptTemplate.category, PromptTemplate.action).all()

        print(f"✅ Fetched {len(templates)} templates from local DB\n")

        # Convert SQLAlchemy models to dict format
        template_dicts = []
        for t in templates:
            template_dicts.append(
                {
                    "category": t.category,
                    "action": t.action,
                    "pre_condition": t.pre_condition,
                    "post_condition": t.post_condition,
                    "description": t.description,
                    "version": t.version,
                    "model": t.model,
                    "temperature": t.temperature,
                    "max_tokens": t.max_tokens,
                    "active": t.active,
                }
            )

        return template_dicts

    finally:
        db.close()


def generate_init_script(templates):
    """Generate the init_prompt_templates.py script with local DB data"""

    # Group templates by category
    by_category = {}
    for template in templates:
        category = template["category"]
        action = template["action"]

        if category not in by_category:
            by_category[category] = {}

        by_category[category][action] = {
            "pre_condition": template["pre_condition"],
            "post_condition": template["post_condition"],
            "description": template["description"],
            "version": template["version"],
            "model": template["model"],
            "temperature": float(template["temperature"]),
            "max_tokens": template["max_tokens"],
            "active": template["active"],
        }

    # Generate Python code
    script_content = f'''#!/usr/bin/env python3
"""
Seeding script for prompt templates.
Exported from Dev-DB on {datetime.now().strftime("%Y-%m-%d")}.
This script seeds the database with all prompt templates.

Usage:
    python scripts/init_prompt_templates.py
"""

import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from sqlalchemy.orm import Session

from db.database import get_db
from db.models import PromptTemplate


# Prompt templates exported from Dev-DB ({datetime.now().strftime("%Y-%m-%d")})
TEMPLATES = {{
'''

    # Add templates
    for category in sorted(by_category.keys()):
        script_content += f'    "{category}": {{\n'

        for action in sorted(by_category[category].keys()):
            template = by_category[category][action]
            script_content += f'        "{action}": {{\n'
            script_content += f'            "pre_condition": """{template["pre_condition"]}""",\n'
            script_content += f'            "post_condition": """{template["post_condition"]}""",\n'
            script_content += f'            "description": "{template["description"]}",\n'
            script_content += f'            "version": "{template["version"]}",\n'
            script_content += f'            "model": "{template["model"]}",\n'
            script_content += f'            "temperature": {template["temperature"]},\n'
            script_content += f'            "max_tokens": {template["max_tokens"]},\n'
            script_content += f'            "active": {template["active"]},\n'
            script_content += "        },\n"

        script_content += "    },\n"

    script_content += '''}


def seed_prompt_templates():
    """Seed the database with prompt templates"""
    db: Session = next(get_db())

    try:
        inserted_count = 0
        updated_count = 0

        print("Starting prompt template seeding...\\\\n")

        for category, actions in TEMPLATES.items():
            print(f"Processing category: {category}")

            for action, template_data in actions.items():
                print(f"  Processing action: {action}")

                # Check if template already exists
                existing = (
                    db.query(PromptTemplate)
                    .filter(PromptTemplate.category == category, PromptTemplate.action == action)
                    .first()
                )

                if existing:
                    print(f"    Template exists (ID: {existing.id}), updating...")
                    # Update existing template with all fields
                    existing.pre_condition = template_data["pre_condition"]
                    existing.post_condition = template_data["post_condition"]
                    existing.description = template_data["description"]
                    existing.version = template_data["version"]
                    existing.model = template_data["model"]
                    existing.temperature = template_data["temperature"]
                    existing.max_tokens = template_data["max_tokens"]
                    existing.active = template_data["active"]
                    updated_count += 1
                else:
                    print("    Creating new template...")
                    # Create new template
                    new_template = PromptTemplate(
                        category=category,
                        action=action,
                        pre_condition=template_data["pre_condition"],
                        post_condition=template_data["post_condition"],
                        description=template_data["description"],
                        version=template_data["version"],
                        model=template_data["model"],
                        temperature=template_data["temperature"],
                        max_tokens=template_data["max_tokens"],
                        active=template_data["active"],
                    )
                    db.add(new_template)
                    inserted_count += 1

        # Commit all changes
        db.commit()

        print("\\\\n✅ Seeding completed successfully!")
        print(f"   - Inserted: {inserted_count} new templates")
        print(f"   - Updated:  {updated_count} existing templates")
        print(f"   - Total:    {inserted_count + updated_count} templates processed")

        return True

    except Exception as e:
        print(f"\\\\n❌ Error during seeding: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


def verify_templates():
    """Verify that all templates were seeded correctly"""
    db: Session = next(get_db())

    try:
        templates = db.query(PromptTemplate).filter(PromptTemplate.active).all()

        print("\\\\n📊 Verification Results:")
        print(f"   Total active templates in DB: {len(templates)}")

        if len(templates) == 0:
            print("   ⚠️  WARNING: No templates found in database!")
            return False

        # Group by category for display
        by_category = {}
        for template in templates:
            if template.category not in by_category:
                by_category[template.category] = []
            by_category[template.category].append(
                {"action": template.action, "model": template.model, "version": template.version}
            )

        print("\\\\n   Templates by category:")
        for category, actions in sorted(by_category.items()):
            print(f"\\\\n   {category}:")
            for action_data in sorted(actions, key=lambda x: x["action"]):
                print(f"     - {action_data['action']} (v{action_data['version']}, {action_data['model']})")

        # Check if we have the expected number of templates
        expected_count = sum(len(actions) for actions in TEMPLATES.values())
        if len(templates) >= expected_count:
            print(f"\\\\n   ✅ All {expected_count} expected templates are present")
            return True
        else:
            print(f"\\\\n   ⚠️  Expected {expected_count} templates, but found {len(templates)}")
            return False

    except Exception as e:
        print(f"\\\\n❌ Error during verification: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Prompt Template Seeding Script")
    print("=" * 60)
    print("This script will seed/update all prompt templates")
    print("=" * 60 + "\\\\n")

    if seed_prompt_templates():
        if verify_templates():
            print("\\\\n🎉 Seeding and verification completed successfully!")
            sys.exit(0)
        else:
            print("\\\\n⚠️  Templates seeded but verification has warnings!")
            sys.exit(1)
    else:
        print("\\\\n💥 Seeding failed!")
        sys.exit(1)
'''

    return script_content


def main():
    """Main export function"""
    print("📦 Prompt Template Export Script")
    print("=" * 60)
    print("Source: Local Dev-DB")
    print("Target: scripts/init_prompt_templates.py")
    print("=" * 60 + "\n")

    try:
        # Fetch templates from local database
        templates = fetch_templates()

        if not templates:
            print("❌ No templates found in local database!")
            return False

        # Display fetched templates
        print("Templates by category:")
        by_cat = {}
        for t in templates:
            if t["category"] not in by_cat:
                by_cat[t["category"]] = []
            by_cat[t["category"]].append(f"{t['action']} (v{t['version']}, {t['model']})")

        for category in sorted(by_cat.keys()):
            print(f"\n  {category}:")
            for action in by_cat[category]:
                print(f"    - {action}")

        print(f"\nTotal: {len(templates)} templates")

        # Generate init script
        print("\n" + "=" * 60)
        print("Generating init_prompt_templates.py...")
        script_content = generate_init_script(templates)

        # Write to file
        output_path = "scripts/init_prompt_templates.py"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        print(f"✅ Successfully wrote {output_path}")
        print(f"   File size: {len(script_content)} bytes")

        print("\n" + "=" * 60)
        print("🎉 Export completed successfully!")
        print("\nNext steps:")
        print("  1. Review the generated init_prompt_templates.py")
        print("  2. Run: python scripts/init_prompt_templates.py")
        print("     to apply these templates to any target database")

        return True

    except Exception as e:
        print(f"\n❌ Error during export: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
