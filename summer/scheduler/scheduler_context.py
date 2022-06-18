from __future__ import annotations
import datetime
import queue
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from uuid import uuid4

from summer.application.context_extension import ContextExtension, ContextExtensionRunThread
from summer.autowire.context import SummerBeanContext
from summer.autowire.exceptions import ValidationError
from summer.scheduler.scheduled_task import ISchedulerPlaceholder, OneTimeScheduledTask, RepeatAfterTimeTask, ScheduledTask, StartRegularilyTask
from summer.scheduler.scheduler_run_thread import SchedulerRunThread
from summer.util import inspection_util, time_util


T = TypeVar('T', bound=Callable)
_ATTR_SCHEDULER_REFERENCE = "__scheduler_reference__"


class SummerSchedulerContextExtension(ContextExtension, ISchedulerPlaceholder):
    def __init__(self, bean_context: SummerBeanContext) -> None:
        self.bean_context = bean_context
        self.prepared_schedules: List[Tuple[Dict[str, Any], Callable]] = []
        self._scheduler_queue = queue.Queue()
        self._run_thread: Optional[SchedulerRunThread] = None
        self._background_job_running = True
        self._schedule_self_references = {}

    def get_background_job(self) -> ContextExtensionRunThread:
        if self._run_thread is None:
            self._run_thread = SchedulerRunThread(self._scheduler_queue)
        return self._run_thread

    def process_beans(self, beans: Dict[str, Any]):
        for bean in beans.values():
            for method in inspection_util.get_methods(bean):
                scheduler_reference = getattr(
                    method, _ATTR_SCHEDULER_REFERENCE, None)
                if scheduler_reference is not None:
                    self._schedule_self_references[scheduler_reference] = bean

    def schedule_at(self, function: Callable[..., Any], schedule_at:  Union[datetime.datetime, float, int]):
        return self.schedule(function, once_at_time=schedule_at)

    def schedule_in(self, function: Callable[..., Any], schedule_in: Union[datetime.timedelta, float, int]):
        return self.schedule(function, once_in=schedule_in)

    def schedule_repeated(self, function: Callable[..., Any], repeat_after: Optional[Union[datetime.timedelta, float, int]] = None, reschedule_after_completion=False, first_in: Optional[Union[datetime.timedelta, float, int]] = None):
        kwargs = {'first_in': first_in}
        if reschedule_after_completion:
            kwargs['repeat_after'] = repeat_after
        else:
            kwargs['repeat_every'] = repeat_after

        return self.schedule(function, **kwargs)

    def schedule(self, function: Callable[..., Any], **kwargs):
        """_summary_

        Args:
        """
        patterns = ['once_at_time', 'once_at_datetime',
                    "once_in", 'repeat_every', 'repeat_after']
        if sum([1 for x in patterns if kwargs.get(x) is not None]) != 1:
            raise ValidationError(
                f"exactly one argument of \"{str(patterns)}\" must be present")

        if 'once_at_time' in kwargs or 'once_at_datetime' in kwargs:
            return self._schedule_once_at(function, **kwargs)
        if 'once_in' in kwargs:
            return self._schedule_once_in(function, **kwargs)
        if 'repeat_every' in kwargs:
            return self._schedule_repeat_every(function, **kwargs)
        if 'repeat_after' in kwargs:
            return self._schedule_repeat_after(function, **kwargs)

    def _autowired_callable(self, function: Callable[..., Any]) -> Callable[[], None]:
        def inner():
            reference = getattr(function, _ATTR_SCHEDULER_REFERENCE, None)
            args = []
            if reference is not None:
                referenced_value = self._schedule_self_references.get(
                    reference)
                if referenced_value is not None:
                    args.append(referenced_value)
            return self.bean_context.autowire_and_run(function, *args)
        return inner

    def _schedule_once_at(self,  function: Callable[...], **kwargs):
        if 'once_at_time' in kwargs:
            at = time_util.coerce_time(kwargs['once_at_time'])
            at = time_util.time_today(at)
            if datetime.datetime.now() > at:
                at = at +  datetime.timedelta(days=1)
        if 'once_at_datetime' in kwargs:
            at = time_util.coerce_datetime(kwargs['once_at_datetime'])
        autowired_callable = self._autowired_callable(function)
        task = OneTimeScheduledTask(autowired_callable)
        self.schedule_task_at(task, at)

    def _schedule_once_in(self,  function: Callable[...], **kwargs):
        once_in = kwargs['once_in']
        once_in = time_util.coerce_duration(once_in)
        at = datetime.datetime.now() + once_in
        autowired_callable = self._autowired_callable(function)
        task = OneTimeScheduledTask(autowired_callable)
        self.schedule_task_at(task, at)

    def _schedule_repeat_every(self,  function: Callable[...], **kwargs):
        repeat_every = kwargs['repeat_every']
        repeat_every = time_util.coerce_duration(repeat_every)
        first_in = time_util.coerce_duration(kwargs.get('first_in'))
        at = datetime.datetime.now() + first_in

        autowired_callable = self._autowired_callable(function)
        task = StartRegularilyTask(self, autowired_callable, repeat_every)
        self.schedule_task_at(task, at)

    def _schedule_repeat_after(self,  function: Callable[...], **kwargs):
        repeat_after = kwargs['repeat_after']
        repeat_after = time_util.coerce_duration(repeat_after)
        first_in = time_util.coerce_duration(kwargs.get('first_in'))
        at = datetime.datetime.now() + first_in

        autowired_callable = self._autowired_callable(function)
        task = RepeatAfterTimeTask(self, autowired_callable, repeat_after)
        self.schedule_task_at(task, at)

    def schedule_task_at(self, task: ScheduledTask, at: Union[datetime.datetime, float]):
        if isinstance(at, float):
            at_timestamp = datetime.datetime.fromtimestamp(at)
        else:
            at_timestamp = at
        self._scheduler_queue.put((task, at_timestamp), block=True)

    def scheduled(self, **kwargs) -> Callable[[T], T]:
        def inner(fn: T) -> T:
            reference = getattr(fn, _ATTR_SCHEDULER_REFERENCE, None)
            if reference is None:
                reference = uuid4()
                setattr(fn, _ATTR_SCHEDULER_REFERENCE, reference)
            self._schedule_self_references[reference] = None
            self.schedule(fn, **kwargs)
            return fn
        return inner
