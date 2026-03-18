import serial
import csv
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
PORT     = 'COM3'       # Change this to your ESP32 port e.g. COM4, COM5
BAUD     = 115200
BASE     = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE, '..', 'dataset', 'raw', 'sensor_data.csv')

# ── Setup CSV ─────────────────────────────────────────────────────────────────
file_exists = os.path.exists(OUT_FILE)

with serial.Serial(PORT, BAUD, timeout=2) as ser, \
     open(OUT_FILE, 'a', newline='') as f:

    writer = csv.writer(f)

    if not file_exists:
        writer.writerow(['timestamp', 'temperature', 'humidity', 'gas_raw'])
        print("Created new CSV file.")

    print(f"Logging data from {PORT} at {BAUD} baud...")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()

            if not line or ',' not in line:
                continue

            parts = line.split(',')

            if len(parts) != 3:
                continue

            temp, hum, gas = parts
            timestamp = datetime.now().isoformat()
            row = [timestamp, temp.strip(), hum.strip(), gas.strip()]

            writer.writerow(row)
            f.flush()

            print(f"[{timestamp}]  Temp: {temp}°C  |  Humidity: {hum}%  |  Gas: {gas}")

        except KeyboardInterrupt:
            print("\nLogging stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue