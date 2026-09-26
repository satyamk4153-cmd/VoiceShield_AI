import os
from typing import Optional
from app.schemas.audio import AudioQualityResult
from app.utils.audio_dsp import decode_wav_file, compute_audio_quality_metrics, AudioDecodeError
from app.core.logging import logger


class AudioAnalyzerService:
    @staticmethod
    def analyze_audio_quality(file_path: Optional[str]) -> AudioQualityResult:
        """
        Analyzes audio quality, calculating SNR, RMS, clipping, VAD speech ratio,
        and telephony condition directly from waveform samples.
        """
        if not file_path or not os.path.exists(file_path):
            return AudioQualityResult(
                duration_seconds=0.0,
                sample_rate=0,
                channels=0,
                rms_energy=0.0,
                snr_db=0.0,
                clipping_ratio=0.0,
                silence_ratio=1.0,
                bandwidth_hz=0,
                quality_score=0.0,
                quality_level="POOR",
                telephony_condition="NORMAL",
                quality_notes=["No audio file provided for acoustic analysis."]
            )

        try:
            samples, sample_rate, duration = decode_wav_file(file_path)
            return compute_audio_quality_metrics(samples, sample_rate)
        except AudioDecodeError as e:
            logger.error(f"Audio analysis decode failure on {file_path}: {e}")
            raise
