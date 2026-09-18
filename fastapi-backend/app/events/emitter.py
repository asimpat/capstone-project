from collections import defaultdict
from typing import Callable, Any


class EventEmitter:
    def __init__(self):
        self.listeners = defaultdict(list)

    def on(self, event_name: str, listener: Callable):
        self.listeners[event_name].append(listener)

    def emit(self, event_name: str, data: Any = None):
        for listener in self.listeners[event_name]:
            try:
                listener(data)
            except Exception as e:
                print(
                    f"Event listener failed for "
                    f"{event_name}: {e}"
                )


event_emitter = EventEmitter()
