import uvicorn
import datetime as dt
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import init_db, Appointment, get_db

# Step 3: Pydantic Models PEHLE define karo
class AppointmentRequest(BaseModel):
    patient_name: str
    reason: str
    start_time: dt.datetime

class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    reason: str | None
    start_time: dt.datetime
    canceled: bool
    created_at: dt.datetime

class CancelAppointmentRequest(BaseModel):
    patient_name: str
    date: dt.date

class CancelAppointmentResponse(BaseModel):
    canceled_count: int

# Step 2: FastAPI app
init_db()
app = FastAPI()

@app.post("/schedule_appointment/")
def schedule_appointment(request: AppointmentRequest, db: Session = Depends(get_db)):
    new_appointment = Appointment(
        patient_name=request.patient_name,
        reason=request.reason,
        start_time=request.start_time,
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return AppointmentResponse(
        id=new_appointment.id,
        patient_name=new_appointment.patient_name,
        reason=new_appointment.reason,
        start_time=new_appointment.start_time,
        canceled=new_appointment.canceled,
        created_at=new_appointment.created_at
    )

@app.post("/cancel_appointment/")
def cancel_appointment(request: CancelAppointmentRequest, db: Session = Depends(get_db)):
    start_dt = dt.datetime.combine(request.date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)
    result = db.execute(
        select(Appointment)
        .where(Appointment.patient_name == request.patient_name)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time <= end_dt)
        .where(Appointment.canceled == False)
    )
    appointments = result.scalars().all()
    if not appointments:
        raise HTTPException(status_code=404, detail="No matching appointment found")
    for appointment in appointments:
        appointment.canceled = True
    db.commit()
    return CancelAppointmentResponse(canceled_count=len(appointments))

@app.post("/list_appointments/")
def list_appointments(request: AppointmentRequest, db: Session = Depends(get_db)):
    start_dt = dt.datetime.combine(request.start_time, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=1)
    result = db.execute(
        select(Appointment)
        .where(Appointment.canceled == False)
        .where(Appointment.start_time >= start_dt)
        .where(Appointment.start_time < end_dt)
        .order_by(Appointment.start_time.asc())
    )
    booked_appointments = []
    for appointment in result.scalars().all():
        booked_appointments.append(AppointmentResponse(
            id=appointment.id,
            patient_name=appointment.patient_name,
            reason=appointment.reason,
            start_time=appointment.start_time,
            canceled=appointment.canceled,
            created_at=appointment.created_at
        ))
    return booked_appointments

@app.get("/appointments/")
def get_appointments(db: Session = Depends(get_db)):
    result = db.execute(
        select(Appointment)
        .where(Appointment.canceled == False)
        .order_by(Appointment.start_time.asc())
    )
    appointments = result.scalars().all()
    return [
        AppointmentResponse(
            id=a.id,
            patient_name=a.patient_name,
            reason=a.reason,
            start_time=a.start_time,
            canceled=a.canceled,
            created_at=a.created_at
        )
        for a in appointments  # ← YE FIX KARO
    ]

    @app.get("/appointments/")
    def get_all_appointments(db: Session = Depends(get_db)):
        result = db.execute(
            select(Appointment)
            .where(Appointment.canceled == False)
            .order_by(Appointment.start_time.asc())
    )
    return result.scalars().all()

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=4444, reload=True)