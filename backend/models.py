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