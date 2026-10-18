import cv2
import time
import subprocess
import numpy as np

class CameraStream:
    def __init__(self):
        print("📷 Iniciando cámara con BYPASS DEFINITIVO (Subprocess)...")
        self.width = 640
        self.height = 480
        
        # Matemáticas: Un frame en formato YUV420 pesa exactamente (Ancho * Alto * 1.5) bytes
        self.frame_size = int(self.width * self.height * 1.5)
        
        # Comando mágico: libcamera-vid en modo infinito, escupiendo video por la terminal
        cmd = [
            "libcamera-vid", 
            "-t", "0",               # Tiempo infinito
            "--width", str(self.width), 
            "--height", str(self.height), 
            "--framerate", "15",     # 15 fps es perfecto para no saturar el WiFi
            "--codec", "yuv420",     # Formato crudo y rápido
            "-n",                    # Sin ventana de previsualización
            "-o", "-"                # Enviar los datos por la salida estándar (stdout)
        ]
        
        # Abrimos el túnel de conexión con el sistema operativo
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        time.sleep(2) # Calentamiento del sensor

    def get_frame(self):
        try:
            # Leemos exactamente los bytes que componen 1 foto
            raw_data = self.process.stdout.read(self.frame_size)
            if len(raw_data) != self.frame_size:
                return None
            
            # Convertimos esos bytes en una imagen entendible para OpenCV
            yuv = np.frombuffer(raw_data, dtype=np.uint8).reshape((int(self.height * 1.5), self.width))
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            
            # Redimensionamos la imagen para que tu navegador web no sufra lag
            frame_web = cv2.resize(bgr, (320, 240))
            
            # Comprimimos a JPEG para enviar
            ret, buffer = cv2.imencode('.jpg', frame_web)
            return buffer.tobytes()
            
        except Exception as e:
            print(f"❌ Error en el flujo de video: {e}")
            return None

    def stop(self):
        # Apagamos el proceso cuando se cierra el servidor
        if self.process:
            self.process.terminate()