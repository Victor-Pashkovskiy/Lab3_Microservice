
import asyncio
import json
from typing import Callable, Dict, List

class InMemoryEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.history = []
    def subscribe(self, topic: str, callback: Callable):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

    async def publish(self, topic: str, event: dict):
        if event.get("eventId") in self.history:
            print(f"[EventBus] Event {event['eventId']} already processed. Skipping.")
            return
        
        self.history.append(event.get("eventId"))
        print(f"[EventBus] Published to {topic}: {event['eventType']}")
        
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                # Запуск обработчиков
                asyncio.create_task(callback(event))

# глоб экземпляр 
event_bus = InMemoryEventBus()