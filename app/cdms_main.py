"""Change Data Management Service."""

from fastapi import FastAPI

from app.cdms.channels import imports, webhook

app = FastAPI(title="CDMS")
app.include_router(webhook.router)
app.include_router(imports.router)
