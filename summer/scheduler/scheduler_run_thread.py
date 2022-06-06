
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from typing import Any, Optional, Tuple, List
import datetime
from summer.application.context_extension import ContextExtensionRunThread

from summer.scheduler.scheduler_context import ScheduledTask
from summer.summer_logging import get_summer_logger
from summer.util import time_util


class SchedulerRunThread(ContextExtensionRunThread):
    def __init__(self, queue: Queue) -> None:
        self.queue = queue
        self.scheduled_actions: List[Tuple[datetime.datetime, ScheduledTask]] = []
        self._background_job_running = False

    def _next_execution_wait_time(self) -> datetime.timedelta:
        self.scheduled_actions = sorted(self.scheduled_actions, key=lambda x: x[0])

        next_scheduled = self.scheduled_actions[0] if len(self.scheduled_actions) > 0 else None
        return (next_scheduled[0] - datetime.datetime.now()) if next_scheduled is not None else datetime.timedelta(hours=1)

    def _get_from_queue(self, wait_for: float) -> Tuple[ScheduledTask, datetime.datetime]:
        return self.queue.get(timeout=wait_for)

    def _wait_and_handle_new_schedulings(self):
        while self._background_job_running:
            try:
                wait_for = self._next_execution_wait_time().total_seconds()
                if wait_for <= 0:
                    return
                task, at_timestamp = self._get_from_queue(wait_for)
                if task is not None:
                    at_timestamp_no_tz = time_util.coerce_datetime(at_timestamp)
                    self.scheduled_actions.append((at_timestamp_no_tz, task))

            except Empty:
                pass

    def _next_task(self) -> Optional[ScheduledTask]:
        if len(self.scheduled_actions) == 0:
            return None
        
        at, task = self.scheduled_actions[0]
        if at <= datetime.datetime.now():
            self.scheduled_actions = self.scheduled_actions[1:]
            return task

        return None
    
    def _run_task(self, task: ScheduledTask):
        try:
            task.run()
        except:
            get_summer_logger().error("Running scheduled task led to an error", exc_info=True)

    def run(self) -> Any:
        threadpool = ThreadPoolExecutor()
        
        try:
            self._background_job_running = True
            while self._background_job_running:
                self._wait_and_handle_new_schedulings()
                next_task = self._next_task()
                if next_task is None:
                    continue
                threadpool.submit(self._run_task, next_task)

        finally:
            self._background_job_running = False
            threadpool.shutdown(cancel_futures=True)
            get_summer_logger().info("Scheduler shutdown completed")

    def stop(self):
        self._background_job_running = False
        self.queue.put((None, None))