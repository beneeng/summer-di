import os
from pathlib import Path
import re

from typing import Callable, List, TypeVar, Union
from summer.application.default_beans import DEFAULT_BEANS
from summer.application.summer_context import SummerContext
from summer.database.database_connection_factory import DatabaseConnectionFactory
from summer.database.database_context_extension import DatabaseContextExtension
from summer.scheduler.scheduler_context import SummerSchedulerContextExtension
from summer.util import resources

CONFIG_FILE_PATTERN = re.compile(
    "^(application|config)\.(json|ya?ml)$", flags=re.RegexFlag.IGNORECASE)

T = TypeVar('T')

def _build_default_context() -> SummerContext:
    ctx = SummerContext()
    for file in _get_default_config_files():
        try:
            ctx.load_configuration(file)
        except:
            pass
    for b in DEFAULT_BEANS:
        ctx.register_component(b)

    return ctx


def find_default_config_files(directory: Union[str, Path]) -> List[str]:
    directory_files = os.listdir(directory)
    matching_filenames = [
        file for file in directory_files if CONFIG_FILE_PATTERN.match(file) is not None]
    return [os.path.join(directory, f) for f in matching_filenames]


def _get_default_config_files() -> List[str]:
    resource_folder = resources.get_resources_folder()
    return find_default_config_files(resource_folder)


_DEFAULT_CTX = _build_default_context()


def component(**kwargs) -> Callable[[T], T]:
    return _DEFAULT_CTX.component(**kwargs)

def entity(clazz: T) -> T:
    database_extension = _DEFAULT_CTX.get_extension(DatabaseContextExtension)
    if database_extension is None:
        database_extension = DatabaseContextExtension()
        _DEFAULT_CTX.register_context_extension(database_extension)
    database_extension.register_entity(clazz)
    return clazz

def enable_scheduling():
    scheduler_extension = _DEFAULT_CTX.get_extension(
        SummerSchedulerContextExtension)
    if scheduler_extension is None:
        scheduler_extension = SummerSchedulerContextExtension(_DEFAULT_CTX)
        _DEFAULT_CTX.register_context_extension(scheduler_extension)

def scheduled(*args, **kwargs) -> Callable[[T], T]:
    enable_scheduling()
    scheduler_extension = _DEFAULT_CTX.get_extension(
        SummerSchedulerContextExtension)
    return scheduler_extension.scheduled(*args, **kwargs)


def load_configuration(*configuration_files):
    _DEFAULT_CTX.load_configuration(*configuration_files)


def run():
    _DEFAULT_CTX.run()


def shutdown(exit_code: int):
    _DEFAULT_CTX.shutdown(exit_code)
