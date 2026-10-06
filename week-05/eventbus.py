"""A small in-process event bus (provided — infrastructure, not the lesson).

    bus = EventBus(mode="sync")            # or mode="async"
    bus.subscribe(SomeEvent, handler)      # handler(event) -> None
    bus.publish(SomeEvent(...))

* The publisher never sees a handler's exception: failures are recorded in bus.errors.
* "sync":  handlers run inside publish(), one after the other.
* "async": publish() only puts the event on a queue; a worker thread runs the handlers later.
           bus.drain() waits until the queue is empty (useful in tests and demos).
* No durability: events live in memory. If a handler fails, the event is NOT retried.
  (A production broker such as RabbitMQ or Kafka adds persistence, retries and delivery guarantees.)
"""
import queue
import threading


class EventBus:
    def __init__(self, mode="sync"):
        if mode not in ("sync", "async"):
            raise ValueError("mode must be 'sync' or 'async'")
        self.mode = mode
        self.handlers = {}          # event type -> list of handlers
        self.errors = []            # (handler name, event, exception)
        self.published = []         # every event ever published (for demos and tests)
        if mode == "async":
            self._queue = queue.Queue()
            threading.Thread(target=self._worker, daemon=True).start()

    def subscribe(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def publish(self, event):
        self.published.append(event)
        for handler in self.handlers.get(type(event), []):
            if self.mode == "sync":
                self._deliver(handler, event)
            else:
                self._queue.put((handler, event))

    def drain(self, timeout=5.0):
        """Async mode: block until every queued event has been handled."""
        if self.mode == "async":
            done = threading.Event()
            threading.Thread(target=lambda: (self._queue.join(), done.set()), daemon=True).start()
            done.wait(timeout)

    def _deliver(self, handler, event):
        try:
            handler(event)
        except Exception as exc:  # a consumer's failure must not reach the publisher
            name = getattr(handler, "__qualname__", repr(handler))
            self.errors.append((name, event, exc))

    def _worker(self):
        while True:
            handler, event = self._queue.get()
            self._deliver(handler, event)
            self._queue.task_done()
