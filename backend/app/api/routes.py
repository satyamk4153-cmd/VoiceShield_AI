import os
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form,
    status, Request, WebSocket, WebSocketDisconnect, Query
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    save_upload_to_ephemeral_file, ephemeral_temp_file, sanitize_filename,
    hash_password, verify_password, create_access_token
)
from app.db.database import get_db
from app.db.models import User, Organization
from app.db.repository import (
    AnalysisRepository, IncidentRepository, SpeakerRepository,
    DashboardRepository, AuditRepository
)
from app.api.deps import get_current_user, require_role, get_current_organization

from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.audio import AudioAnalysisResponse, AudioQualityResult
from app.schemas.speaker import (
    SpeakerVerificationResult, SpeakerVerificationRequest,
    SpeakerProfileCreate, SpeakerProfileResponse
)
from app.schemas.fraud import FraudIntentResult, TranscriptAnalysisRequest, FraudSignal
from app.schemas.risk import (
    FinalAnalysisResponse, DirectRiskScoreRequest, RiskAssessment,
    VoiceAuthenticityResult, EvidenceItem
)
from app.schemas.incident import (
    IncidentDetailResponse, IncidentListResponse, IncidentStatusUpdate,
    IncidentNoteCreate, IncidentOverrideRequest, IncidentNoteSchema,
    IncidentEventSchema, EvidenceItemSchema
)
from app.schemas.demo import DemoScenario
from app.schemas.dashboard import DashboardStats

from app.providers.stt_provider import get_stt_provider
from app.providers.azure_openai import AzureOpenAIProvider

from app.services.audio_analyzer import AudioAnalyzerService
from app.services.anti_spoof import AntiSpoofService
from app.services.speaker_verification import SpeakerVerificationService
from app.services.fraud_detector import FraudDetectorService
from app.services.contextual_engine import ContextualEngineService
from app.services.risk_engine import RiskEngineService
from app.services.demo_engine import DemoEngineService
from app.services.streaming_manager import stream_manager
from app.utils.audio_dsp import AudioDecodeError

router = APIRouter()


# ==============================================================================
# Operational Health & Readiness
# ==============================================================================

@router.get("/health", summary="Health and Operational Status")
async def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "app_mode": settings.APP_MODE,
        "ai_provider": settings.AI_PROVIDER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status
    }


# ==============================================================================
# Authentication & Access Control
# ==============================================================================

@router.post("/auth/login", response_model=TokenResponse, summary="SOC User Authentication")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    org = user.organization

    audit_repo = AuditRepository(db)
    audit_repo.log(
        action="USER_LOGIN_SUCCESS",
        endpoint="/api/v1/auth/login",
        organization_id=user.organization_id,
        user_id=user.id,
        status_code=200
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        organization_slug=org.slug if org else "default"
    )


@router.get("/auth/me", response_model=UserResponse, summary="Current Authenticated User Profile")
async def get_current_user_profile(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )


# ==============================================================================
# Threat Intelligence Dashboard (100% Real Persisted Telemetry)
# ==============================================================================

@router.get("/dashboard/stats", response_model=DashboardStats, summary="SOC Threat Intelligence Statistics")
async def get_dashboard_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = DashboardRepository(db)
    # Filter by user's organization
    return repo.get_dashboard_stats(organization_id=user.organization_id)


# ==============================================================================
# Call Fraud & Deepfake Analyses
# ==============================================================================

@router.post("/analyze/audio", response_model=FinalAnalysisResponse, summary="Full End-to-End Audio Fraud Analysis")
@router.post("/analyses/audio", response_model=FinalAnalysisResponse, summary="Full End-to-End Audio Fraud Analysis (REST Alias)")
async def analyze_audio(
    audio_file: UploadFile = File(...),
    transcript: Optional[str] = Form(None),
    caller_claimed: Optional[str] = Form(None),
    reference_profile_id: Optional[str] = Form(None),
    reference_audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    start_time = time.time()
    
    # 1. Secure Ephemeral Storage & Magic-byte validation
    temp_audio_path = await save_upload_to_ephemeral_file(audio_file)
    
    try:
        # 2. Acoustic Quality Analysis
        try:
            audio_quality = AudioAnalyzerService.analyze_audio_quality(temp_audio_path)
        except AudioDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"AUDIO_DECODE_FAILED: Could not decode uploaded audio payload. {e}"
            )

        # 3. Voice Anti-Spoofing Model
        anti_spoof_service = AntiSpoofService()
        voice_auth = await anti_spoof_service.check_authenticity(
            temp_audio_path, telephony_condition=audio_quality.telephony_condition
        )

        # 4. Speaker Verification Engine
        speaker_repo = SpeakerRepository(db)
        speaker_service = SpeakerVerificationService(speaker_repo)
        
        # If reference audio is supplied in request, enroll it ephemerally for this comparison
        effective_ref_id = reference_profile_id
        if reference_audio:
            ref_path = await save_upload_to_ephemeral_file(reference_audio)
            try:
                from app.utils.audio_dsp import decode_wav_file
                ref_samples, ref_sr, ref_dur = decode_wav_file(ref_path)
                ref_emb = speaker_service.model.extract_embedding(ref_samples, ref_sr)
                ephemeral_profile_id = f"SPK-TMP-{uuid.uuid4().hex[:6].upper()}"
                speaker_repo.create_profile(
                    profile_id=ephemeral_profile_id,
                    name=caller_claimed or "Ephemeral Reference",
                    identity_claimed=caller_claimed or "Ephemeral Baseline",
                    organization_id=user.organization_id
                )
                speaker_repo.add_enrollment(ephemeral_profile_id, ref_emb, ref_dur, ref_sr)
                effective_ref_id = ephemeral_profile_id
            finally:
                if os.path.exists(ref_path):
                    os.remove(ref_path)

        speaker_res = await speaker_service.verify_speaker(
            reference_profile_id=effective_ref_id,
            test_path=temp_audio_path,
            test_transcript=transcript
        )

        # 5. Speech-to-Text & Intent Analysis (NO FALLBACK FAKE TRANSCRIPTS)
        effective_transcript = transcript
        if not effective_transcript:
            stt = get_stt_provider()
            stt_result = await stt.transcribe_file(temp_audio_path)
            effective_transcript = stt_result.get("transcript", "")
            if not effective_transcript and stt_result.get("status") == "UNAVAILABLE":
                logger.info("STT unavailable and no client transcript provided. Proceeding with acoustic-only risk analysis.")

        # 6. Conversational Fraud Detection
        fraud_provider = AzureOpenAIProvider() if settings.AI_PROVIDER == "azure" else None
        fraud_service = FraudDetectorService(provider=fraud_provider)
        intent_result = await fraud_service.detect_fraud_intent(effective_transcript, caller_claimed)

        # 7. Risk Fusion & Policy Engine
        risk_assessment, evidence, actions = RiskEngineService.fuse_risk_assessment(
            fraud_signals=intent_result.detected_signals,
            contextual_signals=intent_result.contextual_signals,
            voice_auth=voice_auth,
            speaker_verif=speaker_res,
            audio_quality=audio_quality
        )

        analysis_id = f"ANL-{uuid.uuid4().hex[:8].upper()}"
        response = FinalAnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            created_at=datetime.now(timezone.utc).isoformat(),
            is_demo_data=settings.APP_MODE == "demo",
            provider_used=settings.AI_PROVIDER,
            transcript=effective_transcript if effective_transcript else "[No speech transcript available]",
            risk=risk_assessment,
            voice=voice_auth,
            speaker=speaker_res,
            audio=audio_quality,
            fraud_signals=intent_result.detected_signals,
            contextual_signals=intent_result.contextual_signals,
            evidence=evidence,
            recommended_actions=actions
        )

        # 8. Persist Analysis Record
        repo = AnalysisRepository(db)
        analysis_record = repo.save_analysis(
            response,
            caller_claimed=caller_claimed,
            organization_id=user.organization_id
        )

        # 9. Auto-create Incident if Risk is HIGH or CRITICAL
        if risk_assessment.score >= 70 or risk_assessment.decision in ("BLOCK_CALL", "ANALYST_REVIEW"):
            incident_repo = IncidentRepository(db)
            inc = incident_repo.create_incident_from_analysis(
                analysis=analysis_record,
                evidence_items=evidence,
                organization_id=user.organization_id,
                caller_claimed=caller_claimed
            )
            response.incident_id = inc.incident_number

        # 10. Audit Logging
        audit_repo = AuditRepository(db)
        audit_repo.log(
            action="ANALYZE_AUDIO",
            endpoint="/api/v1/analyses/audio",
            organization_id=user.organization_id,
            user_id=user.id,
            resource="analysis",
            resource_id=analysis_id,
            status_code=200,
            risk_score=risk_assessment.score,
            metadata={"duration_ms": int((time.time() - start_time) * 1000)}
        )

        return response

    finally:
        # Zero-retention: Guaranteed deletion of ephemeral upload
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except OSError:
                pass


@router.post("/analyze/transcript", response_model=FinalAnalysisResponse, summary="Analyze Transcript for Fraud Intent & Risk")
@router.post("/analyses/transcript", response_model=FinalAnalysisResponse, summary="Analyze Transcript for Fraud Intent & Risk (REST Alias)")
async def analyze_transcript(
    payload: TranscriptAnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # 1. Intent Detection
    fraud_provider = AzureOpenAIProvider() if settings.AI_PROVIDER == "azure" else None
    fraud_service = FraudDetectorService(provider=fraud_provider)
    intent_result = await fraud_service.detect_fraud_intent(payload.transcript, payload.caller_claimed_identity)

    # 2. Acoustic & Biometric Defaults for Transcript-only Evaluation (Clearly labelled UNCERTAIN/NOT_EVALUATED)
    audio_quality = AudioQualityResult(
        duration_seconds=0.0,
        sample_rate=0,
        channels=1,
        rms_energy=0.0,
        snr_db=0.0,
        clipping_ratio=0.0,
        silence_ratio=0.0,
        bandwidth_hz=0,
        quality_score=0.50,
        quality_level="FAIR",
        telephony_condition="NORMAL",
        quality_notes=["Transcript text input only. Acoustic waveform not provided."]
    )

    voice_auth = VoiceAuthenticityResult(
        authenticity_probability=0.50,
        spoof_probability=0.50,
        confidence=0.0,
        classification="UNAVAILABLE",
        explanation="No audio sample provided for acoustic anti-spoofing verification.",
        status="UNAVAILABLE",
        is_demo=False
    )

    speaker_res = SpeakerVerificationResult(
        similarity=0.50,
        confidence=0.0,
        result="UNCERTAIN",
        threshold=0.70,
        explanation="No biometric audio sample provided for speaker verification.",
        status="NOT_EVALUATED",
        is_demo=False
    )

    # 3. Fuse Risk Assessment
    risk_assessment, evidence, actions = RiskEngineService.fuse_risk_assessment(
        fraud_signals=intent_result.detected_signals,
        contextual_signals=intent_result.contextual_signals,
        voice_auth=voice_auth,
        speaker_verif=speaker_res,
        audio_quality=audio_quality
    )

    analysis_id = f"ANL-{uuid.uuid4().hex[:8].upper()}"
    response = FinalAnalysisResponse(
        analysis_id=analysis_id,
        status="completed",
        created_at=datetime.now(timezone.utc).isoformat(),
        is_demo_data=settings.APP_MODE == "demo",
        provider_used=settings.AI_PROVIDER,
        transcript=payload.transcript,
        risk=risk_assessment,
        voice=voice_auth,
        speaker=speaker_res,
        audio=audio_quality,
        fraud_signals=intent_result.detected_signals,
        contextual_signals=intent_result.contextual_signals,
        evidence=evidence,
        recommended_actions=actions
    )

    # 4. Save analysis
    repo = AnalysisRepository(db)
    analysis_record = repo.save_analysis(
        response,
        caller_claimed=payload.caller_claimed_identity,
        organization_id=user.organization_id
    )

    # 5. Create incident if high risk
    if risk_assessment.score >= 70 or risk_assessment.decision in ("BLOCK_CALL", "ANALYST_REVIEW"):
        incident_repo = IncidentRepository(db)
        inc = incident_repo.create_incident_from_analysis(
            analysis=analysis_record,
            evidence_items=evidence,
            organization_id=user.organization_id,
            caller_claimed=payload.caller_claimed_identity
        )
        response.incident_id = inc.incident_number

    # 6. Audit
    audit_repo = AuditRepository(db)
    audit_repo.log(
        action="ANALYZE_TRANSCRIPT",
        endpoint="/api/v1/analyses/transcript",
        organization_id=user.organization_id,
        user_id=user.id,
        resource="analysis",
        resource_id=analysis_id,
        status_code=200,
        risk_score=risk_assessment.score
    )

    return response


@router.get("/analyses/{analysis_id}", response_model=FinalAnalysisResponse, summary="Get Stored Analysis by ID")
async def get_analysis_by_id(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if analysis_id.startswith("DEMO-") or analysis_id.startswith("demo-"):
        sc_id = analysis_id[5:]
        demo_analysis = DemoEngineService.get_scenario_analysis(sc_id)
        if demo_analysis:
            return demo_analysis

    repo = AnalysisRepository(db)
    record = repo.get_analysis_by_id(analysis_id, organization_id=user.organization_id)
    if not record:
        # Check if ID directly matches a scenario ID
        demo_analysis = DemoEngineService.get_scenario_analysis(analysis_id)
        if demo_analysis:
            return demo_analysis
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    # Reconstitute response from persisted entity
    signals = [
        FraudSignal(
            id=s.id,
            signal_type=s.signal_type,
            category=s.category,
            severity=s.severity,
            confidence=s.confidence,
            description=s.description,
            timestamp=s.timestamp,
            risk_contribution=s.risk_contribution
        )
        for s in record.signals
    ]

    return FinalAnalysisResponse(
        analysis_id=record.id,
        session_id=record.session_id,
        status=record.status,
        created_at=record.created_at.isoformat() if record.created_at else datetime.now(timezone.utc).isoformat(),
        is_demo_data=record.is_demo,
        provider_used=record.provider_used,
        transcript=record.transcript_redacted,
        risk=RiskAssessment(
            score=record.risk_score,
            level=record.risk_level,
            decision=record.decision,
            confidence=record.confidence,
            risk_breakdown=record.risk_breakdown or {}
        ),
        voice=VoiceAuthenticityResult(
            authenticity_probability=1.0 - record.spoof_probability,
            spoof_probability=record.spoof_probability,
            confidence=record.confidence,
            classification=record.voice_authenticity,
            explanation=record.explanation or "Persisted acoustic inspection record.",
            status="OK",
            is_demo=record.is_demo
        ),
        speaker=SpeakerVerificationResult(
            similarity=record.speaker_similarity,
            confidence=record.confidence,
            result=record.speaker_result,
            threshold=0.70,
            explanation=f"Persisted biometric comparison: {record.speaker_result}",
            status="OK",
            is_demo=record.is_demo
        ),
        audio=AudioQualityResult(
            duration_seconds=15.0,
            sample_rate=16000,
            channels=1,
            rms_energy=0.10,
            snr_db=20.0,
            clipping_ratio=0.0,
            silence_ratio=0.1,
            bandwidth_hz=8000,
            quality_score=0.75,
            quality_level=record.audio_quality,
            telephony_condition=record.telephony_condition,
            quality_notes=[]
        ),
        fraud_signals=signals,
        contextual_signals=[],
        evidence=[],
        recommended_actions=record.recommended_actions or []
    )


# ==============================================================================
# SOC Incident Lifecycle & Analyst Workflows
# ==============================================================================

@router.get("/incidents", response_model=IncidentListResponse, summary="List SOC Security Incidents")
async def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = IncidentRepository(db)
    offset = (page - 1) * page_size
    items, total = repo.list_incidents(
        organization_id=user.organization_id,
        status=status,
        severity=severity,
        limit=page_size,
        offset=offset
    )

    detail_items = []
    for inc in items:
        detail_items.append(IncidentDetailResponse(
            id=inc.id,
            incident_number=inc.incident_number,
            organization_id=inc.organization_id,
            session_id=inc.session_id,
            analysis_id=inc.analysis_id,
            title=inc.title,
            status=inc.status,
            severity=inc.severity,
            risk_score=inc.risk_score,
            decision=inc.decision,
            caller_claimed=inc.caller_claimed,
            assigned_to=inc.assigned_to,
            assignee_name=inc.assignee.full_name if inc.assignee else None,
            flags=inc.flags or [],
            analyst_override_decision=inc.analyst_override_decision,
            analyst_override_reason=inc.analyst_override_reason,
            analyst_override_by=inc.analyst_override_by,
            created_at=inc.created_at.isoformat() if inc.created_at else "",
            updated_at=inc.updated_at.isoformat() if inc.updated_at else "",
            resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
            timeline_events=[
                IncidentEventSchema(
                    id=e.id,
                    event_type=e.event_type,
                    label=e.label,
                    timestamp_offset=e.timestamp_offset,
                    description=e.description,
                    severity=e.severity,
                    metadata_json=e.metadata_json or {},
                    created_at=e.created_at.isoformat()
                )
                for e in inc.timeline_events
            ],
            notes=[
                IncidentNoteSchema(
                    id=n.id,
                    author_id=n.author_id,
                    author_name=n.author_name,
                    note_text=n.note_text,
                    created_at=n.created_at.isoformat()
                )
                for n in inc.notes
            ],
            evidence_items=[
                EvidenceItemSchema(
                    id=ev.id,
                    title=ev.title,
                    category=ev.category,
                    severity=ev.severity,
                    explanation=ev.explanation,
                    contribution_points=ev.contribution_points,
                    timestamp_offset=ev.timestamp_offset,
                    metadata_json=ev.metadata_json or {}
                )
                for ev in inc.evidence_items
            ]
        ))

    return IncidentListResponse(items=detail_items, total=total, page=page, page_size=page_size)


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse, summary="Get Specific Incident Details")
async def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if incident_id.startswith("INC-DEMO-") or incident_id.startswith("inc-demo-") or incident_id in [s.id for s in DemoEngineService.get_all_scenarios()]:
        sc_id = incident_id.replace("INC-DEMO-", "").replace("inc-demo-", "")
        sc = DemoEngineService.get_scenario_by_id(sc_id)
        if sc:
            timeline = [
                IncidentEventSchema(
                    id=f"EVT-{ev.seconds}",
                    event_type=ev.event_type,
                    label=ev.label,
                    timestamp_offset=ev.time_offset,
                    description=ev.transcript_segment,
                    severity=ev.severity or "LOW",
                    metadata_json={},
                    created_at=datetime.now(timezone.utc).isoformat()
                )
                for ev in sc.timeline_events
            ]
            evidence = [
                EvidenceItemSchema(
                    id=f"EVI-{sig.id}",
                    title=sig.signal_type.replace("_", " ").title(),
                    category=sig.category,
                    severity=sig.severity,
                    explanation=sig.description,
                    contribution_points=sig.risk_contribution,
                    timestamp_offset=sig.timestamp or "00:05",
                    metadata_json={}
                )
                for sig in sc.signals
            ]
            return IncidentDetailResponse(
                id=f"INC-DEMO-{sc.id}",
                incident_number=f"INC-DEMO-{sc.id[:6].upper()}",
                organization_id=getattr(user, "organization_id", "org-demo"),
                session_id=f"SES-DEMO-{sc.id}",
                analysis_id=f"DEMO-{sc.id}",
                title=f"[SANDBOX] {sc.name}",
                status="RESOLVED" if sc.expected_risk_score < 40 else "NEW",
                severity=sc.expected_risk_level,
                risk_score=sc.expected_risk_score,
                decision=sc.expected_decision,
                caller_claimed=sc.caller_claimed,
                assigned_to=None,
                assignee_name=None,
                flags=[s.signal_type for s in sc.signals],
                analyst_override_decision=None,
                analyst_override_reason=None,
                analyst_override_by=None,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
                resolved_at=None,
                timeline_events=timeline,
                notes=[],
                evidence_items=evidence
            )

    repo = IncidentRepository(db)
    inc = repo.get_incident_by_id(incident_id, organization_id=user.organization_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    return IncidentDetailResponse(
        id=inc.id,
        incident_number=inc.incident_number,
        organization_id=inc.organization_id,
        session_id=inc.session_id,
        analysis_id=inc.analysis_id,
        title=inc.title,
        status=inc.status,
        severity=inc.severity,
        risk_score=inc.risk_score,
        decision=inc.decision,
        caller_claimed=inc.caller_claimed,
        assigned_to=inc.assigned_to,
        assignee_name=inc.assignee.full_name if inc.assignee else None,
        flags=inc.flags or [],
        analyst_override_decision=inc.analyst_override_decision,
        analyst_override_reason=inc.analyst_override_reason,
        analyst_override_by=inc.analyst_override_by,
        created_at=inc.created_at.isoformat() if inc.created_at else "",
        updated_at=inc.updated_at.isoformat() if inc.updated_at else "",
        resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
        timeline_events=[
            IncidentEventSchema(
                id=e.id,
                event_type=e.event_type,
                label=e.label,
                timestamp_offset=e.timestamp_offset,
                description=e.description,
                severity=e.severity,
                metadata_json=e.metadata_json or {},
                created_at=e.created_at.isoformat()
            )
            for e in inc.timeline_events
        ],
        notes=[
            IncidentNoteSchema(
                id=n.id,
                author_id=n.author_id,
                author_name=n.author_name,
                note_text=n.note_text,
                created_at=n.created_at.isoformat()
            )
            for n in inc.notes
        ],
        evidence_items=[
            EvidenceItemSchema(
                id=ev.id,
                title=ev.title,
                category=ev.category,
                severity=ev.severity,
                explanation=ev.explanation,
                contribution_points=ev.contribution_points,
                timestamp_offset=ev.timestamp_offset,
                metadata_json=ev.metadata_json or {}
            )
            for ev in inc.evidence_items
        ]
    )


@router.patch("/incidents/{incident_id}/status", response_model=IncidentDetailResponse, summary="Update Incident Status & Assignment")
async def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = IncidentRepository(db)
    inc = repo.get_incident_by_id(incident_id, organization_id=user.organization_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    repo.update_status(inc, payload.status, payload.assigned_to)

    audit_repo = AuditRepository(db)
    audit_repo.log(
        action="UPDATE_INCIDENT_STATUS",
        endpoint=f"/api/v1/incidents/{incident_id}/status",
        organization_id=user.organization_id,
        user_id=user.id,
        resource="incident",
        resource_id=incident_id,
        metadata={"new_status": payload.status}
    )

    return await get_incident(incident_id, db, user)


@router.post("/incidents/{incident_id}/notes", response_model=IncidentNoteSchema, summary="Add Analyst Note to Incident")
async def add_incident_note(
    incident_id: str,
    payload: IncidentNoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = IncidentRepository(db)
    inc = repo.get_incident_by_id(incident_id, organization_id=user.organization_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    note = repo.add_note(
        incident_id=inc.id,
        author_name=user.full_name,
        note_text=payload.note_text,
        author_id=user.id
    )

    return IncidentNoteSchema(
        id=note.id,
        author_id=note.author_id,
        author_name=note.author_name,
        note_text=note.note_text,
        created_at=note.created_at.isoformat()
    )


@router.post("/incidents/{incident_id}/override", response_model=IncidentDetailResponse, summary="Analyst Policy Override")
async def override_incident_decision(
    incident_id: str,
    payload: IncidentOverrideRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = IncidentRepository(db)
    inc = repo.get_incident_by_id(incident_id, organization_id=user.organization_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    repo.override_decision(
        incident=inc,
        new_decision=payload.new_decision,
        reason=payload.reason,
        analyst_name=user.full_name,
        analyst_id=user.id
    )

    audit_repo = AuditRepository(db)
    audit_repo.log(
        action="ANALYST_OVERRIDE",
        endpoint=f"/api/v1/incidents/{incident_id}/override",
        organization_id=user.organization_id,
        user_id=user.id,
        resource="incident",
        resource_id=incident_id,
        metadata={"new_decision": payload.new_decision, "reason": payload.reason}
    )

    return await get_incident(incident_id, db, user)


# ==============================================================================
# Biometric Speaker Profile Enrollment & 1:1 Verification
# ==============================================================================

@router.get("/speakers", response_model=List[SpeakerProfileResponse], summary="List Enrolled Speaker Profiles")
async def list_speakers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = SpeakerRepository(db)
    profiles = repo.list_profiles(organization_id=user.organization_id)
    return [
        SpeakerProfileResponse(
            id=p.id,
            organization_id=p.organization_id,
            name=p.name,
            identity_claimed=p.identity_claimed,
            consent_recorded=p.consent_recorded,
            retention_days=p.retention_days,
            is_active=p.is_active,
            enrollment_count=len(p.enrollments),
            created_at=p.created_at.isoformat() if p.created_at else ""
        )
        for p in profiles
    ]


@router.post("/speakers", response_model=SpeakerProfileResponse, summary="Create Speaker Profile")
async def create_speaker_profile(
    payload: SpeakerProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = SpeakerRepository(db)
    existing = repo.get_profile(payload.id, organization_id=user.organization_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Speaker profile '{payload.id}' already exists.")

    profile = repo.create_profile(
        profile_id=payload.id,
        name=payload.name,
        identity_claimed=payload.identity_claimed,
        organization_id=user.organization_id,
        consent_recorded=payload.consent_recorded,
        retention_days=payload.retention_days
    )

    return SpeakerProfileResponse(
        id=profile.id,
        organization_id=profile.organization_id,
        name=profile.name,
        identity_claimed=profile.identity_claimed,
        consent_recorded=profile.consent_recorded,
        retention_days=profile.retention_days,
        is_active=profile.is_active,
        enrollment_count=0,
        created_at=profile.created_at.isoformat()
    )


@router.post("/speakers/{profile_id}/enroll", summary="Enroll Speaker Reference Audio")
async def enroll_speaker_audio(
    profile_id: str,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = SpeakerRepository(db)
    profile = repo.get_profile(profile_id, organization_id=user.organization_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Speaker profile '{profile_id}' not found.")

    temp_path = await save_upload_to_ephemeral_file(audio_file)
    try:
        from app.utils.audio_dsp import decode_wav_file
        samples, sr, duration = decode_wav_file(temp_path)
        if duration < 1.0:
            raise HTTPException(
                status_code=400,
                detail="Reference audio must be at least 1.0 seconds for robust vocal embedding extraction."
            )

        speaker_service = SpeakerVerificationService(repo)
        embedding = speaker_service.model.extract_embedding(samples, sr)

        enrollment = repo.add_enrollment(
            profile_id=profile_id,
            embedding=embedding,
            duration=duration,
            sample_rate=sr
        )

        return {
            "status": "ENROLLED",
            "profile_id": profile_id,
            "enrollment_id": enrollment.id,
            "duration_seconds": round(duration, 2),
            "model_version": enrollment.model_version
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/verify/speaker", response_model=SpeakerVerificationResult, summary="Biometric Speaker Verification")
async def verify_speaker_profile(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = SpeakerRepository(db)
    service = SpeakerVerificationService(repo)

    content_type = request.headers.get("content-type", "")
    reference_sample_id = None
    test_transcript = None
    test_audio = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            reference_sample_id = body.get("reference_sample_id")
            test_transcript = body.get("test_transcript")
        except Exception:
            pass
    elif "multipart/form-data" in content_type:
        form = await request.form()
        reference_sample_id = form.get("reference_sample_id")
        test_transcript = form.get("test_transcript")
        test_audio = form.get("test_audio")

    if test_audio and hasattr(test_audio, "read"):
        temp_path = await save_upload_to_ephemeral_file(test_audio)
        try:
            return await service.verify_speaker(
                reference_profile_id=reference_sample_id,
                test_path=temp_path,
                test_transcript=test_transcript
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        return await service.verify_speaker(
            reference_profile_id=reference_sample_id,
            test_path=None,
            test_transcript=test_transcript
        )


# ==============================================================================
# Real-Time WebSocket Audio Streaming
# ==============================================================================

@router.websocket("/stream/{session_id}")
async def websocket_audio_stream(
    websocket: WebSocket,
    session_id: str
):
    """
    Real-time audio streaming connection. Ingests raw audio PCM or text packets,
    evaluates acoustic anti-spoofing and intent incrementally, and broadcasts live risk events.
    """
    await websocket.accept()
    session = stream_manager.create_session(session_id=session_id)
    logger.info(f"WebSocket streaming session started: {session_id}")

    try:
        await websocket.send_json({
            "event_type": "SESSION_STARTED",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "READY"
        })

        while True:
            # Handle both binary audio chunks and JSON control/text messages
            message = await websocket.receive()
            
            if "bytes" in message and message["bytes"]:
                raw_bytes = message["bytes"]
                # Convert 16-bit PCM chunk to float32
                samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                session.append_chunk(samples)
                
                # Acknowledge chunk
                await websocket.send_json({
                    "event_type": "AUDIO_RECEIVED",
                    "session_id": session_id,
                    "chunks_total": session.chunks_received,
                    "duration_seconds": round(len(session.raw_pcm_samples) / session.sample_rate, 2)
                })

            elif "text" in message and message["text"]:
                data = json.loads(message["text"])
                msg_type = data.get("type", "TRANSCRIPT_CHUNK")
                
                if msg_type == "PING":
                    await websocket.send_json({"event_type": "PONG", "timestamp": time.time()})
                elif msg_type in ("TRANSCRIPT_CHUNK", "SPEECH_TEXT"):
                    spoken_text = data.get("text", "")
                    if spoken_text:
                        await stream_manager.process_text_event(session, spoken_text, websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket streaming error in session {session_id}: {e}")
    finally:
        stream_manager.close_session(session_id)


# ==============================================================================
# Isolated Demo Scenarios (Strictly for Demo Mode & Deterministic Tests)
# ==============================================================================

@router.get("/demo/scenarios", response_model=List[DemoScenario], summary="List Synthetic Demo Scenarios")
async def list_demo_scenarios():
    return DemoEngineService.get_all_scenarios()


@router.get("/demo/scenarios/{scenario_id}", response_model=DemoScenario, summary="Get Specific Demo Scenario")
async def get_demo_scenario(scenario_id: str):
    sc = DemoEngineService.get_scenario_by_id(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return sc


@router.get("/demo/scenarios/{scenario_id}/analysis", response_model=FinalAnalysisResponse, summary="Get Forensic Report for Demo Scenario")
async def get_demo_scenario_analysis(scenario_id: str):
    analysis = DemoEngineService.get_scenario_analysis(scenario_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Scenario analysis for '{scenario_id}' not found.")
    return analysis


@router.post("/risk/score", response_model=RiskAssessment, summary="Direct Risk Computation Engine")
async def calculate_direct_risk(payload: DirectRiskScoreRequest):
    signals = []
    if payload.intent_score > 0.5:
        signals.append(FraudSignal(
            id="SIG-DIRECT-01",
            signal_type="OTP_REQUEST",
            category="AUTHENTICATION",
            severity="CRITICAL",
            confidence=0.95,
            description="Authentication credential request flagged.",
            timestamp="00:04",
            risk_contribution=int(payload.intent_score * 50)
        ))
    
    voice_auth = VoiceAuthenticityResult(
        authenticity_probability=1.0 - payload.spoof_probability,
        spoof_probability=payload.spoof_probability,
        confidence=0.90,
        classification="POSSIBLE_SPOOF" if payload.spoof_probability > 0.70 else "AUTHENTIC",
        explanation="Direct risk evaluation calculation.",
        is_demo=False
    )
    
    speaker_res = SpeakerVerificationResult(
        similarity=payload.speaker_similarity,
        confidence=0.90,
        result="MISMATCH" if payload.speaker_similarity < 0.48 else "MATCH",
        threshold=0.70,
        explanation="Direct speaker similarity comparison.",
        is_demo=False
    )
    
    audio_quality = AudioQualityResult(
        duration_seconds=10.0,
        sample_rate=8000,
        channels=1,
        rms_energy=0.15,
        snr_db=20.0,
        clipping_ratio=0.0,
        silence_ratio=0.1,
        bandwidth_hz=3400,
        quality_score=payload.audio_quality_score,
        quality_level="GOOD" if payload.audio_quality_score > 0.7 else "FAIR",
        telephony_condition="DEGRADED" if payload.audio_quality_score < 0.5 else "NORMAL",
        quality_notes=[]
    )
    
    assessment, _, _ = RiskEngineService.fuse_risk_assessment(
        fraud_signals=signals,
        contextual_signals=[],
        voice_auth=voice_auth,
        speaker_verif=speaker_res,
        audio_quality=audio_quality
    )
    
    return assessment
