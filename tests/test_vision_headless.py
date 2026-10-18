import cv2
import numpy as np
import subprocess
import time

print("🛠️ Iniciando Diagnóstico Óptico V11.0 (Headless + Bypass)")

# BYPASS DEFINITIVO: Usar libcamera-vid enviando MJPEG a la salida estándar
comando = [
    "libcamera-vid",
    "--codec", "mjpeg",
    "--width", "320",
    "--height", "240",
    "--framerate", "15",
    "-t", "0",      # Tiempo infinito
    "--nopreview",  # Sin ventana de previsualización
    "-o", "-"       # Salida estándar (stdout)
]

# Iniciar el subproceso de captura
try:
    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
except Exception as e:
    print(f"❌ Error al iniciar libcamera: {e}")
    exit()

print("✅ Bypass iniciado. Coloque el Lego a 20cm en el eje central.")
print("Presione Ctrl+C en la terminal para salir.")

bytes_data = b''

try:
    while True:
        # Leer bloque de datos del subproceso
        chunk = proceso.stdout.read(4096)
        if not chunk:
            continue
        bytes_data += chunk
        
        # Buscar marcadores de inicio y fin de una imagen JPEG
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')
        
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:] # Limpiar el buffer
            
            # Decodificar el frame en memoria
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            if frame is not None:
                # 1. Conversión a HSV
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # 2. Máscara de color ROJO
                mask1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
                mask = mask1 + mask2
                
                # 3. Filtrado de ruido
                kernel = np.ones((5,5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                
                # 4. Detección
                contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contornos:
                    c = max(contornos, key=cv2.contourArea)
                    area = cv2.contourArea(c)
                    if area > 100:
                        M = cv2.moments(c)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            desviacion = cx - 160
                            print(f"🎯 OBJETIVO | Area: {area:.0f} | CX: {cx} (Desv: {desviacion}) | CY: {cy}")
                else:
                    print("🔍 Buscando rojo...")

except KeyboardInterrupt:
    print("\n🛑 Diagnóstico abortado manualmente por el Teniente.")
finally:
    proceso.terminate()
    print("👋 Subproceso de cámara apagado de forma segura.")