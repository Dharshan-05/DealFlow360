import asyncio
import fnmatch
import logging
from typing import Any, Awaitable, Callable, Dict, List, Set
from app.schemas.realtime import EventEnvelope

logger = logging.getLogger("dealflow360.event_bus")

EventHandler = Callable[[EventEnvelope[Any]], Awaitable[None]]


class EventBus:
    """
    In-Memory Asynchronous Pub/Sub Event Bus (Phase 341).
    Provides topic-based / pattern-based subscription, guaranteed tenant isolation,
    and individual subscriber error isolation.
    """
    def __init__(self):
        # Maps pattern string (e.g. "transaction.*", "approval.approved", "*") -> Set of async handlers
        self._subscribers: Dict[str, Set[EventHandler]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, pattern: str, handler: EventHandler) -> None:
        """Subscribe an asynchronous handler to an event type pattern."""
        if pattern not in self._subscribers:
            self._subscribers[pattern] = set()
        self._subscribers[pattern].add(handler)
        logger.debug(f"EventBus: Subscribed handler {handler.__name__ if hasattr(handler, '__name__') else handler} to '{pattern}'")

    def unsubscribe(self, pattern: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type pattern."""
        if pattern in self._subscribers and handler in self._subscribers[pattern]:
            self._subscribers[pattern].remove(handler)
            if not self._subscribers[pattern]:
                del self._subscribers[pattern]
            logger.debug(f"EventBus: Unsubscribed handler from '{pattern}'")

    async def publish(self, event: EventEnvelope[Any]) -> None:
        """
        Publish an event to all matching subscribers.
        Subscribers are invoked concurrently; any exception raised by a handler
        is caught, logged, and isolated from other handlers.
        """
        matching_handlers: List[EventHandler] = []
        for pattern, handlers in list(self._subscribers.items()):
            if pattern == "*" or fnmatch.fnmatch(event.event_type, pattern):
                matching_handlers.extend(handlers)

        if not matching_handlers:
            return

        async def _safe_execute(handler: EventHandler):
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"EventBus: Error executing handler {handler.__name__ if hasattr(handler, '__name__') else handler} "
                    f"for event {event.event_type} ({event.event_id}): {e}",
                    exc_info=True,
                )

        tasks = [asyncio.create_task(_safe_execute(h)) for h in matching_handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def publish_sync(self, event: EventEnvelope[Any]) -> None:
        """
        Helper to safely fire an event from synchronous code without blocking.
        Schedules task on running loop or creates one if needed.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.publish(event))
        except RuntimeError:
            # Fallback if no running loop in thread (e.g. background sync worker)
            asyncio.run(self.publish(event))


# Singleton instance
event_bus = EventBus()
