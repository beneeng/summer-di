
from __future__ import annotations


from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, List


@dataclass
class MethodProxyContext:
    args: List[Any]
    kwargs: Dict[str, Any]

T = TypeVar("T")
class MethodProxy(Generic[T]):

    def __init__(self, method: Callable[..., T]) -> None:
        self._method = method
        self._pre_run_hooks: List[Callable[[MethodProxyContext], Any]] = []
        self._post_run_hooks: List[Callable[[T], T]] = []

    
    def __call__(self, *args: Any, **kwds: Any) -> T:
        context = MethodProxyContext(args, kwds)
        for _, hook in self._pre_run_hooks:
            hook(context)
        result = self._method(*args, **kwds)

        for _, hook in self._post_run_hooks:
            result = hook(result)
        
        return result
    
    def pre_run(self, hook: Callable[[MethodProxyContext], Any], name: Optional[str] = None):
        self.remove_pre_run(name)    
        self._pre_run_hooks.append((name, hook))
    
    def post_run(self, hook: Callable[[T], T], name: Optional[str] = None):
        self.remove_post_run(name)
        self._post_run_hooks.append((name, hook))

    def remove_pre_run(self, name: str) -> bool:
        before = len(self._pre_run_hooks)
        self._pre_run_hooks = [(n, h) for n, h in self._pre_run_hooks if n != name]
        after = len(self._pre_run_hooks)
        return before != after # length changed?

    def remove_post_run(self, name: str) -> bool:
        before = len(self._post_run_hooks)
        self._post_run_hooks = [(n, h) for n, h in self._post_run_hooks if n != name]
        after = len(self._post_run_hooks)
        return before != after # length changed?

    @staticmethod
    def create_proxy(method: Callable[..., T]) -> MethodProxy[T]:
        if isinstance(method, MethodProxy):
            return method
        return MethodProxy(method)





    



    
