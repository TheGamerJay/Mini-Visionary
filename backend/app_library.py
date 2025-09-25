# app_library.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from models import (
    get_session, Poster, Asset, PosterJob, CreditLedger,
    PosterStyle
)
from app_auth import get_current_user, require_auth

library_bp = Blueprint("library", __name__, url_prefix="/api")

@library_bp.get("/library")
@require_auth()
def get_library():
    """
    Get user's poster library with filtering and pagination
    Query params: style, page, limit, search
    """
    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 20)), 100)  # Max 100 per page
    style_filter = request.args.get("style")
    search = request.args.get("search", "").strip()

    offset = (page - 1) * limit

    with get_session() as s:
        query = s.query(Poster).filter_by(
            user_id=g.user.id,
            is_deleted=False
        )

        # Apply filters
        if style_filter and style_filter in PosterStyle._value2member_map_:
            query = query.filter_by(style=PosterStyle(style_filter))

        if search:
            query = query.filter(
                func.lower(Poster.title).contains(search.lower()) |
                func.lower(Poster.tagline).contains(search.lower())
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        posters = query.order_by(
            Poster.created_at.desc()
        ).offset(offset).limit(limit).all()

        # Format response
        poster_list = []
        for poster in posters:
            # Get associated asset
            asset = s.query(Asset).filter_by(id=poster.output_asset_id).first()

            poster_list.append({
                "id": poster.id,
                "title": poster.title,
                "tagline": poster.tagline,
                "style": poster.style.value,
                "url": asset.public_url if asset else None,
                "width": poster.width,
                "height": poster.height,
                "is_private": poster.is_private,
                "created_at": poster.created_at.isoformat(),
                "job_id": poster.job_id
            })

        return {
            "ok": True,
            "posters": poster_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

@library_bp.get("/posters/<int:poster_id>")
@require_auth()
def get_poster(poster_id):
    """Get single poster details"""
    with get_session() as s:
        poster = s.query(Poster).filter_by(
            id=poster_id,
            user_id=g.user.id,
            is_deleted=False
        ).first()

        if not poster:
            return {"ok": False, "error": "Poster not found"}, 404

        # Get associated data
        asset = s.query(Asset).filter_by(id=poster.output_asset_id).first()
        job = s.query(PosterJob).filter_by(id=poster.job_id).first()

        return {
            "ok": True,
            "poster": {
                "id": poster.id,
                "title": poster.title,
                "tagline": poster.tagline,
                "style": poster.style.value,
                "url": asset.public_url if asset else None,
                "width": poster.width,
                "height": poster.height,
                "is_private": poster.is_private,
                "created_at": poster.created_at.isoformat(),
                "job": {
                    "id": job.id,
                    "mode": job.mode.value,
                    "prompt": job.prompt,
                    "status": job.status.value
                } if job else None
            }
        }

@library_bp.put("/posters/<int:poster_id>")
@require_auth()
def update_poster(poster_id):
    """
    Update poster metadata
    Body: {title?, tagline?, is_private?}
    """
    data = request.get_json()
    if not data:
        return {"ok": False, "error": "JSON body required"}, 400

    with get_session() as s:
        poster = s.query(Poster).filter_by(
            id=poster_id,
            user_id=g.user.id,
            is_deleted=False
        ).first()

        if not poster:
            return {"ok": False, "error": "Poster not found"}, 404

        # Update fields if provided
        if "title" in data:
            title = data["title"].strip() if data["title"] else None
            poster.title = title[:160] if title else None

        if "tagline" in data:
            tagline = data["tagline"].strip() if data["tagline"] else None
            poster.tagline = tagline[:220] if tagline else None

        if "is_private" in data:
            poster.is_private = bool(data["is_private"])

        poster.updated_at = datetime.utcnow()
        s.commit()

        return {
            "ok": True,
            "poster": {
                "id": poster.id,
                "title": poster.title,
                "tagline": poster.tagline,
                "is_private": poster.is_private,
                "updated_at": poster.updated_at.isoformat()
            }
        }

@library_bp.delete("/posters/<int:poster_id>")
@require_auth()
def delete_poster(poster_id):
    """Soft delete poster"""
    with get_session() as s:
        poster = s.query(Poster).filter_by(
            id=poster_id,
            user_id=g.user.id,
            is_deleted=False
        ).first()

        if not poster:
            return {"ok": False, "error": "Poster not found"}, 404

        poster.is_deleted = True
        poster.updated_at = datetime.utcnow()
        s.commit()

        return {"ok": True, "message": "Poster deleted"}

@library_bp.get("/profile")
@require_auth()
def get_profile():
    """Get user profile with stats"""
    with get_session() as s:
        # Get poster count
        poster_count = s.query(Poster).filter_by(
            user_id=g.user.id,
            is_deleted=False
        ).count()

        # Get credit ledger summary
        credit_spent = s.query(func.sum(CreditLedger.amount)).filter(
            CreditLedger.user_id == g.user.id,
            CreditLedger.event == 'spend'
        ).scalar() or 0

        credit_purchased = s.query(func.sum(CreditLedger.amount)).filter(
            CreditLedger.user_id == g.user.id,
            CreditLedger.event == 'purchase'
        ).scalar() or 0

        return {
            "ok": True,
            "profile": {
                "id": g.user.id,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "plan": user.plan,
                "credits": user.credits,
                "created_at": user.created_at.isoformat(),
                "stats": {
                    "posters_created": poster_count,
                    "credits_spent": abs(credit_spent),
                    "credits_purchased": credit_purchased
                }
            }
        }

@library_bp.put("/profile")
@require_auth()
def update_profile():
    """
    Update user profile
    Body: {display_name?, avatar_url?}
    """
    data = request.get_json()
    if not data:
        return {"ok": False, "error": "JSON body required"}, 400

    with get_session() as s:
        if "display_name" in data:
            display_name = data["display_name"].strip()
            if not display_name:
                return {"ok": False, "error": "Display name cannot be empty"}, 400
            user.display_name = display_name[:120]

        if "avatar_url" in data:
            avatar_url = data["avatar_url"].strip() if data["avatar_url"] else None
            user.avatar_url = avatar_url[:512] if avatar_url else None

        user.updated_at = datetime.utcnow()
        s.commit()

        return {
            "ok": True,
            "profile": {
                "id": g.user.id,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "updated_at": user.updated_at.isoformat()
            }
        }