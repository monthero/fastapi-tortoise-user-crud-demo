from dry_pyutils import to_camel_case
from pydantic import BaseConfig as PydanticBaseConfig


class BaseConfig(PydanticBaseConfig):
    anystr_strip_whitespace: bool = True
    allow_population_by_field_name: bool = True
    arbitrary_types_allowed: bool = True
    alias_generator = to_camel_case
    allow_mutation: bool = True
    extra: str = "ignore"
    validate_all: bool = True
