from __future__ import annotations
import enum
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine, MetaData, Enum, String, Text, Integer, Boolean, DateTime,
    ForeignKey, Index, func
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, Session
)

# ---------- DB ENGINE ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata_obj = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

class Base(DeclarativeBase):
    metadata = metadata_obj

# ---------- ENUMS ----------
class PosterMode(str, enum.Enum):
    TEXT_TO_POSTER = "text_to_poster"
    IMAGE_TO_POSTER = "image_to_poster"

class PosterStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"

class PosterStyle(str, enum.Enum):
    FANTASY = "fantasy"
    SCIFI = "scifi"
    HORROR = "horror"
    ROMANCE = "romance"
    ACTION = "action"
    ANIME = "anime"
    CUSTOM = "custom"

class CreditEventType(str, enum.Enum):
    GRANT = "grant"          # manual/admin or signup bonus
    PURCHASE = "purchase"    # user bought credits
    SPEND = "spend"          # generation spend
    REFUND = "refund"        # failed job auto-refund
    ADJUST = "adjust"        # admin correction

class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    FAILED = "failed"

# ---------- TABLES ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))  # bcrypt hash
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512))
    plan: Mapped[str] = mapped_column(String(32), default="free")  # free/growth/max
    credits: Mapped[int] = mapped_column(Integer, default=20)     # simple credit bucket
    ad_free: Mapped[bool] = mapped_column(Boolean, default=False)  # $5/mo subscription
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(64))  # for portal access
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    accept_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    posters: Mapped[list["Poster"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[list["PosterJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    credit_ledger: Mapped[list["CreditLedger"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class StylePreset(Base):
    """
    Optional curated presets users can pick (prompt templates, color grading, borders).
    """
    __tablename__ = "style_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # e.g., "fantasy_epic_v1"
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[PosterStyle] = mapped_column(Enum(PosterStyle), default=PosterStyle.CUSTOM)
    prompt_template: Mapped[Optional[str]] = mapped_column(Text)      # jinja-like text
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)        # free-form JSON (borders, credits layout)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Asset(Base):
    """
    Any file we store: originals, masks, finals. Store only URLs/keys (S3/R2/Supabase).
    """
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # original | mask | poster | thumb
    storage_key: Mapped[str] = mapped_column(String(512), index=True) # e.g., r2 key
    public_url: Mapped[str] = mapped_column(String(1024))
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    checksum: Mapped[Optional[str]] = mapped_column(String(128))

    user: Mapped["User"] = relationship()

Index("ix_assets_user_kind_created", Asset.user_id, Asset.kind, Asset.created_at.desc())

class PosterJob(Base):
    """
    One generation run. Tracks status/logs and links inputs/outputs.
    """
    __tablename__ = "poster_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[PosterMode] = mapped_column(Enum(PosterMode))
    style: Mapped[PosterStyle] = mapped_column(Enum(PosterStyle), default=PosterStyle.FANTASY)
    preset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("style_presets.id"))
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text)
    input_asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"))
    output_asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"))
    status: Mapped[PosterStatus] = mapped_column(Enum(PosterStatus), default=PosterStatus.QUEUED, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="jobs")
    preset: Mapped[Optional["StylePreset"]] = relationship()
    input_asset: Mapped[Optional["Asset"]] = relationship(foreign_keys=[input_asset_id])
    output_asset: Mapped[Optional["Asset"]] = relationship(foreign_keys=[output_asset_id])
    poster: Mapped[Optional["Poster"]] = relationship(back_populates="job", uselist=False)

Index("ix_jobs_user_status", PosterJob.user_id, PosterJob.status)

class Poster(Base):
    """
    Final poster entity (library item). Tied to a job + output asset.
    """
    __tablename__ = "posters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("poster_jobs.id", ondelete="SET NULL"))
    title: Mapped[Optional[str]] = mapped_column(String(160))
    tagline: Mapped[Optional[str]] = mapped_column(String(220))
    style: Mapped[PosterStyle] = mapped_column(Enum(PosterStyle), default=PosterStyle.FANTASY)
    output_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="posters")
    job: Mapped["PosterJob"] = relationship(back_populates="poster")
    asset: Mapped["Asset"] = relationship(foreign_keys=[output_asset_id])

Index("ix_posters_user_created", Poster.user_id, Poster.created_at.desc())

class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event: Mapped[CreditEventType] = mapped_column(Enum(CreditEventType))
    amount: Mapped[int] = mapped_column(Integer)  # + or -
    ref: Mapped[Optional[str]] = mapped_column(String(64))  # job_id, purchase_id, etc.
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="credit_ledger")

Index("ix_credit_ledger_user_created", CreditLedger.user_id, CreditLedger.created_at.desc())

class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_key: Mapped[str] = mapped_column(String(64))  # e.g., "credits_100"
    credits: Mapped[int] = mapped_column(Integer)         # amount granted on success
    amount_cents: Mapped[int] = mapped_column(Integer)    # 999 = $9.99
    provider: Mapped[str] = mapped_column(String(32))     # stripe, lemon, etc.
    provider_ref: Mapped[Optional[str]] = mapped_column(String(128))  # session/payment id
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="purchases")

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship()

# ---------- UTILITIES ----------
def init_db(drop_all: bool = False):
    """Create tables (optionally drop first for local dev)."""
    if drop_all:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

# ---------- Quick local bootstrap ----------
if __name__ == "__main__":
    print(f"Using DB: {DATABASE_URL}")
    init_db()
    print("DB ready.")