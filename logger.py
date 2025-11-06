# python
"""
Lightweight game logging utilities for state snapshots and discrete events.

Files:
- game_state.jsonl: One JSON object per line, sampled ~1/sec up to _MAX_SECONDS.
  Example entry:
    {"timestamp":"12:34:56.789","elapsed_s":3,"frame":180,"screen_size":[1280,720],
     "updatable":{"count":12,"sprites":[{"type":"Asteroid","pos":[10.5,20.0],"vel":[1.2,-0.3],"rad":16},{"type":"Player","pos":[640.0,360.0],"rot":45.0}]}}
- game_events.jsonl: One JSON object per line per event.
  Example entry:
    {"timestamp":"12:34:59.012","elapsed_s":6,"frame":360,"type":"shot_hit","asteroid_size":16}

Usage:
- Call log_state() once per frame (after updates).
- Call log_event(type, **details) when notable events occur.
"""

import inspect
import json
import math
from datetime import datetime

# Public API of this module
__all__ = ["log_state", "log_event"]

_FPS = 60
_MAX_SECONDS = 16
_SPRITE_SAMPLE_LIMIT = 10  # Max sprites to sample per group snapshot

# Module-level state for throttling and file-init handling
_frame_count = 0
_state_log_initialized = False
_event_log_initialized = False
_start_time = datetime.now()


def log_state():
    """Capture a lightweight snapshot of the game's state about once per second."""
    global _frame_count, _state_log_initialized

    # Stop logging after the time budget is exceeded
    if _frame_count > _FPS * _MAX_SECONDS:
        return

    # Advance frame counter and sample roughly once per second
    _frame_count += 1
    if _frame_count % _FPS != 0:
        return

    now = datetime.now()

    # Introspect caller frame to read local variables from the game loop
    frame = inspect.currentframe()
    if frame is None:
        return

    frame_back = frame.f_back
    if frame_back is None:
        return

    local_vars = frame_back.f_locals.copy()

    screen_size = []
    game_state = {}

    # Look for pygame surfaces and sprite groups in caller locals
    for key, value in local_vars.items():
        # Screen surface (for dimensions)
        if "pygame" in str(type(value)) and hasattr(value, "get_size"):
            screen_size = value.get_size()

        # Sprite groups: sample a limited number of sprites with key properties
        if hasattr(value, "__class__") and "Group" in value.__class__.__name__:
            sprites_data = []

            for i, sprite in enumerate(value):
                if i >= _SPRITE_SAMPLE_LIMIT:
                    break

                sprite_info = {"type": sprite.__class__.__name__}

                if hasattr(sprite, "position"):
                    sprite_info["pos"] = [
                        round(sprite.position.x, 2),
                        round(sprite.position.y, 2),
                    ]

                if hasattr(sprite, "velocity"):
                    sprite_info["vel"] = [
                        round(sprite.velocity.x, 2),
                        round(sprite.velocity.y, 2),
                    ]

                if hasattr(sprite, "radius"):
                    sprite_info["rad"] = sprite.radius

                if hasattr(sprite, "rotation"):
                    sprite_info["rot"] = round(sprite.rotation, 2)

                sprites_data.append(sprite_info)

            game_state[key] = {"count": len(value), "sprites": sprites_data}

        # If no groups found yet, allow logging of a single standalone sprite-like object
        if len(game_state) == 0 and hasattr(value, "position"):
            sprite_info = {"type": value.__class__.__name__}

            sprite_info["pos"] = [
                round(value.position.x, 2),
                round(value.position.y, 2),
            ]

            if hasattr(value, "velocity"):
                sprite_info["vel"] = [
                    round(value.velocity.x, 2),
                    round(value.velocity.y, 2),
                ]

            if hasattr(value, "radius"):
                sprite_info["rad"] = value.radius

            if hasattr(value, "rotation"):
                sprite_info["rot"] = round(value.rotation, 2)

            game_state[key] = sprite_info

    # Build the JSON entry
    entry = {
        "timestamp": now.strftime("%H:%M:%S.%f")[:-3],  # millisecond precision
        "elapsed_s": math.floor((now - _start_time).total_seconds()),
        "frame": _frame_count,
        "screen_size": screen_size,
        **game_state,
    }

    # Create file on first write, append thereafter
    mode = "w" if not _state_log_initialized else "a"
    with open("game_state.jsonl", mode) as f:
        f.write(json.dumps(entry) + "\n")

    _state_log_initialized = True


def log_event(event_type, **details):
    """Append a single event with arbitrary details to the event log."""
    global _event_log_initialized

    now = datetime.now()

    event = {
        "timestamp": now.strftime("%H:%M:%S.%f")[:-3],  # millisecond precision
        "elapsed_s": math.floor((now - _start_time).total_seconds()),
        "frame": _frame_count,  # frame number at time of event
        "type": event_type,
        **details,
    }

    # Create file on first write, append thereafter
    mode = "w" if not _event_log_initialized else "a"
    with open("game_events.jsonl", mode) as f:
        f.write(json.dumps(event) + "\n")

    _event_log_initialized = True