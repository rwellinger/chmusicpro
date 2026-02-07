"""Unit tests for equipment_transformer

Pure unit tests for business logic (no DB, no infrastructure).
"""

import pytest

from business.equipment_transformer import (
    BLOCKED_EXTENSIONS,
    MAX_FILE_SIZE,
    generate_s3_attachment_key,
    get_content_type_from_filename,
    validate_file_extension,
    validate_file_size,
)


@pytest.mark.unit
class TestValidateFileExtension:
    """Test validate_file_extension function"""

    def test_valid_extension_pdf(self):
        """Test that PDF files are allowed"""
        # Act
        is_valid, error = validate_file_extension("manual.pdf")

        # Assert
        assert is_valid is True
        assert error is None

    def test_valid_extension_image(self):
        """Test that image files are allowed"""
        # Act
        is_valid, error = validate_file_extension("photo.jpg")

        # Assert
        assert is_valid is True
        assert error is None

    def test_valid_extension_uppercase(self):
        """Test that uppercase extensions are handled correctly"""
        # Act
        is_valid, error = validate_file_extension("document.PDF")

        # Assert
        assert is_valid is True
        assert error is None

    def test_blocked_extension_exe(self):
        """Test that .exe files are blocked"""
        # Act
        is_valid, error = validate_file_extension("installer.exe")

        # Assert
        assert is_valid is False
        assert error == "File type '.exe' is not allowed (executables blocked)"

    def test_blocked_extension_bat(self):
        """Test that .bat files are blocked"""
        # Act
        is_valid, error = validate_file_extension("script.bat")

        # Assert
        assert is_valid is False
        assert error == "File type '.bat' is not allowed (executables blocked)"

    def test_blocked_extension_uppercase(self):
        """Test that blocked extensions are case-insensitive"""
        # Act
        is_valid, error = validate_file_extension("INSTALLER.EXE")

        # Assert
        assert is_valid is False
        assert error == "File type '.exe' is not allowed (executables blocked)"

    def test_no_extension(self):
        """Test that files without extension are rejected"""
        # Act
        is_valid, error = validate_file_extension("readme")

        # Assert
        assert is_valid is False
        assert error == "File must have an extension"

    def test_all_blocked_extensions(self):
        """Test that all blocked extensions are rejected"""
        for ext in BLOCKED_EXTENSIONS:
            is_valid, error = validate_file_extension(f"file.{ext}")
            assert is_valid is False, f"Extension .{ext} should be blocked"
            assert "not allowed" in error


@pytest.mark.unit
class TestValidateFileSize:
    """Test validate_file_size function"""

    def test_valid_size_small(self):
        """Test that small files are valid"""
        # Act
        is_valid, error = validate_file_size(1024)  # 1 KB

        # Assert
        assert is_valid is True
        assert error is None

    def test_valid_size_at_limit(self):
        """Test that files exactly at the limit are valid"""
        # Act
        is_valid, error = validate_file_size(MAX_FILE_SIZE)

        # Assert
        assert is_valid is True
        assert error is None

    def test_invalid_size_over_limit(self):
        """Test that files over the limit are rejected"""
        # Act
        is_valid, error = validate_file_size(MAX_FILE_SIZE + 1)

        # Assert
        assert is_valid is False
        assert error == "File size exceeds 50 MB limit"

    def test_invalid_size_way_over_limit(self):
        """Test that large files are rejected"""
        # Act
        is_valid, error = validate_file_size(100 * 1024 * 1024)  # 100 MB

        # Assert
        assert is_valid is False
        assert "exceeds" in error

    def test_zero_size(self):
        """Test that zero-byte files are valid"""
        # Act
        is_valid, error = validate_file_size(0)

        # Assert
        assert is_valid is True
        assert error is None


@pytest.mark.unit
class TestGenerateS3AttachmentKey:
    """Test generate_s3_attachment_key function"""

    def test_basic_key_generation(self):
        """Test basic S3 key generation"""
        # Act
        key = generate_s3_attachment_key("user123", "eq456", "att789", "manual.pdf")

        # Assert
        assert key == "user123/eq456/att789_manual.pdf"

    def test_filename_with_spaces(self):
        """Test that spaces in filenames are converted to underscores"""
        # Act
        key = generate_s3_attachment_key("user1", "eq1", "att1", "my document.pdf")

        # Assert
        assert key == "user1/eq1/att1_my_document.pdf"

    def test_filename_with_slashes(self):
        """Test that slashes in filenames are converted to underscores"""
        # Act
        key = generate_s3_attachment_key("user1", "eq1", "att1", "path/to/file.pdf")

        # Assert
        assert key == "user1/eq1/att1_path_to_file.pdf"

    def test_filename_with_multiple_special_chars(self):
        """Test that multiple special characters are handled"""
        # Act
        key = generate_s3_attachment_key("user1", "eq1", "att1", "my file/name here.pdf")

        # Assert
        assert key == "user1/eq1/att1_my_file_name_here.pdf"

    def test_uuid_style_ids(self):
        """Test with UUID-style IDs"""
        # Act
        key = generate_s3_attachment_key(
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
            "document.pdf",
        )

        # Assert
        assert key == (
            "550e8400-e29b-41d4-a716-446655440000/"
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8/"
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8_document.pdf"
        )


@pytest.mark.unit
class TestGetContentTypeFromFilename:
    """Test get_content_type_from_filename function"""

    def test_pdf_mime_type(self):
        """Test PDF MIME type detection"""
        # Act
        content_type = get_content_type_from_filename("document.pdf")

        # Assert
        assert content_type == "application/pdf"

    def test_png_mime_type(self):
        """Test PNG MIME type detection"""
        # Act
        content_type = get_content_type_from_filename("image.png")

        # Assert
        assert content_type == "image/png"

    def test_jpeg_mime_type(self):
        """Test JPEG MIME type detection"""
        # Act
        content_type = get_content_type_from_filename("photo.jpg")

        # Assert
        assert content_type == "image/jpeg"

    def test_jpeg_alternative_extension(self):
        """Test JPEG with .jpeg extension"""
        # Act
        content_type = get_content_type_from_filename("photo.jpeg")

        # Assert
        assert content_type == "image/jpeg"

    def test_text_mime_type(self):
        """Test text file MIME type detection"""
        # Act
        content_type = get_content_type_from_filename("readme.txt")

        # Assert
        assert content_type == "text/plain"

    def test_unknown_extension(self):
        """Test that unknown extensions return octet-stream"""
        # Act
        content_type = get_content_type_from_filename("file.xyz123unknown")

        # Assert
        assert content_type == "application/octet-stream"

    def test_no_extension(self):
        """Test that files without extension return octet-stream"""
        # Act
        content_type = get_content_type_from_filename("noextension")

        # Assert
        assert content_type == "application/octet-stream"
