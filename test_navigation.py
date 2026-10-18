import time
# 👇 AQUÍ ESTÁ EL CAMBIO: Apuntamos a la carpeta drivers
from drivers.robot_controller import Robot 
from navigation_engine import NavigationEngine

print("🚀 Iniciando prueba del HITO 2: Navegación y Supervivencia...")

try:
    print("Encendiendo controladores de hardware...")
    bot = Robot()
    navegador = NavigationEngine(bot)
except Exception as e:
    print(f"❌ Error al iniciar los motores: {e}")
    exit()

print("\n⚠️ ATENCIÓN: El robot intentará avanzar.")
print("🖐️  PON TU MANO FRENTE AL RADAR PARA PROBAR LOS FRENOS.")
print("Presiona Ctrl+C en cualquier momento para abortar.\n")

# Cuenta regresiva de seguridad
for i in range(3, 0, -1):
    print(f"Arrancando en {i}...")
    time.sleep(1)

try:
    while True:
        # El robot evalúa su entorno y decide si avanza o frena a 10 FPS
        navegador.avanzar_seguro()
        time.sleep(0.1) 

except KeyboardInterrupt:
    print("\n🛑 Prueba detenida por el piloto.")
finally:
    navegador.detener()
    print("Sistemas motrices apagados y seguros.")