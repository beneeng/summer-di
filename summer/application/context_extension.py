


from abc import abstractmethod
from typing import Any, Dict, Iterable


class ContextExtensionRunThread:

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.run()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def stop(self):
        pass

class ContextExtension:

    def get_beans(self) -> Iterable[Any]:
        return [] 

    def get_background_job(self) -> ContextExtensionRunThread:
        return None

    @abstractmethod
    def process_beans(self, beans: Dict[str, Any]):
        pass
