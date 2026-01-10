
class EventManager:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, handler):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type, handler):
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def notify(self, event_type, *args, **kwargs):
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(*args, **kwargs)
