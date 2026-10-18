import time
import math
from drivers import servo

class MissionLoop:
    def __init__(self, bot, vision, nav):
        self.bot = bot
        self.vision = vision
        self.nav = nav
        self.estado = "BUSCANDO"
        
        # --- CONSTANTES FÍSICAS ---
        self.H_EJE = 19.0
        self.X_OFFSET = 1.5
        self.L_CAM = 3.0
        self.OFFSET_BRAZO = 10   # Gap compensado
        self.Z_GRAB = 10.5         # Cota de agarre ideal
        
        # --- SERVOS Y ESCANEO ---
        self.angulo_radar = 90
        self.angulo_tilt  = 90
        self.direccion_scan = 3         # Velocidad de barrido horizontal
        self.direccion_tilt_scan = 2    # V11.8: Velocidad del cabeceo vertical
        self.canal_tilt = 5
        
        # --- UMBRALES DE DISTANCIA ---
        self.distancia_parada_p1 = 18
        self.distancia_parada_final = 22.0
        
        # --- PARÁMETROS VISUALES ---
        self.TARGET_CX = 147      # Compensación de lente
        self.TARGET_CY = 120
        
        # --- PID ---
        self.Kp = 2.5
        self.Ki = 0.01
        self.Kd = 0.5
        self.error_previo = 0
        self.integral     = 0

        self.muestras_us = []
        self.fase_guia   = ""
        self._grab_x           = 0.0  
        self._grab_y           = 0.0  
        self._grab_z           = 0.0  
        self._grab_area_inicio = 0.0  
        self._grab_intentos    = 0    
        
        # --- CONTROL DE TELEMETRÍA ---
        self.ultimo_log = 0.0

        print(f"👁️ [V11.8-ACTIVE-SCAN]: Escaneo 2D en Rejilla y Telemetría Táctica activados.")

    def log_telemetria(self, cx, cy, area, dist_actual):
        """Imprime un frame de datos sincronizable con video cada 0.5s"""
        if time.time() - self.ultimo_log > 0.5:
            print(f"📡 [LOG] Est: {self.estado:12} | Fase: {self.fase_guia:10} | "
                  f"CX: {cx:3} CY: {cy:3} Área: {area:4.0f} | "
                  f"Tilt: {self.angulo_tilt}° Radar: {self.angulo_radar}° | "
                  f"US_Real: {dist_actual:.1f}cm")
            self.ultimo_log = time.time()

    #def pausa_tactica(self, proximo_estado):
     #   self.bot.parar()
      #  dist_us = self.bot.medir_distancia() + self.OFFSET_BRAZO
       # print(f"\n⏸️  ESTADO COMPLETADO. Próximo: {proximo_estado}")
        #print(f"📏 Lectura X radial (US+Offset): {dist_us:.1f} cm")
        #input("👉 Verifique y presione ENTER para continuar...")

    def calcular_distancia_visual(self, cy):
        rad = math.radians(90 - self.angulo_tilt)
        z_lente = self.H_EJE - (self.L_CAM * math.sin(rad))
        x_lente = self.X_OFFSET + (self.L_CAM * math.cos(rad))
        if rad <= 0: return 100.0
        return x_lente + (z_lente / math.tan(rad))

    def _calcular_xy_desde_radar(self, dist_radial):
        angulo_rad = math.radians(self.angulo_radar - 90)
        return (dist_radial * math.cos(angulo_rad), dist_radial * math.sin(angulo_rad))

    def ejecutar_ciclo(self, frame_bytes):
        ve_objeto, cx, cy, area = self.vision.buscar_coordenadas_rojas(frame_bytes)
        dist_actual_bruta = self.bot.medir_distancia()
        
        # Disparar telemetría
        self.log_telemetria(cx, cy, area, dist_actual_bruta)

        # ── BUSCANDO ────────────────────────────────────────────
        if self.estado == "BUSCANDO":
            if ve_objeto:
                print("🔄 [LOG-EVENTO] -> Transición a ALINEANDO")
                self.estado = "ALINEANDO"
            else:
                # Escaneo Horizontal (Radar)
                self.angulo_radar += self.direccion_scan
                if self.angulo_radar >= 150 or self.angulo_radar <= 30:
                    self.direccion_scan *= -1
                servo.ctrl(self.bot.canales['base'], self.angulo_radar)
                
                # Escaneo Vertical Activo (Cabeceo)
                self.angulo_tilt += self.direccion_tilt_scan
                # Limites del cabeceo: 30° (suelo) a 100° (frente)
                if self.angulo_tilt >= 100 or self.angulo_tilt <= 30:
                    self.direccion_tilt_scan *= -1
                servo.ctrl(self.canal_tilt, self.angulo_tilt)
                
                time.sleep(0.05)

        # ── ALINEANDO ───────────────────────────────────────────
        elif self.estado == "ALINEANDO":
            if not ve_objeto:
                print("⚠️ [LOG-EVENTO] Objeto perdido en ALINEANDO -> Abortando a BUSCANDO")
                self.estado = "BUSCANDO"
                return

            if cx < (self.TARGET_CX - 10): self.angulo_radar += 2
            elif cx > (self.TARGET_CX + 10): self.angulo_radar -= 2
            self.angulo_radar = max(30, min(150, self.angulo_radar))
            servo.ctrl(self.bot.canales['base'], self.angulo_radar)

            if abs(self.angulo_radar - 90) < 6:
                self.error_previo = 0; self.integral = 0
                print("🔄 [LOG-EVENTO] -> Transición a ACERCANDO_P1")
                self.estado = "ACERCANDO_P1"
            else:
                v_giro = 77
                if self.angulo_radar > 90: self.bot.girar_derecha(v=v_giro)
                else: self.bot.girar_izquierda(v=v_giro)
                time.sleep(0.04); self.bot.parar()

        # ── ACERCANDO P1 ────────────────────────────────────────
        elif self.estado == "ACERCANDO_P1":
            dist_actual = dist_actual_bruta + self.OFFSET_BRAZO
            
            if not ve_objeto:
                self.bot.parar()
                self._grab_intentos += 1
                if self._grab_intentos > 15:
                    print(f"⚠️ [LOG-EVENTO] Objeto perdido en P1 por 15 ciclos -> Abortando a BUSCANDO")
                    self.estado = "BUSCANDO"
                    self._grab_intentos = 0
                return
            self._grab_intentos = 0

            error = dist_actual - self.distancia_parada_p1
            if error <= 0:
                self.tiempo_eval = time.time(); self.muestras_us = []
                print("🔄 [LOG-EVENTO] -> Transición a EVALUANDO")
                self.estado = "EVALUANDO"
            else:
                self.integral += error
                v_pid = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * (error - self.error_previo))
                self.bot.avanzar(v=max(45, min(80, int(v_pid))))
                self.error_previo = error

            # Tracking vertical comprobado (- es abajo)
            if cy > 130: self.angulo_tilt -= 2
            elif cy < 110: self.angulo_tilt += 2
            self.angulo_tilt = max(15, min(100, self.angulo_tilt))
            servo.ctrl(self.canal_tilt, self.angulo_tilt)

        # ── EVALUANDO ───────────────────────────────────────────
        elif self.estado == "EVALUANDO":
            dist_lectura = dist_actual_bruta
            if dist_lectura <= 2.0 or dist_lectura > 80.0: return  
            dist_actual = dist_lectura + self.OFFSET_BRAZO
            diff_p1 = dist_actual - self.distancia_parada_p1

            if abs(diff_p1) > 2.5:
                self.bot.avanzar(v=45) if diff_p1 > 0 else self.bot.retroceder(v=45)
                time.sleep(0.06); self.bot.parar()
                self.tiempo_eval = time.time(); self.muestras_us = []
                return

            if time.time() - self.tiempo_eval < 0.8:
                self.muestras_us.append(dist_actual)
                return

            if not self.muestras_us: self.muestras_us.append(dist_actual)
            self.error_previo = 0; self.integral = 0
            print("🔄 [LOG-EVENTO] -> Transición a ACERCANDO_P2")
            self.estado = "ACERCANDO_P2"

        # ── ACERCANDO P2 ────────────────────────────────────────
        elif self.estado == "ACERCANDO_P2":
            dist_lectura = dist_actual_bruta
            dist_actual  = dist_lectura + self.OFFSET_BRAZO

            # Paciencia Táctica: Bajar la mirada si lo pierde
            if dist_lectura <= 0 or not ve_objeto:
                self.bot.parar()
                self.angulo_tilt -= 1 # Sigue buscando hacia abajo
                servo.ctrl(self.canal_tilt, max(15, self.angulo_tilt))
                self._grab_intentos += 1
                if self._grab_intentos > 20:
                    print(f"❌ [LOG-EVENTO] Ceguera total en P2 (20 intentos). Abortando a BUSCANDO. Tilt actual: {self.angulo_tilt}")
                    self.estado = "BUSCANDO"
                    self._grab_intentos = 0
                return
            self._grab_intentos = 0

            # Tracking agresivo en fase final
            if cy > 140: self.angulo_tilt -= 3
            elif cy < 100: self.angulo_tilt += 2
            self.angulo_tilt = max(15, min(100, self.angulo_tilt))
            servo.ctrl(self.canal_tilt, self.angulo_tilt)

            error = dist_actual - self.distancia_parada_final
            if error <= 0:
                x_pred, y_pred = self._calcular_xy_desde_radar(dist_actual)
                #self.pausa_tactica("CAPTURANDO")
                self.fase_guia = "HOVER"
                self._grab_intentos = 0
                print("🔄 [LOG-EVENTO] -> Transición a CAPTURANDO")
                self.estado = "CAPTURANDO"
            else:
                self.integral += error
                v_pid = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * (error - self.error_previo))
                self.bot.avanzar(v=max(45, min(65, int(v_pid))))
                self.error_previo = error

        elif self.estado == "CAPTURANDO":
            self._ejecutar_grab_guiado(ve_objeto, cx, cy, area)

        elif self.estado == "COMPLETADO":
            self.bot.parar()

    def _ejecutar_grab_guiado(self, ve_objeto, cx, cy, area):
        if self.fase_guia == "HOVER":
            print("🦾 [GRAB] HOVER — Desplegando brazo alto.")
            self.bot.pinza_abrir()
            self.bot.mover_brazo_a(14, 0, 12)
            self.tiempo_lock = time.time(); self._grab_intentos = 0
            self.fase_guia = "CENTERING"

        elif self.fase_guia == "CENTERING":
            if time.time() - self.tiempo_lock < 0.5: return  

            if not ve_objeto:
                self.angulo_tilt -= 2 # Busca hacia abajo
                servo.ctrl(self.canal_tilt, max(15, self.angulo_tilt))
                self._grab_intentos += 1
                if self._grab_intentos > 15:
                    print("⚠️ [LOG-EVENTO] Objeto perdido en CENTERING. Rebotando a HOVER.")
                    self.fase_guia = "HOVER"
                return

            error_x = self.TARGET_CX - cx
            if abs(error_x) > 5:
                self.angulo_radar += (1 if error_x > 0 else -1)
                self.angulo_radar = max(30, min(150, self.angulo_radar))
                servo.ctrl(self.bot.canales['base'], self.angulo_radar)
                self._grab_intentos = 0   
                return

            # Zona Muerta Y: Solo ajusta si está muy cerca de los bordes
            if cy < 60:
                self.angulo_tilt += 1 # Mira arriba
                self.angulo_tilt = min(110, self.angulo_tilt)
                servo.ctrl(self.canal_tilt, self.angulo_tilt)
                return
            elif cy > 180:
                self.angulo_tilt -= 1 # Mira abajo
                self.angulo_tilt = max(15, self.angulo_tilt)
                servo.ctrl(self.canal_tilt, self.angulo_tilt)
                return

            print("✅ [GRAB] Ejes alineados. Pasando a GRAB_ALIGN.")
            self.fase_guia = "GRAB_ALIGN"
            self._grab_intentos = 0

        elif self.fase_guia == "GRAB_ALIGN":
            dist_lectura = self.bot.medir_distancia()
            if dist_lectura < 2 or dist_lectura > 60:
                self._grab_intentos += 1
                if self._grab_intentos > 10: self.fase_guia = "HOVER"
                return

            dist_radial = min(dist_lectura + self.OFFSET_BRAZO, 23.5)
            if not ve_objeto:
                self._grab_intentos += 1
                if self._grab_intentos > 10: self.fase_guia = "CENTERING"
                return

            self._grab_x, self._grab_y = self._calcular_xy_desde_radar(dist_radial)
            self._grab_z = 12.0
            print(f"📐 Solución: X={self._grab_x:.1f} Y={self._grab_y:.1f} Z={self._grab_z}")
            self.fase_guia = "GRAB_DESCEND"; self._grab_intentos = 0

        elif self.fase_guia == "GRAB_DESCEND":
            if self._grab_z <= self.Z_GRAB:
                self.fase_guia = "GRAB_CLOSE"
                return

            if ve_objeto:
                error_x = self.TARGET_CX - cx
                if abs(error_x) > 10:
                    self.angulo_radar += (1 if error_x > 0 else -1)
                    self.angulo_radar = max(30, min(150, self.angulo_radar))
                    servo.ctrl(self.bot.canales['base'], self.angulo_radar)
                    time.sleep(0.15)
                    dist_lectura = self.bot.medir_distancia()
                    if 2 < dist_lectura < 60:
                        self._grab_x, self._grab_y = self._calcular_xy_desde_radar(min(dist_lectura + self.OFFSET_BRAZO, 23.5))
            else:
                self._grab_intentos += 1
                if self._grab_intentos > 5:
                    self._grab_z = 12.0; self.fase_guia = "CENTERING"
                    self.bot.mover_brazo_a(14, 0, 12)
                return

            siguiente_z = max(self.Z_GRAB, self._grab_z - 2.0)
            self._grab_z = siguiente_z
            self.bot.mover_brazo_a(self._grab_x, self._grab_y, self._grab_z)
            time.sleep(0.6)
            self._grab_intentos = 0

        elif self.fase_guia == "GRAB_CLOSE":
            if self._grab_area_inicio == 0.0:
                self._grab_area_inicio = area if ve_objeto else 500.0

            ang_actual = self.bot.angulos.get('garra', 130)
            nuevo_ang = max(50, ang_actual - 20)
            servo.ctrl(self.bot.canales['garra'], nuevo_ang)
            self.bot.angulos['garra'] = nuevo_ang
            time.sleep(0.5)

            if nuevo_ang <= 50:
                self._verificar_y_finalizar(ve_objeto, area)
            else:
                if self._grab_area_inicio > 0 and ve_objeto:
                    if (area / self._grab_area_inicio) > 1.3:
                        self.bot.pinza_abrir()
                        self._grab_z = 12.0; self._grab_area_inicio = 0.0
                        self.bot.mover_brazo_a(14, 0, 12)
                        time.sleep(0.5); self.fase_guia = "CENTERING"

    def _verificar_y_finalizar(self, ve_objeto, area):
        print("🎉 CRITERIO DE ÉXITO: Pinza cerrada. Elevando carga...")
        self.bot.mover_brazo_a(12, 0, 20)
        time.sleep(1.0)
        self._grab_area_inicio = 0.0
        self.bot.emocion_feliz()
        self.bot.escribir_oled(2, "Mision: OK")
        self.bot.escribir_oled(3, "Lego Asegurado")
        self.estado = "COMPLETADO"