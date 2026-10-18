import Adafruit_PCA9685
from . import config_robot as cfg

pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)

def clean_all():
    pwm.set_all_pwm(0, 0)

def servo_init():
    # Posición inicial segura (Home)
    ctrl(0, 90)
    ctrl(1, 130) # Horizontal
    ctrl(2, 90)  # Angulo L

def ctrl(channel, angle):
    """
    Mueve el servo 'channel' al ángulo 'angle' (0-180).
    Usa los límites definidos en config_robot.py
    """
    if channel not in cfg.SERVO_LIMITS:
        return

    # 1. Obtener límites de este motor específico
    pwm_min, pwm_max = cfg.SERVO_LIMITS[channel]
    
    # 2. Asegurar que el ángulo no sea loco (Clamp 0-180)
    angle = max(0, min(180, int(angle)))
    
    # 3. Regla de 3 (Mapeo)
    # Si min=500 y max=100, esto invierte automáticamente el movimiento.
    pwm_val = int(pwm_min + (angle / 180.0) * (pwm_max - pwm_min))
    
    # 4. Enviar señal
    pwm.set_pwm(channel, 0, pwm_val)

# Funciones legacy para compatibilidad (puedes dejarlas vacías o usarlas)
def lookleft(speed): pass
def lookright(speed): pass
# ... (el resto de tus funciones antiguas no son críticas ahora)