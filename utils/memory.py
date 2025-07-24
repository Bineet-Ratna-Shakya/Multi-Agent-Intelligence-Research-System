# Memory

from typing import Dict, List, Any
from datetime import datetime, timedelta

class SimpleMemory:
    
    def __init__(self, ttl_minutes: int = 60):
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> None:
        self.storage[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
    
    def retrieve(self, key: str) -> Any:
        if key not in self.storage:
            return None
        
        entry = self.storage[key]
        
        if datetime.now() - entry["timestamp"] > self.ttl:
            del self.storage[key]
            return None
        
        return entry["value"]
    
    def get_metadata(self, key: str) -> Dict[str, Any]:
        if key not in self.storage:
            return {}
        
        entry = self.storage[key]
        
        if datetime.now() - entry["timestamp"] > self.ttl:
            del self.storage[key]
            return {}
        
        return entry["metadata"]
    
    def exists(self, key: str) -> bool:
        return self.retrieve(key) is not None
    
    def clear_expired(self) -> None:
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self.storage.items()
            if current_time - entry["timestamp"] > self.ttl
        ]
        
        for key in expired_keys:
            del self.storage[key]
    
    def clear_all(self) -> None:
        self.storage.clear()
    
    def get_all_keys(self) -> List[str]:
        self.clear_expired()
        return list(self.storage.keys())

