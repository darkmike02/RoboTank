# drivers/config_robot.py

# --- DIMENSIONES FÍSICAS (cm) ---
L1_HUMERUS = 13.0
L2_FOREARM = 13.0
L0_SHOULDER_HEIGHT = 20.0

# --- OFFSETS DE SERVOS ---
OFFSET_SHOULDER = 50
OFFSET_ELBOW = 135

# --- LÍMITES DE SERVOS (Min, Max) ---
# 0:Base, 1:Hombro, 2:Codo, 3:Pinza
SERVO_LIMITS = {
    0: (100, 500),
    1: (100, 500),
    2: (100, 500),
    3: (100, 500),
    4: (100, 500),
    5: (100, 500)  # <--- AÑADIMOS EL CANAL 5 PARA EL BYPASS
}

# --- PINES DE MOTORES (GPIO) ---
PIN_IN1 = 17
PIN_IN2 = 27
PIN_IN3 = 22
PIN_IN4 = 23
PIN_ENA = 25
PIN_ENB = 24