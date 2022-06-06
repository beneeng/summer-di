from dataclasses import dataclass, field
import logging
import sys
from typing import Dict


"""logging is done globally with python logging. We unify the configuration process here and add buffering for alerting later"""


_SUMMER_LOGGER = None

def get_summer_logger() -> logging.Logger:
    return _SUMMER_LOGGER


@dataclass
class LoggingConfiguration:
    logfile: str = field(default=None)
    level: str = field(default="INFO")
    log_stdout: bool = field(default=True)
    loggers: Dict[str, str] = field(default_factory=dict)


def init_logging(configuration: LoggingConfiguration):
    global _SUMMER_LOGGER

    level = getattr(logging, configuration.level.upper())
    format = '%(asctime)s | %(name)20.20s | %(levelname)8s | %(message)s'
    formatter = logging.Formatter(format)

    handlers = []
    if configuration.logfile:
        handler = logging.FileHandler(configuration.logfile, mode='a')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        handlers.append(handler)

    if configuration.log_stdout:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        handlers.append(handler)

    if len(handlers) == 0:
        handlers = [logging.NullHandler()]

    logging.basicConfig(level=level, format=format, handlers=handlers)

    logging.info("setting log level to {}".format(configuration.level))

    if configuration.loggers is not None:
        for logger, level_str in configuration.loggers.items():
            level = getattr(logging, level_str.upper())
            if level is not None:
                logging.getLogger(logger).setLevel(level)

    _SUMMER_LOGGER = logging.getLogger("summer-di")