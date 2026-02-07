"""Tests for SongProjectTransformer - Business logic unit tests (100% coverage)"""

from unittest.mock import Mock

from business.song_project_transformer import (
    calculate_file_hash,
    calculate_pagination_meta,
    detect_file_type,
    generate_s3_prefix,
    get_default_folder_structure,
    get_display_cover_info,
    get_mime_type,
    normalize_project_name,
    transform_file_to_response,
    transform_folder_to_response,
    transform_project_detail_to_response,
    transform_project_to_response,
    validate_project_status,
)


class TestGenerateS3Prefix:
    """Test generate_s3_prefix() - slug generation from project name"""

    def test_basic_slug_generation(self):
        """Generate slug from simple project name"""
        project_name = "My Awesome Song"
        user_id = "test-user-123"

        result = generate_s3_prefix(project_name, user_id)

        assert result == "test-user-123/my-awesome-song/"

    def test_special_characters_removed(self):
        """Special characters are replaced with hyphens"""
        project_name = "Café Müller (2024)"
        user_id = "test-user-123"

        result = generate_s3_prefix(project_name, user_id)

        # Umlauts and special chars are removed (not transliterated)
        assert result == "test-user-123/caf-m-ller-2024/"

    def test_multiple_spaces_collapsed(self):
        """Multiple spaces/hyphens are collapsed to single hyphen"""
        project_name = "My    Song  -  Project"
        user_id = "test-user-123"

        result = generate_s3_prefix(project_name, user_id)

        assert result == "test-user-123/my-song-project/"

    def test_leading_trailing_hyphens_removed(self):
        """Leading and trailing hyphens are removed"""
        project_name = "---My Song---"
        user_id = "test-user-123"

        result = generate_s3_prefix(project_name, user_id)

        assert result == "test-user-123/my-song/"

    def test_numbers_preserved(self):
        """Numbers are preserved in slug"""
        project_name = "Song 2024 v3"
        user_id = "test-user-123"

        result = generate_s3_prefix(project_name, user_id)

        assert result == "test-user-123/song-2024-v3/"

    def test_empty_string_handling(self):
        """Empty string produces user_id/ prefix with empty slug"""
        project_name = ""
        user_id = "test-user-123"

        result = generate_s3_prefix(project_name, user_id)

        assert result == "test-user-123//"


class TestGetDefaultFolderStructure:
    """Test get_default_folder_structure() - folder list generation"""

    def test_returns_list(self):
        """Returns a list of folder definitions"""
        result = get_default_folder_structure()

        assert isinstance(result, list)

    def test_has_10_folders(self):
        """Returns exactly 10 default folders"""
        result = get_default_folder_structure()

        assert len(result) == 10

    def test_folder_structure_format(self):
        """Each folder has required keys"""
        result = get_default_folder_structure()

        for folder in result:
            assert "folder_name" in folder
            assert "folder_type" in folder
            assert "custom_icon" in folder

    def test_folder_names_ordered(self):
        """Folders are numbered 01-10"""
        result = get_default_folder_structure()

        assert result[0]["folder_name"] == "01 Arrangement"
        assert result[1]["folder_name"] == "02 AI"
        assert result[9]["folder_name"] == "10 Archive"

    def test_folder_types_assigned(self):
        """Each folder has a unique type"""
        result = get_default_folder_structure()

        folder_types = [f["folder_type"] for f in result]
        assert "arrangement" in folder_types
        assert "ai" in folder_types
        assert "pictures" in folder_types

    def test_icons_use_font_awesome(self):
        """Icons use Font Awesome classes"""
        result = get_default_folder_structure()

        for folder in result:
            assert folder["custom_icon"].startswith("fas fa-")


class TestDetectFileType:
    """Test detect_file_type() - file type detection from extension"""

    def test_audio_files(self):
        """Detects audio file extensions"""
        assert detect_file_type("song.mp3") == "audio"
        assert detect_file_type("track.wav") == "audio"
        assert detect_file_type("music.flac") == "audio"
        assert detect_file_type("audio.m4a") == "audio"

    def test_image_files(self):
        """Detects image file extensions"""
        assert detect_file_type("cover.jpg") == "image"
        assert detect_file_type("photo.png") == "image"
        assert detect_file_type("graphic.svg") == "image"
        assert detect_file_type("pic.webp") == "image"

    def test_document_files(self):
        """Detects document file extensions"""
        assert detect_file_type("lyrics.txt") == "document"
        assert detect_file_type("notes.pdf") == "document"
        assert detect_file_type("readme.md") == "document"
        assert detect_file_type("doc.docx") == "document"

    def test_archive_files(self):
        """Detects archive file extensions"""
        assert detect_file_type("project.zip") == "archive"
        assert detect_file_type("backup.rar") == "archive"
        assert detect_file_type("files.7z") == "archive"

    def test_video_files(self):
        """Detects video file extensions"""
        assert detect_file_type("promo.mp4") == "video"
        assert detect_file_type("clip.avi") == "video"
        assert detect_file_type("video.mkv") == "video"

    def test_unknown_extension(self):
        """Returns 'other' for unknown extensions"""
        assert detect_file_type("file.xyz") == "other"
        assert detect_file_type("unknown.abc") == "other"

    def test_no_extension(self):
        """Handles files without extension"""
        assert detect_file_type("README") == "other"

    def test_case_insensitive(self):
        """File type detection is case-insensitive"""
        assert detect_file_type("SONG.MP3") == "audio"
        assert detect_file_type("Cover.JPG") == "image"


class TestGetMimeType:
    """Test get_mime_type() - MIME type detection from extension"""

    def test_audio_mime_types(self):
        """Returns correct MIME types for audio files"""
        assert get_mime_type("song.mp3") == "audio/mpeg"
        assert get_mime_type("track.wav") == "audio/wav"
        assert get_mime_type("music.flac") == "audio/flac"
        assert get_mime_type("audio.m4a") == "audio/mp4"

    def test_image_mime_types(self):
        """Returns correct MIME types for image files"""
        assert get_mime_type("cover.jpg") == "image/jpeg"
        assert get_mime_type("photo.png") == "image/png"
        assert get_mime_type("graphic.svg") == "image/svg+xml"
        assert get_mime_type("pic.webp") == "image/webp"

    def test_document_mime_types(self):
        """Returns correct MIME types for documents"""
        assert get_mime_type("notes.txt") == "text/plain"
        assert get_mime_type("doc.pdf") == "application/pdf"
        assert get_mime_type("file.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_archive_mime_types(self):
        """Returns correct MIME types for archives"""
        assert get_mime_type("project.zip") == "application/zip"
        assert get_mime_type("backup.rar") == "application/x-rar-compressed"

    def test_video_mime_types(self):
        """Returns correct MIME types for video files"""
        assert get_mime_type("promo.mp4") == "video/mp4"
        assert get_mime_type("clip.avi") == "video/x-msvideo"

    def test_unknown_extension_returns_none(self):
        """Returns None for unknown extensions"""
        assert get_mime_type("file.xyz") is None
        assert get_mime_type("unknown.abc") is None

    def test_no_extension_returns_none(self):
        """Returns None for files without extension"""
        assert get_mime_type("README") is None

    def test_case_insensitive(self):
        """MIME type detection is case-insensitive"""
        assert get_mime_type("SONG.MP3") == "audio/mpeg"
        assert get_mime_type("Cover.JPG") == "image/jpeg"


class TestTransformProjectToResponse:
    """Test transform_project_to_response() - project to API response"""

    def test_basic_transformation(self):
        """Transforms project model to response dict"""
        project = Mock()
        project.id = "550e8400-e29b-41d4-a716-446655440000"
        project.project_name = "My Project"
        project.s3_prefix = "projects/my-project/"
        project.cover_image_id = None
        project.tags = ["rock", "demo"]
        project.description = "A test project"
        project.project_status = "progress"
        project.created_at = Mock()
        project.created_at.isoformat.return_value = "2024-01-01T12:00:00"
        project.updated_at = Mock()
        project.updated_at.isoformat.return_value = "2024-01-02T12:00:00"

        result = transform_project_to_response(project)

        assert result["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["project_name"] == "My Project"
        assert result["s3_prefix"] == "projects/my-project/"
        assert result["tags"] == ["rock", "demo"]
        assert result["description"] == "A test project"
        assert result["project_status"] == "progress"
        assert result["created_at"] == "2024-01-01T12:00:00"
        assert result["updated_at"] == "2024-01-02T12:00:00"

    def test_null_timestamps(self):
        """Handles None timestamps correctly"""
        project = Mock()
        project.id = "550e8400-e29b-41d4-a716-446655440000"
        project.project_name = "Test"
        project.s3_prefix = None
        project.cover_image_id = None
        project.tags = []
        project.description = None
        project.project_status = "new"
        project.created_at = None
        project.updated_at = None

        result = transform_project_to_response(project)

        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["project_status"] == "new"


class TestTransformFolderToResponse:
    """Test transform_folder_to_response() - folder to API response"""

    def test_basic_transformation(self):
        """Transforms folder model to response dict"""
        folder = Mock()
        folder.id = "folder-id-123"
        folder.folder_name = "01 Arrangement"
        folder.folder_type = "arrangement"
        folder.s3_prefix = "projects/test/01 Arrangement/"
        folder.custom_icon = "fas fa-music"
        folder.created_at = Mock()
        folder.created_at.isoformat.return_value = "2024-01-01T12:00:00"

        result = transform_folder_to_response(folder)

        assert result["id"] == "folder-id-123"
        assert result["folder_name"] == "01 Arrangement"
        assert result["folder_type"] == "arrangement"
        assert result["s3_prefix"] == "projects/test/01 Arrangement/"
        assert result["custom_icon"] == "fas fa-music"
        assert result["created_at"] == "2024-01-01T12:00:00"


class TestTransformFileToResponse:
    """Test transform_file_to_response() - file to API response"""

    def test_basic_transformation(self):
        """Transforms file model to response dict"""
        file = Mock()
        file.id = "file-id-123"
        file.filename = "song.mp3"
        file.relative_path = "01 Arrangement/song.mp3"
        file.file_type = "audio"
        file.mime_type = "audio/mpeg"
        file.file_size_bytes = 5000000
        file.is_synced = True
        file.created_at = Mock()
        file.created_at.isoformat.return_value = "2024-01-01T12:00:00"
        file.updated_at = Mock()
        file.updated_at.isoformat.return_value = "2024-01-02T12:00:00"

        result = transform_file_to_response(file, download_url="https://s3.example.com/song.mp3")

        assert result["id"] == "file-id-123"
        assert result["filename"] == "song.mp3"
        assert result["relative_path"] == "01 Arrangement/song.mp3"
        assert result["file_type"] == "audio"
        assert result["mime_type"] == "audio/mpeg"
        assert result["file_size_bytes"] == 5000000
        assert result["is_synced"] is True
        assert result["download_url"] == "https://s3.example.com/song.mp3"
        assert result["created_at"] == "2024-01-01T12:00:00"
        assert result["updated_at"] == "2024-01-02T12:00:00"

    def test_without_download_url(self):
        """Handles missing download URL"""
        file = Mock()
        file.id = "file-id-123"
        file.filename = "song.mp3"
        file.relative_path = "song.mp3"
        file.file_type = "audio"
        file.mime_type = "audio/mpeg"
        file.file_size_bytes = 5000000
        file.is_synced = False
        file.created_at = None
        file.updated_at = None

        result = transform_file_to_response(file)

        assert result["filename"] == "song.mp3"
        assert result["is_synced"] is False
        assert result["download_url"] is None


class TestTransformProjectDetailToResponse:
    """Test transform_project_detail_to_response() - project with folders and files"""

    def test_basic_transformation(self):
        """Transforms project with folders and files"""
        # Create mock file
        file = Mock()
        file.id = "file-id"
        file.filename = "song.mp3"
        file.relative_path = "01 Arrangement/song.mp3"
        file.file_type = "audio"
        file.mime_type = "audio/mpeg"
        file.file_size_bytes = 5000000
        file.storage_backend = "s3"
        file.s3_key = "user-id/project/01 Arrangement/song.mp3"
        file.is_synced = True
        file.created_at = None
        file.updated_at = None

        # Create mock folder
        folder = Mock()
        folder.id = "folder-id"
        folder.folder_name = "01 Arrangement"
        folder.folder_type = "arrangement"
        folder.s3_prefix = "projects/test/01 Arrangement/"
        folder.custom_icon = "fas fa-music"
        folder.created_at = None
        folder.files = [file]

        # Create mock project
        project = Mock()
        project.id = "project-id"
        project.project_name = "Test Project"
        project.s3_prefix = "projects/test/"
        project.local_path = None
        project.sync_status = "local"
        project.last_sync_at = None
        project.cover_image_id = None
        project.tags = []
        project.description = None
        project.total_files = 1
        project.total_size_bytes = 5000000
        project.created_at = None
        project.updated_at = None
        project.folders = [folder]

        result = transform_project_detail_to_response(project)

        assert result["id"] == "project-id"
        assert result["project_name"] == "Test Project"
        assert len(result["folders"]) == 1
        assert result["folders"][0]["folder_name"] == "01 Arrangement"
        assert len(result["folders"][0]["files"]) == 1
        assert result["folders"][0]["files"][0]["filename"] == "song.mp3"


class TestCalculatePaginationMeta:
    """Test calculate_pagination_meta() - pagination metadata calculation"""

    def test_has_more_true(self):
        """Returns has_more=True when more items exist"""
        result = calculate_pagination_meta(total=100, limit=20, offset=0)

        assert result["total"] == 100
        assert result["limit"] == 20
        assert result["offset"] == 0
        assert result["has_more"] is True

    def test_has_more_false(self):
        """Returns has_more=False when no more items"""
        result = calculate_pagination_meta(total=15, limit=20, offset=0)

        assert result["total"] == 15
        assert result["limit"] == 20
        assert result["offset"] == 0
        assert result["has_more"] is False

    def test_has_more_at_boundary(self):
        """Returns has_more=False when exactly at last item"""
        result = calculate_pagination_meta(total=20, limit=20, offset=0)

        assert result["has_more"] is False

    def test_has_more_with_offset(self):
        """Calculates has_more correctly with offset"""
        result = calculate_pagination_meta(total=100, limit=20, offset=80)

        assert result["has_more"] is False  # 80 + 20 = 100


class TestNormalizeProjectName:
    """Test normalize_project_name() - string normalization"""

    def test_trims_whitespace(self):
        """Removes leading and trailing whitespace"""
        assert normalize_project_name("  My Project  ") == "My Project"

    def test_empty_string(self):
        """Handles empty string"""
        assert normalize_project_name("") == ""

    def test_whitespace_only(self):
        """Handles whitespace-only string"""
        assert normalize_project_name("   ") == ""

    def test_no_changes_needed(self):
        """Returns unchanged if already normalized"""
        assert normalize_project_name("My Project") == "My Project"


class TestCalculateFileHash:
    """Test calculate_file_hash() - SHA256 hash calculation for Mirror sync"""

    def test_basic_hash_calculation(self):
        """Calculates SHA256 hash for simple input"""
        file_data = b"Hello World"

        result = calculate_file_hash(file_data)

        assert result == "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"

    def test_empty_file(self):
        """Handles empty file (0 bytes)"""
        file_data = b""

        result = calculate_file_hash(file_data)

        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_hash_length(self):
        """Hash is always 64 characters (SHA256 hex)"""
        file_data = b"Test data"

        result = calculate_file_hash(file_data)

        assert len(result) == 64

    def test_deterministic_hash(self):
        """Same input produces same hash (deterministic)"""
        file_data = b"Consistent data"

        result1 = calculate_file_hash(file_data)
        result2 = calculate_file_hash(file_data)

        assert result1 == result2

    def test_different_input_different_hash(self):
        """Different inputs produce different hashes"""
        data1 = b"File version 1"
        data2 = b"File version 2"

        hash1 = calculate_file_hash(data1)
        hash2 = calculate_file_hash(data2)

        assert hash1 != hash2

    def test_binary_data(self):
        """Handles binary data (not just text)"""
        # Simulate FLAC header bytes
        file_data = b"\x66\x4c\x61\x43\x00\x00\x00\x22"

        result = calculate_file_hash(file_data)

        assert len(result) == 64
        assert isinstance(result, str)

    def test_large_file_simulation(self):
        """Handles larger data chunks (simulate file data)"""
        # Simulate 1MB of data
        file_data = b"A" * (1024 * 1024)

        result = calculate_file_hash(file_data)

        assert len(result) == 64
        # Verify deterministic (same input = same hash)
        result2 = calculate_file_hash(file_data)
        assert result == result2


class TestValidateProjectStatus:
    """Test validate_project_status() - Enum validation for project status"""

    def test_valid_status_new(self):
        """Validates 'new' status"""
        assert validate_project_status("new") is True

    def test_valid_status_progress(self):
        """Validates 'progress' status"""
        assert validate_project_status("progress") is True

    def test_valid_status_archived(self):
        """Validates 'archived' status"""
        assert validate_project_status("archived") is True

    def test_invalid_status(self):
        """Rejects invalid status"""
        assert validate_project_status("invalid") is False

    def test_invalid_status_empty(self):
        """Rejects empty status"""
        assert validate_project_status("") is False

    def test_invalid_status_case_sensitive(self):
        """Status validation is case-sensitive"""
        assert validate_project_status("NEW") is False
        assert validate_project_status("Progress") is False
        assert validate_project_status("ARCHIVED") is False


class TestGetDisplayCoverInfo:
    """Test get_display_cover_info() - Cover display logic for Song Projects"""

    def test_no_releases_returns_placeholder(self):
        """Returns placeholder when no releases are assigned"""
        releases = []

        result = get_display_cover_info(releases)

        assert result == {"source": "placeholder", "release_id": None, "release_name": None}

    def test_single_valid_release(self):
        """Returns release info for single valid release"""
        release = Mock()
        release.id = "abc-123"
        release.name = "Summer EP"
        release.status = "released"
        release.release_date = "2024-06-01"

        result = get_display_cover_info([release])

        assert result == {"source": "release", "release_id": "abc-123", "release_name": "Summer EP"}

    def test_multiple_releases_selects_newest(self):
        """Selects release with highest release_date when multiple exist"""
        old_release = Mock()
        old_release.id = "old-123"
        old_release.name = "Old Release"
        old_release.status = "released"
        old_release.release_date = "2023-01-01"

        new_release = Mock()
        new_release.id = "new-456"
        new_release.name = "New Release"
        new_release.status = "uploaded"
        new_release.release_date = "2024-12-01"

        result = get_display_cover_info([old_release, new_release])

        assert result == {"source": "release", "release_id": "new-456", "release_name": "New Release"}

    def test_filters_rejected_status(self):
        """Filters out releases with 'rejected' status"""
        rejected = Mock()
        rejected.id = "rejected-123"
        rejected.name = "Rejected EP"
        rejected.status = "rejected"
        rejected.release_date = "2024-01-01"

        result = get_display_cover_info([rejected])

        assert result == {"source": "placeholder", "release_id": None, "release_name": None}

    def test_filters_downtaken_status(self):
        """Filters out releases with 'downtaken' status"""
        downtaken = Mock()
        downtaken.id = "downtaken-123"
        downtaken.name = "Downtaken Album"
        downtaken.status = "downtaken"
        downtaken.release_date = "2024-03-01"

        result = get_display_cover_info([downtaken])

        assert result == {"source": "placeholder", "release_id": None, "release_name": None}

    def test_filters_archived_status(self):
        """Filters out releases with 'archived' status"""
        archived = Mock()
        archived.id = "archived-123"
        archived.name = "Archived Release"
        archived.status = "archived"
        archived.release_date = "2024-02-01"

        result = get_display_cover_info([archived])

        assert result == {"source": "placeholder", "release_id": None, "release_name": None}

    def test_mixed_valid_and_invalid_selects_valid(self):
        """Selects valid release when mixed with invalid statuses"""
        rejected = Mock()
        rejected.id = "rejected-123"
        rejected.name = "Rejected EP"
        rejected.status = "rejected"
        rejected.release_date = "2024-05-01"

        valid = Mock()
        valid.id = "valid-456"
        valid.name = "Valid Album"
        valid.status = "released"
        valid.release_date = "2024-03-01"

        result = get_display_cover_info([rejected, valid])

        assert result == {"source": "release", "release_id": "valid-456", "release_name": "Valid Album"}

    def test_handles_none_release_date(self):
        """Handles releases with None release_date (treats as very old)"""
        no_date = Mock()
        no_date.id = "no-date-123"
        no_date.name = "Draft Release"
        no_date.status = "draft"
        no_date.release_date = None

        with_date = Mock()
        with_date.id = "with-date-456"
        with_date.name = "Scheduled Release"
        with_date.status = "uploaded"
        with_date.release_date = "2024-12-01"

        result = get_display_cover_info([no_date, with_date])

        # Should select the one with actual date (newer)
        assert result == {"source": "release", "release_id": "with-date-456", "release_name": "Scheduled Release"}

    def test_all_releases_have_none_date_selects_first(self):
        """Selects first release when all have None release_date"""
        release1 = Mock()
        release1.id = "release1"
        release1.name = "Release 1"
        release1.status = "draft"
        release1.release_date = None

        release2 = Mock()
        release2.id = "release2"
        release2.name = "Release 2"
        release2.status = "draft"
        release2.release_date = None

        result = get_display_cover_info([release1, release2])

        # Should return one of them (order doesn't matter if all None)
        assert result["source"] == "release"
        assert result["release_id"] in ["release1", "release2"]

    def test_sorts_chronologically_newest_first(self):
        """Verifies newest release_date is selected (DESC order)"""
        release1 = Mock()
        release1.id = "2023-release"
        release1.name = "2023 Album"
        release1.status = "released"
        release1.release_date = "2023-06-15"

        release2 = Mock()
        release2.id = "2024-release"
        release2.name = "2024 Single"
        release2.status = "uploaded"
        release2.release_date = "2024-01-10"

        release3 = Mock()
        release3.id = "2024-latest"
        release3.name = "2024 Latest"
        release3.status = "mastering"
        release3.release_date = "2024-11-20"

        result = get_display_cover_info([release1, release2, release3])

        # Should select the chronologically latest (2024-11-20)
        assert result == {"source": "release", "release_id": "2024-latest", "release_name": "2024 Latest"}

    def test_accepts_various_valid_statuses(self):
        """Accepts all valid statuses except rejected/downtaken/archived"""
        valid_statuses = ["draft", "arranging", "mixing", "mastering", "uploaded", "released"]

        for status in valid_statuses:
            release = Mock()
            release.id = f"{status}-id"
            release.name = f"{status} Release"
            release.status = status
            release.release_date = "2024-01-01"

            result = get_display_cover_info([release])

            assert result["source"] == "release", f"Status '{status}' should be valid"
            assert result["release_id"] == f"{status}-id"
