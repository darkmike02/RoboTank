import time
print("⏳ Intentando importar el módulo drivers...")

try:
    # Si esta línea no falla, la arquitectura de carpetas es un ÉXITO
    from drivers.robot_controller import Robot
    print("✅ ¡ÉXITO! Se importó drivers.robot_controller correctamente.")
    
    print("🤖 Instanciando la clase Robot (Hardware Check)...")
    bot = Robot()
    print("✅ Hardware inicializado sin errores.")
    
    # Pequeña prueba de vida (si es seguro)
    # bot.mover_brazo_a(10, 0, 20) 
    
except Exception as e:
    print(f"\n❌ ERROR CRÍTICO DE INTEGRACIÓN:\n{e}")