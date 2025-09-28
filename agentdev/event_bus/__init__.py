# agentdev/event_bus/__init__.py
"""
Event Bus - Stub implementation
"""

class StubEventBus:
    def __init__(self):
        pass
    
    def publish(self, *args, **kwargs):
        return {"status": "stub"}

event_bus = StubEventBus()
