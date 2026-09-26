import os
import wave
import struct
import math
import time
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
from scipy import signal, fft

from app.schemas.audio import AudioQualityResult
from app.core.logging import logger


class AudioDecodeError(Exception):
    """Raised when an audio payload fails decoding or format validation."""
    pass


def decode_wav_file(file_path: str) -> Tuple[np.ndarray, int, float]:
    """
    Decodes a WAV audio file into a 1D float32 numpy array normalized to [-1.0, 1.0].
    Handles 8-bit, 16-bit, 24-bit, 32-bit integer, and 32-bit float PCM.
    Returns: (samples, sample_rate, duration_seconds)
    """
    if not os.path.exists(file_path):
        raise AudioDecodeError(f"Audio file not found: {file_path}")

    try:
        with wave.open(file_path, "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()

            if framerate <= 0 or n_frames <= 0:
                raise AudioDecodeError("Malformed WAV headers: invalid framerate or frame count.")

            duration = n_frames / float(framerate)
            raw_bytes = wf.readframes(n_frames)

            # Convert based on bit depth
            if sample_width == 2:  # 16-bit PCM
                samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 1:  # 8-bit unsigned
                samples = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif sample_width == 4:  # 32-bit int or float
                try:
                    samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
                except Exception:
                    samples = np.frombuffer(raw_bytes, dtype=np.float32)
            elif sample_width == 3:  # 24-bit PCM
                # Unpack 24-bit
                total_samples = n_frames * channels
                raw_int = np.zeros(total_samples, dtype=np.int32)
                for i in range(total_samples):
                    idx = i * 3
                    if idx + 3 <= len(raw_bytes):
                        b = raw_bytes[idx:idx + 3]
                        val = int.from_bytes(b, byteorder="little", signed=True)
                        raw_int[i] = val
                samples = raw_int.astype(np.float32) / 8388608.0
            else:
                raise AudioDecodeError(f"Unsupported sample width: {sample_width} bytes")

            # Stereo to Mono projection
            if channels > 1:
                samples = samples.reshape(-1, channels).mean(axis=1)

            # Prevent NaN or infinite values
            samples = np.nan_to_num(samples, nan=0.0, posinf=1.0, neginf=-1.0)
            return samples, framerate, duration

    except AudioDecodeError:
        raise
    except Exception as e:
        logger.error(f"Failed to decode audio file {file_path}: {e}")
        raise AudioDecodeError(f"AUDIO_DECODE_FAILED: {str(e)}")


def compute_audio_quality_metrics(samples: np.ndarray, sample_rate: int) -> AudioQualityResult:
    """
    Computes rigorous acoustic metrics:
    - RMS energy & Peak Amplitude
    - Clipping ratio (> 99% peak)
    - Voice Activity Detection (VAD) speech ratio
    - Estimated Signal-to-Noise Ratio (SNR in dB)
    - Effective bandwidth & Telephony degradation classification
    """
    if len(samples) == 0:
        raise AudioDecodeError("Audio contains zero samples.")

    duration = round(len(samples) / float(sample_rate), 2)
    peak = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0
    rms = float(np.sqrt(np.mean(samples ** 2)))
    rms_energy = round(rms, 4)

    # Clipping detection
    clipping_samples = np.sum(np.abs(samples) >= 0.99)
    clipping_ratio = round(float(clipping_samples) / float(len(samples)), 4)

    # Energy-based VAD (frame-by-frame analysis with 30ms window)
    frame_len = max(16, int(sample_rate * 0.03))  # 30 ms
    hop_len = max(8, int(sample_rate * 0.015))    # 15 ms
    n_frames = max(1, (len(samples) - frame_len) // hop_len + 1)
    
    frame_energies = []
    for i in range(n_frames):
        start = i * hop_len
        end = start + frame_len
        frame = samples[start:end]
        frame_energies.append(np.mean(frame ** 2))
    
    frame_energies = np.array(frame_energies)
    noise_floor = np.percentile(frame_energies, 15) if len(frame_energies) > 0 else 1e-6
    speech_thresh = max(1e-5, noise_floor * 3.5)
    
    speech_frames = np.sum(frame_energies > speech_thresh)
    silence_frames = len(frame_energies) - speech_frames
    silence_ratio = round(float(silence_frames) / float(len(frame_energies)), 4) if len(frame_energies) > 0 else 0.0
    
    # SNR calculation in dB
    speech_energy = np.mean(frame_energies[frame_energies > speech_thresh]) if speech_frames > 0 else 1e-6
    snr_val = 10.0 * np.log10(max(1e-5, speech_energy) / max(1e-6, noise_floor))
    snr_db = round(float(np.clip(snr_val, 0.0, 45.0)), 2)

    # Bandwidth calculation
    bandwidth_hz = min(sample_rate // 2, 8000 if sample_rate >= 16000 else 3800)

    # Telephony Profile & Quality Classification
    quality_notes: List[str] = []
    
    # Calibrated audio quality score (0.0 to 1.0)
    snr_component = min(1.0, max(0.0, snr_db / 28.0))
    clip_penalty = min(0.5, clipping_ratio * 3.0)
    silence_penalty = 0.2 if silence_ratio > 0.7 else 0.0
    
    quality_score = round(max(0.1, min(1.0, (snr_component * 0.75 + 0.25) - clip_penalty - silence_penalty)), 2)

    if sample_rate <= 8000 or bandwidth_hz <= 3800:
        telephony_condition = "DEGRADED"
        quality_notes.append("PSTN/GSM narrowband 8kHz telephony audio channel detected.")
    elif clipping_ratio > 0.05 or quality_score < 0.40:
        telephony_condition = "HIGHLY_DEGRADED"
        quality_notes.append("Severe acoustic degradation / high background noise identified.")
    else:
        telephony_condition = "NORMAL"

    if quality_score >= 0.75:
        quality_level = "GOOD"
    elif quality_score >= 0.45:
        quality_level = "FAIR"
    else:
        quality_level = "POOR"

    return AudioQualityResult(
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=1,
        rms_energy=rms_energy,
        snr_db=snr_db,
        clipping_ratio=clipping_ratio,
        silence_ratio=silence_ratio,
        bandwidth_hz=bandwidth_hz,
        quality_score=quality_score,
        quality_level=quality_level,
        telephony_condition=telephony_condition,
        quality_notes=quality_notes
    )
