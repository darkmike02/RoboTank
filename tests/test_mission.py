import time
from drivers.robot_controller import Robot
from drivers.camera_stream import CameraStream
from vision_engine import VisionEngine
from navigation_engine import NavigationEngine
from mission_loop import MissionLoop

print("🚀 Iniciando prueba del HITO 3: Autonomía Total (Modo Cazador)...")

try:
    print("Iniciando Módulos del Sistema...")
    bot = Robot()
    print("✅ Hardware Robot OK")
    
    camara = CameraStream()
    print("✅ Stream de Cámara Iniciado")
    
    vision = VisionEngine()
    print("✅ Motor de Visión OK")
    
    nav = NavigationEngine(bot)
    
    # Inyectamos todos los subsistemas en el Cerebro Central
    cerebro = MissionLoop(bot, vision, nav)
    print("✅ Cerebro Central (MissionLoop) Inyectado")
    
except Exception as e:
    print(f"❌ Error crítico en la inicialización: {e}")
    exit()

time.sleep(2)
print("\n✅ Sistemas Integrados. El RoboTank V9 es ahora AUTÓNOMO.")
print("Pon la pelota roja en el suelo. Presiona Ctrl+C para abortar.\n")

# Contador para no saturar la terminal
ciclos_sin_frame = 0

try:
    print("🟢 Entrando al bucle principal de ejecución...")
    while True:
        # 1. Intentar capturar la realidad
        frame_bytes = camara.get_frame()

        if frame_bytes is not None:
            ciclos_sin_frame = 0 # Reset de error
            
            if cerebro.estado == "COMPLETADO":
                print("🎉 MISIÓN EXITOSA. Fin del bucle.")
                break
                
            # 2. Ejecutar lógica del cerebro
            # He añadido este print para saber que el ciclo está girando
            # print(f"--- Ejecutando Ciclo: Estado actual {cerebro.estado} ---")
            cerebro.ejecutar_ciclo(frame_bytes)

        else:
            ciclos_sin_frame += 1
            if ciclos_sin_frame % 20 == 0: # Avisar cada 2 segundos aprox
                print("⚠️  Advertencia: Esperando frames de la cámara... (Buffer vacío)")

        time.sleep(0.1) # Refresco a 10 Hz

except KeyboardInterrupt:
    print("\n🛑 Sistemas detenidos por el piloto (Ctrl+C).")
except Exception as e:
    print(f"💥 Error inesperado en el bucle: {e}")
finally:
    print("Cerrando sistemas...")
    bot.parar()
    camara.stop()
    print("👋 Módulos apagados de forma segura.")