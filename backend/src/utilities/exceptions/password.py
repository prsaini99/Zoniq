# Exception raised when the provided password does not match the stored hashed password
class PasswordDoesNotMatch(Exception):
    """
    Throw an exception when the account password does not match the entitiy's hashed password from the database.
    """
