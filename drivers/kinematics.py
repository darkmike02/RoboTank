import math
from . import config_robot as cfg

class RobotKinematics:
    def __init__(self):
        print("📐 Kinematics V9.1 (Standard Geometric Mode)...")

    def inverse_kinematics(self, x, y, z):
        """
        Calcula ángulos (Base, Hombro, Codo) para coordenada (x,y,z).
        Retorna diccionario con pulsos para servos o None si es imposible.
        """
        
        # --- 1. PREPARACIÓN DEL ESCENARIO ---
        # Altura relativa desde el hombro
        z_local = z - cfg.L0_SHOULDER_HEIGHT
        
        # Distancia horizontal al objetivo (proyección en el suelo)
        r_reach = math.sqrt(x**2 + y**2)
        
        # Distancia absoluta desde el hombro al objetivo (Hipotenusa 3D)
        dist_total = math.sqrt(r_reach**2 + z_local**2)

        # --- 2. CHEQUEO DE SEGURIDAD (¿Llego?) ---
        longitud_brazo = cfg.L1_HUMERUS + cfg.L2_FOREARM
        if dist_total > longitud_brazo:
            print(f"⚠️ OBJETIVO IMPOSIBLE: {dist_total:.1f}cm (Máx: {longitud_brazo}cm)")
            return None
            
        # Evitar división por cero si el objetivo es el mismo hombro
        if dist_total < 1.0:
            print("⚠️ Objetivo demasiado cerca del cuerpo.")
            return None

        # --- 3. CÁLCULO DE LA BASE (Theta 0) ---
        # atan2 maneja los cuadrantes automáticamente.
        # Asumimos que Y+ es Izquierda y Y- es Derecha (o viceversa según tu cableado)
        angle_base = math.degrees(math.atan2(y, x))
        # Ajuste: Si servo 90 mira al frente.
        servo_base = 90 + angle_base


        # --- 4. RESOLUCIÓN DEL TRIÁNGULO (Ley de Cosenos) ---
        # Tenemos un triángulo con lados: L1 (Húmero), L2 (Antebrazo), D (Distancia)
        
        try:
            # ÁNGULO DEL CODO (Gamma) - Opuesto al lado D
            # c^2 = a^2 + b^2 - 2ab*cos(gamma)
            numerador_codo = (cfg.L1_HUMERUS**2 + cfg.L2_FOREARM**2 - dist_total**2)
            denominador_codo = (2 * cfg.L1_HUMERUS * cfg.L2_FOREARM)
            cos_codo = numerador_codo / denominador_codo
            
            # Clamp para errores de punto flotante (ej: 1.0000001)
            cos_codo = max(-1.0, min(1.0, cos_codo))
            
            # Ángulo interno del codo (en radianes)
            gamma_rad = math.acos(cos_codo)
            # El servo no usa el ángulo interno, sino la deflexión desde "recto" (180 - interno)
            elbow_deflection_deg = 180 - math.degrees(gamma_rad)


            # ÁNGULO DEL HOMBRO (Alpha) - Parte interna del triángulo
            # L2^2 = L1^2 + D^2 - 2*L1*D*cos(alpha)
            numerador_hombro = (cfg.L1_HUMERUS**2 + dist_total**2 - cfg.L2_FOREARM**2)
            denominador_hombro = (2 * cfg.L1_HUMERUS * dist_total)
            cos_hombro = numerador_hombro / denominador_hombro
            cos_hombro = max(-1.0, min(1.0, cos_hombro))
            
            alpha_rad = math.acos(cos_hombro)
            
            # Ángulo de elevación del objetivo (Phi)
            phi_rad = math.atan2(z_local, r_reach)
            
            # HOMBRO TOTAL = Elevación (Phi) + Ángulo interno (Alpha)
            # (Usamos + Alpha para configuración "Codo Arriba", que es lo normal en tanks)
            shoulder_total_deg = math.degrees(phi_rad + alpha_rad)

        except ValueError:
            print("⚠️ Error matemático en cálculo de ángulos.")
            return None

        # --- 5. MAPEO A MOTORES ---
        
        # HOMBRO:
        # Offset 50 es horizontal. +Grados sube.
        servo_shoulder = cfg.OFFSET_SHOULDER + shoulder_total_deg
        
        # CODO:
        # Offset 36 es recto. 
        # IMPORTANTE: ¿Tu servo suma o resta al doblar?
        # Asumimos que SUMA (36 -> 120). Si el codo se va al revés, cambia a resta (-).
        servo_elbow = cfg.OFFSET_ELBOW + elbow_deflection_deg

        # Debug Print (Opcional, para ver qué piensa el robot)
        print(f"🎯 Target: {x},{z} | D:{dist_total:.1f} | 🧠 Angles -> Base:{servo_base:.0f} Sho:{shoulder_total_deg:.0f} Elb:{elbow_deflection_deg:.0f}")

        return {
            "base": int(servo_base),
            "hombro": int(servo_shoulder),
            "codo": int(servo_elbow)
        }