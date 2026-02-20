# JWT (JSON Web Token) schemas for token payload and account identity claims
import datetime

import pydantic


# Schema representing the JWT token payload (claims)
class JWToken(pydantic.BaseModel):
    # Token expiration timestamp; after this time the token is invalid
    exp: datetime.datetime
    # Subject claim: typically the username or user identifier encoded in the token
    sub: str


# Schema representing the account identity claims extracted from a JWT
# Used internally to identify the authenticated user after token validation
class JWTAccount(pydantic.BaseModel):
    # Username of the authenticated user
    username: str
    # Email of the authenticated user
    email: pydantic.EmailStr
    # Role of the user (defaults to "user"; can be "admin")
    role: str = "user"
