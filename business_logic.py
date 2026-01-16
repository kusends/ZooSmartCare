import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Імпорти інструментів
from dependencies import get_db, get_current_user, require_role

# Імпорти моделей та схем
from models import (
    IoTDevice, SensorReading, Enclosure, Animal, 
    ClimateProfile, Alert, FeedingSchedule, Species,
    MedicalRecord, MaintenanceLog, User
)
from schemas import (
    TelemetryData, SyncConfigResponse, 
    FeedingScheduleCreate, FeedingScheduleResponse, FeedingScheduleUpdate,
    AlertResponse, AlertUpdate,
    SpeciesCreate, SpeciesResponse, SpeciesUpdate,
    ClimateProfileCreate, ClimateProfileResponse, ClimateProfileUpdate,
    AnimalResponse, AnimalUpdate,
    MedicalRecordCreate, MedicalRecordResponse, MedicalRecordUpdate,
    MaintenanceLogCreate, MaintenanceLogResponse, MaintenanceLogUpdate,
    SensorReadingResponse
)

router = APIRouter(prefix="/api/business", tags=["Business Logic & Operations"])

# ==============================================================================
# 1. БАЗА ЗНАНЬ (ВИДИ ТА КЛІМАТ)
# ==============================================================================

# --- SPECIES (Види) ---

@router.get("/species/", response_model=List[SpeciesResponse])
def read_all_species(db: Session = Depends(get_db)):
    return db.query(Species).all()

@router.post("/species/", response_model=SpeciesResponse)
def create_species(
    species: SpeciesCreate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "admin"]))
):
    db_species = Species(**species.dict())
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species

@router.get("/species/{species_id}", response_model=SpeciesResponse)
def read_species_detail(species_id: int, db: Session = Depends(get_db)):
    """[NEW] Деталі виду"""
    species = db.query(Species).filter(Species.species_id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species

@router.put("/species/{species_id}", response_model=SpeciesResponse)
def update_species(
    species_id: int, 
    update_data: SpeciesUpdate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "admin"]))
):
    """[NEW] Редагувати вид"""
    species = db.query(Species).filter(Species.species_id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Оновлюємо тільки передані поля
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(species, key, value)
        
    db.commit()
    db.refresh(species)
    return species

@router.delete("/species/{species_id}")
def delete_species(
    species_id: int, 
    db: Session = Depends(get_db), 
    admin: User = Depends(require_role(["admin", "zoologist"]))
):
    """[NEW] Видалити вид"""
    species = db.query(Species).filter(Species.species_id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Перевірка, чи є тварини цього виду
    if species.animals:
        raise HTTPException(status_code=400, detail="Cannot delete species with assigned animals")

    db.delete(species)
    db.commit()
    return {"detail": "Species deleted successfully"}


# --- CLIMATE PROFILES (Кліматичні норми) ---

@router.get("/climate-profiles/", response_model=List[ClimateProfileResponse])
def read_climate_profiles(db: Session = Depends(get_db)):
    return db.query(ClimateProfile).all()

@router.post("/climate-profiles/", response_model=ClimateProfileResponse)
def create_climate_profile(
    profile: ClimateProfileCreate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "admin"]))
):
    db_profile = ClimateProfile(**profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.put("/climate-profiles/{profile_id}", response_model=ClimateProfileResponse)
def update_climate_profile(
    profile_id: int, 
    update_data: ClimateProfileUpdate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "admin"]))
):
    """[NEW] Змінити норми"""
    profile = db.query(ClimateProfile).filter(ClimateProfile.profile_id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(profile, key, value)
        
    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/climate-profiles/{profile_id}")
def delete_climate_profile(
    profile_id: int, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "admin"]))
):
    """[NEW] Видалити профіль"""
    profile = db.query(ClimateProfile).filter(ClimateProfile.profile_id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    db.delete(profile)
    db.commit()
    return {"detail": "Climate profile deleted successfully"}

# ==============================================================================
# 2. ЩОДЕННИЙ ДОГЛЯД (ТВАРИНИ)
# ==============================================================================

@router.get("/animals/", response_model=List[AnimalResponse])
def read_animals(
    species_id: Optional[int] = None, 
    enclosure_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """Список тварин (фільтри: вольєр, вид)"""
    query = db.query(Animal)
    # Якщо буде поле status, можна додати: .filter(Animal.status != "archived")
    if species_id:
        query = query.filter(Animal.species_id == species_id)
    if enclosure_id:
        query = query.filter(Animal.enclosure_id == enclosure_id)
    return query.all()

@router.get("/animals/{animal_id}", response_model=AnimalResponse)
def read_animal(animal_id: int, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.animal_id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal

@router.put("/animals/{animal_id}", response_model=AnimalResponse)
def update_animal_status(
    animal_id: int, 
    animal_update: AnimalUpdate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "vet"]))
):
    """Оновити статус/прізвисько"""
    db_animal = db.query(Animal).filter(Animal.animal_id == animal_id).first()
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    for key, value in animal_update.dict(exclude_unset=True).items():
        setattr(db_animal, key, value)
        
    db.commit()
    db.refresh(db_animal)
    return db_animal

# ==============================================================================
# 3. КЕРУВАННЯ ГОДУВАННЯМ (SCHEDULES)
# ==============================================================================

@router.post("/schedules/", response_model=FeedingScheduleResponse)
def create_schedule(
    schedule: FeedingScheduleCreate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "keeper"]))
):
    new_schedule = FeedingSchedule(**schedule.dict())
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    return new_schedule

@router.get("/enclosures/{enclosure_id}/schedules", response_model=List[FeedingScheduleResponse])
def read_enclosure_schedules(enclosure_id: int, db: Session = Depends(get_db)):
    return db.query(FeedingSchedule).filter(FeedingSchedule.enclosure_id == enclosure_id).all()

@router.put("/schedules/{schedule_id}", response_model=FeedingScheduleResponse)
def update_schedule(
    schedule_id: int, 
    schedule_update: FeedingScheduleUpdate, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "keeper"]))
):
    """[NEW] Змінити час або порцію"""
    schedule = db.query(FeedingSchedule).filter(FeedingSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    for key, value in schedule_update.dict(exclude_unset=True).items():
        setattr(schedule, key, value)
        
    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int, 
    db: Session = Depends(get_db), 
    zoologist: User = Depends(require_role(["zoologist", "keeper"]))
):
    schedule = db.query(FeedingSchedule).filter(FeedingSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"detail": "Schedule deleted"}

# ==============================================================================
# 4. ВЕТЕРИНАРІЯ (MEDICAL RECORDS)
# ==============================================================================

@router.post("/medical-records/", response_model=MedicalRecordResponse)
def create_medical_record(
    rec: MedicalRecordCreate, 
    db: Session = Depends(get_db), 
    vet: User = Depends(require_role(["vet"]))
):
    new_rec = MedicalRecord(**rec.dict(), user_id=vet.user_id)
    db.add(new_rec)
    db.commit()
    db.refresh(new_rec)
    return new_rec

@router.get("/animals/{id}/medical-history", response_model=List[MedicalRecordResponse])
def get_medical_history(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(MedicalRecord).filter(MedicalRecord.animal_id == id).all()

@router.put("/medical-records/{record_id}", response_model=MedicalRecordResponse)
def update_medical_record(
    record_id: int, 
    rec_update: MedicalRecordUpdate, 
    db: Session = Depends(get_db), 
    vet: User = Depends(require_role(["vet"]))
):
    """[NEW] Доповнити запис (наприклад, лікування завершено)"""
    record = db.query(MedicalRecord).filter(MedicalRecord.record_id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    for key, value in rec_update.dict(exclude_unset=True).items():
        setattr(record, key, value)
        
    db.commit()
    db.refresh(record)
    return record

# ==============================================================================
# 5. ТЕХНІЧНЕ ОБСЛУГОВУВАННЯ (MAINTENANCE LOGS)
# ==============================================================================

@router.post("/maintenance-logs/", response_model=MaintenanceLogResponse)
def create_maintenance_log(
    log: MaintenanceLogCreate, 
    db: Session = Depends(get_db), 
    tech: User = Depends(require_role(["technician", "keeper", "admin"]))
):
    new_log = MaintenanceLog(**log.dict(), user_id=tech.user_id)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

@router.get("/enclosures/{enclosure_id}/logs", response_model=List[MaintenanceLogResponse])
def get_enclosure_maintenance_logs(
    enclosure_id: int, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """[NEW] Історія обслуговування вольєра"""
    return db.query(MaintenanceLog).filter(MaintenanceLog.enclosure_id == enclosure_id).order_by(desc(MaintenanceLog.timestamp)).all()

# ==============================================================================
# 6. СПОВІЩЕННЯ (ALERTS)
# ==============================================================================

@router.get("/alerts/", response_model=List[AlertResponse])
def get_active_alerts(
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Активні тривоги"""
    return db.query(Alert).filter(Alert.status == "New").order_by(desc(Alert.timestamp)).all()

@router.put("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """Позначити як вирішене"""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "Resolved"
    db.commit()
    return {"detail": "Alert resolved"}

@router.get("/alerts/history", response_model=List[AlertResponse])
def get_alerts_history(
    enclosure_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """[NEW] Архів тривог (фільтр за вольєром)"""
    query = db.query(Alert)
    if enclosure_id:
        query = query.filter(Alert.enclosure_id == enclosure_id)
    
    return query.order_by(desc(Alert.timestamp)).limit(limit).all()

# ==============================================================================
# 7. IOT & TELEMETRY
# ==============================================================================

@router.post("/telemetry/", status_code=status.HTTP_201_CREATED)
def receive_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    """
    Основна точка входу для даних з датчиків.
    """
    # 1. Валідація
    device = db.query(IoTDevice).filter(IoTDevice.mac_address == data.mac_address).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device unknown")

    device.last_sync = datetime.datetime.utcnow()
    device.status = "Online"

    # 2. Збереження
    # SensorReading не має enclosure_id в моделі, тільки device_id
    reading = SensorReading(
        device_id=device.device_id,
        temperature_val=data.temperature,
        humidity_val=data.humidity,
        light_val=data.light,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(reading)

    # 3. Аналіз на алерти (спрощено)
    alerts_triggered = []
    if device.enclosure_id:
        animal = db.query(Animal).filter(Animal.enclosure_id == device.enclosure_id).first()
        if animal:
            profile = db.query(ClimateProfile).filter(ClimateProfile.species_id == animal.species_id).first()
            if profile:
                alert_msg = None
                if data.temperature > profile.max_temperature:
                    alert_msg = f"TEMP HIGH: {data.temperature}°C"
                elif data.temperature < profile.min_temperature:
                    alert_msg = f"TEMP LOW: {data.temperature}°C"
                
                if alert_msg:
                    # Перевірка дублікатів (Anti-spam)
                    existing = db.query(Alert).filter(
                        Alert.enclosure_id == device.enclosure_id, 
                        Alert.status == "New", 
                        Alert.alert_type == "Climate"
                    ).first()
                    
                    if not existing:
                        new_alert = Alert(
                            enclosure_id=device.enclosure_id,
                            alert_type="Climate",
                            message=alert_msg,
                            status="New",
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.add(new_alert)
                        alerts_triggered.append(alert_msg)

    db.commit()
    return {"status": "processed", "alerts": alerts_triggered}

@router.get("/config/{mac_address}", response_model=SyncConfigResponse)
def sync_device_config(mac_address: str, db: Session = Depends(get_db)):
    """IoT пристрій запитує налаштування"""
    device = db.query(IoTDevice).filter(IoTDevice.mac_address == mac_address).first()
    if not device or not device.enclosure_id:
        raise HTTPException(status_code=404, detail="Device not ready")
    
    config = {
        "target_temperature_min": 20.0,
        "target_temperature_max": 25.0,
        "feeding_schedule": []
    }
    
    animal = db.query(Animal).filter(Animal.enclosure_id == device.enclosure_id).first()
    if animal:
        profile = db.query(ClimateProfile).filter(ClimateProfile.species_id == animal.species_id).first()
        if profile:
            config["target_temperature_min"] = profile.min_temperature
            config["target_temperature_max"] = profile.max_temperature
            
    schedules = db.query(FeedingSchedule).filter(FeedingSchedule.enclosure_id == device.enclosure_id).all()
    for s in schedules:
        config["feeding_schedule"].append({
            "time": s.feed_time.strftime("%H:%M"),
            "portion": s.portion_size,
            "food_type": s.food_type
        })
        
    return config

@router.get("/telemetry/enclosure/{enclosure_id}/latest", response_model=Optional[SensorReadingResponse])
def get_latest_telemetry(enclosure_id: int, db: Session = Depends(get_db)):
    """Поточні показники (Join через IoTDevice)"""
    reading = db.query(SensorReading)\
        .join(IoTDevice, SensorReading.device_id == IoTDevice.device_id)\
        .filter(IoTDevice.enclosure_id == enclosure_id)\
        .order_by(desc(SensorReading.timestamp))\
        .first()
    return reading

@router.get("/telemetry/history/{enclosure_id}", response_model=List[SensorReadingResponse])
def get_telemetry_history(
    enclosure_id: int, 
    start: Optional[datetime.datetime] = None,
    end: Optional[datetime.datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """[NEW] Історія для графіків"""
    query = db.query(SensorReading)\
        .join(IoTDevice, SensorReading.device_id == IoTDevice.device_id)\
        .filter(IoTDevice.enclosure_id == enclosure_id)
        
    if start:
        query = query.filter(SensorReading.timestamp >= start)
    if end:
        query = query.filter(SensorReading.timestamp <= end)
        
    return query.order_by(desc(SensorReading.timestamp)).limit(limit).all()

# ==============================================================================
# 8. АНАЛІТИКА (Reports)
# ==============================================================================

@router.get("/reports/feeding-consumption")
def report_consumption(db: Session = Depends(get_db), user: User = Depends(require_role(["zoologist", "admin"]))):
    total_meat = db.query(func.sum(FeedingSchedule.portion_size))\
        .filter(FeedingSchedule.food_type == "М'ясо").scalar()
    return {"total_meat_daily_kg": total_meat or 0}

@router.get("/reports/temperature-avg/{enclosure_id}")
def report_avg_temp(enclosure_id: int, db: Session = Depends(get_db)):
    one_day_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    # Join потрібен, бо в reading немає enclosure_id
    avg = db.query(func.avg(SensorReading.temperature_val))\
        .join(IoTDevice, SensorReading.device_id == IoTDevice.device_id)\
        .filter(IoTDevice.enclosure_id == enclosure_id)\
        .filter(SensorReading.timestamp >= one_day_ago).scalar()
    return {"enclosure_id": enclosure_id, "avg_temp_24h": avg or 0}