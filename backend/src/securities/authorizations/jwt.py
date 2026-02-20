import datetime

import pydantic
from jose import jwt as jose_jwt, JWTError as JoseJWTError

from src.config.manager import settings
from src.models.db.account import Account
from src.models.schemas.jwt import JWTAccount, JWToken
from src.utilities.exceptions.database import EntityDoesNotExist


# Handles JWT token generation and decoding for user authentication
class JWTGenerator:
    def __init__(self):
        pass

    # Internal method to create a signed JWT token with an expiry time
    def _generate_jwt_token(
        self,
        *,
        jwt_data: dict[str, str],
        expires_delta: datetime.timedelta | None = None,
    ) -> str:
        to_encode = jwt_data.copy()

        # Use custom expiry delta if provided, otherwise fall back to default JWT_MIN from settings
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta

        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_MIN)

        # Merge expiry timestamp and subject into the token payload
        to_encode.update(JWToken(exp=expire, sub=settings.JWT_SUBJECT).dict())

        # Encode and sign the JWT using the configured secret key and algorithm
        return jose_jwt.encode(to_encode, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Generate an access token for an authenticated user account
    def generate_access_token(self, account: Account) -> str:
        # Ensure the account entity exists before token generation
        if not account:
            raise EntityDoesNotExist(f"Cannot generate JWT token for without Account entity!")

        # Build JWT payload from account details and sign with the configured access token expiry
        return self._generate_jwt_token(
            jwt_data=JWTAccount(
                username=account.username,
                email=account.email,
                role=account.role,
            ).dict(),  # type: ignore
            expires_delta=datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_TIME),
        )

    # Decode a JWT token and extract the username and email from its payload
    def retrieve_details_from_token(self, token: str, secret_key: str) -> list[str]:
        try:
            # Decode and verify the token signature and expiry
            payload = jose_jwt.decode(token=token, key=secret_key, algorithms=[settings.JWT_ALGORITHM])
            # Parse the payload into a structured JWTAccount object
            jwt_account = JWTAccount(
                username=payload["username"],
                email=payload["email"],
                role=payload.get("role", "user"),
            )

        except JoseJWTError as token_decode_error:
            # Token is malformed, expired, or has an invalid signature
            raise ValueError("Unable to decode JWT Token") from token_decode_error

        except pydantic.ValidationError as validation_error:
            # Token payload does not match the expected schema
            raise ValueError("Invalid payload in token") from validation_error

        # Return username and email extracted from the token
        return [jwt_account.username, jwt_account.email]


# Factory function to create a new JWTGenerator instance
def get_jwt_generator() -> JWTGenerator:
    return JWTGenerator()


# Module-level singleton instance — shared across the application for JWT operations
jwt_generator: JWTGenerator = get_jwt_generator()
