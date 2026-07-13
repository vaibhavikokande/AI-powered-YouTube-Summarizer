import asyncio
import io

from gtts import gTTS


class TTSService:
    """Generates a spoken-word MP3 of text via gTTS (Google Text-to-Speech)."""

    async def generate_audio(self, text: str, language: str = "en") -> bytes:
        return await asyncio.to_thread(self._synthesize, text, language)

    @staticmethod
    def _synthesize(text: str, language: str) -> bytes:
        buffer = io.BytesIO()
        gTTS(text=text, lang=language).write_to_fp(buffer)
        return buffer.getvalue()
