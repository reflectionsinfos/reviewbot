"""
Voice Interface Module
Handles speech-to-text and text-to-speech conversions
"""
import os
from typing import Optional, BinaryIO
from pathlib import Path
from app.core.config import settings


class VoiceInterface:
    """Handle voice interactions (STT and TTS)"""
    
    def __init__(self):
        self.openai_client = None
        self.elevenlabs_client = None
        
        # Initialize OpenAI if API key available
        if settings.OPENAI_API_KEY:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize ElevenLabs if API key available
        if settings.ELEVENLABS_API_KEY:
            # Optional: from elevenlabs import ElevenLabs
            # self.elevenlabs_client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
            pass
    
    async def speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """
        Convert speech audio file to text transcript
        Uses OpenAI Whisper API
        """
        if not self.openai_client:
            return None
        
        try:
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            with open(audio_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=settings.DEFAULT_LANGUAGE
                )
            
            return transcript.text
        except Exception as e:
            print(f"STT Error: {e}")
            return None
    
    async def text_to_speech(self, text: str, output_path: str, voice: str = "alloy") -> bool:
        """
        Convert text to speech audio
        Uses OpenAI TTS API (or ElevenLabs if configured)
        """
        if not self.openai_client:
            return False
        
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Save to file
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            response.stream_to_file(str(output))
            
            return True
        except Exception as e:
            print(f"TTS Error: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available voice options"""
        return [
            {"id": "alloy", "name": "Alloy (Neutral)"},
            {"id": "echo", "name": "Echo (Male)"},
            {"id": "fable", "name": "Fable (British)"},
            {"id": "onyx", "name": "Onyx (Deep)"},
            {"id": "nova", "name": "Nova (Female)"},
            {"id": "shimmer", "name": "Shimmer (Warm)"}
        ]
    
    async def process_voice_input(
        self,
        audio_file_path: str,
        context: Optional[str] = None
    ) -> dict:
        """
        Process voice input and return structured response
        """
        transcript = await self.speech_to_text(audio_file_path)
        
        if not transcript:
            return {
                "success": False,
                "transcript": None,
                "error": "Could not transcribe audio"
            }
        
        # Simple intent detection based on keywords
        transcript_lower = transcript.lower()
        intent = "answer"
        
        if any(word in transcript_lower for word in ["yes", "yeah", "yep", "correct"]):
            intent = "affirmative"
        elif any(word in transcript_lower for word in ["no", "nope", "incorrect"]):
            intent = "negative"
        elif any(word in transcript_lower for word in ["skip", "next", "later"]):
            intent = "skip"
        elif any(word in transcript_lower for word in ["repeat", "again", "what"]):
            intent = "clarify"
        
        return {
            "success": True,
            "transcript": transcript,
            "intent": intent,
            "context": context
        }


# Global instance
_voice_interface: Optional[VoiceInterface] = None


def get_voice_interface() -> VoiceInterface:
    """Get or create voice interface instance"""
    global _voice_interface
    if _voice_interface is None:
        _voice_interface = VoiceInterface()
    return _voice_interface
