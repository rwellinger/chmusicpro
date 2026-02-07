"""Unit tests for song_release_transformer - Pure functions for transformations and business logic"""

from datetime import date, datetime
from unittest.mock import Mock
from uuid import UUID

from business.song_release_transformer import (
    generate_s3_cover_key,
    get_presigned_cover_url_placeholder,
    get_status_filter_values,
    transform_project_to_assigned_response,
    transform_release_to_list_response,
    transform_release_to_response,
    validate_cover_dimensions,
    validate_required_fields_for_status,
)


class TestValidateRequiredFieldsForStatus:
    """Tests for validate_required_fields_for_status()"""

    def test_draft_status_with_base_fields_valid(self):
        """Test draft status with all base fields is valid"""
        # Arrange
        data = {"type": "single", "name": "Test Song", "genre": "Rock"}

        # Act
        is_valid, error = validate_required_fields_for_status("draft", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_draft_status_missing_name(self):
        """Test draft status missing name field"""
        # Arrange
        data = {"type": "single", "genre": "Rock"}

        # Act
        is_valid, error = validate_required_fields_for_status("draft", data)

        # Assert
        assert is_valid is False
        assert error == "Missing required fields for status 'draft': Name"

    def test_draft_status_missing_multiple_fields(self):
        """Test draft status missing multiple fields"""
        # Arrange
        data = {}

        # Act
        is_valid, error = validate_required_fields_for_status("draft", data)

        # Assert
        assert is_valid is False
        assert "Type" in error
        assert "Name" in error
        assert "Genre" in error

    def test_arranging_status_base_fields_only(self):
        """Test arranging status requires only base fields"""
        # Arrange
        data = {"type": "album", "name": "Test Album", "genre": "Pop"}

        # Act
        is_valid, error = validate_required_fields_for_status("arranging", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_uploaded_status_valid(self):
        """Test uploaded status with all required fields"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "upc": "123456789012",
            "copyright_info": "(C) 2024 Artist Name",
            "cover_s3_key": "releases/user/release/cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("uploaded", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_uploaded_status_missing_upc(self):
        """Test uploaded status with missing UPC (now optional)"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "copyright_info": "(C) 2024",
            "cover_s3_key": "cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("uploaded", data)

        # Assert - UPC is optional, so this should be valid
        assert is_valid is True
        assert error is None

    def test_uploaded_status_missing_cover_image(self):
        """Test uploaded status missing cover image"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "upc": "123",
            "copyright_info": "(C) 2024",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("uploaded", data)

        # Assert
        assert is_valid is False
        assert "Cover Image" in error

    def test_released_status_valid(self):
        """Test released status with all required fields"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "release_date": "2024-01-15",
            "upc": "123",
            "isrc": "US-XXX-24-00001",
            "copyright_info": "(C) 2024",
            "cover_s3_key": "cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("released", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_released_status_missing_isrc(self):
        """Test released status with missing ISRC (now optional)"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "release_date": "2024-01-15",
            "upc": "123",
            "copyright_info": "(C) 2024",
            "cover_s3_key": "cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("released", data)

        # Assert - ISRC is optional, so this should be valid
        assert is_valid is True
        assert error is None

    def test_released_status_missing_release_date(self):
        """Test released status missing release_date"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "upc": "123",
            "isrc": "US-XXX-24-00001",
            "copyright_info": "(C) 2024",
            "cover_s3_key": "cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("released", data)

        # Assert
        assert is_valid is False
        assert "Release Date" in error

    def test_rejected_status_with_reason(self):
        """Test rejected status requires rejected_reason"""
        # Arrange
        data = {"type": "single", "name": "Test", "genre": "Rock", "rejected_reason": "Quality issues"}

        # Act
        is_valid, error = validate_required_fields_for_status("rejected", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_rejected_status_missing_reason(self):
        """Test rejected status missing rejected_reason"""
        # Arrange
        data = {"type": "single", "name": "Test", "genre": "Rock"}

        # Act
        is_valid, error = validate_required_fields_for_status("rejected", data)

        # Assert
        assert is_valid is False
        assert "Rejected Reason" in error

    def test_downtaken_status_valid(self):
        """Test downtaken status with all required fields"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "release_date": "2024-01-15",
            "downtaken_date": "2024-02-01",
            "downtaken_reason": "Copyright claim",
            "upc": "123",
            "isrc": "US-XXX-24-00001",
            "copyright_info": "(C) 2024",
            "cover_s3_key": "cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("downtaken", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_downtaken_status_missing_downtaken_date(self):
        """Test downtaken status missing downtaken_date"""
        # Arrange
        data = {
            "type": "single",
            "name": "Test",
            "genre": "Rock",
            "upload_date": "2024-01-01",
            "release_date": "2024-01-15",
            "downtaken_reason": "Copyright claim",
            "upc": "123",
            "isrc": "US-XXX-24-00001",
            "copyright_info": "(C) 2024",
            "cover_s3_key": "cover.jpg",
        }

        # Act
        is_valid, error = validate_required_fields_for_status("downtaken", data)

        # Assert
        assert is_valid is False
        assert "Downtaken Date" in error

    def test_archived_status_base_fields_only(self):
        """Test archived status requires only base fields"""
        # Arrange
        data = {"type": "ep", "name": "Old Project", "genre": "Jazz"}

        # Act
        is_valid, error = validate_required_fields_for_status("archived", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_pre_release_status_base_fields_only(self):
        """Test pre_release status requires only base fields (like mastering)"""
        # Arrange
        data = {"type": "single", "name": "SoundCloud Track", "genre": "Electronic"}

        # Act
        is_valid, error = validate_required_fields_for_status("pre_release", data)

        # Assert
        assert is_valid is True
        assert error is None

    def test_pre_release_status_missing_genre(self):
        """Test pre_release status missing genre field"""
        # Arrange
        data = {"type": "single", "name": "SoundCloud Track"}

        # Act
        is_valid, error = validate_required_fields_for_status("pre_release", data)

        # Assert
        assert is_valid is False
        assert "Genre" in error

    def test_unknown_status_defaults_to_base_fields(self):
        """Test unknown status defaults to base fields only"""
        # Arrange
        data = {"type": "single", "name": "Test", "genre": "Rock"}

        # Act
        is_valid, error = validate_required_fields_for_status("unknown_status", data)

        # Assert
        assert is_valid is True
        assert error is None


class TestValidateCoverDimensions:
    """Tests for validate_cover_dimensions()"""

    def test_valid_dimensions_200x200(self):
        """Test valid cover dimensions 200x200"""
        # Act
        is_valid, error = validate_cover_dimensions(200, 200)

        # Assert
        assert is_valid is True
        assert error is None

    def test_invalid_width_too_large(self):
        """Test invalid width (too large)"""
        # Act
        is_valid, error = validate_cover_dimensions(300, 200)

        # Assert
        assert is_valid is False
        assert error == "Cover image must be 200x200 pixels, got 300x200"

    def test_invalid_height_too_large(self):
        """Test invalid height (too large)"""
        # Act
        is_valid, error = validate_cover_dimensions(200, 300)

        # Assert
        assert is_valid is False
        assert error == "Cover image must be 200x200 pixels, got 200x300"

    def test_invalid_dimensions_too_small(self):
        """Test invalid dimensions (both too small)"""
        # Act
        is_valid, error = validate_cover_dimensions(199, 199)

        # Assert
        assert is_valid is False
        assert error == "Cover image must be 200x200 pixels, got 199x199"

    def test_invalid_dimensions_completely_wrong(self):
        """Test completely wrong dimensions"""
        # Act
        is_valid, error = validate_cover_dimensions(1920, 1080)

        # Assert
        assert is_valid is False
        assert error == "Cover image must be 200x200 pixels, got 1920x1080"


class TestGenerateS3CoverKey:
    """Tests for generate_s3_cover_key()"""

    def test_generate_s3_cover_key_jpg(self):
        """Test S3 key generation with .jpg extension"""
        # Act
        result = generate_s3_cover_key("abc-123", "def-456", "my-cover.jpg")

        # Assert
        assert result == "releases/abc-123/def-456/cover.jpg"

    def test_generate_s3_cover_key_png(self):
        """Test S3 key generation with .png extension"""
        # Act
        result = generate_s3_cover_key("user-1", "release-2", "album.png")

        # Assert
        assert result == "releases/user-1/release-2/cover.png"

    def test_generate_s3_cover_key_jpeg(self):
        """Test S3 key generation with .jpeg extension"""
        # Act
        result = generate_s3_cover_key("user-abc", "release-xyz", "photo.jpeg")

        # Assert
        assert result == "releases/user-abc/release-xyz/cover.jpeg"

    def test_generate_s3_cover_key_no_extension(self):
        """Test S3 key generation with no file extension (defaults to .jpg)"""
        # Act
        result = generate_s3_cover_key("user-1", "release-1", "noextension")

        # Assert
        assert result == "releases/user-1/release-1/cover.jpg"

    def test_generate_s3_cover_key_multiple_dots(self):
        """Test S3 key generation with multiple dots in filename"""
        # Act
        result = generate_s3_cover_key("user-1", "release-1", "my.cover.image.png")

        # Assert
        assert result == "releases/user-1/release-1/cover.png"


class TestGetPresignedCoverUrlPlaceholder:
    """Tests for get_presigned_cover_url_placeholder()"""

    def test_get_placeholder_with_key(self):
        """Test placeholder URL generation with S3 key"""
        # Act
        result = get_presigned_cover_url_placeholder("releases/user/release/cover.jpg")

        # Assert
        assert result == "s3://releases/user/release/cover.jpg"

    def test_get_placeholder_with_none(self):
        """Test placeholder URL generation with None"""
        # Act
        result = get_presigned_cover_url_placeholder(None)

        # Assert
        assert result is None

    def test_get_placeholder_with_empty_string(self):
        """Test placeholder URL generation with empty string"""
        # Act
        result = get_presigned_cover_url_placeholder("")

        # Assert
        assert result is None


class TestTransformReleaseToResponse:
    """Tests for transform_release_to_response()"""

    def test_transform_release_complete_data(self):
        """Test transforming release with all fields populated"""
        # Arrange
        release = Mock()
        release.id = UUID("12345678-1234-5678-1234-567812345678")
        release.user_id = UUID("87654321-4321-8765-4321-876543218765")
        release.type = "single"
        release.name = "My Awesome Song"
        release.status = "released"
        release.genre = "Rock"
        release.description = "A great rock song"
        release.tags = "rock,guitar,energetic"
        release.upload_date = date(2024, 1, 1)
        release.release_date = date(2024, 1, 15)
        release.downtaken_date = None
        release.downtaken_reason = None
        release.rejected_reason = None
        release.upc = "123456789012"
        release.isrc = "US-XXX-24-00001"
        release.copyright_info = "(C) 2024 Artist Name"
        release.cover_s3_key = "releases/user/release/cover.jpg"
        release.created_at = datetime(2024, 1, 1, 10, 0, 0)
        release.updated_at = datetime(2024, 1, 15, 12, 30, 0)

        # Act
        result = transform_release_to_response(release)

        # Assert
        assert result["id"] == "12345678-1234-5678-1234-567812345678"
        assert result["user_id"] == "87654321-4321-8765-4321-876543218765"
        assert result["type"] == "single"
        assert result["name"] == "My Awesome Song"
        assert result["status"] == "released"
        assert result["genre"] == "Rock"
        assert result["description"] == "A great rock song"
        assert result["tags"] == "rock,guitar,energetic"
        assert result["upload_date"] == "2024-01-01"
        assert result["release_date"] == "2024-01-15"
        assert result["downtaken_date"] is None
        assert result["downtaken_reason"] is None
        assert result["rejected_reason"] is None
        assert result["upc"] == "123456789012"
        assert result["isrc"] == "US-XXX-24-00001"
        assert result["copyright_info"] == "(C) 2024 Artist Name"
        assert result["cover_url"] == "s3://releases/user/release/cover.jpg"
        assert result["created_at"] == "2024-01-01T10:00:00"
        assert result["updated_at"] == "2024-01-15T12:30:00"

    def test_transform_release_minimal_data(self):
        """Test transforming release with minimal fields (draft)"""
        # Arrange
        release = Mock()
        release.id = UUID("11111111-1111-1111-1111-111111111111")
        release.user_id = UUID("22222222-2222-2222-2222-222222222222")
        release.type = "album"
        release.name = "Work in Progress"
        release.status = "draft"
        release.genre = "Electronic"
        release.description = None
        release.tags = None
        release.upload_date = None
        release.release_date = None
        release.downtaken_date = None
        release.downtaken_reason = None
        release.rejected_reason = None
        release.upc = None
        release.isrc = None
        release.copyright_info = None
        release.cover_s3_key = None
        release.created_at = None
        release.updated_at = None

        # Act
        result = transform_release_to_response(release)

        # Assert
        assert result["id"] == "11111111-1111-1111-1111-111111111111"
        assert result["type"] == "album"
        assert result["name"] == "Work in Progress"
        assert result["status"] == "draft"
        assert result["genre"] == "Electronic"
        assert result["description"] is None
        assert result["upload_date"] is None
        assert result["release_date"] is None
        assert result["upc"] is None
        assert result["cover_url"] is None
        assert result["created_at"] is None

    def test_transform_release_with_assigned_projects(self):
        """Test transforming release with assigned projects"""
        # Arrange
        release = Mock()
        release.id = UUID("12345678-1234-5678-1234-567812345678")
        release.user_id = UUID("87654321-4321-8765-4321-876543218765")
        release.type = "single"
        release.name = "Test Song"
        release.status = "draft"
        release.genre = "Pop"
        release.description = None
        release.tags = None
        release.upload_date = None
        release.release_date = None
        release.downtaken_date = None
        release.downtaken_reason = None
        release.rejected_reason = None
        release.upc = None
        release.isrc = None
        release.copyright_info = None
        release.cover_s3_key = None
        release.created_at = None
        release.updated_at = None

        project1 = Mock()
        project1.id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        project1.project_name = "Song Project 1"
        project1.s3_prefix = "user/project-1/"
        project1.project_status = "progress"

        project2 = Mock()
        project2.id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        project2.project_name = "Song Project 2"
        project2.s3_prefix = "user/project-2/"
        project2.project_status = "completed"

        projects = [project1, project2]

        # Act
        result = transform_release_to_response(release, projects=projects)

        # Assert
        assert "assigned_projects" in result
        assert len(result["assigned_projects"]) == 2
        assert result["assigned_projects"][0]["id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        assert result["assigned_projects"][0]["project_name"] == "Song Project 1"
        assert result["assigned_projects"][1]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        assert result["assigned_projects"][1]["project_name"] == "Song Project 2"

    def test_transform_release_downtaken(self):
        """Test transforming downtaken release with all dates"""
        # Arrange
        release = Mock()
        release.id = UUID("12345678-1234-5678-1234-567812345678")
        release.user_id = UUID("87654321-4321-8765-4321-876543218765")
        release.type = "single"
        release.name = "Downtaken Song"
        release.status = "downtaken"
        release.genre = "Rock"
        release.description = "Was removed"
        release.tags = None
        release.upload_date = date(2024, 1, 1)
        release.release_date = date(2024, 1, 15)
        release.downtaken_date = date(2024, 2, 1)
        release.downtaken_reason = "Copyright claim"
        release.rejected_reason = None
        release.upc = "123456789012"
        release.isrc = "US-XXX-24-00001"
        release.copyright_info = "(C) 2024"
        release.cover_s3_key = "cover.jpg"
        release.created_at = datetime(2024, 1, 1, 10, 0, 0)
        release.updated_at = datetime(2024, 2, 1, 15, 0, 0)

        # Act
        result = transform_release_to_response(release)

        # Assert
        assert result["status"] == "downtaken"
        assert result["upload_date"] == "2024-01-01"
        assert result["release_date"] == "2024-01-15"
        assert result["downtaken_date"] == "2024-02-01"
        assert result["downtaken_reason"] == "Copyright claim"


class TestTransformReleaseToListResponse:
    """Tests for transform_release_to_list_response()"""

    def test_transform_list_response_complete(self):
        """Test transforming release to list item with all fields"""
        # Arrange
        release = Mock()
        release.id = UUID("12345678-1234-5678-1234-567812345678")
        release.name = "My Song"
        release.type = "single"
        release.status = "released"
        release.genre = "Rock"
        release.release_date = date(2024, 1, 15)
        release.cover_s3_key = "releases/user/release/cover.jpg"

        # Act
        result = transform_release_to_list_response(release)

        # Assert
        assert result == {
            "id": "12345678-1234-5678-1234-567812345678",
            "name": "My Song",
            "type": "single",
            "status": "released",
            "genre": "Rock",
            "release_date": "2024-01-15",
            "cover_url": "s3://releases/user/release/cover.jpg",
        }

    def test_transform_list_response_minimal(self):
        """Test transforming release to list item with minimal fields"""
        # Arrange
        release = Mock()
        release.id = UUID("11111111-1111-1111-1111-111111111111")
        release.name = "Draft Song"
        release.type = "album"
        release.status = "draft"
        release.genre = "Jazz"
        release.release_date = None
        release.cover_s3_key = None

        # Act
        result = transform_release_to_list_response(release)

        # Assert
        assert result == {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Draft Song",
            "type": "album",
            "status": "draft",
            "genre": "Jazz",
            "release_date": None,
            "cover_url": None,
        }


class TestTransformProjectToAssignedResponse:
    """Tests for transform_project_to_assigned_response()"""

    def test_transform_project_to_assigned_response(self):
        """Test transforming project to assigned response"""
        # Arrange
        project = Mock()
        project.id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        project.project_name = "My Song Project"
        project.s3_prefix = "user-1/my-song-project/"
        project.project_status = "progress"

        # Act
        result = transform_project_to_assigned_response(project)

        # Assert
        assert result == {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "project_name": "My Song Project",
            "s3_prefix": "user-1/my-song-project/",
            "project_status": "progress",
        }

    def test_transform_project_completed_status(self):
        """Test transforming completed project"""
        # Arrange
        project = Mock()
        project.id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
        project.project_name = "Finished Track"
        project.s3_prefix = "user-2/finished-track/"
        project.project_status = "completed"

        # Act
        result = transform_project_to_assigned_response(project)

        # Assert
        assert result["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        assert result["project_status"] == "completed"


class TestGetStatusFilterValues:
    """Tests for get_status_filter_values()"""

    def test_progress_filter(self):
        """Test progress filter returns correct statuses"""
        # Act
        result = get_status_filter_values("progress")

        # Assert
        assert result == ["arranging", "mixing", "mastering", "pre_release"]

    def test_uploaded_filter(self):
        """Test uploaded filter returns correct status"""
        # Act
        result = get_status_filter_values("uploaded")

        # Assert
        assert result == ["uploaded"]

    def test_released_filter(self):
        """Test released filter returns correct status"""
        # Act
        result = get_status_filter_values("released")

        # Assert
        assert result == ["released"]

    def test_archive_filter(self):
        """Test archive filter returns correct statuses"""
        # Act
        result = get_status_filter_values("archive")

        # Assert
        assert result == ["rejected", "downtaken", "archived"]

    def test_all_filter(self):
        """Test all filter returns None (no filtering)"""
        # Act
        result = get_status_filter_values("all")

        # Assert
        assert result is None

    def test_unknown_filter(self):
        """Test unknown filter returns None"""
        # Act
        result = get_status_filter_values("unknown_filter")

        # Assert
        assert result is None
