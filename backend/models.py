import os
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Index, func, event, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

Base = declarative_base()

class PosterMode(PyEnum):
    TEXT_TO_POSTER = "text_to_poster"
    IMAGE_TO_POSTER = "image_to_poster"

class PosterStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PosterStyle(PyEnum):
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    HORROR = "horror"
    COMEDY = "comedy"
    DRAMA = "drama"
    ACTION = "action"

class CreditEventType(PyEnum):
    GRANT = "grant"
    PURCHASE = "purchase"
    SPEND = "spend"
    BONUS = "bonus"
    REFUND = "refund"

class Poster(Base):
    """
    Final poster entity (library item). Tied to a job + output asset.
    """
    __tablename__ = "posters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[Optional[int]] = mapped_column(  # nullable because ondelete="SET NULL"
        ForeignKey("poster_jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(160))
    tagline: Mapped[Optional[str]] = mapped_column(String(220))
    style: Mapped[PosterStyle] = mapped_column(Enum(PosterStyle), default=PosterStyle.FANTASY)
    output_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="posters")
    job: Mapped[Optional["PosterJob"]] = relationship(back_populates="poster")
    asset: Mapped["Asset"] = relationship(foreign_keys=[output_asset_id])


Index("ix_posters_user_created", Poster.user_id, Poster.created_at.desc())


class User(Base):
    """User account."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_image_url: Mapped[Optional[str]] = mapped_column(Text)
    avatar_video_url: Mapped[Optional[str]] = mapped_column(Text)
    credits: Mapped[int] = mapped_column(Integer, default=0)
    ad_free: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    posters: Mapped[list["Poster"]] = relationship(back_populates="user")
    jobs: Mapped[list["PosterJob"]] = relationship(back_populates="user")


class PosterJob(Base):
    """Job processing state for poster generation."""
    __tablename__ = "poster_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[PosterMode] = mapped_column(Enum(PosterMode))
    status: Mapped[PosterStatus] = mapped_column(Enum(PosterStatus), default=PosterStatus.PENDING)
    prompt: Mapped[Optional[str]] = mapped_column(String(2000))
    style: Mapped[PosterStyle] = mapped_column(Enum(PosterStyle), default=PosterStyle.FANTASY)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # Progress percentage 0-100
    error_message: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="jobs")
    poster: Mapped[Optional["Poster"]] = relationship(back_populates="job")


class Asset(Base):
    """File/image asset storage."""
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500))  # S3/R2 key or local path
    public_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class CreditLedger(Base):
    """Credit transaction history."""
    __tablename__ = "credit_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[CreditEventType] = mapped_column(Enum(CreditEventType))
    amount: Mapped[int] = mapped_column(Integer)  # positive for credit, negative for debit
    balance_after: Mapped[int] = mapped_column(Integer)  # user balance after this transaction
    reference: Mapped[Optional[str]] = mapped_column(String(255))  # external ref (invoice, etc)
    notes: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship()


# Database setup
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./mini_visionary.db")

        if database_url.startswith("sqlite"):
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            _engine = create_engine(database_url)
    return _engine

def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal()

def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # Run migrations for existing databases
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if display_name column exists, add if missing
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'display_name'
            """))

            if not result.fetchone():
                print("Adding missing display_name column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
                conn.commit()
                print("✅ Added display_name column")
    except Exception as e:
        print(f"Migration warning: {e}")
        # Continue anyway - this might be a new database