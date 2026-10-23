import time
from drivers.robot_controller import Robot
from drivers.camera_stream import CameraStream
from vision_engine import VisionEngine
from navigation_engine import NavigationEngine
from mission_loop import MissionLoop

print("🚀 [ROBOTANK V10] Iniciando Ejecutor Autónomo...")

try:
    bot = Robot()
    camara = CameraStream()
    vision = VisionEngine()
    nav = NavigationEngine(bot)
    cerebro = MissionLoop(bot, vision, nav)
except Exception as e:
    print(f"❌ Error crítico en inicialización: {e}")
    exit(1)

# Sincronizar memoria de ángulos en Robot para evitar latigazos tras IK
time.sleep(2)
print("\n✅ Sistema Autónomo Listo. Iniciando ciclo a 10 Hz (Ctrl+C para abortar)...\n")

ciclos_sin_frame = 0
t_inicio = time.time()
historial_estados = [cerebro.estado]

try:
    while True:
        frame_bytes = camara.get_frame()
        if frame_bytes is not None:
            ciclos_sin_frame = 0
            estado_prev = cerebro.estado
            cerebro.ejecutar_ciclo(frame_bytes)
            
            if cerebro.estado != estado_prev:
                historial_estados.append(f"{cerebro.estado} ({time.time()-t_inicio:.1f}s)")
                
            if cerebro.estado == "COMPLETADO":
                print("🎉 MISIÓN COMPLETADA CON ÉXITO.")
                break
        else:
            ciclos_sin_frame += 1
            if ciclos_sin_frame % 20 == 0:
                print("⚠️ Advertencia: Buffer de cámara vacío...")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 Abortado manualmente por el operador.")
except Exception as e:
    print(f"💥 Excepción en tiempo de ejecución: {e}")
finally:
    duracion = time.time() - t_inicio
    print("\n" + "="*50)
    print("📊 REPORTE DE TELEMETRÍA PARA IA ARQUITECTA:")
    print(f"⏱️ Duración total: {duracion:.1f} s")
    print(f"🔄 Secuencia de estados: {' -> '.join(historial_estados)}")
    print(f"📐 Último Estado/Subfase: {cerebro.estado} / {cerebro.fase_guia}")
    print(f"🎯 Ángulos finales: Radar={cerebro.angulo_radar}° Tilt={cerebro.angulo_tilt}°")
    print(f"📏 Última solución IK: X={cerebro._grab_x:.1f}, Y={cerebro._grab_y:.1f}, Z={cerebro._grab_z:.1f}")
    print("="*50 + "\n")
    bot.parar()
    camara.stop()
