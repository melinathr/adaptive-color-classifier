import serial
import json
import time
from sklearn.neighbors import KNeighborsClassifier
import datetime

#  AIoT SERVER CONFIGURATION (Simulated)
PORT = "COM8"
BAUD_RATE = 9600

GREEN_MARGIN = 50   
EQUAL_TOLERANCE = 40 

base_colors = {'red': [255, 0, 0], 'blue': [0, 0, 255]}
user_slots = {} 
MAX_SLOTS = 5
current_active_slot = 0 
model_version = 1.0

clf = KNeighborsClassifier(n_neighbors=1)

def log_http(method, endpoint, payload, status=200):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] \"{method} {endpoint} HTTP/1.1\" {status} - Payload: {payload}")

def train_model():
    global model_version
    X = []
    y = []
    for name, rgb in base_colors.items():
        X.append(rgb); y.append(name)
    for idx, data in user_slots.items():
        X.append(data['rgb']); y.append(data['name'])
        
    if len(X) > 0:
        clf.fit(X, y)
        model_version += 0.1
        print(f"\n[SYSTEM] Model Retrained (v{model_version:.1f}). Classes: {list(set(y))}")
        print("[SYSTEM] OTA Update: Pushing new logic to client...\n")

train_model()

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=0.1)
    print(f"\n[SERVER] Started on {PORT}. Waiting for IoT Client...\n")
except Exception as e:
    print(f"[CRITICAL] Serial Port Error: {e}")
    exit()

def send_response(r, g, b):
    resp = json.dumps({"cmd": "led", "R": int(r), "G": int(g), "B": int(b)}) + '\n'
    ser.write(resp.encode('utf-8'))

def decide_led_logic(pred_name, r, g, b):
    if pred_name in ['red', 'green', 'blue']:
        if pred_name == 'red': return (255, 0, 0)
        if pred_name == 'green': return (0, 255, 0)
        if pred_name == 'blue': return (0, 0, 255)

    diff_rg = abs(r - g); diff_gb = abs(g - b); diff_rb = abs(r - b)
    if diff_rg < EQUAL_TOLERANCE and diff_gb < EQUAL_TOLERANCE and diff_rb < EQUAL_TOLERANCE:
        return (255, 255, 255)

    vals = [('r', r), ('g', g), ('b', b)]
    vals.sort(key=lambda x: x[1], reverse=True)
    out = {'r': 0, 'g': 0, 'b': 0}
    out[vals[0][0]] = 255
    out[vals[1][0]] = 255
    return (out['r'], out['g'], out['b'])

while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line: continue
            
            try:
                data = json.loads(line)
            except:
                print(f"[WARN] Corrupted Packet: {line}")
                continue

            if data.get("type") == "data":
                r, g, b = data['r'], data['g'], data['b']
                
                try:
                    pred_name = clf.predict([[r, g, b]])[0]
                except:
                    pred_name = "unknown"

                led_r, led_g, led_b = decide_led_logic(pred_name, r, g, b)
                
                log_http("POST", "/api/predict", {"rgb": [r,g,b], "result": pred_name})
                
                send_response(led_r, led_g, led_b)

            elif data.get("type") == "cmd":
                action = data['action']
                r, g, b = data['r'], data['g'], data['b']
                
                log_http("POST", f"/api/control/{action}", {"slot": current_active_slot+1})

                if action == "next_slot":
                    current_active_slot = (current_active_slot + 1) % MAX_SLOTS
                    print(f">>> Client switched to SLOT {current_active_slot + 1}")
                    send_response(0, 0, 0); time.sleep(0.1); send_response(255, 255, 255)

                elif action == "learn":
                    name = f"s{current_active_slot + 1}"
                    if (g - r > GREEN_MARGIN) and (g - b > GREEN_MARGIN):
                        name = "green"
                    
                    user_slots[current_active_slot] = {'name': name, 'rgb': [r, g, b]}
                    train_model()
                    send_response(0, 255, 0); time.sleep(0.5)

                elif action == "delete":
                    if current_active_slot in user_slots:
                        del user_slots[current_active_slot]
                        train_model()
                        send_response(255, 0, 0); time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
        break
    except Exception as e:
        print(f"[ERROR] {e}")
        break

ser.close()
