import time
import json
import re
import os
import sys

# Спробуємо імпортувати Paho MQTT (стандарт для ПК)
try:
    import paho.mqtt.client as mqtt
    USING_PAHO = True
except ImportError:
    # Fallback для MicroPython
    from umqtt.simple import MQTTClient
    USING_PAHO = False
# --- 1. ДОДАЄМО БАТЬКІВСЬКУ ДИРЕКТОРІЮ В PATH ---
# Це дозволяє бачити 'dependencies.py' та 'models.py', які лежать на рівень вище
current_dir = os.path.dirname(os.path.abspath(__file__)) # Папка: .../ZooSmartCare/IoT
parent_dir = os.path.dirname(current_dir)                # Папка: .../ZooSmartCare

# Додаємо батьківську папку в початок списку шляхів пошуку
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Імпортуємо твої класи
from core_business_logic import HardwareManager, LogicController
from dependencies import SessionLocal

# --- ВАЖЛИВО: Імпортуємо моделі для ORM запитів ---
from models import Enclosure, Animal, Species, ClimateProfile

# --- Функція для читання configuration.py ---
def load_config_file():
    """
    Читає файл configuration.py як JSON.
    """
    try:
        with open('configuration.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if "=" in content:
                content = content.split("=", 1)[1].strip()
            return json.loads(content)
    except Exception as e:
        print(f"⚠️ Error reading configuration.py: {e}")
        return {
            "aviary_id": "AV_001",
            "mqtt_server": "broker.hivemq.com",
            "temp_min": 20.0, "temp_max": 25.0, "hysteresis": 0.5,
            "dht_pin": 4, "relay_heat_pin": 5, "relay_fan_pin": 18, "servo_pin": 19,
            "feeding_schedule": []
        }

# --- ОНОВЛЕНА ФУНКЦІЯ: ВИКОРИСТАННЯ ORM ---
def update_climate_from_db(cfg):
    """
    Знаходить enclosure_id з рядка 'AV_001' -> 1,
    і бере з БД налаштування температури через моделі SQLAlchemy.
    """
    print("📡 Connecting to Database (ORM Mode)...")
    db = SessionLocal()
    
    try:
        # 1. Витягуємо цифру з ID вольєру
        aviary_str = str(cfg.get('aviary_id', '1'))
        digits = re.findall(r'\d+', aviary_str)
        enc_id = int(digits[0]) if digits else 1
            
        print(f"🔍 Searching configuration for Enclosure ID: {enc_id}...")

        # 2. ORM ЗАПИТ
        # Логіка: Знайти тварину в цьому вольєрі -> Отримати її вид -> Отримати профіль
        
        # Крок А: Шукаємо першу тварину в цьому вольєрі
        animal = db.query(Animal).filter(Animal.enclosure_id == enc_id).first()
        
        if not animal:
            print(f"⚠️ No animals found in Enclosure {enc_id}.")
            return

        print(f"   Found Animal: {animal.nickname} (Species ID: {animal.species_id})")

        # Крок Б: Шукаємо кліматичний профіль для цього виду
        # (Можна додати фільтр по сезону, якщо потрібно, тут беремо перший ліпший)
        climate = db.query(ClimateProfile).filter(ClimateProfile.species_id == animal.species_id).first()
        
        if climate:
            cfg['temp_min'] = float(climate.min_temperature)
            cfg['temp_max'] = float(climate.max_temperature)
            print(f"✅ CONFIG UPDATED: {animal.nickname} needs {climate.min_temperature}-{climate.max_temperature}°C")
        else:
            print(f"⚠️ No climate profile found for Species ID {animal.species_id}.")

    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        db.close()

# --- ГОЛОВНА ПРОГРАМА ---
print("Starting ZooSmartCare Client...")

# 1. Завантажуємо конфіг
config = load_config_file()

# 2. Оновлюємо його даними з бази через ORM
update_climate_from_db(config)

# 3. Ініціалізуємо залізо та логіку
hw = HardwareManager(config)
logic = LogicController(config)

# 4. Підключення до MQTT
mqtt_client = None
client_id = f"ZooClient_{config.get('aviary_id', 'Unknown')}"

try:
    if USING_PAHO:
        mqtt_client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.connect(config['mqtt_server'], 1883, 60)
        mqtt_client.loop_start()
    else:
        mqtt_client = MQTTClient(client_id, config['mqtt_server'])
        mqtt_client.connect()
        
    print(f"✅ MQTT Connected to {config['mqtt_server']}")
except Exception as e:
    print(f"❌ MQTT Failed: {e}. Running in OFFLINE mode.")

# --- Допоміжна функція годування ---
def feed_animal_routine():
    print("🥕 Feeding started...")
    hw.move_servo(90)
    time.sleep(1)
    hw.move_servo(0)
    print("✅ Feeding done.")

# --- MAIN LOOP ---
last_feed_time = 0

try:
    while True:
        # A. Зчитування
        raw_t, raw_h = hw.read_sensors()
        filtered_t = logic.filter_data(raw_t)
        
        limits_info = f"[{config['temp_min']}..{config['temp_max']}]"
        print(f"T: {filtered_t} {limits_info}, H: {raw_h}%")

        # B. Клімат-контроль
        status = "error"
        heat_on = False
        fan_on = False
        
        if filtered_t is not None:
            status, heat_on, fan_on = logic.process_climate(filtered_t)
            hw.set_heater(heat_on)
            hw.set_fan(fan_on)

        # C. Критичні стани
        is_critical = False
        if status != "stable" and filtered_t is not None:
            if filtered_t < (config['temp_min'] - 2) or filtered_t > (config['temp_max'] + 2):
                is_critical = True

        # D. Годування
        fed_now = False
        if logic.check_feeding_schedule():
            if time.time() - last_feed_time > 60:
                feed_animal_routine()
                fed_now = True
                last_feed_time = time.time()

        # E. Формування даних
        payload = {
            "aviary_id": config['aviary_id'],
            "temp": filtered_t,
            "hum": raw_h,
            "heater": 1 if heat_on else 0,
            "fan": 1 if fan_on else 0,
            "status": status,
            "timestamp": time.time()
        }

        # F. Відправка
        if mqtt_client:
            try:
                msg_str = json.dumps(payload)
                mqtt_client.publish("zoo/telemetry", msg_str)
                
                if is_critical:
                    alert = {"level": "CRITICAL", "msg": f"Temp warning: {filtered_t}"}
                    mqtt_client.publish("zoo/alerts", json.dumps(alert))
                
                if fed_now:
                    feed_evt = {"event": "FEEDING_DONE", "time": time.time()}
                    mqtt_client.publish("zoo/events", json.dumps(feed_evt))
                    
            except Exception as e:
                print(f"MQTT Publish Error: {e}")

        time.sleep(5)

except KeyboardInterrupt:
    print("Stopped.")
    if mqtt_client and USING_PAHO:
        mqtt_client.loop_stop()