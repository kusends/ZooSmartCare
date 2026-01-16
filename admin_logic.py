import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Імпортуємо спільні інструменти
from dependencies import (
    get_db, 
    verify_password, 
    get_password_hash, 
    create_access_token, 
    require_role, 
    get_current_user
)
from models import (
    User, Enclosure, Animal, IoTDevice, 
    MaintenanceLog, Alert
)
from schemas import (
    UserCreate, UserResponse, UserUpdate, Token, 
    EnclosureCreate, EnclosureResponse, EnclosureUpdate,
    AnimalCreate, AnimalResponse,
    IoTDeviceCreate, IoTDeviceResponse, IoTDeviceUpdate
)

router = APIRouter(prefix="/api/admin", tags=["Administration & Assets"])

# ==============================================================================
# А. АВТЕНТИФІКАЦІЯ (Вже було)
# ==============================================================================

@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Ендпоінт для отримання токена.
    Swagger UI автоматично надсилає сюди username та password.
    Ми використовуємо 'username' з форми як 'full_name' в нашій базі.
    Поля client_id та client_secret можна ігнорувати.
    """
    # 1. Шукаємо користувача. 
    # Увага: form_data.username - це те, що ввів користувач у полі "Username"
    user = db.query(User).filter(User.full_name == form_data.username).first()
    
    # 2. Перевірка пароля
    if not user:
        # Для безпеки не кажемо, що саме невірно (юзер чи пароль), але для дебагу можна вивести
        print(f"Login failed: User '{form_data.username}' not found.") 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(form_data.password, user.login_credentials):
        print(f"Login failed: Invalid password for '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Генерація токена
    # sub (subject) - унікальний ідентифікатор, за яким ми потім знайдемо юзера (full_name)
    access_token = create_access_token(data={"sub": user.full_name, "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer"}

# ==============================================================================
# Б. КОРИСТУВАЧІ (USERS)
# ==============================================================================

@router.post("/users/register", response_model=UserResponse)
def register_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """Створення користувача (доступ тільки для Адміна)"""
    db_user = db.query(User).filter(User.full_name == user.full_name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User with this name already registered")
    
    hashed_password = get_password_hash(user.login_credentials)
    new_user = User(
        full_name=user.full_name,
        role=user.role,
        login_credentials=hashed_password,
        contact_info=user.contact_info
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_admin_action(db, admin.user_id, None, "User Created", f"Created user {user.full_name}")
    return new_user

@router.get("/users/", response_model=List[UserResponse])
def get_all_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """[NEW] Отримати список усіх користувачів (фільтр за роллю)"""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """[NEW] Отримати дані конкретного користувача"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """[NEW] Оновити дані користувача"""
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.full_name:
        db_user.full_name = user_update.full_name
    if user_update.role:
        db_user.role = user_update.role
    if user_update.contact_info:
        db_user.contact_info = user_update.contact_info
    if user_update.password:
        db_user.login_credentials = get_password_hash(user_update.password)
        
    db.commit()
    db.refresh(db_user)
    log_admin_action(db, admin.user_id, None, "User Updated", f"Updated user ID {user_id}")
    return db_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """[NEW] Видалити користувача"""
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Забороняємо видаляти самого себе
    if db_user.user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(db_user)
    db.commit()
    log_admin_action(db, admin.user_id, None, "User Deleted", f"Deleted user ID {user_id}")
    return {"detail": "User deleted successfully"}

# ==============================================================================
# В. ВОЛЬЄРИ (ENCLOSURES)
# ==============================================================================

@router.post("/enclosures/", response_model=EnclosureResponse)
def create_enclosure(
    enclosure: EnclosureCreate, 
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin", "zoologist"]))
):
    """Створити новий вольєр"""
    qr_code_data = f"zoo://enclosure/{uuid.uuid4()}"
    db_enclosure = Enclosure(
        name=enclosure.name,
        geo_location=enclosure.geo_location,
        qr_code_string=qr_code_data
    )
    db.add(db_enclosure)
    db.commit()
    db.refresh(db_enclosure)
    log_admin_action(db, admin.user_id, db_enclosure.enclosure_id, "Enclosure Created", f"Created {enclosure.name}")
    return db_enclosure

@router.get("/enclosures/", response_model=List[EnclosureResponse])
def get_all_enclosures(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user) # Доступно всім авторизованим
):
    """[NEW] Отримати список всіх вольєрів"""
    return db.query(Enclosure).all()

@router.get("/enclosures/{enclosure_id}", response_model=EnclosureResponse)
def get_enclosure_detail(
    enclosure_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """[NEW] Деталі вольєра"""
    enclosure = db.query(Enclosure).filter(Enclosure.enclosure_id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(status_code=404, detail="Enclosure not found")
    return enclosure

@router.put("/enclosures/{enclosure_id}", response_model=EnclosureResponse)
def update_enclosure(
    enclosure_id: int,
    update_data: EnclosureUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin", "zoologist"]))
):
    """[NEW] Оновити дані вольєра"""
    enclosure = db.query(Enclosure).filter(Enclosure.enclosure_id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(status_code=404, detail="Enclosure not found")
    
    if update_data.name: enclosure.name = update_data.name
    if update_data.geo_location: enclosure.geo_location = update_data.geo_location
    if update_data.qr_code_string: enclosure.qr_code_string = update_data.qr_code_string
    
    db.commit()
    db.refresh(enclosure)
    log_admin_action(db, admin.user_id, enclosure_id, "Enclosure Updated", "Updated details")
    return enclosure

@router.delete("/enclosures/{enclosure_id}")
def delete_enclosure(
    enclosure_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """[NEW] Видалити вольєр (обережно, якщо є тварини!)"""
    enclosure = db.query(Enclosure).filter(Enclosure.enclosure_id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(status_code=404, detail="Enclosure not found")
    
    # Перевірка на наявність тварин
    if enclosure.animals:
        raise HTTPException(status_code=400, detail="Cannot delete enclosure with animals inside")

    db.delete(enclosure)
    db.commit()
    log_admin_action(db, admin.user_id, enclosure_id, "Enclosure Deleted", f"Deleted enclosure ID {enclosure_id}")
    return {"detail": "Enclosure deleted successfully"}

# ==============================================================================
# Г. IOT ПРИСТРОЇ (DEVICES)
# ==============================================================================

@router.post("/devices/register", response_model=IoTDeviceResponse)
def register_iot_device(
    device: IoTDeviceCreate, 
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """Зареєструвати новий пристрій"""
    existing = db.query(IoTDevice).filter(IoTDevice.mac_address == device.mac_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device MAC already registered")
    
    new_device = IoTDevice(
        mac_address=device.mac_address,
        enclosure_id=device.enclosure_id,
        firmware_version=device.firmware_version or "1.0.0",
        status=device.status or "Offline"
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    log_admin_action(db, admin.user_id, device.enclosure_id, "Device Registered", f"MAC: {device.mac_address}")
    return new_device

@router.get("/devices/", response_model=List[IoTDeviceResponse])
def get_all_devices(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin", "technician"]))
):
    """[NEW] Список пристроїв (фільтр: Online/Offline)"""
    query = db.query(IoTDevice)
    if status_filter:
        query = query.filter(IoTDevice.status == status_filter)
    return query.all()

@router.put("/devices/{device_id}", response_model=IoTDeviceResponse)
def update_device(
    device_id: int,
    update_data: IoTDeviceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin", "technician"]))
):
    """[NEW] Оновити пристрій (прив'язати до іншого вольєра, змінити статус)"""
    device = db.query(IoTDevice).filter(IoTDevice.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if update_data.mac_address: device.mac_address = update_data.mac_address
    if update_data.firmware_version: device.firmware_version = update_data.firmware_version
    if update_data.status: device.status = update_data.status
    if update_data.enclosure_id is not None: device.enclosure_id = update_data.enclosure_id
    
    db.commit()
    db.refresh(device)
    log_admin_action(db, admin.user_id, device.enclosure_id, "Device Updated", f"Updated Device ID {device_id}")
    return device

@router.delete("/devices/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"]))
):
    """[NEW] Видалити пристрій"""
    device = db.query(IoTDevice).filter(IoTDevice.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    log_admin_action(db, admin.user_id, None, "Device Deleted", f"Deleted Device ID {device_id}")
    return {"detail": "Device deleted successfully"}

# ==============================================================================
# Д. ТВАРИНИ (ANIMALS - Адмін частина)
# ==============================================================================

@router.post("/animals/", response_model=AnimalResponse)
def create_animal_card(
    animal: AnimalCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin", "zoologist"]))
):
    """Створити картку тварини"""
    new_animal = Animal(**animal.dict())
    db.add(new_animal)
    db.commit()
    db.refresh(new_animal)
    log_admin_action(db, user.user_id, animal.enclosure_id, "Animal Created", f"Created {animal.nickname}")
    return new_animal

@router.delete("/animals/{animal_id}")
def archive_animal_card(
    animal_id: int, 
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin", "zoologist"]))
):
    """Архівувати/Видалити картку тварини"""
    animal = db.query(Animal).filter(Animal.animal_id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    
    log_admin_action(db, user.user_id, animal.enclosure_id, "Animal Deleted", f"Deleted ID {animal_id}")
    
    db.delete(animal) # Повне видалення. Для архівування треба було б змінити статус, але це не вимагалося.
    db.commit()
    
    return {"detail": "Animal card deleted successfully"}

# ==============================================================================
# Е. СИСТЕМНІ ФУНКЦІЇ
# ==============================================================================

def log_admin_action(db: Session, user_id: int, enclosure_id: Optional[int], action: str, notes: str):
    """Внутрішня функція для запису дій в лог"""
    log_entry = MaintenanceLog(
        user_id=user_id,
        enclosure_id=enclosure_id, # Може бути None, якщо дія не стосується вольєра
        action_type=action,
        notes=notes,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()

@router.get("/system/health-check")
def system_health_check(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin", "technician"]))
):
    """Перевірка стану системи"""
    # Перевірка "мертвих" пристроїв (немає зв'язку більше 30 хв)
    timeout_threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
    offline_devices = db.query(IoTDevice).filter(IoTDevice.last_sync < timeout_threshold).all()
    
    updated_count = 0
    for dev in offline_devices:
        if dev.status != "Offline":
            dev.status = "Offline"
            updated_count += 1
            # Створюємо системний алерт
            if dev.enclosure_id:
                alert = Alert(
                    enclosure_id=dev.enclosure_id,
                    alert_type="System",
                    message=f"Device {dev.mac_address} lost connection",
                    status="New",
                    timestamp=datetime.datetime.utcnow()
                )
                db.add(alert)
    
    if updated_count > 0:
        db.commit()
        
    return {
        "status": "System Operational",
        "offline_devices_detected": len(offline_devices),
        "db_connection": "OK"
    }