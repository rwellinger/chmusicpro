"""
Encryption Service for sensitive data (passwords, license keys, prices).

Uses Fernet symmetric encryption (AES-128) for reversible encryption.
This is DIFFERENT from password hashing (bcrypt) which is one-way.

Usage:
    from business.encryption_service import encryption_service

    # Encrypt
    encrypted = encryption_service.encrypt("my-secret")

    # Decrypt
    decrypted = encryption_service.decrypt(encrypted)
"""

from cryptography.fernet import Fernet, InvalidToken

from config.settings import ENCRYPTION_SECRET_KEY
from utils.logger import logger


class EncryptionService:
    """Service for reversible encryption/decryption of sensitive data"""

    def __init__(self, secret_key: str):
        """
        Initialize encryption service with secret key.

        Args:
            secret_key: Base64-encoded 32-byte key (generate with Fernet.generate_key())

        Raises:
            ValueError: If secret_key is invalid
        """
        try:
            self.cipher = Fernet(secret_key.encode())
            logger.debug("Encryption service initialized")
        except Exception as e:
            logger.error("Failed to initialize encryption service", error=str(e))
            raise ValueError(f"Invalid encryption key: {str(e)}")

    def encrypt(self, plaintext: str | None) -> str | None:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None/empty

        Example:
            >>> service.encrypt("my-password")
            'gAAAAABh...'
        """
        if not plaintext:
            return None

        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode("utf-8"))
            encrypted_str = encrypted_bytes.decode("utf-8")
            logger.debug("Data encrypted", length=len(plaintext))
            return encrypted_str
        except Exception as e:
            logger.error("Encryption failed", error=str(e), error_type=type(e).__name__)
            raise

    def decrypt(self, ciphertext: str | None) -> str | None:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string, or None if input is None/empty

        Raises:
            InvalidToken: If ciphertext is invalid or corrupted

        Example:
            >>> service.decrypt('gAAAAABh...')
            'my-password'
        """
        if not ciphertext:
            return None

        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode("utf-8"))
            decrypted_str = decrypted_bytes.decode("utf-8")
            logger.debug("Data decrypted")
            return decrypted_str
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or corrupted data")
            raise
        except Exception as e:
            logger.error("Decryption failed", error=str(e), error_type=type(e).__name__)
            raise


# Global instance (initialized with key from environment)
# Only initialize if key is present (allows tests to create their own instances)
encryption_service = EncryptionService(ENCRYPTION_SECRET_KEY) if ENCRYPTION_SECRET_KEY else None
