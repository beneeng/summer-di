

from types import NoneType
from typing import Any, Callable, List, Set, Tuple, Type, TypeVar, Union, get_args, get_origin
import inspect


from numpy import isin

T = TypeVar('T')


def _empty_to_none(val):
    return val if val is not inspect._empty else None


def get_all_base_classes(t: type) -> List[type]:
    if t is None:
        return []
    return [x for x in inspect.getmro(t)]


def get_return_type_annotation(call: Callable[..., T]) -> Type[T]:
    if inspect.isclass(call):
        return
    else:
        return inspect.get_annotations(call).get('return')


def get_constructor_annotated_parameter_classes(t: type) -> List[type]:
    return [x for x in inspect.get_annotations(t.__init__).values() if x is not None]


def is_autowirable_collection(t: type) -> bool:
    origin, _ = destruct_autowirable_collection(t)
    return origin is not None


def destruct_autowirable_collection(t: Type) -> Tuple[Type, Type]:
    origin = get_origin(t)
    if origin is not None and issubclass(origin, (Set, List)):
        return origin, get_args(t)[0]

    return None, t


def get_castable_type(t: Type[T]) -> T:
    origin = get_origin(t)
    if origin == Union:
        (a1, a2) = get_args(t)
        if a2 == NoneType:
            return get_castable_type(a1)
        if a1 == NoneType:
            return get_castable_type(a2)
        raise TypeError(
            f"can not get castable type from union type with several valid types ({a1}, {a2})")
    if origin is not None:
        return origin
    return T

def isinstance_safe(o: Any, t: Type) -> bool:
    origin = get_origin(t)
    if origin is None:
        return isinstance(o, t)
    if issubclass(origin, (set, list)):
        value_type = get_args(t)[0]
        return all((isinstance(x, value_type) for x in o))
    if issubclass(origin, dict):
        if isinstance(o, dict):
            k_type, v_type = get_args(t)
            kv_isinstance = (isinstance(k, k_type) and isinstance(v, v_type) for k,v in o.items())
            return all(kv_isinstance)
        else: 
            return False
    return False


def get_parameters(fun: Callable[..., Any]) -> Tuple[str, type, Any]:
    """
    Get parameters, prodvided type annotation and information about defaut arguments from a function

    Args:
        fun (Callable[...]): function to get the parameters from

    Returns:
        Tuple[str, type, bool]: response containing the following information per parameter
                name: name of the parameter
                annotated type: type the parameter is supposed to have
                default: default value for this parameter
    """
    parameters = inspect.signature(fun).parameters
    return [(pname, _empty_to_none(ptype.annotation), _empty_to_none(ptype.default)) for pname, ptype in parameters.items()]


def get_parameters_simple(fun: Callable[..., Any]) -> Tuple[str, type, bool]:
    """
    Get parameters, prodvided type annotation and information about defaut arguments from a function in a simpler way

    Args:
        fun (Callable[...]): function to get the parameters from

    Returns:
        Tuple[str, type, bool]: response containing the following information per parameter
                name: name of the parameter
                annotated type: type the parameter is supposed to have
                has_default: information about the existence of a default value for that parameter
    """
    return [(pname, pannotation, pdefault is not None) for pname, pannotation, pdefault in get_parameters(fun)]


def get_methods(o: Any) -> List[Callable[..., Any]]:
    return [getattr(o, attr) for attr in dir(o) if inspect.ismethod(getattr(o, attr))]
