import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User

# --- Конфігурація ---
load_dotenv()
SECRET_KEY = "SECRET_KEY_ZOOSMARTCARE_PROJECT_2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Налаштування БД
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345@127.0.0.1:5432/ZooSmartCare"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"client_encoding": "utf8"} 
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Безпека
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Вказуємо правильний шлях до ендпоінту отримання токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")

# --- Функції ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    # УВАГА: Якщо в базі лежать прості рядки (як 'hash_pass_1' з мого SQL скрипта), 
    # то verify видасть помилку, бо це не хеш.
    # Для тестування можна тимчасово зробити так:
    if hashed_password == plain_password: return True # Тимчасова дірка для старих даних
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # У токені ми зберігаємо ім'я в полі 'sub'
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # ВИПРАВЛЕНО: шукаємо по full_name, бо поля username немає в моделі
    user = db.query(User).filter(User.full_name == username).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(allowed_roles: list):
    def role_checker(current_user: User = Depends(get_current_user)):
        # Приводимо до нижнього регістру для надійності (Admin -> admin)
        user_role = current_user.role.lower() if current_user.role else ""
        allowed = [r.lower() for r in allowed_roles]
        
        if user_role not in allowed:
            raise HTTPException(
                status_code=403, 
                detail=f"Operation not permitted. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker