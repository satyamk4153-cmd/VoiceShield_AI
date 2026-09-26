import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from fastapi import WebSocket, WebSocketDisconnect
import numpy as np

from app.core.logging import logger
from app.schemas.audio import AudioQualityResult
from app.schemas.speaker import SpeakerVerificationResult
from app.schemas.risk import VoiceAuthenticityResult
from app.schemas.fraud import FraudSignal
from app.services.anti_spoof import _model_instance as anti_spoof_model
from app.services.speaker_verification import _speaker_model as speaker_model
from app.services.fraud_detector import FraudDetectorService
from app.services.risk_engine import RiskEngineService
from app.utils.audio_dsp import compute_audio_quality_metrics, AudioDecodeError


class StreamingSession:
    def __init__(
        self,
        session_id: str,
        organization_id: str = "org-default-01",
        claimed_identity: Optional[str] = None,
        reference_profile_id: Optional[str] = None,
        sample_rate: int = 16000
    ):
        self.session_id = session_id
        self.organization_id = organization_id
        self.claimed_identity = claimed_identity
        self.reference_profile_id = reference_profile_id
        self.sample_rate = sample_rate
        
        self.created_at = datetime.now(timezone.utc)
        self.last_heartbeat = time.time()
        self.chunks_received = 0
        self.raw_pcm_samples: List[float] = []
        self.accumulated_transcript = ""
        self.detected_signals: List[FraudSignal] = []
        self.current_risk_score = 0
        self.current_decision = "ALLOW"
        self.is_active = True

    def append_chunk(self, samples: np.ndarray) -> None:
        self.raw_pcm_samples.extend(samples.tolist())
        self.chunks_received += 1
        self.last_heartbeat = time.time()
        # Cap memory buffer to 5 minutes maximum
        max_samples = self.sample_rate * 300
        if len(self.raw_pcm_samples) > max_samples:
            self.raw_pcm_samples = self.raw_pcm_samples[-max_samples:]


class StreamingManager:
    """
    Manages real-time audio WebSocket streams, incremental DSP feature extraction,
    live anti-spoof scoring, live speaker comparison, and continuous policy evaluation.
    """

    def __init__(self):
        self.active_sessions: Dict[str, StreamingSession] = {}
        self.fraud_detector = FraudDetectorService()

    def create_session(
        self,
        session_id: Optional[str] = None,
        organization_id: str = "org-default-01",
        claimed_identity: Optional[str] = None,
        reference_profile_id: Optional[str] = None,
        sample_rate: int = 16000
    ) -> StreamingSession:
        sid = session_id or str(uuid.uuid4())
        session = StreamingSession(
            session_id=sid,
            organization_id=organization_id,
            claimed_identity=claimed_identity,
            reference_profile_id=reference_profile_id,
            sample_rate=sample_rate
        )
        self.active_sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        return self.active_sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        if session_id in self.active_sessions:
            self.active_sessions[session_id].is_active = False
            del self.active_sessions[session_id]

    async def process_text_event(
        self,
        session: StreamingSession,
        new_text: str,
        websocket: WebSocket
    ) -> Dict[str, Any]:
        """Processes partial or incremental spoken text from the stream."""
        session.accumulated_transcript += " " + new_text.strip()
        
        # Analyze fraud intent
        intent_res = await self.fraud_detector.detect_fraud_intent(
            session.accumulated_transcript, session.claimed_identity
        )
        session.detected_signals = intent_res.detected_signals

        # Live acoustic evaluations on buffered samples
        samples_arr = np.array(session.raw_pcm_samples, dtype=np.float32)
        if len(samples_arr) > int(session.sample_rate * 0.5):
            audio_quality = compute_audio_quality_metrics(samples_arr, session.sample_rate)
            spoof_res = anti_spoof_model.predict(samples_arr, session.sample_rate, audio_quality.telephony_condition)
            voice_auth = VoiceAuthenticityResult(
                authenticity_probability=spoof_res["bonafide_probability"],
                spoof_probability=spoof_res["spoof_probability"],
                confidence=spoof_res["confidence"],
                classification=spoof_res["classification"],
                explanation=spoof_res["explanation"],
                status=spoof_res["status"],
                is_demo=False
            )
        else:
            audio_quality = AudioQualityResult(
                duration_seconds=0.0, sample_rate=session.sample_rate, channels=1,
                rms_energy=0.0, snr_db=0.0, clipping_ratio=0.0, silence_ratio=1.0,
                bandwidth_hz=session.sample_rate // 2, quality_score=0.5,
                quality_level="FAIR", telephony_condition="NORMAL", quality_notes=[]
            )
            voice_auth = VoiceAuthenticityResult(
                authenticity_probability=0.5, spoof_probability=0.5, confidence=0.0,
                classification="UNCERTAIN", explanation="Awaiting sufficient speech samples.",
                status="UNCERTAIN", is_demo=False
            )

        speaker_res = SpeakerVerificationResult(
            similarity=0.5, confidence=0.0, result="UNCERTAIN",
            threshold=0.70, explanation="Awaiting reference comparison.",
            status="NOT_EVALUATED", is_demo=False
        )

        # Re-fuse risk
        risk, evidence, actions = RiskEngineService.fuse_risk_assessment(
            fraud_signals=session.detected_signals,
            contextual_signals=intent_res.contextual_signals,
            voice_auth=voice_auth,
            speaker_verif=speaker_res,
            audio_quality=audio_quality
        )

        session.current_risk_score = risk.score
        session.current_decision = risk.decision

        update_event = {
            "event_type": "RISK_UPDATED",
            "session_id": session.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_score": risk.score,
            "risk_level": risk.level,
            "decision": risk.decision,
            "signals": [s.model_dump() for s in session.detected_signals],
            "actions_required": actions,
            "evidence": [e.model_dump() for e in evidence]
        }
        await websocket.send_json(update_event)
        return update_event


stream_manager = StreamingManager()
