import time
import drivers.ultra as ultra 

class NavigationEngine:
    def __init__(self, bot):
        print("🧭 [NAVIGATION ENGINE]: Inicializando Reflejos de Supervivencia...")
        self.bot = bot
        self.distancia_limite = 20.0 # Frenar a los 20 cm del objetivo/obstáculo

    def avanzar_seguro(self):
        """Avanza, pero frena instantáneamente si detecta una colisión inminente"""
        try:
            # Usamos el nombre exacto de la función en tu archivo ultra.py
            distancia = ultra.checkdist()
        except Exception as e:
            print(f"⚠️ Error de hardware en el radar: {e}")
            self.bot.parar()
            return False

        # Si tu script devuelve -1, significa que no rebotó nada (camino libre)
        if distancia == -1 or distancia > 500:
            self.bot.avanzar(v=100) # 🔥 Avance con alto torque
            print("🟢 Camino libre (Sin obstáculos a la vista) -> Orugas adelante.")
            return True 

        # Si la distancia es mayor a 20cm, avanzamos
        if distancia > self.distancia_limite:
            self.bot.avanzar(v=100) # 🔥 Avance con alto torque
            print(f"🟢 Camino libre ({distancia:.1f} cm) -> Orugas adelante.")
            return True
        else:
            # Frenazo de emergencia si está muy cerca
            self.bot.parar()
            print(f"🛑 ¡OBSTÁCULO! ({distancia:.1f} cm) -> Frenos de emergencia activados.")
            return False
            
    def detener(self):
        self.bot.parar()