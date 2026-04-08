# Voice Interface

## Use When

- implementing wake word support
- adding voice query STT
- adding TTS playback
- routing audio to a headset-only output

## Current Reality

- voice package structure exists
- actual STT/TTS behavior is still stubbed
- docs make audio-isolation requirements stricter than a normal app

## Non-Negotiables

- TTS must go to an explicit configured output device
- do not rely on system default speakers
- do not allow agent speech to bleed back into meeting capture
- spoken responses should stay short even when full chat responses are long

## Main Files

- `src/recorder/voice/wake_word.py`
- `src/recorder/voice/stt.py`
- `src/recorder/voice/tts.py`
- `src/recorder/voice/audio_router.py`
- `src/recorder/core/config.py`
- `.env.example`

## Common Mistakes

- forgetting to pass or validate device index
- implementing TTS before defining condensation behavior
- ignoring provider-specific config gaps between docs and `settings`

## Minimum Validation

- confirm config values are wired through `settings`
- verify device selection is explicit
- smoke-test provider selection and failure handling
