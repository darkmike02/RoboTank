"""import cv2
import time

print("🔍 Buscando la cámara en el puerto 0...")
# Inicializamos OpenCV en el índice 0
camara = cv2.VideoCapture(-1)

# Damos 2 segundos para que el sensor de luz se caliente/estabilice
time.sleep(2)

# Intentamos tomar una sola foto
exito, imagen = camara.read()

if exito:
    print("✅ ¡Cámara encontrada y leyendo correctamente!")
    cv2.imwrite("foto_prueba.jpg", imagen)
    print("📸 Foto guardada exitosamente como 'foto_prueba.jpg'.")
else:
    print("❌ ERROR: No se pudo capturar la imagen. La cámara no responde al índice 0.")

# Liberar el hardware
camara.release()"""

from drivers.camera_stream import CameraStream
import time

cam = CameraStream()
print("📸 Intentando capturar 10 frames...")
for i in range(10):
    frame = cam.get_frame()
    if frame is not None:
        print(f"✅ Frame {i} recibido (Tamaño: {len(frame)})")
    else:
        print(f"❌ Frame {i} vacío...")
    time.sleep(0.5)
cam.stop()