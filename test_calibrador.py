import sys
import os
import time

# Forzamos que el directorio actual sea visible para Python
directorio_actual = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directorio_actual)

try:
    # Intentamos la importación directa (funciona al ejecutar el script solo)
    import robot_controller
    from robot_controller import Robot 
    from drivers import servo
    print("✅ Módulos cargados correctamente.")
except ImportError:
    try:
        # Intento alternativo si robot_controller está dentro de un subpaquete
        from .robot_controller import Robot
        from .drivers import servo
    except Exception as e:
        print(f"❌ No se pudo encontrar robot_controller.py: {e}")
        print(f"Directorio actual: {os.getcwd()}")
        sys.exit(1)

def calibrador_pid_v2(bot):
    print("\n" + "="*45)
    print("🛠️  CALIBRADOR PID INTERACTIVO - V2.1")
    print("="*45)
    
    # 1. PRUEBA DE ARRANQUE (ZONA MUERTA)
    print("\n1. DETERMINAR PWM MÍNIMO")
    print("Buscando el punto donde las orugas vencen la fricción...")
    pwm_min = 40
    while pwm_min < 85:
        print(f"Probando PWM: {pwm_min}...", end="\r")
        bot.avanzar(v=pwm_min)
        time.sleep(0.7)
        bot.parar()
        
        opcion = input(f"\n¿Se movió el robot con PWM {pwm_min}? (s/n): ").lower()
        if opcion == 's': 
            break
        pwm_min += 5
    
    print(f"\n✅ PWM mínimo fijado en: {pwm_min}")
    
    # 2. BUCLE DE CONTROL PID
    kp, ki, kd = 2.0, 0.0, 0.0 
    distancia_objetivo = 28.0
    offset_brazo = 6.0
    error_previo = 0
    integral = 0
    
    print("\n" + "-"*45)
    print("🎮 MODO CONTROL ACTIVO (Objetivo: 28cm)")
    print("Comandos: 'P I D' (ej: 2.5 0.01 0.4) o 'exit'")
    print("-"*45)
    
    try:
        while True:
            # Medición del sensor (usando el controlador funcional)
            dist_lectura = bot.medir_distancia() 
            dist_actual = dist_lectura + offset_brazo
            error = dist_actual - distancia_objetivo

            if 2.0 < dist_lectura < 400.0:
                # Lógica PID
                integral = max(-15, min(15, integral + error)) # Anti-windup
                derivada = error - error_previo
                salida_pid = (kp * error) + (ki * integral) + (kd * derivada)
                
                # Control de motores
                if abs(error) < 1.0:
                    bot.parar()
                    pwm_final = 0
                else:
                    pwm_final = int(pwm_min + abs(salida_pid))
                    pwm_final = min(90, pwm_final)
                    
                    if error > 0: bot.avanzar(v=pwm_final)
                    else: bot.retroceder(v=pwm_final)

                print(f"\rDist: {dist_actual:.1f}cm | Err: {error:.1f} | PWM: {pwm_final} | Kp:{kp} Ki:{ki} Kd:{kd}    ", end="")
            
            # Interfaz de ajuste
            if abs(error) < 1.5:
                bot.parar()
                print("\n\n📍 ESTABILIZADO. Ingresa nuevos valores 'P I D':")
                linea = input(">> ")
                if linea.lower() == 'exit': break
                try:
                    if linea.strip():
                        kp, ki, kd = map(float, linea.split())
                        integral = 0
                        print("✅ Valores actualizados.")
                except ValueError:
                    print("❌ Error de formato. Usa: P I D")

            error_previo = error
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\n🛑 Finalizado.")
    finally:
        bot.parar()

if __name__ == "__main__":
    try:
        # Usamos la clase Robot que ya funciona en test_ik_fisico.py
        mi_robot = Robot() 
        calibrador_pid_v2(mi_robot)
    except Exception as e:
        print(f"\n❌ Error al iniciar el robot: {e}")