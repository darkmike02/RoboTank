import time
from robot_controller import Robot
from drivers import servo

def modo_enseñanza():
    print("🤖 Iniciando Sistema de Calibración Táctica...")
    
    # Instanciamos el controlador que sabemos que funciona perfectamente
    bot = Robot()
    
    # Ángulos iniciales seguros
    angulos = {
        'base': 90,
        'hombro': 90,
        'codo': 90,
        'tilt': 90,    # Conectado al Servo 5
        'garra': 130
    }
    
    # Mapeo de canales (asegurando el uso del servo 5 para el tilt)
    canales = {
        'base': bot.canales.get('base', 0),
        'hombro': bot.canales.get('hombro', 1),
        'codo': bot.canales.get('codo', 2),
        'tilt': 5,     # Forzando el servo 5 como indicó en su configuración de hardware
        'garra': bot.canales.get('garra', 6)
    }

    # Posición de inicio
    for joint, ang in angulos.items():
        servo.ctrl(canales[joint], ang)
        time.sleep(0.1)

    print("\n✅ Modo Teach Activado. Controles:")
    print("  [w/s] Mover Hombro")
    print("  [e/d] Mover Codo")
    print("  [r/f] Mover Tilt (Muñeca - Servo 5)")
    print("  [t/g] Abrir/Cerrar Garra")
    print("  [x]   SALIR y Guardar Coordenadas\n")

    while True:
        # Lectura en tiempo real del entorno
        dist_us = bot.medir_distancia()
        
        print(f"\r📡 US_Real: {dist_us:05.1f}cm | Hombro:{angulos['hombro']:03}° Codo:{angulos['codo']:03}° Tilt:{angulos['tilt']:03}° Garra:{angulos['garra']:03}°", end="")
        
        cmd = input("\nComando: ").strip().lower()

        if cmd == 'w': angulos['hombro'] = min(180, angulos['hombro'] + 5)
        elif cmd == 's': angulos['hombro'] = max(0, angulos['hombro'] - 5)
        
        elif cmd == 'e': angulos['codo'] = min(180, angulos['codo'] + 5)
        elif cmd == 'd': angulos['codo'] = max(0, angulos['codo'] - 5)
        
        elif cmd == 'r': angulos['tilt'] = min(180, angulos['tilt'] + 5)
        elif cmd == 'f': angulos['tilt'] = max(0, angulos['tilt'] - 5)
        
        elif cmd == 't': angulos['garra'] = max(50, angulos['garra'] - 10)  # Cierra
        elif cmd == 'g': angulos['garra'] = min(150, angulos['garra'] + 10) # Abre
        
        elif cmd == 'x':
            print("\n\n🎯 === REPORTE DE CALIBRACIÓN FINAL ===")
            print(f"Distancia Física del Sensor (US_Real): {dist_us:.1f} cm")
            print(f"Ángulos Perfectos -> Hombro: {angulos['hombro']}°, Codo: {angulos['codo']}°, Tilt: {angulos['tilt']}°")
            print("=======================================\n")
            break

        # Ejecutar el movimiento
        for joint, ang in angulos.items():
            servo.ctrl(canales[joint], ang)

if __name__ == "__main__":
    try:
        modo_enseñanza()
    except KeyboardInterrupt:
        print("\n🛑 Calibración abortada por el piloto.")