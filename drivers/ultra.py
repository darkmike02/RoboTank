#!/usr/bin/python3
# File name   : Ultrasonic.py
# Description : Detection distance with Timeout protection
# Modified by : Gemini for Robot_v2

import RPi.GPIO as GPIO
import time

Tr = 11
Ec = 8

def checkdist():
    # Configuracion de pines (seguridad por si otro script los cambio)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Tr, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(Ec, GPIO.IN)
    
    # Enviar pulso de sonido
    GPIO.output(Tr, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(Tr, GPIO.LOW)
    
    # --- FASE 1: Esperar a que empiece el eco ---
    pulse_start = time.time()
    timeout_start = time.time()
    
    while not GPIO.input(Ec):
        pulse_start = time.time()
        # PROTECCION: Si esperamos mas de 0.05s, abortar
        if pulse_start - timeout_start > 0.05:
            return -1
            
    # --- FASE 2: Esperar a que termine el eco ---
    pulse_end = time.time()
    timeout_end = time.time()
    
    while GPIO.input(Ec):
        pulse_end = time.time()
        # PROTECCION: Si el eco es absurdamente largo, abortar
        if pulse_end - timeout_end > 0.05:
            return -1
            
    # Calculo de distancia
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150 # (34300 cm/s / 2)
    distance = round(distance, 2)
    
    return distance

if __name__ == '__main__':
    try:
        print("Iniciando prueba de ultrasonido (Ctrl+C para salir)...")
        while True:
            dist = checkdist()
            if dist == -1:
                print("Distancia: Fuera de rango / Error")
            else:
                print(f"Distancia: {dist} cm")
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nPrueba finalizada.")