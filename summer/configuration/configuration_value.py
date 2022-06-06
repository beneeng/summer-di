from typing import Generic, Optional, Type, TypeVar

class _NOT_SET_TYPE:
    pass
NOT_SET = _NOT_SET_TYPE()

T = TypeVar("T")
class ConfigurationValue(Generic[T]):
    def __init__(self, configuration_key: str, value_type: Type[T] = str, default: Optional[T] | _NOT_SET_TYPE = NOT_SET) -> None:
        self.configuration_key = configuration_key
        self.value_type = value_type
        self.default = default
    
    def typed(self) -> T:
        return self

    