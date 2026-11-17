from machine import ADC, Pin
import time

ldr_pin = ADC(Pin(2))

VIN = 3.3
R_FIXED = 10000.0
RL10 = 50000.0
GAMMA = 0.7

def read_lux():
    raw = ldr_pin.read_u16()
    if raw <= 0:
        return float('inf')
    if raw >= 65535:
        return 0.0
        
    voltage = (raw / 65535.0) * VIN
    
    r_ldr = R_FIXED * (voltage / (VIN - voltage))
    
    
    lux = 10.0 * ((RL10 / r_ldr) ** (1.0 / GAMMA))
    return lux

while True:
    lux_value = read_lux()
    print(f"Estimated Light: {lux_value:.1f} lux")
    time.sleep(0.5)
