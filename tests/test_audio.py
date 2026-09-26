import io
import wave
import struct
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def generate_synthetic_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 8000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration_sec * sample_rate)
        # Generate simple sine wave
        samples = [int(10000 * struct.unpack('f', struct.pack('f', 0.5))[0]) for _ in range(n_samples)]
        raw_data = struct.pack(f"<{n_samples}h", *samples)
        wf.writeframes(raw_data)
    return buffer.getvalue()


def test_audio_analysis_endpoint_valid_wav():
    wav_bytes = generate_synthetic_wav_bytes(1.0, 8000)
    files = {"audio_file": ("test_call.wav", wav_bytes, "audio/wav")}
    data = {
        "transcript": "Hello Rajesh from HDFC bank, send OTP now.",
        "caller_claimed": "HDFC Bank"
    }
    response = client.post("/api/analyze/audio", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert "risk" in res_data
    assert "voice" in res_data
    assert "audio" in res_data
    assert res_data["audio"]["sample_rate"] == 8000


def test_audio_analysis_unsupported_format():
    files = {"audio_file": ("malicious.exe", b"MZDummyBytes", "application/x-msdownload")}
    response = client.post("/api/analyze/audio", files=files)
    assert response.status_code in [400, 415]


def test_audio_analysis_empty_file():
    files = {"audio_file": ("empty.wav", b"", "audio/wav")}
    response = client.post("/api/analyze/audio", files=files)
    assert response.status_code in [200, 400]
