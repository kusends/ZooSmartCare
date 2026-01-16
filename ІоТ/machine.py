import time

# Глобальний стан для симуляції фізики
# Це дозволяє датчику (dht.py) знати, чи увімкнено обігрівач у цьому файлі
SIMULATION_STATE = {
    'heater_on': False,
    'fan_on': False
}

class Pin:
    OUT = 1
    IN = 0
    PULL_UP = 2
    
    def __init__(self, pin_id, mode=None, pull=None, value=0):
        self.pin_id = pin_id
        self.mode = mode
        self._value = value
        
        # Визначаємо назву на основі твого configuration.py
        # relay_heat_pin: 4, relay_fan_pin: 5
        if pin_id == 4: self.name = "🔥 Heater (Pin 4)"
        elif pin_id == 5: self.name = "❄️ Fan (Pin 5)"
        elif pin_id == 15: self.name = "🌡 DHT Power (Pin 15)"
        else: self.name = f"Pin({pin_id})"
    
    def value(self, val=None):
        if val is not None:
            if self._value != val:
                state = "ON" if val else "OFF"
                print(f"   [HARDWARE] {self.name} -> {state}")
                
                # Оновлюємо глобальний стан симуляції
                if self.pin_id == 4: 
                    SIMULATION_STATE['heater_on'] = bool(val)
                elif self.pin_id == 5: 
                    SIMULATION_STATE['fan_on'] = bool(val)
                    
            self._value = val
        return self._value

class PWM:
    def __init__(self, pin, freq=50):
        self.pin = pin
        self.freq = freq
        self._duty = 0
        
    def duty(self, val):
        # Логуємо тільки значні зміни
        if abs(self._duty - val) > 10:
            pos = "OPEN" if val > 50 else "CLOSED"
            print(f"   [HARDWARE] 🤖 Servo (Pin {self.pin.pin_id}) -> {pos} (val={val})")
        self._duty = val