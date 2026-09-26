import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.core.config import settings
from app.db.models import (
    AnalysisModel, FraudSignalModel, DemoScenarioModel, AuditLogModel,
    Incident, IncidentEvent, IncidentNote, EvidenceItem as EvidenceModel,
    SpeakerProfile, SpeakerEnrollment, CallSession, Organization, User
)
from app.schemas.dashboard import DashboardStats, DistributionPoint, IncidentSummary
from app.schemas.risk import FinalAnalysisResponse


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_analysis(
        self,
        response: FinalAnalysisResponse,
        caller_claimed: Optional[str] = None,
        organization_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AnalysisModel:
        analysis_record = AnalysisModel(
            id=response.analysis_id,
            organization_id=organization_id,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
            status=response.status,
            is_demo=response.is_demo_data,
            provider_used=response.provider_used,
            risk_score=response.risk.score,
            risk_level=response.risk.level,
            decision=response.risk.decision,
            confidence=response.risk.confidence,
            audio_quality=response.audio.quality_level,
            telephony_condition=response.audio.telephony_condition,
            voice_authenticity=response.voice.classification,
            spoof_probability=response.voice.spoof_probability,
            speaker_result=response.speaker.result,
            speaker_similarity=response.speaker.similarity,
            fraud_category=response.fraud_signals[0].category if response.fraud_signals else "BENIGN",
            caller_claimed=caller_claimed,
            transcript_redacted=response.transcript,
            risk_breakdown=response.risk.risk_breakdown,
            recommended_actions=response.recommended_actions,
            explanation=response.voice.explanation if response.voice else None
        )
        self.db.add(analysis_record)
        
        # Save individual fraud signals
        for sig in response.fraud_signals:
            sig_record = FraudSignalModel(
                id=str(uuid.uuid4()),
                analysis_id=response.analysis_id,
                signal_type=sig.signal_type,
                category=sig.category,
                severity=sig.severity,
                confidence=sig.confidence,
                description=sig.description,
                timestamp=sig.timestamp,
                risk_contribution=sig.risk_contribution
            )
            self.db.add(sig_record)

        self.db.commit()
        self.db.refresh(analysis_record)
        return analysis_record

    def get_analysis_by_id(self, analysis_id: str, organization_id: Optional[str] = None) -> Optional[AnalysisModel]:
        query = self.db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id)
        if organization_id:
            query = query.filter(AnalysisModel.organization_id == organization_id)
        return query.first()

    def list_analyses(
        self,
        organization_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnalysisModel]:
        query = self.db.query(AnalysisModel)
        if organization_id:
            query = query.filter(AnalysisModel.organization_id == organization_id)
        return query.order_by(desc(AnalysisModel.created_at)).offset(offset).limit(limit).all()


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_incident_from_analysis(
        self,
        analysis: AnalysisModel,
        evidence_items: List[Any],
        organization_id: str,
        session_id: Optional[str] = None,
        caller_claimed: Optional[str] = None
    ) -> Incident:
        # Determine incident title and severity
        category = analysis.fraud_category.replace("_", " ").title()
        title = f"{category}: {caller_claimed or 'Unverified Caller'}"
        incident_number = f"INC-{uuid.uuid4().hex[:6].upper()}"

        incident = Incident(
            id=str(uuid.uuid4()),
            incident_number=incident_number,
            organization_id=organization_id,
            session_id=session_id,
            analysis_id=analysis.id,
            title=title,
            status="NEW",
            severity=analysis.risk_level,
            risk_score=analysis.risk_score,
            decision=analysis.decision,
            caller_claimed=caller_claimed,
            flags=[s.signal_type for s in analysis.signals] if analysis.signals else []
        )
        self.db.add(incident)

        # Create initial incident timeline event
        event = IncidentEvent(
            id=str(uuid.uuid4()),
            incident_id=incident.id,
            event_type="INCIDENT_CREATED",
            label="Automated Threat Detection",
            timestamp_offset="00:00",
            description=f"Automated policy triggered incident creation with Risk Score {analysis.risk_score}/100 ({analysis.risk_level}).",
            severity=analysis.risk_level
        )
        self.db.add(event)

        # Add evidence items
        for ev in evidence_items:
            ev_record = EvidenceModel(
                id=str(uuid.uuid4()),
                incident_id=incident.id,
                title=getattr(ev, "title", "Acoustic / Semantic Evidence"),
                category=getattr(ev, "category", "GENERAL"),
                severity=getattr(ev, "severity", "HIGH"),
                explanation=getattr(ev, "explanation", ""),
                contribution_points=getattr(ev, "contribution_points", 0),
                timestamp_offset=getattr(ev, "timestamp", "00:00")
            )
            self.db.add(ev_record)

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def list_incidents(
        self,
        organization_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Incident], int]:
        query = self.db.query(Incident)
        if organization_id:
            query = query.filter(Incident.organization_id == organization_id)
        if status:
            query = query.filter(Incident.status == status)
        if severity:
            query = query.filter(Incident.severity == severity)

        total = query.count()
        items = query.order_by(desc(Incident.created_at)).offset(offset).limit(limit).all()
        return items, total

    def get_incident_by_id(self, incident_id: str, organization_id: Optional[str] = None) -> Optional[Incident]:
        query = self.db.query(Incident).filter(
            (Incident.id == incident_id) | (Incident.incident_number == incident_id)
        )
        if organization_id:
            query = query.filter(Incident.organization_id == organization_id)
        return query.first()

    def update_status(self, incident: Incident, new_status: str, assigned_to: Optional[str] = None) -> Incident:
        incident.status = new_status
        if assigned_to is not None:
            incident.assigned_to = assigned_to
        if new_status in ("RESOLVED", "FALSE_POSITIVE"):
            incident.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def add_note(self, incident_id: str, author_name: str, note_text: str, author_id: Optional[str] = None) -> IncidentNote:
        note = IncidentNote(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            author_id=author_id,
            author_name=author_name,
            note_text=note_text
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def override_decision(
        self,
        incident: Incident,
        new_decision: str,
        reason: str,
        analyst_name: str,
        analyst_id: Optional[str] = None
    ) -> Incident:
        old_decision = incident.decision
        incident.analyst_override_decision = new_decision
        incident.analyst_override_reason = reason
        incident.analyst_override_by = analyst_name
        incident.decision = new_decision

        # Log timeline event
        event = IncidentEvent(
            id=str(uuid.uuid4()),
            incident_id=incident.id,
            event_type="ANALYST_OVERRIDE",
            label="Decision Override by Analyst",
            timestamp_offset="00:00",
            description=f"Decision overridden from '{old_decision}' to '{new_decision}' by {analyst_name}. Reason: {reason}",
            severity="INFO"
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(incident)
        return incident


class SpeakerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_profile(
        self,
        profile_id: str,
        name: str,
        identity_claimed: str,
        organization_id: str,
        consent_recorded: bool = True,
        retention_days: int = 365
    ) -> SpeakerProfile:
        profile = SpeakerProfile(
            id=profile_id,
            organization_id=organization_id,
            name=name,
            identity_claimed=identity_claimed,
            consent_recorded=consent_recorded,
            retention_days=retention_days,
            is_active=True
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_profile(self, profile_id: str, organization_id: Optional[str] = None) -> Optional[SpeakerProfile]:
        query = self.db.query(SpeakerProfile).filter(SpeakerProfile.id == profile_id)
        if organization_id:
            query = query.filter(SpeakerProfile.organization_id == organization_id)
        return query.first()

    def list_profiles(self, organization_id: Optional[str] = None) -> List[SpeakerProfile]:
        query = self.db.query(SpeakerProfile)
        if organization_id:
            query = query.filter(SpeakerProfile.organization_id == organization_id)
        return query.filter(SpeakerProfile.is_active == True).all()

    def add_enrollment(
        self,
        profile_id: str,
        embedding: List[float],
        duration: float,
        sample_rate: int,
        model_version: str = "vocal-tract-filterbank-v1"
    ) -> SpeakerEnrollment:
        enrollment = SpeakerEnrollment(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            audio_duration=duration,
            sample_rate=sample_rate,
            embedding_vector=embedding,
            model_version=model_version
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def get_latest_embedding(self, profile_id: str) -> Optional[List[float]]:
        enrollment = self.db.query(SpeakerEnrollment)\
            .filter(SpeakerEnrollment.profile_id == profile_id)\
            .order_by(desc(SpeakerEnrollment.created_at))\
            .first()
        return enrollment.embedding_vector if enrollment else None


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self, organization_id: Optional[str] = None) -> DashboardStats:
        """
        Calculates 100% REAL metrics aggregated from persisted database records.
        Never inflates counts or fabricates synthetic values in production mode.
        """
        analysis_query = self.db.query(AnalysisModel)
        if organization_id:
            analysis_query = analysis_query.filter(AnalysisModel.organization_id == organization_id)

        total_calls = analysis_query.count()

        # If zero calls in DB and in DEMO or DEV mode, return clear sandbox statistics
        if total_calls == 0 and settings.APP_MODE in ("demo", "development"):
            return DashboardStats(
                is_demo_data=True,
                total_calls_analyzed=12,
                high_risk_calls=4,
                possible_spoof_calls=2,
                speaker_mismatches=3,
                average_risk_score=68.4,
                risk_distribution=[
                    DistributionPoint(name="High / Critical (70-100)", value=4, color="#ef4444"),
                    DistributionPoint(name="Medium Risk (40-69)", value=5, color="#f59e0b"),
                    DistributionPoint(name="Low Risk (0-39)", value=3, color="#10b981"),
                ],
                fraud_category_distribution=[
                    DistributionPoint(name="Authentication / OTP Theft", value=5, color="#6366f1"),
                    DistributionPoint(name="Bank Impersonation", value=4, color="#8b5cf6"),
                    DistributionPoint(name="Threats & Account Freezes", value=3, color="#ec4899"),
                ],
                signal_frequencies=[
                    DistributionPoint(name="OTP / PIN Demands", value=6, color="#ef4444"),
                    DistributionPoint(name="Account Block Warnings", value=5, color="#f97316"),
                    DistributionPoint(name="Speaker Voice Mismatch", value=3, color="#eab308"),
                ],
                recent_incidents=[
                    IncidentSummary(
                        id="DEMO-INC-01",
                        timestamp="10 mins ago",
                        title="[DEMO] HDFC Impersonation & OTP Demand",
                        risk_score=94,
                        risk_level="HIGH",
                        caller_claimed="HDFC Bank Security Desk",
                        flags=["OTP Request", "Speaker Mismatch", "Possible Spoof"]
                    )
                ]
            )

        # Real production query
        high_risk_calls = analysis_query.filter(AnalysisModel.risk_score >= 70).count()
        possible_spoof_calls = analysis_query.filter(AnalysisModel.voice_authenticity == "POSSIBLE_SPOOF").count()
        speaker_mismatches = analysis_query.filter(AnalysisModel.speaker_result == "MISMATCH").count()
        
        avg_score_res = analysis_query.with_entities(func.avg(AnalysisModel.risk_score)).scalar()
        average_risk_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

        # Real Risk Distribution
        med_risk_calls = analysis_query.filter(AnalysisModel.risk_score >= 40, AnalysisModel.risk_score < 70).count()
        low_risk_calls = analysis_query.filter(AnalysisModel.risk_score < 40).count()
        risk_distribution = [
            DistributionPoint(name="High / Critical (70-100)", value=high_risk_calls, color="#ef4444"),
            DistributionPoint(name="Medium Risk (40-69)", value=med_risk_calls, color="#f59e0b"),
            DistributionPoint(name="Low Risk (0-39)", value=low_risk_calls, color="#10b981"),
        ]

        # Real Fraud Categories
        categories_query = self.db.query(
            AnalysisModel.fraud_category, func.count(AnalysisModel.id)
        )
        if organization_id:
            categories_query = categories_query.filter(AnalysisModel.organization_id == organization_id)
        cat_counts = categories_query.group_by(AnalysisModel.fraud_category).limit(6).all()
        
        colors = ["#6366f1", "#8b5cf6", "#ec4899", "#06b6d4", "#14b8a6", "#f97316"]
        fraud_category_distribution = [
            DistributionPoint(name=cat.replace("_", " ").title(), value=cnt, color=colors[i % len(colors)])
            for i, (cat, cnt) in enumerate(cat_counts)
        ]

        # Real Signal Frequencies
        sig_counts = self.db.query(
            FraudSignalModel.signal_type, func.count(FraudSignalModel.id)
        ).group_by(FraudSignalModel.signal_type).order_by(desc(func.count(FraudSignalModel.id))).limit(6).all()
        
        sig_colors = ["#ef4444", "#f97316", "#eab308", "#a855f7", "#3b82f6", "#10b981"]
        signal_frequencies = [
            DistributionPoint(name=st.replace("_", " ").title(), value=cnt, color=sig_colors[i % len(sig_colors)])
            for i, (st, cnt) in enumerate(sig_counts)
        ]

        # Real Recent Incidents from persisted Incident table
        incident_query = self.db.query(Incident)
        if organization_id:
            incident_query = incident_query.filter(Incident.organization_id == organization_id)
        recent_records = incident_query.order_by(desc(Incident.created_at)).limit(5).all()
        
        recent_incidents = [
            IncidentSummary(
                id=inc.incident_number,
                timestamp=inc.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if inc.created_at else "Recent",
                title=inc.title,
                risk_score=inc.risk_score,
                risk_level=inc.severity,
                caller_claimed=inc.caller_claimed or "Unknown",
                flags=inc.flags or [],
                status=inc.status
            )
            for inc in recent_records
        ]

        return DashboardStats(
            is_demo_data=False,
            total_calls_analyzed=total_calls,
            high_risk_calls=high_risk_calls,
            possible_spoof_calls=possible_spoof_calls,
            speaker_mismatches=speaker_mismatches,
            average_risk_score=average_risk_score,
            risk_distribution=risk_distribution,
            fraud_category_distribution=fraud_category_distribution,
            signal_frequencies=signal_frequencies,
            recent_incidents=recent_incidents
        )


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        endpoint: str,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        client_ip: str = "unknown",
        status_code: int = 200,
        request_id: Optional[str] = None,
        risk_score: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLogModel:
        log_entry = AuditLogModel(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            endpoint=endpoint,
            client_ip=client_ip,
            status_code=status_code,
            request_id=request_id,
            risk_score_generated=risk_score,
            metadata_json=metadata or {},
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(log_entry)
        self.db.commit()
        return log_entry
