# Exception raised when a queried entity does not exist in the database
class EntityDoesNotExist(Exception):
    """
    Throw an exception when the data does not exist in the database.
    """


# Exception raised when attempting to create an entity that already exists in the database
class EntityAlreadyExists(Exception):
    """
    Throw an exception when the data already exist in the database.
    """
