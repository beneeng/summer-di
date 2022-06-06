
from abc import abstractmethod
import datetime
from typing import Any, Callable, Union


class ScheduledTask:
    @abstractmethod
    def run(self):
        pass


class ISchedulerPlaceholder:

    @abstractmethod
    def schedule_task_at(self, task: ScheduledTask, at: Union[datetime.datetime, float] ):
        pass


class OneTimeScheduledTask(ScheduledTask):
    def __init__(self, callable: Callable[[], Any]) -> None:
        self.callable = callable

    def run(self):
        self.callable()


class StartRegularilyTask(ScheduledTask):
    def __init__(self, scheduler: ISchedulerPlaceholder, callable: Callable[[], Any], start_every: datetime.timedelta) -> None:
        super().__init__()
        self.callable = callable
        self.start_every = start_every
        self.scheduler = scheduler

    def run(self):
        next_run = datetime.datetime.now() + self.start_every
        self.scheduler.schedule_task_at(self, next_run)
        self.callable()


class RepeatAfterTimeTask(ScheduledTask):
    def __init__(self, scheduler: ISchedulerPlaceholder, callable: Callable[[], Any], repeat_after: datetime.timedelta) -> None:
        super().__init__()
        self.callable = callable
        self.repeat_after = repeat_after
        self.scheduler = scheduler

    def run(self):
        try:
            self.callable()
        finally:
            next_run = datetime.datetime.now() + self.repeat_after
            self.scheduler.schedule_task_at(self, next_run)
