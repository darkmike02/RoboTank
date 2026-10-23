# 🧠 CONTEXTO TÉCNICO IA — PROYECTO ROBOTANK (V9 -> V10)

## 1. Reglas de Colaboración (Peer Review)
* **Postura:** Crítica, analítica, sin complacencia. Cuestionar ideas inviables por hardware/matemática y debatir con datos.
* **Flujo de Trabajo:** Desarrollo en Raspberry Pi conectada a GitHub (`darkmike02/RoboTank`). Pruebas físicas ejecutadas en sesiones aisladas; este contexto es la fuente de verdad.
* **Arquitectura Dual:**
  * `main_server.py`: Consola Web Manual (Flask/SocketIO + Joystick + Voz básica). Se mantiene intacta para teleoperación.
  * `run_autonomous.py`: Lanzador del núcleo autónomo (`MissionLoop` + `VisionEngine` + `Robot`).

## 2. Constantes Físicas y Hardware Calibrado
* **Servos PCA9685 (`drivers/robot_controller.py`):**
  * Canal `0`: `base` (Pan cámara/brazo, 90° centro, [20°-160°])
  * Canal `1`: `brazo` (Hombro, `OFFSET_SHOULDER = 50`)
  * Canal `2`: `muneca` (Codo, `OFFSET_ELBOW = 135`, inversión en controlador: `270 - angulo`)
  * Canal `3`: `garra` (Abierta = `130°`, Cerrada = `50°`)
  * Canal `5`: `cam_tilt` (Inclinación cámara, [15°-110°])
* **Dimensiones IK (`drivers/config_robot.py` y `mission_loop.py`):**
  * `L0_SHOULDER_HEIGHT = 20.0 cm`, `L1_HUMERUS = 13.0 cm`, `L2_FOREARM = 13.0 cm`
  * `H_EJE = 19.0 cm`, `OFFSET_BRAZO = 10 cm`, `Z_GRAB = 10.5 cm`, `TARGET_CX = 147`, `TARGET_CY = 120`
  * PID Aproximación: `Kp = 2.5`, `Ki = 0.01`, `Kd = 0.5`

## 3. Hallazgos Abiertos y Deuda Técnica Activa (Para Sesión 03)
1. **Inversión de Umbrales P1/P2 en `mission_loop.py`:** Actualmente `distancia_parada_p1 = 18` y `distancia_parada_final = 22.0`. Provoca salto inmediato de `ACERCANDO_P2`. Pendiente test físico para fijar P1 (~28 cm) y P2 (~18-22 cm).
2. **Desincronización de `self.angulos` en IK:** `mover_brazo_a(x,y,z)` mueve canales 0, 1 y 2 sin actualizar `self.angulos` en `robot_controller.py`.
3. **Hoja de Ruta V10:**
   * Optimizar Pick & Place completo (agarrar objeto -> buscar contenedor -> depositar).
   * Desarrollar `navigation_engine.py` como módulo real de evasión/navegación.
   * Implementar "Bucle de Curiosidad Local" estilo WALL-E (OpenCV ligero: movimiento/rostros) antes de invocar a Gemini.
