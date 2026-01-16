# 1. ІМПОРТИ
from sqlalchemy import Column, Integer, String, Date, Float, Text, Time, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

# Створення базового класу для всіх моделей
Base = declarative_base()

# 2. ENUM ТИПИ
class RoleEnum(str, enum.Enum):
    admin = "Admin"
    zoologist = "Zoologist"
    keeper = "Keeper"
    vet = "Vet"

class SeasonEnum(str, enum.Enum):
    winter = "Winter"
    summer = "Summer"
    spring = "Spring"
    autumn = "Autumn"
    all_seasons = "All"

class DeviceStatusEnum(str, enum.Enum):
    online = "Online"
    offline = "Offline"
    error = "Error"

# 3. ОПИС ТАБЛИЦЬ (КЛАСІВ)

class User(Base):
    __tablename__ = "app_user"  # <--- В базі таблиця називається 'app_user'

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    login_credentials = Column(String(255), nullable=False)
    contact_info = Column(String(100))

    # Зв'язки
    # back_populates="user" означає, що в інших класах змінна називається "user"
    maintenance_logs = relationship("MaintenanceLog", back_populates="user")
    medical_records = relationship("MedicalRecord", back_populates="user")


class Species(Base):
    __tablename__ = "species"

    species_id = Column(Integer, primary_key=True, index=True)
    scientific_name = Column(String(100), nullable=False)
    common_name = Column(String(100))
    general_diet_info = Column(Text)

    animals = relationship("Animal", back_populates="species")
    climate_profiles = relationship("ClimateProfile", back_populates="species")


class Enclosure(Base):
    __tablename__ = "enclosure"

    enclosure_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    qr_code_string = Column(String(255), unique=True)
    geo_location = Column(String(100))

    animals = relationship("Animal", back_populates="enclosure")
    iot_device = relationship("IoTDevice", back_populates="enclosure", uselist=False)
    feeding_schedules = relationship("FeedingSchedule", back_populates="enclosure")
    alerts = relationship("Alert", back_populates="enclosure")
    maintenance_logs = relationship("MaintenanceLog", back_populates="enclosure")


class Animal(Base):
    __tablename__ = "animal"

    animal_id = Column(Integer, primary_key=True, index=True)
    enclosure_id = Column(Integer, ForeignKey("enclosure.enclosure_id"))
    species_id = Column(Integer, ForeignKey("species.species_id"))
    nickname = Column(String(50))
    birth_date = Column(Date)

    enclosure = relationship("Enclosure", back_populates="animals")
    species = relationship("Species", back_populates="animals")
    medical_records = relationship("MedicalRecord", back_populates="animal")


class ClimateProfile(Base):
    __tablename__ = "climate_profile"

    profile_id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("species.species_id"))
    season = Column(String(20))
    min_temperature = Column(Float)
    max_temperature = Column(Float)
    min_humidity = Column(Float)
    lighting_schedule = Column(String(100))

    species = relationship("Species", back_populates="climate_profiles")


class FeedingSchedule(Base):
    __tablename__ = "feeding_schedule"

    schedule_id = Column(Integer, primary_key=True, index=True)
    enclosure_id = Column(Integer, ForeignKey("enclosure.enclosure_id"))
    feed_time = Column(Time, nullable=False)
    portion_size = Column(Float)
    food_type = Column(String(100))
    days_of_week = Column(String(50))

    enclosure = relationship("Enclosure", back_populates="feeding_schedules")


class IoTDevice(Base):
    __tablename__ = "iot_device"

    device_id = Column(Integer, primary_key=True, index=True)
    enclosure_id = Column(Integer, ForeignKey("enclosure.enclosure_id"), unique=True)
    mac_address = Column(String(17), unique=True, nullable=False)
    firmware_version = Column(String(20))
    status = Column(String(20))
    last_sync = Column(DateTime)

    enclosure = relationship("Enclosure", back_populates="iot_device")
    sensor_readings = relationship("SensorReading", back_populates="device")


class SensorReading(Base):
    __tablename__ = "sensor_reading"

    reading_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("iot_device.device_id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature_val = Column(Float)
    humidity_val = Column(Float)
    light_val = Column(Float)

    device = relationship("IoTDevice", back_populates="sensor_readings")


class Alert(Base):
    __tablename__ = "alert"

    alert_id = Column(Integer, primary_key=True, index=True)
    enclosure_id = Column(Integer, ForeignKey("enclosure.enclosure_id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(50))
    message = Column(Text)
    status = Column(String(20), default="New")

    enclosure = relationship("Enclosure", back_populates="alerts")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_log"

    log_id = Column(Integer, primary_key=True, index=True)
    # Тут ForeignKey посилається на таблицю 'app_user' - це ПРАВИЛЬНО
    user_id = Column(Integer, ForeignKey("app_user.user_id"))
    enclosure_id = Column(Integer, ForeignKey("enclosure.enclosure_id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_type = Column(String(50))
    notes = Column(Text)

    # Тут relationship посилається на клас 'User' - це ПРАВИЛЬНО
    user = relationship("User", back_populates="maintenance_logs")
    enclosure = relationship("Enclosure", back_populates="maintenance_logs")


class MedicalRecord(Base):
    __tablename__ = "medical_record"

    record_id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animal.animal_id"))
    # Тут ForeignKey посилається на таблицю 'app_user'
    user_id = Column(Integer, ForeignKey("app_user.user_id"))
    event_date = Column(DateTime, nullable=False)
    diagnosis = Column(String(255))
    severity = Column(String(50))
    treatment_notes = Column(Text)

    animal = relationship("Animal", back_populates="medical_records")
    # Тут relationship посилається на клас 'User'
    user = relationship("User", back_populates="medical_records")