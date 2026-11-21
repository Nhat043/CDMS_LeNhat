"""Change Data Management Service."""

from fastapi import FastAPI

from app.cdms.channels.webhook import router

app = FastAPI(title="CDMS")
app.include_router(router)
