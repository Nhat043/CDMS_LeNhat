"""Accepting an Excel upload into the inbox."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cdms.excel import parse
from app.cdms.models import IngestBatch, IngestEvent
from app.core.config import get_settings
from app.core.db import get_cdms_db

router = APIRouter(prefix="/cdms/v1", tags=["Imports"])


@router.post("/imports/products", status_code=202)
async def upload_products(file: UploadFile, db: Session = Depends(get_cdms_db)):
    settings = get_settings()

    contents = await file.read(settings.excel_max_bytes + 1)
    if len(contents) > settings.excel_max_bytes:
        raise HTTPException(
            413, f"file is larger than {settings.excel_max_bytes} bytes"
        )

    try:
        rows = parse(contents, settings.excel_max_rows)
    except Exception as exc:
        raise HTTPException(422, f"could not read the workbook: {exc}") from exc

    received_at = datetime.now(timezone.utc)
    batch_id = uuid.uuid4()
    db.add(IngestBatch(batch_id=batch_id, channel="EXCEL", source_name=file.filename))

    for row in rows:
        invalid = row.error is not None
        db.add(
            IngestEvent(
                event_id=uuid.uuid4(),
                batch_id=batch_id,
                channel="EXCEL",
                dedup_key=f"excel:{batch_id}:{row.row_number}",
                product_id=row.product_id,
                # Invalid rows never reach the processor, but the column is
                # NOT NULL, so they carry the upload time.
                observed_at=row.observed_at or received_at,
                raw_payload=row.payload,
                status="INVALID" if invalid else "PENDING",
                error_message=row.error,
                processed_at=received_at if invalid else None,
            )
        )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "batchId": str(batch_id),
        "rows": len(rows),
        "rejected": sum(1 for row in rows if row.error),
    }


@router.get("/imports/{batch_id}")
def import_status(batch_id: uuid.UUID, db: Session = Depends(get_cdms_db)):
    batch = db.get(IngestBatch, batch_id)
    if batch is None:
        raise HTTPException(404, "no such import")

    counts = dict(
        db.execute(
            select(IngestEvent.status, func.count())
            .where(IngestEvent.batch_id == batch_id)
            .group_by(IngestEvent.status)
        ).all()
    )

    errors = db.scalars(
        select(IngestEvent)
        .where(IngestEvent.batch_id == batch_id, IngestEvent.error_message.isnot(None))
        .order_by(IngestEvent.dedup_key)
    ).all()

    return {
        "batchId": str(batch_id),
        "file": batch.source_name,
        "counts": counts,
        "errors": [
            {"row": e.dedup_key.rsplit(":", 1)[-1], "message": e.error_message}
            for e in errors
        ],
    }
