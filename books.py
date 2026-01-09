"""
Meta Vault Event Serialization (Books)
Handles JSON serialization for game events to prevent memory leaks in multiprocessing
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
from datetime import datetime


class EventEncoder(json.JSONEncoder):
    """Custom JSON encoder for game events"""
    
    def default(self, obj: Any) -> Any:
        # Handle Enum types
        if isinstance(obj, Enum):
            return obj.value
        
        # Handle dataclasses
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        return super().default(obj)


def serialize_event(event: Dict[str, Any]) -> str:
    """
    Safely serialize a game event to JSON string.
    
    This function ensures that all game events are properly serialized
    to prevent memory leaks when passing data between processes.
    
    Args:
        event: Event dictionary to serialize
    
    Returns:
        JSON string representation of the event
    """
    try:
        return json.dumps(event, cls=EventEncoder, separators=(',', ':'))
    except (TypeError, ValueError) as e:
        # Fallback: convert problematic values to strings
        safe_event = _make_serializable(event)
        return json.dumps(safe_event, separators=(',', ':'))


def deserialize_event(event_str: str) -> Dict[str, Any]:
    """
    Safely deserialize a JSON string to event dictionary.
    
    Args:
        event_str: JSON string to deserialize
    
    Returns:
        Event dictionary
    """
    return json.loads(event_str)


def _make_serializable(obj: Any) -> Any:
    """Recursively convert object to serializable form"""
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, set):
        return [_make_serializable(item) for item in obj]
    elif hasattr(obj, '__dataclass_fields__'):
        return _make_serializable(asdict(obj))
    elif hasattr(obj, '__dict__'):
        return _make_serializable(obj.__dict__)
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


@dataclass
class SerializedSpinResult:
    """Serialization-safe version of SpinResult"""
    reels: List[List[str]]
    original_reels: List[List[str]]
    wins: List[Dict[str, Any]]
    total_win: float
    multiplier: float
    collector_count: int
    transformations_applied: List[str]
    events: List[Dict[str, Any]]
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return serialize_event(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SerializedSpinResult':
        """Create from JSON string"""
        data = deserialize_event(json_str)
        return cls(**data)


class EventQueue:
    """
    Thread-safe event queue for multiprocessing scenarios.
    
    Prevents memory leaks by ensuring events are serialized before
    being passed between threads/processes.
    """
    
    def __init__(self, max_size: int = 1000):
        self._queue: queue.Queue = queue.Queue(maxsize=max_size)
        self._lock = threading.Lock()
    
    def push(self, event: Dict[str, Any]) -> bool:
        """
        Push an event to the queue.
        
        Events are serialized immediately to prevent holding references
        to complex objects.
        
        Args:
            event: Event dictionary to queue
        
        Returns:
            True if event was queued, False if queue is full
        """
        try:
            serialized = serialize_event(event)
            self._queue.put_nowait(serialized)
            return True
        except queue.Full:
            return False
    
    def pop(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Pop an event from the queue.
        
        Args:
            timeout: Maximum time to wait (None = non-blocking)
        
        Returns:
            Event dictionary or None if queue is empty
        """
        try:
            if timeout is None:
                serialized = self._queue.get_nowait()
            else:
                serialized = self._queue.get(timeout=timeout)
            return deserialize_event(serialized)
        except queue.Empty:
            return None
    
    def flush(self) -> List[Dict[str, Any]]:
        """
        Get all events from the queue.
        
        Returns:
            List of all queued events
        """
        events = []
        while True:
            event = self.pop()
            if event is None:
                break
            events.append(event)
        return events
    
    def size(self) -> int:
        """Get current queue size"""
        return self._queue.qsize()
    
    def clear(self) -> None:
        """Clear all events from queue"""
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break


def create_spin_event(
    spin_id: str,
    reels: List[List[Any]],
    wins: List[Dict[str, Any]],
    total_win: float,
    collector_count: int
) -> str:
    """
    Create a serialized spin event for multiprocessing transmission.
    
    Args:
        spin_id: Unique spin identifier
        reels: Reel result grid
        wins: List of win dictionaries
        total_win: Total win amount
        collector_count: Current collector count
    
    Returns:
        JSON string of the spin event
    """
    event = {
        "type": "spinResult",
        "spinId": spin_id,
        "reels": [[sym.value if hasattr(sym, 'value') else str(sym) for sym in reel] for reel in reels],
        "wins": wins,
        "totalWin": total_win,
        "collectorCount": collector_count,
        "timestamp": datetime.now().isoformat()
    }
    return serialize_event(event)


def create_transformation_event(
    threshold: int,
    transformation: str,
    positions: List[tuple]
) -> str:
    """
    Create a serialized transformation event.
    
    Args:
        threshold: Threshold that triggered transformation
        transformation: Type of transformation (e.g., "H4_TO_H1")
        positions: List of affected positions
    
    Returns:
        JSON string of the transformation event
    """
    event = {
        "type": "symbolTransformation",
        "threshold": threshold,
        "transformation": transformation,
        "positions": positions,
        "timestamp": datetime.now().isoformat()
    }
    return serialize_event(event)


def create_collection_event(
    previous_count: int,
    new_count: int,
    positions: List[tuple]
) -> str:
    """
    Create a serialized collection event for CollectionBar updates.
    
    Args:
        previous_count: Previous collector count
        new_count: New collector count
        positions: Positions where collectors landed
    
    Returns:
        JSON string of the collection event
    """
    event = {
        "type": "collectorCollection",
        "previousCount": previous_count,
        "newCount": new_count,
        "collected": new_count - previous_count,
        "positions": positions,
        "triggerPulse": True,
        "timestamp": datetime.now().isoformat()
    }
    return serialize_event(event)
