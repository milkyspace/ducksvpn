import asyncio
from logging import getLogger
from typing import Coroutine

logger = getLogger(__name__)


class BackgroundTaskManager:
    """Background task manager."""

    __tasks: set[asyncio.Task] = set()

    def add_task(self, func: Coroutine):
        """Add task as background task."""
        task = asyncio.create_task(func)
        self.__tasks.add(task)
        task.add_done_callback(self.__tasks.discard)
        logger.info(
            'added background task',
            extra={'tasks_count': len(self.__tasks)},
        )

    async def stop(self):
        """Stop background tasks."""
        for coro in self.__tasks:
            coro.cancel()

        try:
            await asyncio.gather(*self.__tasks)
        except asyncio.CancelledError:
            logger.info(
                'background tasks stopped',
                extra={'tasks_count': len(self.__tasks)},
            )

background_task_manager = BackgroundTaskManager()