import time
from drivers.robot_controller import Robot

print("🦾 Iniciando Prueba Aislada de Cinemática (HITO 4)...")

try:
    print("Iniciando controladores de hardware...")
    bot = Robot()
    bot.emocion_pensando()
except Exception as e:
    print(f"❌ Error al iniciar el brazo: {e}")
    exit()

print("\n⚠️ ATENCIÓN: El brazo iniciará su secuencia en 3 segundos.")
print("Coloca la pelota (o un objeto de prueba) en el pedestal a ~15 cm de distancia.")
for i in range(3, 0, -1):
    print(f"Iniciando en {i}...")
    time.sleep(1)

try:
    print("\n1️⃣ Preparando herramienta (Abriendo pinza)...")
    bot.pinza_abrir()
    time.sleep(1.5)

    print("2️⃣ Bajando a coordenada de captura (X:15, Y:0, Z:5)...")
    # Utilizamos las coordenadas de la prueba "Grúa"
    exito_ik = bot.mover_brazo_a(15, 0, 0)
    time.sleep(2) # Pausa para que observes la precisión

    if exito_ik:
        print("3️⃣ Ejecutando agarre (Cerrando pinza)...")
        bot.pinza_cerrar()
        time.sleep(1.5)

        print("4️⃣ Levantando carga a posición de transporte (X:10, Y:0, Z:20)...")
        bot.mover_brazo_a(10, 0, 20)
        time.sleep(2)
        
        bot.emocion_feliz()
        print("\n🎉 SECUENCIA DE CAPTURA COMPLETADA.")
    else:
        bot.emocion_peligro()
        print("\n❌ Error: La Cinemática Inversa calculó que la coordenada es inalcanzable.")

except KeyboardInterrupt:
    print("\n🛑 Prueba abortada por el piloto.")
finally:
    print("Sistemas en reposo.")