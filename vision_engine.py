import cv2
import numpy as np

class VisionEngine:
    def __init__(self):
        print("👁️ [VISION ENGINE]: Inicializando Lóbulo Visual Rápido...")
        
        # El color ROJO en el espacio HSV tiene dos rangos (rojo bajo y rojo alto)
        self.lower_red1 = np.array([0, 120, 70])
        self.upper_red1 = np.array([10, 255, 255])
        
        self.lower_red2 = np.array([170, 120, 70])
        self.upper_red2 = np.array([180, 255, 255])

    def buscar_coordenadas_rojas(self, frame_bytes):
        import numpy as np
        import cv2

        # Decodificación estándar
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None: return False, 0, 0, 0
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # RANGOS ESTRICTOS (Evita sombras y ruido azul del entorno)
        lower_red1, upper_red1 = np.array([0, 160, 100]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([170, 160, 100]), np.array([180, 255, 255])
        lower_blue, upper_blue = np.array([100, 180, 100]), np.array([130, 255, 255])

        mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), 
                                  cv2.inRange(hsv, lower_red2, upper_red2))
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        # MORFOLOGÍA: Cerrar agujeros en el plástico rojo (brillos)
        kernel = np.ones((7,7), np.uint8)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)
        
        # Detección de contornos
        cnt_r, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt_b, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rojos = [c for c in cnt_r if cv2.contourArea(c) > 150]
        azules = [c for c in cnt_b if cv2.contourArea(c) > 150]

        for r in rojos:
            area_r = cv2.contourArea(r)
            rx, ry, rw, rh = cv2.boundingRect(r)
            cx_r, cy_r = rx + rw//2, ry + rh//2

            # LOGICA DE BYPASS (10 cm)
            # Si el bloque rojo es muy grande (>5000px), asumimos proximidad 
            # y omitimos la validación del pedestal azul.
            if area_r > 5000:
                return True, cx_r, cy_r, area_r

            # FILTRO ESPACIAL ESTÁNDAR (Rojo sobre Azul)
            for b in azules:
                bx, by, bw, bh = cv2.boundingRect(b)
                cx_b = bx + bw//2
                if abs(cx_r - cx_b) < 60 and ry < (by + 20):
                    return True, cx_r, cy_r, area_r

        return False, 0, 0, 0