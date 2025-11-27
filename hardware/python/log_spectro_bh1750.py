#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import serial.tools.list_ports
import csv
import os
import time

# ================================
# CONFIG
# ================================
BAUD_RATE = 115200
CSV_PATH = "/home/estiberz/UNAL/design_electronic_devices/lightwell_wearable/python/data/mediciones.csv"

# If you want to force a specific port, set it here (e.g., "/dev/ttyACM0").
# Leave as None to auto-detect.
FORCED_PORT = None

# <<<<<< CHANGE THIS FOR YOUR SESSION >>>>>>
LABEL = "8"   # e.g., "lamp_on", "lamp_off", "outdoor", etc.
# <<<<<< CHANGE THIS FOR YOUR SESSION >>>>>>

# ================================
# HELPERS
# ================================
def detectar_puerto():
    if FORCED_PORT:
        return FORCED_PORT
    puertos = list(serial.tools.list_ports.comports())
    if not puertos:
        raise RuntimeError("No se detectó ningún puerto serial. Conecta el Arduino.")
    # Prefer devices that look like ACM/USB
    for p in puertos:
        if "ACM" in p.device or "USB" in p.device:
            print(f"[✔] Detectado posible Arduino en {p.device}")
            return p.device
    print(f"[!] No vi ACM/USB explícito, uso {puertos[0].device}")
    return puertos[0].device

def preparar_csv(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    nuevo = not os.path.exists(path)
    f = open(path, "a", newline="")
    w = csv.writer(f)
    if nuevo:
        w.writerow(["temp","violet","blue","green","yellow","orange","red","lux","label"])
    return f, w

# ================================
# MAIN
# ================================
def main():
    port = detectar_puerto()
    print(f"[INFO] Abriendo {port} @ {BAUD_RATE} baud...")
    with serial.Serial(port, BAUD_RATE, timeout=1) as ser, preparar_csv(CSV_PATH)[0] as f:
        writer = csv.writer(f)
        time.sleep(2)  # pequeño respiro para que el Arduino arranque

        print("[INFO] Leyendo. Ctrl+C para detener.\n")
        num_ok = 0
        try:
            while True:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw or raw.startswith("#"):
                    continue
                parts = raw.split(",")
                if len(parts) != 8:
                    # línea malformada; ignora
                    continue

                # Parseo simple (si falla, ignora la línea)
                try:
                    temp   = float(parts[0])
                    violet = float(parts[1])
                    blue   = float(parts[2])
                    green  = float(parts[3])
                    yellow = float(parts[4])
                    orange = float(parts[5])
                    red    = float(parts[6])
                    lux    = float(parts[7])
                except ValueError:
                    continue

                writer.writerow([temp, violet, blue, green, yellow, orange, red, lux, LABEL])
                f.flush()  # asegura que se guarde en disco
                num_ok += 1

                # feedback ligero en consola cada 20 muestras
                if num_ok % 20 == 0:
                    print(f"[OK] {num_ok} muestras guardadas...")

        except KeyboardInterrupt:
            print(f"\n[STOP] Captura detenida. Total guardadas: {num_ok}")
            print(f"[✔] CSV en: {os.path.abspath(CSV_PATH)}")

if __name__ == "__main__":
    main()
