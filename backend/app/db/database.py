import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {}
pool_kwargs = {"pool_pre_ping": True}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    pool_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    })

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        **pool_kwargs
    )
    # Test connection immediately
    with engine.connect() as conn:
        pass
    logger.info(f"Database engine initialized successfully on: {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    logger.critical(f"FATAL: Database connection failed for [{db_url}]: {e}")
    if settings.APP_MODE == "production":
        logger.critical("Production mode strictly forbids SQLite fallback. Exiting.")
        sys.exit(1)
    else:
        logger.warning("Development mode: Falling back to local SQLite database.")
        db_url = "sqlite:///./sentinelvoice.db"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified.")

    # Seed default organization and SOC accounts for development/demo
    try:
        from app.db.models import Organization, User
        from app.core.security import hash_password
        db = SessionLocal()
        try:
            org = db.query(Organization).filter(Organization.slug == "default").first()
            if not org:
                org = Organization(
                    id="org-default-01",
                    name="SentinelVoice SOC Enterprise",
                    slug="default"
                )
                db.add(org)
                db.commit()
                logger.info("Seeded default organization: SentinelVoice SOC Enterprise")

            users_to_seed = [
                ("analyst@sentinelvoice.internal", "SentinelAnalyst2026!", "SOC Lead Analyst", "ADMIN"),
                ("soc_analyst@sentinelvoice.internal", "AnalystSecure2026!", "Tier-2 SOC Analyst", "SOC_ANALYST"),
                ("admin@sentinelvoice.internal", "AdminSecure2026!", "Security Administrator", "ADMIN"),
            ]
            for email, raw_pwd, name, role in users_to_seed:
                existing = db.query(User).filter(User.email == email).first()
                if not existing:
                    u = User(
                        id=f"user-{email.split('@')[0]}",
                        organization_id=org.id,
                        email=email,
                        hashed_password=hash_password(raw_pwd),
                        full_name=name,
                        role=role,
                        is_active=True
                    )
                    db.add(u)
                    db.commit()
                    logger.info(f"Seeded SOC user: {email} ({role})")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Seed initialization non-fatal note: {e}")
