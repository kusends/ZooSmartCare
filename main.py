import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Імпортуємо спільні налаштування (БД, engine) з dependencies
from dependencies import engine, Base, get_password_hash # Переконайся, що dependencies.py створено
from models import User

# Імпортуємо наші роутери
from admin_logic import router as admin_router
from business_logic import router as business_router

# Завантаження змінних оточення (якщо треба для config)
load_dotenv()

# Створення таблиць (якщо їх ще немає)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ZooSmartCare API",
    description="Integrated Zoo Management System",
    version="1.1"
)

# ПІДКЛЮЧЕННЯ РОУТЕРІВ
# Тепер вся логіка живе в цих двох файлах
app.include_router(admin_router)
app.include_router(business_router)

# --- Startup Event: Створення адміна ---
@app.on_event("startup")
def create_initial_admin():
    from dependencies import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.role == "admin").first()
        if not user:
            admin_user = User(
                full_name="Super Admin",
                role="admin",
                # Використовуємо хешування з dependencies
                login_credentials=get_password_hash("admin"), 
                contact_info="admin@zoo.system"
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default Admin created (login=admin, pass=admin)")
    finally:
        db.close()