"""
Unit tests for EncryptionService (Fernet symmetric encryption).

CRITICAL: 100% coverage for pure business logic (per CLAUDE.md).
"""

import pytest
from cryptography.fernet import Fernet, InvalidToken

from business.encryption_service import EncryptionService


@pytest.fixture
def encryption_service():
    """Create encryption service with test key"""
    test_key = Fernet.generate_key().decode()
    return EncryptionService(test_key)


def test_encrypt_decrypt_success(encryption_service):
    """Test successful encryption and decryption roundtrip"""
    plaintext = "my-secret-password"
    encrypted = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(encrypted)

    assert encrypted != plaintext, "Encrypted text should differ from plaintext"
    assert decrypted == plaintext, "Decrypted text should match original plaintext"


def test_encrypt_none(encryption_service):
    """Test that None input returns None"""
    assert encryption_service.encrypt(None) is None


def test_decrypt_none(encryption_service):
    """Test that None input returns None"""
    assert encryption_service.decrypt(None) is None


def test_encrypt_empty_string(encryption_service):
    """Test that empty string returns None"""
    assert encryption_service.encrypt("") is None


def test_encrypt_whitespace_only(encryption_service):
    """Test that whitespace-only string is encrypted (not None)"""
    result = encryption_service.encrypt("   ")
    assert result is not None, "Whitespace-only string should be encrypted"


def test_decrypt_invalid_token(encryption_service):
    """Test that invalid token raises InvalidToken exception"""
    with pytest.raises(InvalidToken):
        encryption_service.decrypt("invalid-token-123")


def test_decrypt_wrong_key():
    """Test that decryption with wrong key fails"""
    # Encrypt with one key
    key1 = Fernet.generate_key().decode()
    service1 = EncryptionService(key1)
    encrypted = service1.encrypt("secret")

    # Try to decrypt with different key
    key2 = Fernet.generate_key().decode()
    service2 = EncryptionService(key2)

    with pytest.raises(InvalidToken):
        service2.decrypt(encrypted)


def test_encrypt_decrypt_unicode(encryption_service):
    """Test encryption/decryption with unicode characters"""
    plaintext = "Passwört mit Ümlæut 日本語"
    encrypted = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(encrypted)

    assert decrypted == plaintext, "Unicode characters should be preserved"


def test_encrypt_decrypt_special_characters(encryption_service):
    """Test encryption/decryption with special characters"""
    plaintext = "P@$$w0rd!#%&*()_+-=[]{}|;:',.<>?/~`"
    encrypted = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(encrypted)

    assert decrypted == plaintext, "Special characters should be preserved"


def test_encrypt_decrypt_long_string(encryption_service):
    """Test encryption/decryption with long string"""
    plaintext = "A" * 10000  # 10KB string
    encrypted = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(encrypted)

    assert decrypted == plaintext, "Long strings should be preserved"


def test_invalid_key_initialization():
    """Test that invalid key raises ValueError"""
    with pytest.raises(ValueError):
        EncryptionService("invalid-key")


def test_encrypt_multiple_times_different_result(encryption_service):
    """Test that encrypting same plaintext multiple times produces different ciphertext (IV randomization)"""
    plaintext = "test-password"
    encrypted1 = encryption_service.encrypt(plaintext)
    encrypted2 = encryption_service.encrypt(plaintext)

    # Fernet uses random IV, so same plaintext produces different ciphertext
    assert encrypted1 != encrypted2, "Same plaintext should produce different ciphertext (random IV)"

    # But both should decrypt to same plaintext
    assert encryption_service.decrypt(encrypted1) == plaintext
    assert encryption_service.decrypt(encrypted2) == plaintext
