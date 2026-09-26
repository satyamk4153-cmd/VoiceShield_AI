import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.utils.audio_dsp import decode_wav_file, AudioDecodeError


class BaseSpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe_file(self, file_path: str, language_hint: Optional[str] = None) -> Dict[str, Any]:
        """Transcribes an audio recording file into text with metadata."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Returns provider availability and health status."""
        pass


class AzureSpeechSTTProvider(BaseSpeechToTextProvider):
    """
    Azure AI Speech REST integration for cloud speech transcription.
    """

    def __init__(self):
        self.endpoint = settings.AZURE_SPEECH_ENDPOINT
        self.key = settings.AZURE_SPEECH_KEY
        self.region = settings.AZURE_SPEECH_REGION

    def is_configured(self) -> bool:
        return bool(self.key and (self.region or self.endpoint))

    def health(self) -> Dict[str, Any]:
        return {
            "provider": "Azure AI Speech",
            "configured": self.is_configured(),
            "region": self.region,
            "status": "HEALTHY" if self.is_configured() else "UNCONFIGURED"
        }

    async def transcribe_file(self, file_path: str, language_hint: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured():
            logger.info("Azure Speech key not configured.")
            return {
                "transcript": "",
                "confidence": 0.0,
                "language_detected": "unknown",
                "status": "UNAVAILABLE",
                "reason": "AZURE_SPEECH_NOT_CONFIGURED"
            }

        start_time = time.time()
        url = f"https://{self.region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={language_hint or 'en-US'}&format=detailed"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json"
        }

        try:
            with open(file_path, "rb") as audio_data:
                data = audio_data.read()

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=headers, content=data)
                duration_ms = int((time.time() - start_time) * 1000)

                if res.status_code == 200:
                    payload = res.json()
                    recognition_status = payload.get("RecognitionStatus")
                    if recognition_status == "Success":
                        display_text = payload.get("DisplayText", "")
                        return {
                            "transcript": display_text,
                            "confidence": 0.95,
                            "language_detected": language_hint or "en-US",
                            "duration_ms": duration_ms,
                            "status": "OK"
                        }
                    else:
                        return {
                            "transcript": "",
                            "confidence": 0.0,
                            "language_detected": "unknown",
                            "duration_ms": duration_ms,
                            "status": "NO_SPEECH_DETECTED",
                            "reason": recognition_status
                        }
                else:
                    logger.error(f"Azure Speech API returned status {res.status_code}: {res.text}")
                    return {
                        "transcript": "",
                        "confidence": 0.0,
                        "language_detected": "unknown",
                        "status": "UNAVAILABLE",
                        "reason": f"AZURE_HTTP_{res.status_code}"
                    }

        except Exception as e:
            logger.error(f"Exception during Azure Speech transcription: {e}")
            return {
                "transcript": "",
                "confidence": 0.0,
                "language_detected": "unknown",
                "status": "UNAVAILABLE",
                "reason": str(e)
            }


class LocalSTTProvider(BaseSpeechToTextProvider):
    """
    Local STT provider. If audio is uploaded without text and no cloud STT
    provider is configured, reports STT_UNAVAILABLE honestly rather than
    fabricating a fake transcript.
    """

    def health(self) -> Dict[str, Any]:
        return {
            "provider": "Local Offline STT",
            "configured": True,
            "status": "ACTIVE"
        }

    async def transcribe_file(self, file_path: str, language_hint: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {
                "transcript": "",
                "confidence": 0.0,
                "language_detected": "unknown",
                "status": "FILE_NOT_FOUND"
            }

        try:
            samples, sr, duration = decode_wav_file(file_path)
            # Check if there is active voice
            rms = float(np.sqrt(np.mean(samples ** 2)))
            if rms < 0.005:
                return {
                    "transcript": "",
                    "confidence": 0.0,
                    "language_detected": "none",
                    "status": "SILENCE"
                }

            # In the absence of an on-device ASR weight bundle or Azure credentials:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language_detected": "en",
                "status": "UNAVAILABLE",
                "reason": "OFFLINE_ASR_WEIGHTS_NOT_BUNDLED"
            }
        except AudioDecodeError as e:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language_detected": "unknown",
                "status": "DECODE_ERROR",
                "reason": str(e)
            }


def get_stt_provider() -> BaseSpeechToTextProvider:
    if settings.AI_PROVIDER == "azure" and settings.AZURE_SPEECH_KEY:
        return AzureSpeechSTTProvider()
    return LocalSTTProvider()
