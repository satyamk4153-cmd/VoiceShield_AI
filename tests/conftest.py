import os
import pytest
from app.core.config import settings

# Force test mode
os.environ["APP_MODE"] = "demo"
os.environ["AI_PROVIDER"] = "demo"

from app.db.database import engine, Base, SessionLocal
from app.db.models import Organization, User
from app.core.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Drops old tables and creates fresh schema for the test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        org = Organization(
            id="org-default-01",
            name="Default Enterprise SOC",
            slug="default"
        )
        db.add(org)
        db.commit()

        user = User(
            id="user-default-analyst",
            organization_id=org.id,
            email="analyst@sentinelvoice.internal",
            hashed_password=hash_password("SentinelAnalyst2026!"),
            full_name="SOC Lead Analyst",
            role="ADMIN",
            is_active=True
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

