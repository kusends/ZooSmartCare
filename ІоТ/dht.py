import random
# Імпортуємо стан із сусіднього файлу
from machine import SIMULATION_STATE

class DHT22:
    def __init__(self, pin):
        self.pin = pin
        self._temp = 20.0 # Початкова температура
        self._hum = 50.0

    def measure(self):
        # === ФІЗИКА СИМУЛЯЦІЇ ===
        # Якщо увімкнено обігрівач (Pin 4)
        if SIMULATION_STATE['heater_on']:
            self._temp += 0.8  # Гріємося швидко
            self._hum -= 0.2   # Повітря сушиться
            
        # Якщо увімкнено вентилятор (Pin 5)
        elif SIMULATION_STATE['fan_on']:
            self._temp -= 0.6  # Охолоджуємося
            
        # Природній стан (повільне повернення до кімнатної 22°C)
        if self._temp > 20.0:
            self._temp -= 0.1
        elif self._temp < 20.0:
            self._temp += 0.1
            
            # Додаємо трохи випадкового шуму
        self._temp += random.uniform(-1, 1)

        # Обмежуємо вологість
        self._hum += random.uniform(-0.5, 0.5)
        self._hum = max(0, min(100, self._hum))

    def temperature(self):
        return round(self._temp, 1)

    def humidity(self):
        return round(self._hum, 1)