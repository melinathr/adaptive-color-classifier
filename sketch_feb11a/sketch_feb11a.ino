#include <Arduino.h>
#include <ArduinoJson.h> 

const int PIN_R = A0;
const int PIN_G = A1;
const int PIN_B = A2;
const int BTN = 2;
const int LED_R = 9;
const int LED_G = 10;
const int LED_B = 11;

const unsigned long T_SLOT  = 1000; // 1s -> slot change
const unsigned long T_LEARN = 2000; // 2s -> learn
const unsigned long T_DEL   = 3000; // 3s -> delete
const unsigned long WINDOW = 350;   

unsigned long lastSendTime = 0;
const int sendInterval = 250; 

bool btnStable = HIGH;
bool btnLastReading = HIGH;
unsigned long lastDebounceTime = 0;
bool pressOngoing = false;
unsigned long pressStartTime = 0;
const unsigned long DEBOUNCE_MS = 30;

void setup() {
  Serial.begin(9600);
  pinMode(BTN, INPUT_PULLUP);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  
  digitalWrite(LED_R, 1); delay(100); digitalWrite(LED_R, 0);
  digitalWrite(LED_G, 1); delay(100); digitalWrite(LED_G, 0);
  digitalWrite(LED_B, 1); delay(100); digitalWrite(LED_B, 0);
}

bool inWindow(unsigned long dur, unsigned long target) {
  if (dur + WINDOW < target) return false;
  if (dur >= target + WINDOW) return false;
  return true;
}

void loop() {
  int r = map(analogRead(PIN_R), 0, 1023, 0, 255);
  int g = map(analogRead(PIN_G), 0, 1023, 0, 255);
  int b = map(analogRead(PIN_B), 0, 1023, 0, 255);

  bool reading = digitalRead(BTN);
  if (reading != btnLastReading) {
    lastDebounceTime = millis();
    btnLastReading = reading;
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_MS) {
    if (reading != btnStable) {
      btnStable = reading;

      if (btnStable == LOW) {
        pressOngoing = true;
        pressStartTime = millis();
      } 
      else {
        if (pressOngoing) {
          pressOngoing = false;
          unsigned long dur = millis() - pressStartTime;
          
          StaticJsonDocument<200> doc;
          doc["r"] = r; doc["g"] = g; doc["b"] = b;

          // تشخیص نوع دستور بر اساس زمان
          if (inWindow(dur, T_SLOT)) {
             doc["type"] = "cmd";
             doc["action"] = "next_slot";
          } 
          else if (inWindow(dur, T_LEARN)) {
             doc["type"] = "cmd";
             doc["action"] = "learn";
          }
          else if (inWindow(dur, T_DEL)) {
             doc["type"] = "cmd";
             doc["action"] = "delete";
          }

          if (doc.containsKey("type")) {
            serializeJson(doc, Serial);
            Serial.println();
          }
        }
      }
    }
  }

  if (millis() - lastSendTime > sendInterval && !pressOngoing) {
    lastSendTime = millis();
    StaticJsonDocument<200> doc;
    doc["type"] = "data";
    doc["r"] = r; doc["g"] = g; doc["b"] = b;
    serializeJson(doc, Serial);
    Serial.println();
  }

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, input);

    if (!error) {
      if (doc["cmd"] == "led") {
        int lr = doc["R"];
        int lg = doc["G"];
        int lb = doc["B"];
        analogWrite(LED_R, lr);
        analogWrite(LED_G, lg);
        analogWrite(LED_B, lb);
      }
    }
  }
}
