# Цей файл виконується при завантаженні контролера
# Відповідає за ініціалізацію мережі (Activity Diagram: Init -> CheckWifi)

import network
import json
import time

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except OSError:
        print("Error: config.json not found!")
        return None

def connect_wifi():
    config = load_config()
    if not config:
        return

    ssid = config.get('wifi_ssid')
    password = config.get('wifi_pass')

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        
        # Чекаємо 10 секунд на підключення
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            time.sleep(1)

    if wlan.isconnected():
        print('Network config:', wlan.ifconfig())
    else:
        print('Wifi connection failed. Starting in OFFLINE mode.')

# Запускаємо з'єднання
connect_wifi()