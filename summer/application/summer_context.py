

import atexit
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from threading import Event
from typing import Dict, Optional, Type, TypeVar
from pip import List
from summer import summer_logging
from summer.application.context_extension import ContextExtension, ContextExtensionRunThread
from summer.autowire.context import SummerBeanContext
from summer.configuration.configuration import SummerConfigurationContext
from summer.summer_logging import LoggingConfiguration, get_summer_logger
from summer.util import signal_util
from summer.util.dataobject_mapper import DataObjectMapper

E = TypeVar('E', bound=ContextExtension)


class SummerContext(SummerBeanContext, SummerConfigurationContext):

    def __init__(self) -> None:
        super().__init__()
        self.context_extensions: Dict[Type[ContextExtension], ContextExtension] = {}
        self._executor : Optional[Executor]= None
        self._return_code_future = Future()
        self._run_threads: List[ContextExtensionRunThread] = []

    def _register_additional_beans(self):
        self.register_component(self)
        for extension in self.context_extensions.values():
            self.register_component(extension)
            for bean in extension.get_beans():
                self.register_component(bean)

    def initialize_logging(self):
        logging_configuration_dict = self.get_configuration_value("logging", dict)
        logging_configuration = DataObjectMapper([],[]).deserialize(logging_configuration_dict, LoggingConfiguration)
        summer_logging.init_logging(logging_configuration)


    def initialize(self):
        self.initialize_logging()
        self._register_additional_beans()
        self.initialize_beans()
        self.process_beans(self.beans)
        for context in self.context_extensions.values():
            context.process_beans(self.beans)
        self.post_bean_init()

    def register_context_extension(self, extension: ContextExtension):
        self.context_extensions[extension.__class__] = extension

    def get_extension(self, extension_type: Type[E]) -> Optional[E]:
        extension = self.context_extensions.get(extension_type)
        if isinstance(extension, extension_type):
            return extension
        return None

    def run_extensions(self):
        self._return_code_future.set_running_or_notify_cancel()
        for extension in self.context_extensions.values():
            runner = extension.get_background_job()
            if runner is not None:
                self._run_threads.append(runner)
        
        self._executor = ThreadPoolExecutor(max_workers=len(self._run_threads))

        futures = [self._executor.submit(runner) for runner in self._run_threads]

        for future in futures:
            try:
                future.result()
            except KeyboardInterrupt:
                pass
            except Exception:
                get_summer_logger().error("Shutting down extension led to an error", exc_info=True)
        if not self._return_code_future.done():
            self._return_code_future.set_result(0)
        

    def run(self):
        self.initialize()
        try:
            signal_handler_id = signal_util.add_shutdown_handler(self.pre_destroy) 
            self.run_extensions()
            return self._return_code_future.result(timeout=None)
        finally:
            signal_util.remove_shutdown_handler(signal_handler_id)
            self.pre_destroy()
    
    def shutdown(self, exit_code: int):
        if self._return_code_future.done():
            existing_code = self._return_code_future.result()
            if existing_code != exit_code:
                get_summer_logger().warning("Conflicting exit codes %s versus %s", existing_code, exit_code)
            return
        self._return_code_future.set_result(exit_code)
        get_summer_logger().info("Terminating application, waiting for all threads to finish.")
        for run_thread in self._run_threads:
            run_thread.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

        
