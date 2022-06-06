
import signal
import traceback
from typing import Any, Callable, Dict
from uuid import uuid4

_SIGNAL_HANDLER_SET = False
_SHUTDOWN_HANDLERS: Dict[str,  Callable[[], Any]] = {}



def add_shutdown_handler(method: Callable[[], Any], id=None) -> str:
    __register_shutdown_handler()
    if id is None:
        id = method.__qualname__ + "_" + str(uuid4())
    _SHUTDOWN_HANDLERS[id] = method
    return id

def remove_shutdown_handler(id: str):
    if id in _SHUTDOWN_HANDLERS:
        del _SHUTDOWN_HANDLERS[id]

def __register_shutdown_handler():
    global _SIGNAL_HANDLER_SET
    if _SIGNAL_HANDLER_SET:
        return 
    
    def signal_handler(signal_number, stack):

        for _, f in _SHUTDOWN_HANDLERS:
            try:
                f()
            except:
                traceback.print_exc()
            
        signal.raise_signal(signal_number)

    # The signals included in the array below are the ones that cause the
    # process to terminate when I run it on my system.  This may need
    # fine-tuning for portability.

    to_handle_old = ['SIGHUP', 'SIGINT', 'SIGQUIT', 'SIGILL', 'SIGTRAP', 'SIGIOT',
                 'SIGBUS', 'SIGFPE', 'SIGUSR1', 'SIGSEGV', 'SIGUSR2',
                 'SIGALRM', 'SIGTERM', 'SIGXCPU', 'SIGVTALRM', 'SIGPROF',
                 'SIGPOLL', 'SIGPWR', 'SIGSYS', 'SIGABRT', 'SIGEMT', 'SIGLOST', 
                 'SIGPIPE', 'SIGSTKFLT', 'SIGXFSZ']
    to_handle =  [x for x in dir(signal) if x.startswith("SIG")]

    for signal_name in to_handle:
        signal_number = getattr(signal, signal_name, None)
        if signal_number is None:
            continue
        try:
            handler = signal.getsignal(signal_number)
            if handler is signal.SIG_DFL:
                signal.signal(signal_number, signal_handler)
        except:
            pass