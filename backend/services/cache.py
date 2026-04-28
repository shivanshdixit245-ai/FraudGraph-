import time
import threading
from typing import Any, Dict, Optional, Tuple

class TTLCache:
    """
    A thread-safe In-Memory cache with Time-To-Live (TTL) expiration.
    """
    def __init__(self, ttl_seconds: int = 30):
        self.ttl = ttl_seconds
        self.cache: Dict[Any, Tuple[Any, float]] = {}
        self.lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        """
        Retrieves an item from the cache if it hasn't expired.
        Returns None if key is missing or expired.
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expires_at = self.cache[key]
            if time.time() > expires_at:
                del self.cache[key]
                return None
            
            return value

    def set(self, key: Any, value: Any):
        """
        Stores an item in the cache with the configured TTL.
        """
        with self.lock:
            expires_at = time.time() + self.ttl
            self.cache[key] = (value, expires_at)

    def invalidate(self, key: Any):
        """
        Removes a specific key from the cache.
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self):
        """
        Clears all items from the cache.
        """
        with self.lock:
            self.cache.clear()
