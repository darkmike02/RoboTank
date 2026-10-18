# 🤖 Proyecto RoboTank - Bitácora de Ingeniería y Evolución (V9 -> V10)

## 🎯 Visión del Sistema (Arquitectura VLA)
Evolucionar la plataforma RoboTank V9 hacia un sistema autónomo cognitivo dividido en 3 capas:
1. **Capa Cognitiva (Cerebro):** Toma de decisiones de alto nivel, comandos conversacionales, sugerencias proactivas (ej. alerta de clima/paraguas) y planificación de misiones.
2. **Capa de Percepción y Navegación:** Visión artificial (OpenCV), extracción de contornos/vectores para dibujo y mapeo espacial.
3. **Capa de Control Físico (Músculos):** Cinemática inversa (`robot_controller.py`), locomoción diferencial y manipulación física con brazo robótico.

---

## 📋 Registro de Sesiones (Juntas Creativas)

### Sesión 01 - Inicialización de Control de Versiones y Arquitectura
* **Estado:** Completado ✅
* **Logros:**
  * Configuración de llaves SSH en Raspberry Pi y enlace con repositorio privado en GitHub (`darkmike02/RoboTank`).
  * Primer commit base (`af97d0f`) aislando el código funcional de `robot_v9_system`.
  * Limpieza de archivos multimedia temporales (`.jpg`, `.mjpg`) mediante `.gitignore`.
  * Definición de metodología de trabajo por bloques cerrados y protocolos de prueba.

### 🏛️ Regla de Arquitectura: Separación de Modos (Manual vs. Autónomo)
* **Consola Manual (`main_server.py`):** Se conserva íntegra para teleoperación por joystick, pruebas de entorno y control directo.
* **Núcleo Autónomo (`mission_loop.py` + `vision_engine.py` + `navigation_engine.py`):** Línea principal de desarrollo V10. Aquí se integrará la toma de decisiones cognitiva, secuencias *Pick & Place* (pelota al bote), modo dibujo vectorial y agentes proactivos (clima/entorno).
