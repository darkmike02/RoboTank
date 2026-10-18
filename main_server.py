import os
import re 
import cv2           
import numpy as np    
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
from drivers.camera_stream import CameraStream
from drivers import move
import time
import google.generativeai as genai
import json
import ia_commands # <--- AÑADIR TU NUEVO DICCIONARIO

# --- CONFIGURACIÓN DE IA (GEMINI) ---
genai.configure(api_key=open(".env").read().split("=")[1].strip())
modelo_ia = genai.GenerativeModel('models/gemini-flash-latest')

# --- INICIALIZAR HARDWARE DEL ROBOT ---
try:
    from drivers.robot_controller import Robot
    print("🤖 Controlador del robot cargado correctamente.")
    bot = Robot()
except Exception as e:
    print(f"⚠️ Aviso: Fallo al cargar robot_controller ({e}).")
    bot = None

# --- CONFIGURACIÓN DEL SERVIDOR ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'robotank_v9_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- MEMORIA GLOBAL ---
ultimo_frame_camara = None
MODO_OPERACION = "manual"
MODO_RASTREO_ROJO = False
estado_anterior = {
    "speed": -1, "direction": "none", "turn": "none",
    "cam_x": 0.0, "cam_y": 0.0,
    "brazo": "stop", "garra": "stop", "muneca": "stop"
}

# --- RUTA DE VIDEO STREAMING ---
def generate_frames():
    global ultimo_frame_camara
    camera = CameraStream() # Iniciamos de forma segura dentro del hilo
    while True:
        frame = camera.get_frame()
        if frame:
            ultimo_frame_camara = frame # Guardamos una copia para la IA
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- RECEPTORES DE WEBSOCKETS ---
@socketio.on('connect')
def handle_connect():
    print("🟢 Cliente Web Conectado al WebSocket.")

@socketio.on('cambiar_modo')
def handle_cambio_modo(data):
    global MODO_OPERACION
    nuevo_modo = data.get('modo', 'manual')
    MODO_OPERACION = nuevo_modo
    print(f"\n🔄 CAMBIO DE MANDO: El robot ahora está en modo {MODO_OPERACION.upper()}\n")
    
    if MODO_OPERACION == "auto":
        if bot: bot.parar()
        if bot: bot.escribir_oled(1, "MODO: AUTONOMO")
        if bot: bot.emocion_pensando()
    else:
        if bot: bot.parar()
        if bot: bot.escribir_oled(1, "MODO: MANUAL")
        if bot: bot.emocion_neutra()
@socketio.on('comando_voz')
def handle_comando_voz(data):
    comando_usuario = data.get('texto', '')
    print(f"\n🗣️ PILOTO: {comando_usuario}")
    
    if bot:
        bot.escribir_oled(2, "Escuchando...")
        bot.emocion_pensando()
        
    try:
        elementos_prompt = []
        prompt_sistema = f"""
        Eres 'GeminiBot', un robot explorador.
        El piloto te dice: "{comando_usuario}"
        
        REGLAS VITALES:
        1. Responde de forma natural y amigable (máximo 2 oraciones). Esta será tu voz.
        2. Si la orden implica un movimiento o un saludo, DEBES AÑADIR AL FINAL de tu respuesta una etiqueta oculta de acción.
        
        ETIQUETAS PERMITIDAS:
        - [ACCION: SALUDAR] 
        - [ACCION: RASTREAR_ROJO] (Usa esto si el piloto pide seguir una pelota, juguete o color rojo)
        - [ACCION: DETENER_RASTREO] (Usa esto si el piloto pide que dejes de seguir o de mirar algo)
        - [ACCION: NINGUNA] (Si solo es charla normal)
        """
        elementos_prompt.append(prompt_sistema)
        
        if ultimo_frame_camara:
            temp_path = "vision_chat.jpg"
            with open(temp_path, "wb") as f:
                f.write(ultimo_frame_camara)
            archivo_gemini = genai.upload_file(path=temp_path, display_name="Vista Chat")
            elementos_prompt.append(archivo_gemini)
            
        print("🧠 Pensando respuesta vocal y motriz...")
        respuesta = modelo_ia.generate_content(elementos_prompt)
        texto_crudo = respuesta.text.strip()
        
        # --- FILTRO SEPARADOR DE VOZ Y ACCIÓN ---
        accion_detectada = "NINGUNA"
        texto_hablado = texto_crudo
        
        # Buscamos si la IA incluyó un comando oculto como [ACCION: SALUDAR]
        match = re.search(r'\[ACCION:\s*([A-Z_]+)\]', texto_crudo)
        if match:
            accion_detectada = match.group(1)
            # Borramos la etiqueta del texto para que el robot NO la lea en voz alta
            texto_hablado = texto_crudo.replace(match.group(0), "").strip()
            
        print(f"🗣️ ROBOT DICE: {texto_hablado}")
        print(f"⚙️ ACCION IA : {accion_detectada}\n")
        
        if bot:
            bot.escribir_oled(2, "Hablando...")
            bot.emocion_feliz()
            
        # 1. Enviar solo el texto limpio a la web para que lo lea
        socketio.emit('respuesta_voz', {'texto': texto_hablado})
        
        # 2. Ejecutar la acción física o alterar el estado cognitivo
        global MODO_RASTREO_ROJO
        if accion_detectada == "RASTREAR_ROJO":
            MODO_RASTREO_ROJO = True
            print("👁️ [SISTEMA VISUAL]: Activando seguimiento de objeto rojo.")
        elif accion_detectada == "DETENER_RASTREO":
            MODO_RASTREO_ROJO = False
            print("👁️ [SISTEMA VISUAL]: Desactivando seguimiento visual.")
        elif accion_detectada != "NINGUNA":
            ia_commands.ejecutar(accion_detectada, bot)
            
    except Exception as e:
        print(f"❌ Error en chat de voz: {e}")
        socketio.emit('respuesta_voz', {'texto': "Mis circuitos de comunicación tienen interferencia, Capitán."})
        if bot: bot.emocion_peligro()
        
    finally:
        if bot: time.sleep(2); bot.emocion_neutra(); bot.escribir_oled(2, "Esperando...")

@socketio.on('joystick_data')
def handle_joystick(data):
    global estado_anterior, MODO_OPERACION
    
    if MODO_OPERACION == "auto":
        return
    
    x = data.get('eje_x', 0.0)
    y = -data.get('eje_y', 0.0)
    
    if abs(x) < 0.1: x = 0.0
    if abs(y) < 0.1: y = 0.0
    speed = int(max(abs(x), abs(y)) * 100)

    direction = 'forward' if y > 0 else ('backward' if y < 0 else 'no')
    turn = 'left' if x > 0 else ('right' if x < 0 else 'no')

    if (speed != estado_anterior["speed"] or direction != estado_anterior["direction"] or turn != estado_anterior["turn"]):
        try:
            if speed == 0:
                move.motorStop()
            else:
                move.move(speed, direction, turn)
            estado_anterior["speed"] = speed
            estado_anterior["direction"] = direction
            estado_anterior["turn"] = turn
        except Exception as e:
            pass

    cam_x = data.get('cam_x', 0.0)
    cam_y = data.get('cam_y', 0.0)
    if abs(cam_x) > 0.1 or abs(cam_y) > 0.1:
        if bot: bot.mover_camara(cam_x, cam_y)

    estado_brazo = "subiendo" if data.get('brazo_subir') else ("bajando" if data.get('brazo_bajar') else "stop")
    if estado_brazo != estado_anterior.get("brazo"):
        estado_anterior["brazo"] = estado_brazo
    if estado_brazo == "subiendo":
        if bot: bot.brazo_subir()
    elif estado_brazo == "bajando":
        if bot: bot.brazo_bajar()

    estado_garra = "cerrando" if data.get('garra_cerrar') else ("abriendo" if data.get('garra_abrir') else "stop")
    if estado_garra != estado_anterior.get("garra"):
        estado_anterior["garra"] = estado_garra
    if estado_garra == "abriendo":
        if bot: bot.garra_abrir()
    elif estado_garra == "cerrando":
        if bot: bot.garra_cerrar()

    estado_muneca = "subiendo" if data.get('muneca_subir') else ("bajando" if data.get('muneca_bajar') else "stop")
    if estado_muneca != estado_anterior.get("muneca"):
        estado_anterior["muneca"] = estado_muneca
    if estado_muneca == "subiendo":
        if bot: bot.muneca_subir()
    elif estado_muneca == "bajando":
        if bot: bot.muneca_bajar()

# --- CEREBELO: REFLEJOS DE VISIÓN RÁPIDA (OPENCV) ---
def cv_tracking_loop():
    global ultimo_frame_camara, MODO_RASTREO_ROJO
    while True:
        if MODO_RASTREO_ROJO and ultimo_frame_camara and bot:
            try:
                # 1. Convertir la foto de bytes a imagen matemática
                nparr = np.frombuffer(ultimo_frame_camara, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # 2. Buscar el color ROJO
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                mask1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
                mask = mask1 + mask2
                
                # 3. Encontrar el contorno más grande (la pelota)
                contornos, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                if contornos:
                    c = max(contornos, key=cv2.contourArea)
                    if cv2.contourArea(c) > 500: # Si es lo bastante grande
                        M = cv2.moments(c)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            
                            # 4. Calcular el error desde el centro (Resolución 640x480)
                            err_x = cx - 320
                            err_y = cy - 240
                            
                            # 5. Mover los motores si se sale del centro (Zona muerta de 40px)
                            cam_x = 0.0
                            cam_y = 0.0
                            if err_x > 40: cam_x = -1.0   # Mover derecha
                            elif err_x < -40: cam_x = 1.0 # Mover izquierda
                            
                            if err_y > 40: cam_y = -1.0   # Mover abajo
                            elif err_y < -40: cam_y = 1.0 # Mover arriba
                            
                            if cam_x != 0 or cam_y != 0:
                                bot.mover_camara(cam_x, cam_y)
                                
            except Exception as e:
                pass # Ignoramos errores visuales menores para no saturar la consola
                
        socketio.sleep(0.05) # 20 FPS (Súper rápido)

# --- TAREA DE TELEMETRÍA Y CEREBRO IA ---
def background_telemetry():
    global ultimo_frame_camara
    zona_actual = "desconocida" 
    ultimo_pensamiento = 0 
    
    while True:
        if bot:
            dist = bot.medir_distancia()
            dist_val = round(dist, 1)
            imu_data = bot.leer_imu() 
            
            socketio.emit('telemetria', {'distancia': dist_val, 'imu': imu_data})
            
            # 🧠 MODO IA 
            if MODO_OPERACION == "auto":
                tiempo_actual = time.time()
                
                if tiempo_actual - ultimo_pensamiento > 60.0:
                    ultimo_pensamiento = tiempo_actual
                    
                    bot.escribir_oled(3, "IA: Observando...")
                    bot.emocion_pensando() 
                    
                    try:
                        if ultimo_frame_camara:
                            temp_path = "vision_ia.jpg"
                            with open(temp_path, "wb") as f:
                                f.write(ultimo_frame_camara)
                            
                            archivo_gemini = genai.upload_file(path=temp_path, display_name="Vista Robot")
                            
                            prompt_sistema = f"""
                            Eres la consciencia del robot 'GeminiBot'. 
                            Tu radar frontal detecta un objeto a {dist_val} cm de distancia.
                            Mira la imagen enviada.
                            
                            Responde ÚNICAMENTE con dos líneas usando estos comandos:
                            ANALISIS: [Describe lo que ves en máximo 3 palabras]
                            LUCES: [ROJO si está muy cerca/peligro, AMARILLO si es precaución, VERDE si está libre]
                            """
                            
                            print("🧠 Consultando a Gemini...")
                            respuesta = modelo_ia.generate_content([prompt_sistema, archivo_gemini])
                            texto = respuesta.text
                            print(f"\n⚡ RESPUESTA GEMINI:\n{texto}\n")
                            
                            comandos = texto.split('\n')
                            for linea in comandos:
                                linea = linea.strip().upper()
                                if "ANALISIS:" in linea:
                                    pensamiento = linea.replace("ANALISIS:", "").strip()
                                    bot.escribir_oled(3, pensamiento)
                                elif "LUCES:" in linea:
                                    bot.luces.pause()
                                    if "ROJO" in linea: bot.luces.setColor(255, 0, 0)
                                    elif "VERDE" in linea: bot.luces.setColor(0, 255, 0)
                                    elif "AMARILLO" in linea: bot.luces.setColor(255, 255, 0)
                                    else: bot.luces.setColor(0, 0, 255)
                                    
                    except Exception as e:
                        print(f"❌ Error IA: {e}")
                        bot.escribir_oled(3, "Error IA")
            
            # 🎮 MODO MANUAL 
            else:
                bot.escribir_oled(4, f"RADAR: {dist_val} cm")
                if bot.luces:
                    if dist_val < 5.0: nueva_zona = "rojo"
                    elif dist_val <= 10.0: nueva_zona = "amarillo"
                    else: nueva_zona = "verde"
                        
                    if nueva_zona != zona_actual:
                        bot.luces.pause() 
                        if nueva_zona == "rojo": bot.luces.setColor(255, 0, 0)     
                        elif nueva_zona == "amarillo": bot.luces.setColor(255, 255, 0)   
                        elif nueva_zona == "verde": bot.luces.setColor(0, 255, 0)     
                        zona_actual = nueva_zona 
        
        socketio.sleep(1.0)

if __name__ == '__main__':
    print("🚀 Servidor RoboTank V9 Iniciado (Visión + Joystick + Sensores).")
    socketio.start_background_task(background_telemetry)
    socketio.start_background_task(cv_tracking_loop)
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)