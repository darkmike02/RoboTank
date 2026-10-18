# ==========================================
# 🧠 DICCIONARIO DE HABILIDADES FÍSICAS (IA)
# ==========================================

def ejecutar(accion, bot):
    if not bot: return
    
    accion = accion.upper().strip()

    habilidades = {
        "SALUDAR": bot.saludo,
        "AVANZAR": bot.avanzar,
        "RETROCEDER": bot.retroceder,
        "IZQUIERDA": bot.girar_izquierda,
        "DERECHA": bot.girar_derecha,
        "PARAR": bot.parar,
        "PINZA_ABRIR": bot.pinza_abrir,
        "PINZA_CERRAR": bot.pinza_cerrar
    }

    if accion in habilidades:
        print(f"⚙️ [SISTEMA NERVIOSO]: Ejecutando acción -> {accion}")
        habilidades[accion]() 
    elif accion not in ["RASTREAR_ROJO", "DETENER_RASTREO", "NINGUNA"]:
        print(f"⚠️ [SISTEMA NERVIOSO]: La acción '{accion}' no existe.")