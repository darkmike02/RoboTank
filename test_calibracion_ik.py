import time
import json
from drivers.robot_controller import Robot

print("📐 Iniciando Protocolo de Calibración de Cinemática Inversa (Mapeo de Error)...")

try:
    bot = Robot()
    bot.emocion_pensando()
except Exception as e:
    print(f"❌ Error crítico: {e}")
    exit()

# 10 Puntos de prueba variando Altura (Z), Extensión (X) y Giro (Y)
puntos_teoricos = [
    {"id": 1, "coord": (15, 0, 5),  "desc": "Alcance medio, centrado, altura baja"},
    {"id": 2, "coord": (20, 0, 10), "desc": "Alcance largo, centrado, altura media"},
    {"id": 3, "coord": (10, 0, 0),  "desc": "Alcance corto, centrado, a ras de suelo"},
    {"id": 4, "coord": (25, 0, 15), "desc": "Alcance MAX, centrado, altura alta"},
    {"id": 5, "coord": (15, 10, 5), "desc": "Alcance medio, derecha, altura baja"},
    {"id": 6, "coord": (15, -10, 5),"desc": "Alcance medio, izquierda, altura baja"},
    {"id": 7, "coord": (12, 0, 15), "desc": "Alcance corto, centrado, altura alta (Grúa)"},
    {"id": 8, "coord": (18, 5, 0),  "desc": "Alcance medio-largo, ligera der, suelo"},
    {"id": 9, "coord": (18, -5, 0), "desc": "Alcance medio-largo, ligera izq, suelo"},
    {"id": 10, "coord": (20, 0, 20),"desc": "Alcance largo, centrado, posición transporte"}
]

resultados = []

print("\n⚠️ INSTRUCCIONES:")
print("- El brazo se moverá a 10 puntos diferentes.")
print("- En cada punto, usa una regla para medir (en centímetros) la posición REAL de la pinza.")
print("- Eje X: Distancia hacia adelante desde el centro de giro del robot.")
print("- Eje Y: Desviación lateral (positivo = derecha, negativo = izquierda).")
print("- Eje Z: Altura desde el suelo hasta la punta de la pinza.")
print("- Si un punto se ve peligroso, escribe 's' para saltarlo.\n")
input("Presiona ENTER para iniciar la secuencia de calibración...")

for pt in puntos_teoricos:
    x_t, y_t, z_t = pt["coord"]
    print(f"\n==================================================")
    print(f"📍 PUNTO {pt['id']}/10: {pt['desc']}")
    print(f"🎯 OBJETIVO TEÓRICO -> X: {x_t}, Y: {y_t}, Z: {z_t}")
    
    # Mover el brazo
    exito = bot.mover_brazo_a(x_t, y_t, z_t)
    time.sleep(1.5) # Dejar que se estabilice
    
    if not exito:
        print("❌ El modelo IK rechazó esta coordenada. Saltando...")
        continue
        
    print("\n📏 Mide la posición real de la pinza (o escribe 's' para saltar):")
    try:
        medida_x = input(f"   X Real (esperado {x_t}): ")
        if medida_x.lower() == 's': continue
        
        medida_y = input(f"   Y Real (esperado {y_t}): ")
        medida_z = input(f"   Z Real (esperado {z_t}): ")
        
        resultados.append({
            "punto_id": pt["id"],
            "teorico": {"x": x_t, "y": y_t, "z": z_t},
            "real": {
                "x": float(medida_x), 
                "y": float(medida_y), 
                "z": float(medida_z)
            },
            "error": {
                "dx": round(float(medida_x) - x_t, 2),
                "dy": round(float(medida_y) - y_t, 2),
                "dz": round(float(medida_z) - z_t, 2)
            }
        })
    except ValueError:
        print("⚠️ Valor inválido. Saltando registro de este punto.")

# Regresar a posición segura
print("\n🔄 Secuencia terminada. Guardando brazo en posición segura...")
bot.mover_brazo_a(10, 0, 20)
time.sleep(1)

# Imprimir el reporte final para el LLM
print("\n📋 ================= REPORTE DE CALIBRACIÓN ================= 📋")
print("Copia y pega este bloque JSON en el chat para que lo analice:")
print(json.dumps(resultados, indent=2))
print("===================================================================")