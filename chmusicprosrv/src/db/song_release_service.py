"""Song Release Service - Database operations for song release management"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, desc, nullslast, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from db.models import ReleaseProjectReference, SongProject, SongRelease
from utils.logger import logger


class SongReleaseService:
    """Service for song release database operations (CRUD only, NO business logic)"""

    def create_release(
        self,
        db: Session,
        user_id: UUID,
        type: str,
        name: str,
        status: str,
        genre: str,
        description: str | None = None,
        tags: str | None = None,
        upload_date: date | None = None,
        release_date: date | None = None,
        downtaken_date: date | None = None,
        downtaken_reason: str | None = None,
        rejected_reason: str | None = None,
        upc: str | None = None,
        isrc: str | None = None,
        copyright_info: str | None = None,
        smart_link: str | None = None,
        cover_s3_key: str | None = None,
    ) -> SongRelease | None:
        """
        Create a new song release record

        Args:
            db: Database session
            user_id: User ID (from JWT)
            type: Release type ('single', 'album')
            name: Release name
            status: Release status ('draft', 'arranging', 'mixing', etc.)
            genre: Music genre
            description: Release description
            tags: Comma-separated tags
            upload_date: Upload date to platforms
            release_date: Public release date
            downtaken_date: Downtaken date
            downtaken_reason: Reason for downtake
            rejected_reason: Reason for rejection
            upc: Universal Product Code
            isrc: International Standard Recording Code
            copyright_info: Copyright information
            smart_link: Smart link URL (DistroKid, ToneDen, etc.)
            cover_s3_key: S3 key for cover image

        Returns:
            SongRelease instance if successful, None otherwise
        """
        try:
            release = SongRelease(
                user_id=user_id,
                type=type,
                name=name,
                status=status,
                genre=genre,
                description=description,
                tags=tags,
                upload_date=upload_date,
                release_date=release_date,
                downtaken_date=downtaken_date,
                downtaken_reason=downtaken_reason,
                rejected_reason=rejected_reason,
                upc=upc,
                isrc=isrc,
                copyright_info=copyright_info,
                smart_link=smart_link,
                cover_s3_key=cover_s3_key,
            )

            db.add(release)
            db.commit()
            db.refresh(release)

            logger.info(
                "Song release created",
                release_id=str(release.id),
                name=name,
                type=type,
                status=status,
                user_id=str(user_id),
            )
            return release

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Release creation DB error", error=str(e), error_type=e.__class__.__name__)
            return None
        except Exception as e:
            logger.error("Release creation failed", error=str(e), error_type=e.__class__.__name__)
            return None

    def get_release_by_id(self, db: Session, release_id: UUID, user_id: UUID) -> SongRelease | None:
        """
        Get release by ID with user ownership check

        Args:
            db: Database session
            release_id: Release UUID
            user_id: User ID (from JWT)

        Returns:
            SongRelease instance if found and owned by user, None otherwise
        """
        try:
            release = (
                db.query(SongRelease)
                .filter(SongRelease.id == release_id, SongRelease.user_id == user_id)
                .options(joinedload(SongRelease.project_references).joinedload(ReleaseProjectReference.project))
                .first()
            )

            if release:
                logger.debug("Release retrieved", release_id=str(release_id), user_id=str(user_id))
            else:
                logger.debug("Release not found", release_id=str(release_id), user_id=str(user_id))

            return release

        except SQLAlchemyError as e:
            logger.error("Get release DB error", error=str(e), release_id=str(release_id))
            return None

    def get_releases_paginated(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> tuple[list[SongRelease], int]:
        """
        Get paginated releases with filters

        Args:
            db: Database session
            user_id: User ID (from JWT)
            limit: Max number of results
            offset: Skip first N results
            status_filter: Filter by status group ('all', 'progress', 'uploaded', 'released', 'archive')
            search: Search in name/genre

        Returns:
            Tuple of (releases list, total count)
        """
        try:
            query = db.query(SongRelease).filter(SongRelease.user_id == user_id)

            # Apply status filter
            if status_filter:
                if status_filter == "all":
                    # Exclude rejected, downtaken, archived
                    query = query.filter(SongRelease.status.notin_(["rejected", "downtaken", "archived"]))
                elif status_filter == "progress":
                    query = query.filter(SongRelease.status.in_(["arranging", "mixing", "mastering"]))
                elif status_filter == "uploaded":
                    query = query.filter(SongRelease.status == "uploaded")
                elif status_filter == "released":
                    query = query.filter(SongRelease.status == "released")
                elif status_filter == "archive":
                    query = query.filter(SongRelease.status.in_(["rejected", "downtaken", "archived"]))

            # Apply search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(or_(SongRelease.name.ilike(search_term), SongRelease.genre.ilike(search_term)))

            # Get total count
            total = query.count()

            # Apply status-based smart sorting
            # - released: sort by release_date (not created_at!)
            # - uploaded: sort by upload_date
            # - downtaken: sort by downtaken_date
            # - archived/rejected: sort by updated_at
            # - draft/arranging/mixing/mastering: sort by created_at (newest first)
            sort_field = case(
                (SongRelease.status == "released", SongRelease.release_date),
                (SongRelease.status == "uploaded", SongRelease.upload_date),
                (SongRelease.status == "downtaken", SongRelease.downtaken_date),
                (SongRelease.status.in_(["archived", "rejected"]), SongRelease.updated_at),
                else_=SongRelease.created_at,  # draft, arranging, mixing, mastering
            )

            # Apply pagination and sorting (NULL dates go to end)
            releases = (
                query.order_by(
                    nullslast(desc(sort_field)),  # Primary: status-based date field
                    desc(SongRelease.created_at),  # Secondary: created_at as tiebreaker
                )
                .limit(limit)
                .offset(offset)
                .all()
            )

            logger.debug(
                "Releases retrieved",
                user_id=str(user_id),
                total=total,
                limit=limit,
                offset=offset,
                filter=status_filter,
                search=search,
            )
            return releases, total

        except SQLAlchemyError as e:
            logger.error("Get releases paginated DB error", error=str(e), user_id=str(user_id))
            return [], 0

    def update_release(
        self, db: Session, release_id: UUID, user_id: UUID, update_data: dict[str, Any]
    ) -> SongRelease | None:
        """
        Update release record

        Args:
            db: Database session
            release_id: Release UUID
            user_id: User ID (from JWT)
            update_data: Dictionary of fields to update

        Returns:
            Updated SongRelease instance if successful, None otherwise
        """
        try:
            release = db.query(SongRelease).filter(SongRelease.id == release_id, SongRelease.user_id == user_id).first()

            if not release:
                logger.warning("Release not found for update", release_id=str(release_id), user_id=str(user_id))
                return None

            # Update allowed fields
            allowed_fields = {
                "type",
                "name",
                "status",
                "genre",
                "description",
                "tags",
                "upload_date",
                "release_date",
                "downtaken_date",
                "downtaken_reason",
                "rejected_reason",
                "upc",
                "isrc",
                "copyright_info",
                "smart_link",
                "cover_s3_key",
            }

            for key, value in update_data.items():
                if key in allowed_fields and hasattr(release, key):
                    setattr(release, key, value)

            release.updated_at = datetime.now()
            db.commit()
            db.refresh(release)

            logger.info(
                "Release updated",
                release_id=str(release_id),
                user_id=str(user_id),
                fields_updated=list(update_data.keys()),
            )
            return release

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Update release DB error", error=str(e), release_id=str(release_id))
            return None

    def delete_release(self, db: Session, release_id: UUID, user_id: UUID) -> bool:
        """
        Delete release and all related project references

        Args:
            db: Database session
            release_id: Release UUID
            user_id: User ID (from JWT)

        Returns:
            True if successful, False otherwise
        """
        try:
            release = db.query(SongRelease).filter(SongRelease.id == release_id, SongRelease.user_id == user_id).first()

            if not release:
                logger.warning("Release not found for deletion", release_id=str(release_id), user_id=str(user_id))
                return False

            db.delete(release)  # Cascade will delete project_references
            db.commit()

            logger.info("Release deleted", release_id=str(release_id), user_id=str(user_id))
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Delete release DB error", error=str(e), release_id=str(release_id))
            return False

    def assign_projects(self, db: Session, release_id: UUID, project_ids: list[UUID]) -> bool:
        """
        Assign projects to release (replaces all existing assignments)

        Args:
            db: Database session
            release_id: Release UUID
            project_ids: List of project UUIDs to assign

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing references
            db.query(ReleaseProjectReference).filter(ReleaseProjectReference.release_id == release_id).delete()

            # Create new references
            for project_id in project_ids:
                reference = ReleaseProjectReference(release_id=release_id, project_id=project_id)
                db.add(reference)

            db.commit()

            logger.info(
                "Projects assigned to release",
                release_id=str(release_id),
                project_ids=[str(pid) for pid in project_ids],
                count=len(project_ids),
            )
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Assign projects DB error", error=str(e), release_id=str(release_id))
            return False

    def get_assigned_projects(self, db: Session, release_id: UUID) -> list[SongProject]:
        """
        Get all projects assigned to a release

        Args:
            db: Database session
            release_id: Release UUID

        Returns:
            List of SongProject instances
        """
        try:
            projects = (
                db.query(SongProject)
                .join(ReleaseProjectReference, ReleaseProjectReference.project_id == SongProject.id)
                .filter(ReleaseProjectReference.release_id == release_id)
                .order_by(SongProject.project_name)
                .all()
            )

            logger.debug("Assigned projects retrieved", release_id=str(release_id), count=len(projects))
            return projects

        except SQLAlchemyError as e:
            logger.error("Get assigned projects DB error", error=str(e), release_id=str(release_id))
            return []

    def remove_project_assignment(self, db: Session, release_id: UUID, project_id: UUID) -> bool:
        """
        Remove a single project assignment from release

        Args:
            db: Database session
            release_id: Release UUID
            project_id: Project UUID to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            deleted = (
                db.query(ReleaseProjectReference)
                .filter(
                    ReleaseProjectReference.release_id == release_id, ReleaseProjectReference.project_id == project_id
                )
                .delete()
            )

            db.commit()

            if deleted > 0:
                logger.info(
                    "Project assignment removed",
                    release_id=str(release_id),
                    project_id=str(project_id),
                )
                return True
            else:
                logger.warning(
                    "Project assignment not found for removal",
                    release_id=str(release_id),
                    project_id=str(project_id),
                )
                return False

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Remove project assignment DB error",
                error=str(e),
                release_id=str(release_id),
                project_id=str(project_id),
            )
            return False


# Singleton instance
song_release_service = SongReleaseService()
