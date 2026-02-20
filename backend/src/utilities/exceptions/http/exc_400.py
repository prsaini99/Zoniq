"""
The HyperText Transfer Protocol (HTTP) 400 Bad Request response status code indicates that the server
cannot or will not process the request due to something that is perceivedto be a client error
(for example, malformed request syntax, invalid request message framing, or deceptive request routing).
"""

import fastapi

from src.utilities.messages.exceptions.http.exc_details import (
    http_400_email_details,
    http_400_sigin_credentials_details,
    http_400_signup_credentials_details,
    http_400_username_details,
)


# Raise a 400 error when signup credentials are invalid or incomplete
async def http_exc_400_credentials_bad_signup_request() -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_400_BAD_REQUEST,
        detail=http_400_signup_credentials_details(),
    )


# Raise a 400 error when signin credentials are invalid or incorrect
async def http_exc_400_credentials_bad_signin_request() -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_400_BAD_REQUEST,
        detail=http_400_sigin_credentials_details(),
    )


# Raise a 400 error when the requested username is already taken
async def http_400_exc_bad_username_request(username: str) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_400_BAD_REQUEST,
        detail=http_400_username_details(username=username),
    )


# Raise a 400 error when the requested email is already registered
async def http_400_exc_bad_email_request(email: str) -> Exception:
    return fastapi.HTTPException(
        status_code=fastapi.status.HTTP_400_BAD_REQUEST,
        detail=http_400_email_details(email=email),
    )
