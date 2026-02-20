# Base schema module providing the foundational Pydantic model for all API schemas
import datetime
import typing

import pydantic
from pydantic import ConfigDict

from src.utilities.formatters.datetime_formatter import format_datetime_into_isoformat
from src.utilities.formatters.field_formatter import format_dict_key_to_camel_case


# Base Pydantic model that all schema classes inherit from
# Provides consistent serialization behavior across the entire API
class BaseSchemaModel(pydantic.BaseModel):
    model_config = ConfigDict(
        # Allow populating model fields from ORM model attributes (e.g., SQLAlchemy objects)
        from_attributes=True,
        # Re-validate fields when they are reassigned after model creation
        validate_assignment=True,
        # Allow using either the original field name or its alias when populating the model
        populate_by_name=True,
        # Automatically convert snake_case field names to camelCase for JSON responses
        alias_generator=format_dict_key_to_camel_case,
    )
