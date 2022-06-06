from re import T
from typing import Any, Callable, Dict, Iterable, List, Optional, Type, TypeVar
import inspect
from summer.autowire.autowirer import Autowirer

from summer.autowire.bean_provider import BeanProvider, ClassBeanProvider, FunctionBeanProvider, StaticObjectBeanProvider
from summer.autowire.exceptions import AmbiguousBeanReference
from summer.summer_logging import _SUMMER_LOGGER
from summer.util import inspection_util


T = TypeVar('T')
C = TypeVar('C', Type, Callable[..., Any])
S = TypeVar('S')


class SummerBeanContext:
    beans: Dict[str, Any] = {}
    bean_providers: List[BeanProvider] = []
    _destroyed = False

    def register_component(self, component, **kwargs):
        provider: Optional[BeanProvider[T]] = None
        if not callable(component):
            provider = StaticObjectBeanProvider(component) 
        elif inspect.isclass(component):
            provider = ClassBeanProvider(component, **kwargs)
        else:
            provider = FunctionBeanProvider(component, **kwargs)
        provider.validate() # throws an exception if this fails
        self.bean_providers.append(provider)

    def component(self, **kwargs) -> Callable[[C], C]:
        """to be used as decorator when registering a bean provider

        Returns:
            A decorator to register a class
        """
        def inner(element: C) -> C:
            self.register_component(element, **kwargs)
            return element
        return inner

    def get_bean(self, cls: Optional[Type[T]] = None, name: Optional[str] = None) -> T:
        if name is not None:
            return self.beans[name]
        if cls is not None:
            beans = self.get_beans(cls)
            if len(beans) == 0:
                raise KeyError(f"bean not found {cls.__name__}")
            if len(beans) > 1:
                raise AmbiguousBeanReference(f"More than one bean of type {cls.__name__} have been found")
            return beans[0]
        raise ValueError("class or name of the bean must be provided")

    def get_beans(self, cls: Type[T]) -> List[T]:
        return [bean for bean in self.beans.values() if isinstance(bean, cls)]

    def autowire_and_run(self, function: Callable[..., T], *args) -> T:
        parameters = inspection_util.get_parameters_simple(function)
        parameter_map = {}
        for parameter_name, parameter_type, has_default in parameters:
            if len(args) != 0:
               parameter_map[parameter_name] = args[0]
               args = args[1:] 
               continue
            try:
                bean = self.get_bean(cls=parameter_type)
                parameter_map[parameter_name] = bean
            except KeyError:
                if not has_default:
                    raise
                
        return function(*args, **parameter_map)

    def initialize_beans(self):
        autowirer = Autowirer(self.bean_providers)
        self.beans = autowirer.autowire_beans()

    def post_bean_init(self):
        for bean in self.beans.values():
            if isinstance(bean, Iterable):
                for bean_element in bean:
                    self._bean_post_init(bean_element)
            else:
                self._bean_post_init(bean)

    def pre_destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        for bean in self.beans.values():
            if isinstance(bean, Iterable):
                for bean_element in bean:
                    self._pre_destroy(bean_element)
            else:
                self._pre_destroy(bean)

    def _bean_post_init(self, bean):
        if "__post_bean_init__" in dir(bean) and callable(bean.__post_bean_init__):
            bean.__post_bean_init__()

    def _pre_destroy(self, bean):
        if "__pre_destroy__" in dir(bean) and callable(bean.__pre_destroy__):
            bean.__pre_destroy__()


   




        
