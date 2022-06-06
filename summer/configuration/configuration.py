from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from summer.autowire.context import SummerBeanContext
from summer.autowire.exceptions import ValidationError
from summer.configuration.configuration_value import ConfigurationValue, _NOT_SET_TYPE, NOT_SET
from summer.util import dict_util, inspection_util
from summer.util.dataobject_mapper import DataObjectMapper

_BOUND_CONFIGURATION_PROPERTY = "__bound_configuration__"



T = TypeVar("T")

class SummerConfigurationContext:
    
    def __init__(self) -> None:
        if not isinstance(self, SummerBeanContext):
            raise TypeError("SummerConfigurationContext must be used as mixin with SummerBeanContext")
        self._config_files = []
        self._configuration = {}
        self._configuration_cache: Dict[Tuple[str, Type[T]], T] = {}
        self._data_mapper: Optional[DataObjectMapper] = None
    
    def _get_data_mapper(self) -> DataObjectMapper:
        if self._data_mapper is None and isinstance(self, SummerBeanContext):
            self._data_mapper = self.get_bean(DataObjectMapper)
        return self._data_mapper

    def load_configuration(self, *config_files):
        for file in config_files:
            self._config_files.append(file)
            new_config = self._load_config_from_file(file)
            self._configuration.update(new_config)
            self._configuration_cache = {}

    def get_configuration_value(self, key: str, value_type: Type[T], default: T | _NOT_SET_TYPE = NOT_SET) -> T:
        try:
            return self._get_value_internal_cached(key, value_type)
        except KeyError:
            if not isinstance(default, _NOT_SET_TYPE):
                return default
            raise

    def _get_configuration_value_by_object(self, value: ConfigurationValue) -> Any:
        return self.get_configuration_value(value.configuration_key, value.value_type, value.default)


    def _get_value_internal_cached(self, key: str, value_type: Type[T])->T:
        cache_key = (key, value_type)
        if cache_key in self._configuration_cache:
            return self._configuration_cache[cache_key]
        
        value = self._get_value_internal(key, value_type)
        self._configuration_cache[cache_key] = value
        return value

    def _get_value_internal(self, key: str, value_type: Type[T])->T:
        configuration_value = self._configuration[key]
        if inspection_util.isinstance_safe(configuration_value, value_type):
            return configuration_value
        return self._get_data_mapper().deserialize(configuration_value, value_type) 


    def process_beans(self, beans: Dict[str, Any]):
        for _, bean in beans.items():
            self._instrument_bean(bean)


    def _instrument_bean(self, bean: Any):
            bound_bean = getattr(bean, _BOUND_CONFIGURATION_PROPERTY, None)
            if bound_bean is not None:
                raise ValidationError("Bean can not be bound to more than one configuration")
            
            setattr(bean, _BOUND_CONFIGURATION_PROPERTY, self)
            self._replace_getattribute(bean.__class__)
            self._replace_getattribute(bean)



    def _replace_getattribute(self, subject):
            old = subject.__getattribute__
            def new(*args, **kwargs):
                original_value = old(*args, **kwargs)
                if isinstance(original_value, ConfigurationValue):
                    return self._get_configuration_value_by_object(original_value)
                return original_value
            subject.__getattribute__ = new

    def _load_config_from_file(self, filename: str) -> Dict[str, Any]:
        file_dict = dict_util.load_dict_from_file(filename)
        return dict_util.explode_dict(file_dict)



            

        
        
    