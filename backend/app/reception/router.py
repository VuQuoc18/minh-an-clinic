import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import Role, Staff, require_role
from app.clock import get_now
from app.db import get_db
from app.models import AppointmentStatus
from app.reception import service
from app.reception.schemas import (
    AppointmentOut,
    DoctorOut,
    ProfileOut,
    SpecialtyOut,
    SuggestionsOut,
    WalkInRequest,
)

# Chỉ Lễ tân và Quản trị được thao tác trên màn hình Tiếp đón.
CurrentStaff = Annotated[Staff, Depends(require_role(Role.RECEPTIONIST, Role.ADMIN))]
Db = Annotated[Session, Depends(get_db)]
Now = Annotated[dt.datetime, Depends(get_now)]

router = APIRouter(prefix="/reception", tags=["reception"])


@router.get("/appointments")
def list_appointments(
    _staff: CurrentStaff,
    db: Db,
    now: Now,
    q: Annotated[str | None, Query(max_length=100)] = None,
    doctor_id: int | None = None,
    status: AppointmentStatus | None = None,
) -> list[AppointmentOut]:
    return service.list_today(db, now, q, doctor_id, status)


@router.post("/appointments/{appointment_id}/check-in")
def check_in(appointment_id: int, staff: CurrentStaff, db: Db, now: Now) -> AppointmentOut:
    return service.check_in(db, appointment_id, now, staff)


@router.get("/specialties")
def list_specialties(_staff: CurrentStaff, db: Db) -> list[SpecialtyOut]:
    return [SpecialtyOut(id=s.id, name=s.name) for s in service.list_specialties(db)]


@router.get("/doctors")
def list_doctors(_staff: CurrentStaff, db: Db) -> list[DoctorOut]:
    return [
        DoctorOut(id=d.id, full_name=d.full_name, specialty_id=d.specialty_id)
        for d in service.list_doctors(db)
    ]


@router.get("/walk-in/suggestions")
def walk_in_suggestions(
    specialty_id: int, _staff: CurrentStaff, db: Db, now: Now
) -> SuggestionsOut:
    return service.suggest_walk_in_slots(db, specialty_id, now)


@router.get("/profiles")
def search_profiles(
    phone: Annotated[str, Query(max_length=20)], _staff: CurrentStaff, db: Db
) -> list[ProfileOut]:
    return [
        ProfileOut(
            id=p.id,
            full_name=p.full_name,
            birth_date=p.birth_date,
            gender=p.gender,
            phone=p.phone or p.account.phone,
            is_primary=p.is_primary,
        )
        for p in service.search_profiles(db, phone)
    ]


@router.post("/walk-in", status_code=201)
def create_walk_in(body: WalkInRequest, staff: CurrentStaff, db: Db, now: Now) -> AppointmentOut:
    return service.create_walk_in(db, body, now, staff)
