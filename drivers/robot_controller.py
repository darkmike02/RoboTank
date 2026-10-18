import time
import cv2
from . import move        # Motores
from . import servo       # Brazo
from . import ultra        # Distancia
from . import robotLight   # Luces
from . import mpu6050      # Giroscopio
from . import config_robot as cfg
from . import kinematics  # Matemática IK

# Intentamos importar OLED de forma segura
try:
    from . import OLED
    HAY_PANTALLA = True
except ImportError:
    HAY_PANTALLA = False
    print("⚠️ No se encontró librería OLED. Se usará modo sin pantalla.")

class Robot:
    def __init__(self):
        print("🤖 INICIALIZANDO SISTEMA ROBOT V9 (HARDWARE)...")
        
        # 1. Configurar Pantalla OLED
        self.oled = None
        if HAY_PANTALLA:
            try:
                self.oled = OLED.OLED_ctrl()
                self.oled.start()
                self.escribir_oled(1, "SISTEMA: INICIO")
                self.escribir_oled(2, "Cargando...")
            except:
                print("❌ Error al iniciar OLED HW")
        
        # 2. Configurar Motores y Servos
        move.setup()
        servo.clean_all()
        servo.servo_init()
        
        self.canales = {
            'base': 0,     # Gira todo el brazo (Y la cámara Izq/Der)
            'brazo': 1,    # Sube/baja el brazo (Hombro)
            'muneca': 2,   # Sube/baja la parte superior (Codo)
            'garra': 3,    # Abre/cierra
            'cam_tilt': 5  # Inclinación exclusiva de la cámara
        }
        
        self.angulos = {
            'base': 90, 'brazo': 90, 'muneca': 90,
            'garra': 90, 'cam_tilt': 90
        }
        
        # 3. Luces
        try:
            self.luces = robotLight.RobotLight()
            self.luces.start()
            self.emocion_neutra()
            print("💡 Luces RGB activadas.")
        except Exception as e:
            print(f"⚠️ Error al iniciar luces: {e}")
            self.luces = None
        
        # 4. IMU Sensor (MPU6050)
        try:
            mpu6050.init_MPU6050()
            self.imu_listo = True
            print("🧭 Giroscopio MPU6050 activado.")
        except Exception as e:
            print(f"⚠️ Error al iniciar MPU6050: {e}")
            self.imu_listo = False

        # --- CORRECCIÓN BUG-001: Esto estaba atrapado en medir_distancia() ---
        # 5. INICIAR CINEMÁTICA
        self.iniciar_cinematica()
        
        self.escribir_oled(1, "ROBOT V9: ONLINE")
        self.escribir_oled(2, "Esperando IA...")
        print("✅ HARDWARE LISTO.")

    # ==========================================
    #            SENSORES Y PANTALLA
    # ==========================================
    def medir_distancia(self):
        try:
            dist = ultra.checkdist()
            return 999 if dist == -1 else dist
        except Exception as e:
            return 999
            
    def leer_imu(self):
        if self.imu_listo:
            try: return mpu6050.get_sensor_data()
            except: return None
        return None

    def escribir_oled(self, linea, texto):
        if self.oled:
            texto_corto = str(texto)[:18] 
            self.oled.screen_show(linea, texto_corto)

    # ==========================================
    #            CONTROL GAMEPAD (TIEMPO REAL)
    # ==========================================
    def mover_camara(self, cam_x, cam_y):
        paso = 2 
        if cam_x > 0.5: self.angulos['base'] -= paso
        elif cam_x < -0.5: self.angulos['base'] += paso
            
        if cam_y > 0.5: self.angulos['cam_tilt'] -= paso
        elif cam_y < -0.5: self.angulos['cam_tilt'] += paso

        self.angulos['base'] = max(20, min(160, self.angulos['base']))
        self.angulos['cam_tilt'] = max(30, min(150, self.angulos['cam_tilt']))

        servo.ctrl(self.canales['base'], self.angulos['base'])
        servo.ctrl(self.canales['cam_tilt'], self.angulos['cam_tilt'])

    def brazo_subir(self):
        self.angulos['brazo'] += 2
        self.angulos['brazo'] = max(30, min(150, self.angulos['brazo'])) 
        servo.ctrl(self.canales['brazo'], self.angulos['brazo'])

    def brazo_bajar(self):
        self.angulos['brazo'] -= 2
        self.angulos['brazo'] = max(30, min(150, self.angulos['brazo']))
        servo.ctrl(self.canales['brazo'], self.angulos['brazo'])

    def muneca_subir(self):
        self.angulos['muneca'] += 2
        self.angulos['muneca'] = max(20, min(160, self.angulos['muneca']))
        servo.ctrl(self.canales['muneca'], self.angulos['muneca'])

    def muneca_bajar(self):
        self.angulos['muneca'] -= 2
        self.angulos['muneca'] = max(20, min(160, self.angulos['muneca']))
        servo.ctrl(self.canales['muneca'], self.angulos['muneca'])
        
    def garra_abrir(self):
        self.angulos['garra'] += 3 
        self.angulos['garra'] = max(50, min(130, self.angulos['garra']))
        servo.ctrl(self.canales['garra'], self.angulos['garra'])

    def garra_cerrar(self):
        self.angulos['garra'] -= 3
        self.angulos['garra'] = max(50, min(130, self.angulos['garra']))
        servo.ctrl(self.canales['garra'], self.angulos['garra'])

    # ==========================================
    #            CINEMÁTICA INVERSA (IK)
    # ==========================================
    def iniciar_cinematica(self):
        try:
            self.ik = kinematics.RobotKinematics()
            print("📐 Cinemática OK")
        except Exception as e:
            print(f"❌ Error al cargar kinematics: {e}")

    def mover_brazo_a(self, x, y, z):
        """Mueve el brazo a la coordenada (x, y, z) usando IK"""
        if not hasattr(self, 'ik'): return False

        angulos = self.ik.inverse_kinematics(x, y, z)
        if angulos is None: return False
            
        # Parche de Inversión (Elbow Mirroring) - ¡Funciona Perfecto!
        codo_corregido = 270 - angulos['codo']

        # Usamos los ángulos puros sin reducciones
        servo.ctrl(0, angulos['base'])
        time.sleep(0.02)
        servo.ctrl(1, angulos['hombro'])
        time.sleep(0.02)
        servo.ctrl(2, codo_corregido)
        time.sleep(0.1)
        return True

    # ==========================================
    #            EMOCIONES & ESTADO
    # ==========================================
    def emocion_pensando(self): 
        if self.luces: self.luces.breath(0, 0, 150)
        self.escribir_oled(2, "Estado: PENSANDO")

    def emocion_peligro(self): 
        if self.luces: self.luces.police()
        self.escribir_oled(2, "Estado: !ALERTA!")

    def emocion_feliz(self): 
        if self.luces: 
            self.luces.pause()
            self.luces.setColor(0, 255, 0)
        self.escribir_oled(2, "Estado: FELIZ :)")

    def emocion_neutra(self): 
        if self.luces: 
            self.luces.pause()
            self.luces.setColor(50, 50, 50)
        self.escribir_oled(2, "Estado: LISTO")

    def apagar_luces(self): 
        if self.luces: 
            self.luces.pause()
            self.luces.setColor(0,0,0)

    # ==========================================
    #            MACROS FÍSICAS (IA)
    # ==========================================
    def avanzar(self, v=50, t=0): 
        self.escribir_oled(3, "Accion: AVANZAR")
        move.move(v, 'forward', 'no'); self._wait(t)
        
    def retroceder(self, v=50, t=0): 
        self.escribir_oled(3, "Accion: RETRO")
        move.move(v, 'backward', 'no'); self._wait(t)
        
    def girar_izquierda(self, v=50, t=0): 
        self.escribir_oled(3, "Accion: GIRAR IZQ")
        move.move(v, 'no', 'left'); self._wait(t)
        
    def girar_derecha(self, v=50, t=0): 
        self.escribir_oled(3, "Accion: GIRAR DER")
        move.move(v, 'no', 'right'); self._wait(t)
        
    def parar(self): move.motorStop()
    
    def _wait(self, t):
        if t > 0: time.sleep(t); self.parar()

    # --- CORRECCIÓN BUG-003: Eliminamos las funciones viejas y duplicadas ---
    def pinza_abrir(self): 
        self.escribir_oled(3, "Accion: ABRIR")
        self.angulos['garra'] = 130 # Ángulo abierto
        servo.ctrl(self.canales['garra'], self.angulos['garra'])
        
    def pinza_cerrar(self): 
        self.escribir_oled(3, "Accion: CERRAR")
        self.angulos['garra'] = 50 # Ángulo cerrado
        servo.ctrl(self.canales['garra'], self.angulos['garra'])
        
    def saludo(self):
        print("👋 IA ejecutando saludo físico...")
        self.emocion_feliz()
        self.escribir_oled(3, "Accion: SALUDAR")
        
        # Dialecto nuevo por canales
        servo.ctrl(self.canales['brazo'], 130)
        time.sleep(0.3)
        for _ in range(3):
            servo.ctrl(self.canales['base'], 120)
            time.sleep(0.2)
            servo.ctrl(self.canales['base'], 60)
            time.sleep(0.2)
            
        servo.ctrl(self.canales['base'], 90)
        servo.ctrl(self.canales['brazo'], 90)
        self.emocion_neutra()

    def apagar(self):
        print("📴 Apagando HW...")
        self.escribir_oled(1, "SISTEMA: APAGANDO")
        time.sleep(1)
        self.apagar_luces()
        servo.clean_all()
        move.destroy()
        if self.oled: self.oled.stop()