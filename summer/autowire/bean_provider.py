
from abc import abstractmethod
from typing import Any, Generic, Iterable, Optional, Tuple, TypeVar, List, Type, Callable
from xmlrpc.client import boolean
from summer.autowire.exceptions import ValidationError

from summer.util import inspection_util

T = TypeVar('T')


class BeanProvider(Generic[T]):
    @abstractmethod
    def get(self, **kwargs) -> T:
        pass

    @abstractmethod
    def provides(self) -> Type:
        pass

    @abstractmethod
    def requires(self) -> Iterable[Tuple[str, Type, bool]]:
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    def validate(self) -> None:
        if self.provides() is None:
            raise ValidationError(
                f'Can not add component "{self.name()}" because it does not have a clear return type')

        unannotated_non_default_parameters = [
            name for name, pannotation, pdefault in self.requires() if pannotation is None and not pdefault]

        if len(unannotated_non_default_parameters) != 0:
            raise ValidationError(
                f'Can not add component "{self.name()}" because it has unannotated propositional parameters {unannotated_non_default_parameters}')


class ClassBeanProvider(BeanProvider[T]):
    def __init__(self, clazz: Type[T], name: Optional[str] = None) -> None:
        self._clazz: Type[T] = clazz
        self._name = name if name is not None else clazz.__name__
    
    def get(self, **kwargs) -> T:
        return self._clazz(**kwargs)

    def requires(self) -> Iterable[Tuple[str, Type, bool]]:
        init = self._clazz.__init__
        if init == object.__init__:
            return []
        return inspection_util.get_parameters_simple(init)[1:]

    def provides(self) -> Type:
        return self._clazz

    def name(self) -> str:
        return self._name


class FunctionBeanProvider(BeanProvider[T]):
    def __init__(self, fun: Callable[..., T], name: Optional[str] = None) -> None:
        self.fun: Callable[..., T] = fun
        self._name = name if name is not None else fun.__name__

    def get(self, **kwargs) -> T:
        return self.fun(**kwargs)

    def requires(self) -> Iterable[Tuple[str, Type, bool]]:
        return inspection_util.get_parameters_simple(self.fun)

    def provides(self) -> Type:
        return_annotation = inspection_util.get_return_type_annotation(self.fun)
        return return_annotation

    def name(self) -> str:
        return self._name



class StaticObjectBeanProvider(BeanProvider[T]):
    def __init__(self, obj: T, name: Optional[str] = None) -> None:
        self.obj = obj
        self._name = name if name is not None else obj.__class__.__name__

    def get(self, **_) -> T:
        return self.obj

    def requires(self) -> Iterable[Tuple[str, Type, bool]]:
        return []

    def provides(self) -> Type:
        return self.obj.__class__

    def name(self) -> str:
        return self._name
