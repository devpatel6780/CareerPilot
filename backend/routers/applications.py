"""Application tracker endpoints — manual status logging only (no
auto-apply), per the build spec: Not Applied / Applied / Interview /
Rejected / Offer.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.applications import insert_application, list_applications, update_application_status
from db.matches import get_match

router = APIRouter(prefix="/applications", tags=["applications"])

VALID_STATUSES = {"Not Applied", "Applied", "Interview", "Rejected", "Offer"}


class CreateApplicationRequest(BaseModel):
    match_id: int
    resume_version_id: int | None = None


class UpdateApplicationRequest(BaseModel):
    status: str
    date_applied: str | None = None


@router.post("")
def create_application(payload: CreateApplicationRequest):
    if get_match(payload.match_id) is None:
        raise HTTPException(status_code=404, detail=f"No match with id {payload.match_id}")

    application_id = insert_application(payload.match_id, payload.resume_version_id)
    return {"application_id": application_id}


@router.get("")
def get_applications():
    return {"applications": list_applications()}


@router.patch("/{application_id}")
def patch_application(application_id: int, payload: UpdateApplicationRequest):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(VALID_STATUSES)}")

    updated = update_application_status(application_id, payload.status, payload.date_applied)
    if not updated:
        raise HTTPException(status_code=404, detail=f"No application with id {application_id}")
    return {"application_id": application_id, "status": payload.status}
