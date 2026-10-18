#!/usr/bin/env python3
# File name   : mpu6050.py
# Description : IMU Sensor Control (Clean Version)

import smbus
import time
import math
import numpy as np

# Direcciones
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# Intentar conectar al bus I2C
try:
    bus = smbus.SMBus(1)
except:
    bus = None

def init_MPU6050():
    """Inicializa el sensor activando el registro de energía"""
    if bus is None: return
    try:
        bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
    except:
        pass

def read_raw_data(addr):
    if bus is None: return 0
    try:
        high = bus.read_byte_data(MPU6050_ADDR, addr)
        low = bus.read_byte_data(MPU6050_ADDR, addr + 1)
        val = (high << 8) + low
        if val > 32768:
            val = val - 65536
        return val
    except:
        return 0

def get_sensor_data():
    """Devuelve los datos procesados del acelerómetro y giroscopio"""
    if bus is None: return None

    # Leer crudos
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(ACCEL_XOUT_H + 4)

    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_XOUT_H + 2)
    gyro_z = read_raw_data(GYRO_XOUT_H + 4)

    # Conversión simple
    scale_acc = 16384.0
    scale_gyro = 131.0

    return {
        "accel": {
            "x": acc_x / scale_acc,
            "y": acc_y / scale_acc,
            "z": acc_z / scale_acc
        },
        "gyro": {
            "x": gyro_x / scale_gyro,
            "y": gyro_y / scale_gyro,
            "z": gyro_z / scale_gyro
        }
    }