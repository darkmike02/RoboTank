import cv2
import numpy as np
import time

print("🛠️ Iniciando test_vision_debug.py - Calibración V11.0")

# 1. Iniciar cámara ( /dev/video0 es el estándar para USB y CSI )
cap = cv2.VideoCapture(0)

# 2. Forzar resolución a 320x240 (El centro ideal CX es 160)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

if not cap.isOpened():
    print("❌ Error: No se pudo abrir la cámara. Verifique la conexión física.")
    exit()

print("✅ Cámara detectada. Coloque el Lego ROJO a 20cm exactos en el eje central.")
print("Presione 'q' en la ventana de video para salir, o Ctrl+C en la terminal.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Error capturando el frame. Reintentando...")
            time.sleep(0.5)
            continue

        # 3. Conversión de espacio de color
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 4. Umbrales HSV para el color ROJO (Dividido en dos rangos)
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)

        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        mask = mask1 + mask2

        # 5. Filtrado de ruido morfológico (Crucial para sensores nuevos)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 6. Detección de contornos
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contornos:
            c = max(contornos, key=cv2.contourArea)
            area = cv2.contourArea(c)

            if area > 100: # Descartar manchas pequeñas
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    desviacion = cx - 160
                    
                    print(f"🎯 OBJETIVO | Area: {area:.0f} | CX: {cx} (Desviación: {desviacion}) | CY: {cy}")

                    # Trazado visual para debug
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
        else:
            print("🔍 Buscando color rojo...")

        # Dibujar retícula central
        cv2.line(frame, (160, 0), (160, 240), (255, 0, 0), 1)
        cv2.line(frame, (0, 120), (320, 120), (255, 0, 0), 1)

        # Intentar mostrar interfaz gráfica (Si usa OS Desktop/VNC)
        try:
            cv2.imshow("Vision Debug - Camara", frame)
            cv2.imshow("Vision Debug - Mascara", mask)
        except Exception:
            pass # Continúa silenciado si está en OS Lite (Solo terminal)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        time.sleep(0.15) # Evita saturar la consola de texto

except KeyboardInterrupt:
    print("\n🛑 Diagnóstico abortado manualmente.")

cap.release()
cv2.destroyAllWindows()
print("👋 Sistemas visuales desconectados.")