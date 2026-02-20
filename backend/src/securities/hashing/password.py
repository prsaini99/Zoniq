from src.securities.hashing.hash import hash_generator


# High-level password utility that wraps HashGenerator for salt generation, hashing, and verification
class PasswordGenerator:
    # Generate a new Bcrypt-based salt hash for a user's password
    @property
    def generate_salt(self) -> str:
        return hash_generator.generate_password_salt_hash

    # Hash a new password by combining the salt with the raw password through the two-layer scheme
    def generate_hashed_password(self, hash_salt: str, new_password: str) -> str:
        return hash_generator.generate_password_hash(hash_salt=hash_salt, password=new_password)

    # Verify a login password by reconstructing the salted input and comparing against the stored hash
    def is_password_authenticated(self, hash_salt: str, password: str, hashed_password: str) -> bool:
        return hash_generator.is_password_verified(password=hash_salt + password, hashed_password=hashed_password)


# Factory function to create a new PasswordGenerator instance
def get_pwd_generator() -> PasswordGenerator:
    return PasswordGenerator()


# Module-level singleton instance — shared across the application for password operations
pwd_generator: PasswordGenerator = get_pwd_generator()
