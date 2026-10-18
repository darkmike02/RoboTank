import time
from vision_engine import VisionEngine

# 👇 Importamos exactamente la clase CameraStream
from drivers.camera_stream import CameraStream  

print("🚀 Iniciando prueba del HITO 1: Percepción (Modo Seguro)...")
motor_visual = VisionEngine()

print("Conectando con el Bypass Definitivo de libcamera...")
# Instanciamos la clase con su nombre real
camara = CameraStream() 

print("✅ Cámara lista. Pon un objeto ROJO frente al robot. Presiona Ctrl+C para salir.\n")

try:
    while True:
        # Extraemos el fotograma usando tu función
        frame_bytes = camara.get_frame()
        
        if frame_bytes is not None:
            # El motor visual procesa los bytes
            detectado, cx, cy, area = motor_visual.buscar_coordenadas_rojas(frame_bytes)
            
            if detectado:
                print(f"🎯 ¡OBJETO DETECTADO! -> X: {cx} | Y: {cy} | Tamaño: {area:.0f}")
            else:
                print("👀 Buscando objetivo...")
        else:
            print("⚠️ Esperando fotograma del buffer...")
            
        time.sleep(0.1) # 10 FPS de prueba

except KeyboardInterrupt:
    print("\n🛑 Prueba detenida por el piloto.")
finally:
    camara.stop() # Apagamos el subprocess correctamente
    print("Sistemas apagados.")