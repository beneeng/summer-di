
from abc import abstractmethod
from multiprocessing.sharedctypes import Value
from typing import Any, Generic, Iterable, Optional, Tuple, TypeVar, List, Type, Callable
from xmlrpc.client import boolean
from summer.autowire.bean_provider import BeanProvider
from summer.autowire.exceptions import ValidationError
from summer.summer_logging import get_summer_logger

from summer.util import inspection_util

T = TypeVar('T')


class BeanInitializer(Generic[T]):
    def __init__(self, provider: BeanProvider[T]) -> None:
        super().__init__()
        self._provider = provider
        self._bean: Optional[T] = None
        self._args = {}
        self._requires = self._provider.requires()
        self._still_requires = {name: (t, has_default)
                                for name, t, has_default in self._requires}

    def requires(self) -> List[Tuple[str, Type]]:
        return [(n, t) for n, (t, _) in self._still_requires.items()]

    def add_parameter(self, name: str, value: Any):
        requirements = {n: type_ for n, type_, _ in self._requires}
        if name not in requirements:
            get_summer_logger().warn(
                "Unknown parameter '%s' for bean '%s'", name, self.name())
            return

        if not inspection_util.is_autowirable_collection(requirements[name]) and not issubclass(value.__class__, requirements[name]):
            get_summer_logger().warn("bad parameter type '%s' for parameter '%s' on bean '%s'",
                               value.__class__.__name__, name, self.bean_name())
            return

        self._args[name] = value
        if name in self._still_requires:
            del self._still_requires[name]

    def ready(self) -> bool:
        return all([has_default for _, has_default in self._still_requires.values()])

    def get(self) -> T:
        if not self.ready():
            missing_params = [name for name,
                              (_, d) in self._still_requires.items() if not d]
            raise ValidationError(
                "Missing parameters '%s' for bean '%s'", missing_params, self.bean_name())
        if self._bean is None:
            self._bean = self._provider.get(**(self._args))
        return self._bean

    def bean_name(self) -> str:
        return self._provider.name()

    
    def __repr__(self) -> str:
        len_requires = len(self._requires)
        len_still_requires = len(self._still_requires)
        ready = "ready" if self.ready() else "not ready ({len_still_requires}/{len_requires})"
        return f"BeanInitializer({self.bean_name} <{ready}>)"
