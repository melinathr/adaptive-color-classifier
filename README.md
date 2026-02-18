# Adaptive Color Classifier (Arduino + Python + Proteus)

A learnable RGB color classification system.
An **Arduino UNO** (simulated in **Proteus**) reads RGB values and communicates with a **Python serial server** using JSON messages.
The server performs classification using a simple **KNN model** and sends back LED commands to visualize the detected color.
The system also supports **interactive learning** (adding/removing samples) using a single button with different press durations.

## Demo Setup (Proteus)
- 3 potentiometers simulate RGB sensor channels:
  - A0: Red
  - A1: Green
  - A2: Blue
- One push button on D2 (internal pull-up)
- RGB LEDs (PWM):
  - D9: Red LED
  - D10: Green LED
  - D11: Blue LED
- UART Serial JSON communication with the Python server

## Controls (Button Press Duration)
- ~1s: `next_slot` (switch active slot)
- ~2s: `learn` (save a sample and retrain model)
- ~3s: `delete` (delete current slot sample and retrain)

## Repository Structure
- `Project.pdsprj` : Proteus project
- `sketch_feb11a/sketch_feb11a.ino` : Arduino code
- `sketch_feb11a/build/.../*.hex` : compiled HEX for Proteus
- `server.py` : Python serial server (KNN classifier)

## Run (Windows)
### 1) Python Server
Install dependencies:
```bash
pip install pyserial scikit-learn
