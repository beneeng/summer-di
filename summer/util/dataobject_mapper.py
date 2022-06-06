import dataclasses
import datetime
import inspect
from types import NoneType
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Tuple, Union, get_args, get_origin
from collections.abc import Iterable
from abc import abstractmethod

from yaml import serialize_all

class DeserialisationError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

T = TypeVar('T')
SERIALIZED = TypeVar('SERIALIZED')
DESERIALIZED = TypeVar('DESERIALIZED')

class Deserializer(Generic[SERIALIZED, DESERIALIZED]):
    
    @abstractmethod
    def types(self) -> Tuple[Type[SERIALIZED], Type[DESERIALIZED]]:
        pass

    @abstractmethod
    def deserialize(self, value: SERIALIZED) -> DESERIALIZED:
        pass

class Serializer(Generic[SERIALIZED, DESERIALIZED]):
    
    @abstractmethod
    def types(self) -> Tuple[Type[SERIALIZED], Type[DESERIALIZED]]:
        pass

    @abstractmethod
    def serialize(self, value: DESERIALIZED) -> SERIALIZED:
        pass


class DataObjectMapper:    
    _PRIMITIVE_TYPES = (int, str, float, bool)

    def __init__(self, deserializers: List[Deserializer], serializers: List[Serializer]) -> None:
        self._deserializers = deserializers
        self._serializers = serializers
        self._deserializer_map : Optional[Dict[Tuple[Type[SERIALIZED], Type[DESERIALIZED]], Deserializer[Type[SERIALIZED], Type[DESERIALIZED]]]] = None
        self._serializer_map : Optional[Dict[Type[DESERIALIZED], Serializer[Type[SERIALIZED], Type[DESERIALIZED]]]] = None
    
    def _deserializer(self, from_type: Type[SERIALIZED], to_type: Type[DESERIALIZED]) -> Optional[Deserializer[SERIALIZED, DESERIALIZED]]:
        if self._deserializer_map is None:
            self._deserializer_map = {deserializer.types() : deserializer for deserializer in  self._deserializers}
        return self._deserializer_map.get((from_type, to_type), None)

    def _serializer(self, from_type: DESERIALIZED) -> Optional[Serializer[SERIALIZED, DESERIALIZED]]:
        if self._serializer_map is None:
            self._serializer_map = {serializer.types()[1] : serializer for serializer in  self._serializers}
        for k,v in self._serializer_map.items():
            if isinstance(from_type, k):
                return v
        return None
    
    def serialize(self, obj) -> Dict:
        if self._is_primive(obj):
            return obj
        if isinstance(obj, dict):
            return self._serialize_dict(obj)
        if isinstance(obj, Iterable):
            return [self.serialize(elem) for elem in obj] 
        
        serializer = self._serializer(obj)
        if serializer is not None:
            return serializer.serialize(obj)
        return self._object_to_dict(obj)
        
        
    def _serialize_dict(self, obj: Dict) -> Dict[str, Any]:
        result = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(f"Can not use {repr(key)} to as dictionary key")
        result[key] = self.serialize(value)

    def _object_to_dict(self, obj):
        #if dataclasses.is_dataclass(obj):
        #    return dataclasses.asdict(obj)
        result = {}
        for attribute in dir(obj):
            if attribute.startswith("_"):
                continue
            value = getattr(obj, attribute)
            if callable(value):
                continue
            result[attribute] = self.serialize(value)
        return result

    def _is_primive(self, value : Any):
        return value is None or isinstance(value, DataObjectMapper._PRIMITIVE_TYPES)
    
    def _is_primitive_type(self, t):
        return t in DataObjectMapper._PRIMITIVE_TYPES
    

    def _deserialize_primitive(self, serialized, as_type: Type[DESERIALIZED]) -> DESERIALIZED:
        if isinstance(serialized, as_type):
            return serialized
        
    def deserialize(self, serialized:Any, as_type: Type[DESERIALIZED]) -> DESERIALIZED:
        try:
            return self._deserialize(serialized, as_type)
        except KeyError as e:
            raise DeserialisationError(*e.args)

    def _translate_type(self, t: Type[T]) -> type:
        origin = get_origin(t)
        if origin is None:
            return t, None
        if origin == Union:
            (a1, a2) = get_args(t)
            if a2 == NoneType:
                return self._translate_type(a1)
            if a1 == NoneType:
                return self._translate_type(a2)
            raise TypeError(f"can not deserialize union type with two valid types ({a1}, {a2})")
        return origin, get_args(t)

    def _deserialize(self, serialized:Any, as_type: Type[DESERIALIZED]) -> DESERIALIZED:
        
        if serialized is None:
            return None
        as_type, type_args = self._translate_type(as_type)

        if as_type == list and len(type_args) > 0:
            return [ self._deserialize(elem, type_args[0]) for elem in serialized ]


        deserializer = self._deserializer(serialized.__class__, as_type)
        if deserializer is not None:
            return deserializer.deserialize(serialized)

        if self._is_primitive_type(as_type):
            return self._deserialize_primitive(serialized, as_type)
        
        if isinstance(serialized, as_type):
            return serialized
            
        if not isinstance(serialized, dict):
            raise TypeError(f"can not deserialize type from {serialized.__class__}")
        if not dataclasses.is_dataclass(as_type):
            raise TypeError(f"can not deserialize type to {as_type}, because it is not a dataclass")

        field_types_mapping = {f.name: f.type for f in dataclasses.fields(as_type)}
        kwargs = {f:self._deserialize(serialized[f], field_types_mapping[f]) for f in serialized if f in field_types_mapping}

        return as_type(**kwargs)


class DateSerializer(Deserializer[str, datetime.datetime], Serializer[str, datetime.datetime]):

    def __init__(self) -> None:
        super().__init__()

    def types(self) -> Tuple[Type[str], Type[datetime.datetime]]:
        return (str, datetime.datetime)
    
    def deserialize(self, value: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(value)
    
    def serialize(self, value: datetime.datetime) -> str:
        return value.isoformat()
