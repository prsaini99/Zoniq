# Return a 400 error detail message indicating the username is already taken
def http_400_username_details(username: str) -> str:
    return f"The username {username} is taken! Be creative and choose another one!"


# Return a 400 error detail message indicating the email is already registered
def http_400_email_details(email: str) -> str:
    return f"The email {email} is already registered! Be creative and choose another one!"


# Return a 400 error detail message for failed signup due to invalid credentials
def http_400_signup_credentials_details() -> str:
    return "Signup failed! Recheck all your credentials!"


# Return a 400 error detail message for failed signin due to invalid credentials
def http_400_sigin_credentials_details() -> str:
    return "Signin failed! Recheck all your credentials!"


# Return a 401 error detail message for unauthenticated requests
def http_401_unauthorized_details() -> str:
    return "Refused to complete request due to lack of valid authentication!"


# Return a 403 error detail message for forbidden/unauthorized access attempts
def http_403_forbidden_details() -> str:
    return "Refused access to the requested resource!"


# Return a 404 error detail message when an account with the given ID is not found
def http_404_id_details(id: int) -> str:
    return f"Either the account with id `{id}` doesn't exist, has been deleted, or you are not authorized!"


# Return a 404 error detail message when an account with the given username is not found
def http_404_username_details(username: str) -> str:
    return f"Either the account with username `{username}` doesn't exist, has been deleted, or you are not authorized!"


# Return a 404 error detail message when an account with the given email is not found
def http_404_email_details(email: str) -> str:
    return f"Either the account with email `{email}` doesn't exist, has been deleted, or you are not authorized!"
