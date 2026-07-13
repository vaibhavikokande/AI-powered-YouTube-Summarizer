from unittest.mock import MagicMock, patch

from app.services.tts_service import TTSService


async def test_generate_audio_returns_bytes_from_gtts():
    def fake_write_to_fp(fp):
        fp.write(b"fake-mp3-bytes")

    mock_gtts_instance = MagicMock()
    mock_gtts_instance.write_to_fp.side_effect = fake_write_to_fp

    with patch("app.services.tts_service.gTTS", return_value=mock_gtts_instance) as MockGTTS:
        result = await TTSService().generate_audio("Hello world", language="en")

    MockGTTS.assert_called_once_with(text="Hello world", lang="en")
    assert result == b"fake-mp3-bytes"
