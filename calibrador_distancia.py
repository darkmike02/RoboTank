import os
import cv2
import numpy as np

def diagnostico_10cm():
    print("📸 Tomando foto de proximidad crítica (10 cm)...")
    os.system("libcamera-jpeg -o proximidad.jpg -t 500 --width 320 --height 240 --nopreview > /dev/null 2>&1")
    
    img = cv2.imread("proximidad.jpg")
    if img is None: return
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Máscaras
    mask_r = cv2.bitwise_or(cv2.inRange(hsv, np.array([0, 100, 50]), np.array([10, 255, 255])),
                             cv2.inRange(hsv, np.array([160, 100, 50]), np.array([180, 255, 255])))
    mask_b = cv2.inRange(hsv, np.array([100, 100, 50]), np.array([140, 255, 255]))
    
    cnt_r, _ = cv2.findContours(mask_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt_b, _ = cv2.findContours(mask_b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"\n🔍 RESULTADOS A 10 CM:")
    print(f"🔴 Manchas Rojas: {len(cnt_r)}")
    print(f"🔵 Manchas Azules: {len(cnt_b)}")
    
    if len(cnt_r) > 0 and len(cnt_b) == 0:
        print("💡 DIAGNÓSTICO: Veo el Rojo pero PERDÍ EL AZUL. (El pedestal está oculto bajo el rojo).")
    elif len(cnt_r) == 0:
        print("💡 DIAGNÓSTICO: NO VEO EL ROJO. (Probablemente por sombra o desenfoque).")
    
    cv2.imwrite("ver_10cm_mascara.jpg", mask_r)
    print("\n🖼️ Imagen de máscara guardada como 'ver_10cm_mascara.jpg'.")

diagnostico_10cm()