import time
from drivers import servo

print("📡 INICIANDO RADAR DE SERVOS...")
servo.clean_all()

# Vamos a probar los 16 canales posibles de la placa PCA9685
for canal in range(16):
    print(f"▶️ Enviando pulso al CANAL {canal}...")
    
    try:
        # Movemos el motor de un lado a otro
        servo.ctrl(canal, 60)
        time.sleep(0.5)
        servo.ctrl(canal, 120)
        time.sleep(0.5)
        
        # Lo regresamos al centro
        servo.ctrl(canal, 90)
        time.sleep(0.5)
    except Exception as e:
        print(f"Canal {canal} vacío o sin configurar.")

print("✅ Búsqueda terminada. ¿Qué números movieron la cámara?")