from passlib.context import CryptContext

from src.config.manager import settings


# Provides two-layer password hashing: layer 1 (Bcrypt) generates a salt, layer 2 (Argon2) hashes the final password
class HashGenerator:
    # Initialize both hashing context layers and the static salt from application settings
    def __init__(self):
        # Layer 1 hashing context — uses Bcrypt to generate a per-password salt hash
        self._hash_ctx_layer_1: CryptContext = CryptContext(
            schemes=[settings.HASHING_ALGORITHM_LAYER_1], deprecated="auto"
        )
        # Layer 2 hashing context — uses Argon2 to produce the final stored password hash
        self._hash_ctx_layer_2: CryptContext = CryptContext(
            schemes=[settings.HASHING_ALGORITHM_LAYER_2], deprecated="auto"
        )
        # Static salt value from configuration, used as input to layer 1 hashing
        self._hash_ctx_salt: str = settings.HASHING_SALT

    # Return the static hashing salt from settings
    @property
    def _get_hashing_salt(self) -> str:
        return self._hash_ctx_salt

    # Generate a Bcrypt hash of the static salt to use as a per-password salt prefix
    @property
    def generate_password_salt_hash(self) -> str:
        """
        A function to generate a hash from Bcrypt to append to the user password.
        """
        return self._hash_ctx_layer_1.hash(secret=self._get_hashing_salt)

    # Hash the password by combining the salt hash with the raw password, then hashing with Argon2
    def generate_password_hash(self, hash_salt: str, password: str) -> str:
        """
        A function that adds the user's password with the layer 1 Bcrypt hash, before
        hash it for the second time using Argon2 algorithm.
        """
        return self._hash_ctx_layer_2.hash(secret=hash_salt + password)

    # Verify a raw password against the stored Argon2 hash
    def is_password_verified(self, password: str, hashed_password: str) -> bool:
        """
        A function that decodes users' password and verifies whether it is the correct password.
        """
        return self._hash_ctx_layer_2.verify(secret=password, hash=hashed_password)


# Factory function to create a new HashGenerator instance
def get_hash_generator() -> HashGenerator:
    return HashGenerator()


# Module-level singleton instance — shared across the application for password hashing
hash_generator: HashGenerator = get_hash_generator()
