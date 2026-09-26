from typing import Optional, List
from pydantic import BaseModel, Field


class AudioQualityResult(BaseModel):
    duration_seconds: float = Field(..., description="Duration of the audio clip in seconds")
    sample_rate: int = Field(..., description="Sample rate in Hz (e.g. 8000, 16000, 44100)")
    channels: int = Field(1, description="Number of audio channels")
    rms_energy: float = Field(..., description="Root mean square energy")
    snr_db: float = Field(..., description="Signal-to-noise ratio in decibels")
    clipping_ratio: float = Field(0.0, description="Percentage of clipped samples")
    silence_ratio: float = Field(0.0, description="Percentage of silence / non-speech frames")
    bandwidth_hz: int = Field(4000, description="Estimated frequency bandwidth")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Normalized quality score 0.0-1.0")
    quality_level: str = Field("FAIR", description="GOOD, FAIR, or POOR")
    telephony_condition: str = Field("NORMAL", description="NORMAL, DEGRADED, or HIGHLY_DEGRADED")
    quality_notes: List[str] = Field(default_factory=list)


class AudioAnalysisResponse(BaseModel):
    filename: str
    audio_quality: AudioQualityResult
