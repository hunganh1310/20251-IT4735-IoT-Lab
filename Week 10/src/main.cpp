/*
 * IOT Lab - Week 10: Wokwi Simulation Demo
 * 
 * Components:
 * - 3 LEDs (Red, Green, Blue) on GPIO 2, 4, 5
 * - Push button on GPIO 15
 * - DHT22 temperature/humidity sensor on GPIO 13
 * 
 * Features:
 * - LED chaser pattern
 * - Button to change LED mode
 * - Temperature & humidity reading
 * - Serial monitor interaction
 */

#include <Arduino.h>
#include <DHT.h>

// Pin definitions
#define LED_RED    2
#define LED_GREEN  4
#define LED_BLUE   5
#define BUTTON_PIN 15
#define DHT_PIN    13
#define DHT_TYPE   DHT22

// Global variables
DHT dht(DHT_PIN, DHT_TYPE);
int currentMode = 0;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;
unsigned long lastSensorRead = 0;
unsigned long sensorInterval = 2000;  // Read sensor every 2 seconds

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== IOT Lab Week 10 - Wokwi Demo ===");
  Serial.println("Commands: 'r'=red, 'g'=green, 'b'=blue, 'a'=all, 'o'=off, 't'=temperature");
  
  // Initialize LED pins
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  
  // Initialize button with internal pull-up
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initialize DHT22 sensor
  dht.begin();
  
  // Initial LED test - quick flash
  digitalWrite(LED_RED, HIGH);
  delay(200);
  digitalWrite(LED_GREEN, HIGH);
  delay(200);
  digitalWrite(LED_BLUE, HIGH);
  delay(200);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_BLUE, LOW);
  
  Serial.println("Setup complete! Press button to change mode.");
}

void allLedsOff() {
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_BLUE, LOW);
}

void readTemperature() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (!isnan(temperature) && !isnan(humidity)) {
    Serial.println("\n--- Sensor Reading ---");
    Serial.print("Temperature: ");
    Serial.print(temperature, 1);
    Serial.println(" °C");
    Serial.print("Humidity: ");
    Serial.print(humidity, 1);
    Serial.println(" %");
    Serial.println("----------------------");
  } else {
    Serial.println("DHT22 sensor error!");
  }
}

void handleSerialCommand() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    switch (cmd) {
      case 'r':
      case 'R':
        allLedsOff();
        digitalWrite(LED_RED, HIGH);
        Serial.println("Red LED ON");
        break;
      case 'g':
      case 'G':
        allLedsOff();
        digitalWrite(LED_GREEN, HIGH);
        Serial.println("Green LED ON");
        break;
      case 'b':
      case 'B':
        allLedsOff();
        digitalWrite(LED_BLUE, HIGH);
        Serial.println("Blue LED ON");
        break;
      case 'a':
      case 'A':
        digitalWrite(LED_RED, HIGH);
        digitalWrite(LED_GREEN, HIGH);
        digitalWrite(LED_BLUE, HIGH);
        Serial.println("All LEDs ON");
        break;
      case 'o':
      case 'O':
        allLedsOff();
        Serial.println("All LEDs OFF");
        break;
      case 't':
      case 'T':
        readTemperature();
        break;
      default:
        break;
    }
  }
}

void handleButton() {
  int reading = digitalRead(BUTTON_PIN);
  
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    static int buttonState = HIGH;
    if (reading != buttonState) {
      buttonState = reading;
      
      if (buttonState == LOW) {  // Button pressed
        currentMode = (currentMode + 1) % 5;
        Serial.print("Mode changed to: ");
        Serial.println(currentMode);
        
        allLedsOff();
        switch (currentMode) {
          case 0:
            Serial.println("Mode 0: All OFF");
            break;
          case 1:
            digitalWrite(LED_RED, HIGH);
            Serial.println("Mode 1: Red");
            break;
          case 2:
            digitalWrite(LED_GREEN, HIGH);
            Serial.println("Mode 2: Green");
            break;
          case 3:
            digitalWrite(LED_BLUE, HIGH);
            Serial.println("Mode 3: Blue");
            break;
          case 4:
            digitalWrite(LED_RED, HIGH);
            digitalWrite(LED_GREEN, HIGH);
            digitalWrite(LED_BLUE, HIGH);
            Serial.println("Mode 4: All ON");
            break;
        }
      }
    }
  }
  lastButtonState = reading;
}

void autoReadSensor() {
  if (millis() - lastSensorRead >= sensorInterval) {
    lastSensorRead = millis();
    readTemperature();
  }
}

void loop() {
  handleSerialCommand();
  handleButton();
  autoReadSensor();
  delay(10);
}