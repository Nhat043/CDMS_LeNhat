"""Tables for CDMS."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import CHAR, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import CdmsBase


class IngestBatch(CdmsBase):
    """A polling run or Excel import"""

    __tablename__ = "ingest_batch"
    __table_args__ = (
        CheckConstraint("channel IN ('POLLING', 'EXCEL')", name="ck_batch_channel"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class IngestEvent(CdmsBase):
    """A product snapshot waiting to be processed"""

    __tablename__ = "ingest_event"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('WEBHOOK', 'POLLING', 'EXCEL')", name="ck_event_channel"
        ),
        Index("ix_event_pending", "status", "received_at"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingest_batch.batch_id")
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)

    # webhook:{sender event id} / poll:{batch}:{product} / excel:{batch}:{row}
    dedup_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    product_id: Mapped[int | None] = mapped_column(Integer)

    # Time when the product was read from Vietful
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    content_hash: Mapped[str | None] = mapped_column(CHAR(64))

    status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProductState(CdmsBase):
    """Latest snapshot for each product"""

    __tablename__ = "product_state"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProductChange(CdmsBase):
    """Record of a product change"""

    __tablename__ = "product_change"
    __table_args__ = (Index("ix_change_product", "product_id", "observed_at"),)

    change_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Each event can only produce one change
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingest_event.event_id"),
        nullable=False,
        unique=True,
    )

    kind: Mapped[str] = mapped_column(Text, nullable=False)

    # Only the fields that changed: {field: {"from": x, "to": y}}
    diff: Mapped[dict] = mapped_column(JSONB, nullable=False)

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
