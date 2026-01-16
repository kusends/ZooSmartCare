from pydantic import BaseModel
from datetime import date, datetime, time
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
# --- 1. СПІЛЬНІ МОДЕЛІ ---

# Базова схема для User
class UserBase(BaseModel):
    full_name: str
    role: str
    contact_info: Optional[str] = None

class UserCreate(UserBase):
    login_credentials: str  # Пароль передаємо тільки при створенні

class UserResponse(UserBase):
    user_id: int

class UserUpdate(BaseModel):
    """Схема для оновлення даних користувача. Всі поля опціональні."""
    full_name: Optional[str] = None
    role: Optional[str] = None
    contact_info: Optional[str] = None
    password: Optional[str] = None 

    class Config:
        from_attributes = True


# Базова схема для Species
class SpeciesBase(BaseModel):
    scientific_name: str
    common_name: Optional[str] = None
    general_diet_info: Optional[str] = None

class SpeciesCreate(SpeciesBase):
    pass

class SpeciesResponse(SpeciesBase):
    species_id: int

class SpeciesUpdate(BaseModel):
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    general_diet_info: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для Enclosure
class EnclosureBase(BaseModel):
    name: str
    qr_code_string: Optional[str] = None
    geo_location: Optional[str] = None

class EnclosureCreate(EnclosureBase):
    pass

class EnclosureResponse(EnclosureBase):
    enclosure_id: int

class EnclosureUpdate(BaseModel):
    name: Optional[str] = None
    qr_code_string: Optional[str] = None
    geo_location: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для Animal
class AnimalBase(BaseModel):
    nickname: str
    species_id: int
    enclosure_id: int
    birth_date: Optional[date] = None

class AnimalCreate(AnimalBase):
    pass

class AnimalResponse(AnimalBase):
    animal_id: int
    # Можна додати вкладені об'єкти для зручності, але поки тримаємо просто ID
    
class AnimalUpdate(BaseModel):
    nickname: Optional[str] = None
    species_id: Optional[int] = None
    enclosure_id: Optional[int] = None
    birth_date: Optional[date] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для ClimateProfile
class ClimateProfileBase(BaseModel):
    species_id: int
    season: str
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_humidity: Optional[float] = None
    lighting_schedule: Optional[str] = None

class ClimateProfileCreate(ClimateProfileBase):
    pass

class ClimateProfileResponse(ClimateProfileBase):
    profile_id: int

class ClimateProfileUpdate(BaseModel):
    species_id: Optional[int] = None
    season: Optional[str] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_humidity: Optional[float] = None
    lighting_schedule: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для FeedingSchedule
class FeedingScheduleBase(BaseModel):
    enclosure_id: int
    feed_time: time
    portion_size: Optional[float] = None
    food_type: Optional[str] = None
    days_of_week: Optional[str] = None

class FeedingScheduleCreate(FeedingScheduleBase):
    pass

class FeedingScheduleResponse(FeedingScheduleBase):
    schedule_id: int

class FeedingScheduleUpdate(BaseModel):
    enclosure_id: Optional[int] = None
    feed_time: Optional[time] = None
    portion_size: Optional[float] = None
    food_type: Optional[str] = None
    days_of_week: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для IoTDevice
class IoTDeviceBase(BaseModel):
    enclosure_id: int
    mac_address: str
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    last_sync: Optional[datetime] = None

class IoTDeviceCreate(IoTDeviceBase):
    pass

class IoTDeviceResponse(IoTDeviceBase):
    device_id: int

class IoTDeviceUpdate(BaseModel):
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    enclosure_id: Optional[int] = None

    class Config:
        from_attributes = True


# Базова схема для SensorReading
class SensorReadingBase(BaseModel):
    device_id: int
    temperature_val: Optional[float] = None
    humidity_val: Optional[float] = None
    light_val: Optional[float] = None

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingResponse(SensorReadingBase):
    reading_id: int
    timestamp: datetime

class SensorReadingUpdate(BaseModel):
    # Зазвичай покази не редагують, але для уніфікації додаємо
    temperature_val: Optional[float] = None
    humidity_val: Optional[float] = None
    light_val: Optional[float] = None

    class Config:
        from_attributes = True


# Базова схема для Alert
class AlertBase(BaseModel):
    enclosure_id: int
    alert_type: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = "New"

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    alert_id: int
    timestamp: datetime

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    is_active: Optional[bool] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для MaintenanceLog
class MaintenanceLogBase(BaseModel):
    user_id: int
    enclosure_id: int
    action_type: Optional[str] = None
    notes: Optional[str] = None

class MaintenanceLogCreate(MaintenanceLogBase):
    pass

class MaintenanceLogResponse(MaintenanceLogBase):
    log_id: int
    timestamp: datetime

class MaintenanceLogUpdate(BaseModel):
    action_type: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# Базова схема для MedicalRecord
class MedicalRecordBase(BaseModel):
    animal_id: int
    user_id: int
    event_date: datetime
    diagnosis: Optional[str] = None
    severity: Optional[str] = None
    treatment_notes: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordResponse(MedicalRecordBase):
    record_id: int

class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    severity: Optional[str] = None
    treatment_notes: Optional[str] = None
    is_active_treatment: Optional[bool] = None
    event_date: Optional[datetime] = None

    class Config:
        from_attributes = True
        
class TelemetryData(BaseModel):
    mac_address: str
    temperature: float
    humidity: float
    light: Optional[float] = 0.0

class SyncConfigResponse(BaseModel):
    target_temperature_min: float
    target_temperature_max: float
    feeding_schedule: List[dict]