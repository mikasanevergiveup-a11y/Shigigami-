"""
Per-chat song queue.

Each entry is a dict:
  {
      "title":     str,
      "url":       str,
      "file":      str,   # local path after download
      "duration":  int,   # seconds
      "thumb":     str,   # thumbnail URL
      "requested_by": str,
  }
"""
from collections import deque
from typing import Deque, Dict, List, Optional

# chat_id -> deque of track dicts
_queues: Dict[int, Deque[dict]] = {}
# chat_id -> currently-playing track dict (or None)
_playing: Dict[int, Optional[dict]] = {}
# chat_id -> loop enabled flag
_loop: Dict[int, bool] = {}


def get_queue(chat_id: int) -> Deque[dict]:
    if chat_id not in _queues:
        _queues[chat_id] = deque()
    return _queues[chat_id]


def add_to_queue(chat_id: int, track: dict) -> int:
    """Add a track; return its 1-based position in queue."""
    q = get_queue(chat_id)
    q.append(track)
    return len(q)


def get_current(chat_id: int) -> Optional[dict]:
    return _playing.get(chat_id)


def set_current(chat_id: int, track: Optional[dict]) -> None:
    _playing[chat_id] = track


def next_track(chat_id: int) -> Optional[dict]:
    """Pop the next track from the queue (or loop the current one)."""
    if _loop.get(chat_id) and _playing.get(chat_id):
        return _playing[chat_id]
    q = get_queue(chat_id)
    if not q:
        _playing[chat_id] = None
        return None
    track = q.popleft()
    _playing[chat_id] = track
    return track


def clear_queue(chat_id: int) -> None:
    _queues[chat_id] = deque()
    _playing[chat_id] = None
    _loop[chat_id] = False


def queue_list(chat_id: int) -> List[dict]:
    return list(get_queue(chat_id))


def toggle_loop(chat_id: int) -> bool:
    _loop[chat_id] = not _loop.get(chat_id, False)
    return _loop[chat_id]


def is_loop(chat_id: int) -> bool:
    return _loop.get(chat_id, False)
