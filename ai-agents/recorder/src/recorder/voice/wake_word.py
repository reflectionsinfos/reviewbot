"""Wake word detection — "Hey Nexus" activates voice query mode.

Providers: Porcupine (cloud, accurate) | Vosk (local, offline)
Alternative: hotkey Ctrl+Space via pynput.

When activated: starts STT capture for the user's question.
"""

# Implementation: Phase 3
# Skeleton only.


async def listen_for_wake_word() -> None:
    """Block until wake word or hotkey is detected.
    Phase 3 implementation.
    """
    raise NotImplementedError("Wake word detection — Phase 3")
