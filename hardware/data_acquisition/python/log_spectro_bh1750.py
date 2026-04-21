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
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "mediciones.csv")

# If you want to force a specific port, set it here (e.g., "/dev/ttyACM0").
# Leave as None to auto-detect.
FORCED_PORT = None

# <<<<<< CHANGE THIS FOR YOUR SESSION >>>>>>
LABEL = "8"   # e.g., "lamp_on", "lamp_off", "outdoor", etc.
# <<<<<< CHANGE THIS FOR YOUR SESSION >>>>>>

# ================================
# HELPERS
# ================================
def detect_port():
    if FORCED_PORT:
        return FORCED_PORT
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        raise RuntimeError("No serial port detected. Connect the Arduino.")
    # Prefer devices that look like ACM/USB
    for p in ports:
        if "ACM" in p.device or "USB" in p.device:
            print(f"[✔] Possible Arduino detected at {p.device}")
            return p.device
    print(f"[!] No explicit ACM/USB port found, using {ports[0].device}")
    return ports[0].device

def prepare_csv(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new_file = not os.path.exists(path)
    f = open(path, "a", newline="")
    w = csv.writer(f)
    if new_file:
        w.writerow(["temp","violet","blue","green","yellow","orange","red","lux","label"])
    return f, w

# ================================
# MAIN
# ================================
def main():
    port = detect_port()
    print(f"[INFO] Opening {port} @ {BAUD_RATE} baud...")
    with serial.Serial(port, BAUD_RATE, timeout=1) as ser, prepare_csv(CSV_PATH)[0] as f:
        writer = csv.writer(f)
        time.sleep(2)  # brief pause to let the Arduino boot

        print("[INFO] Reading. Press Ctrl+C to stop.\n")
        num_ok = 0
        try:
            while True:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw or raw.startswith("#"):
                    continue
                parts = raw.split(",")
                if len(parts) != 8:
                    # malformed line; skip
                    continue

                # simple parse — skip line on error
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
                f.flush()  # flush to disk immediately
                num_ok += 1

                # lightweight console feedback every 20 samples
                if num_ok % 20 == 0:
                    print(f"[OK] {num_ok} samples saved...")

        except KeyboardInterrupt:
            print(f"\n[STOP] Capture stopped. Total saved: {num_ok}")
            print(f"[✔] CSV at: {os.path.abspath(CSV_PATH)}")

if __name__ == "__main__":
    main()
