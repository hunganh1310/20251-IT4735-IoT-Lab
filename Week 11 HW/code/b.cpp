#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;

const char* STUDENT_ID = "20225164";

// MQTT Topics
String TOPIC_LED_STATE;

#define LED1_PIN 2
#define LED2_PIN 4
#define BUTTON1_PIN 12
#define BUTTON2_PIN 14

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// LED states
bool led1State = false;
bool led2State = false;

// Button debounce
unsigned long lastButton1Press = 0;
unsigned long lastButton2Press = 0;
#define DEBOUNCE_DELAY 200

// FreeRTOS task handles
TaskHandle_t mqttTaskHandle = NULL;
TaskHandle_t buttonTaskHandle = NULL;

// Semaphore for protecting shared resources
SemaphoreHandle_t ledStateMutex = NULL;

void setupWiFi();
void setupMQTT();
void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void publishLedState(const char* source);
void handleButtons();

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  
  // Parse JSON payload
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.printf("JSON parse error: %s\n", error.c_str());
    return;
  }
  
  // Get LED states from JSON
  const char* led1 = doc["led1"];
  const char* led2 = doc["led2"];
  const char* from = doc["from"];
  
  Serial.printf("LED1: %s, LED2: %s, From: %s\n", led1, led2, from);
  
  // Use mutex to protect shared LED state
  if (xSemaphoreTake(ledStateMutex, portMAX_DELAY) == pdTRUE) {
    // Update LED states
    if (led1 != nullptr) {
      led1State = (strcmp(led1, "on") == 0);
      digitalWrite(LED1_PIN, led1State ? HIGH : LOW);
    }
    
    if (led2 != nullptr) {
      led2State = (strcmp(led2, "on") == 0);
      digitalWrite(LED2_PIN, led2State ? HIGH : LOW);
    }
    
    Serial.printf("Updated: LED1=%s, LED2=%s\n", 
                  led1State ? "ON" : "OFF", 
                  led2State ? "ON" : "OFF");
    
    xSemaphoreGive(ledStateMutex);
  }
}

void setupMQTT() {
  TOPIC_LED_STATE = "iot_class_20251/bai6/" + String(STUDENT_ID) + "/led_state";
  
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.println("Connecting to MQTT broker...");
    
    String clientId = "ESP32_" + String(STUDENT_ID) + "_" + String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("MQTT Connected!");
      
      // Subscribe to LED state topic
      mqttClient.subscribe(TOPIC_LED_STATE.c_str());
      Serial.printf("Subscribed to: %s\n", TOPIC_LED_STATE.c_str());
      
    } else {
      Serial.printf("MQTT connection failed, rc=%d\n", mqttClient.state());
      Serial.println("Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void publishLedState(const char* source) {
  JsonDocument doc;
  doc["led1"] = led1State ? "on" : "off";
  doc["led2"] = led2State ? "on" : "off";
  doc["from"] = source;
  
  char jsonBuffer[128];
  serializeJson(doc, jsonBuffer);
  
  // Publish with retain flag = true
  if (mqttClient.publish(TOPIC_LED_STATE.c_str(), jsonBuffer, true)) {
    Serial.printf("Published: %s\n", jsonBuffer);
  } else {
    Serial.println("Failed to publish LED state!");
  }
}

void handleButtons() {
  unsigned long currentTime = millis();
  
  // Button 1 - controls LED1
  if (digitalRead(BUTTON1_PIN) == LOW) {
    if (currentTime - lastButton1Press > DEBOUNCE_DELAY) {
      lastButton1Press = currentTime;
      
      // Use mutex to protect shared LED state
      if (xSemaphoreTake(ledStateMutex, portMAX_DELAY) == pdTRUE) {
        // Toggle LED1
        led1State = !led1State;
        digitalWrite(LED1_PIN, led1State ? HIGH : LOW);
        
        Serial.printf("Button 1 pressed: LED1 = %s\n", led1State ? "ON" : "OFF");
        
        xSemaphoreGive(ledStateMutex);
      }
      
      // Publish to MQTT
      publishLedState("device");
    }
  }
  
  // Button 2 - controls LED2
  if (digitalRead(BUTTON2_PIN) == LOW) {
    if (currentTime - lastButton2Press > DEBOUNCE_DELAY) {
      lastButton2Press = currentTime;
      
      // Use mutex to protect shared LED state
      if (xSemaphoreTake(ledStateMutex, portMAX_DELAY) == pdTRUE) {
        // Toggle LED2
        led2State = !led2State;
        digitalWrite(LED2_PIN, led2State ? HIGH : LOW);
        
        Serial.printf("Button 2 pressed: LED2 = %s\n", led2State ? "ON" : "OFF");
        
        xSemaphoreGive(ledStateMutex);
      }
      
      // Publish to MQTT
      publishLedState("device");
    }
  }
}

// FreeRTOS Task: MQTT Message Processing
void mqttTask(void *parameter) {
  Serial.println("MQTT Task started");
  
  while (true) {
    // Check MQTT connection and reconnect if needed
    if (!mqttClient.connected()) {
      reconnectMQTT();
    }
    
    // Process incoming MQTT messages
    mqttClient.loop();
    
    // Small delay to yield to other tasks
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// FreeRTOS Task: Button Handling
void buttonTask(void *parameter) {
  Serial.println("Button Task started");
  
  while (true) {
    // Check button states and handle presses
    handleButtons();
    
    // Small delay to yield to other tasks
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize LED pins
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  
  // Initialize button pins with internal pull-up
  pinMode(BUTTON1_PIN, INPUT_PULLUP);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);
  
  Serial.println("GPIO initialized");
  
  // Create mutex for protecting shared LED state
  ledStateMutex = xSemaphoreCreateMutex();
  if (ledStateMutex == NULL) {
    Serial.println("Failed to create mutex!");
    return;
  }
  
  setupWiFi();
  setupMQTT();
  
  // Create FreeRTOS tasks
  xTaskCreatePinnedToCore(
    mqttTask,           // Task function
    "MQTT Task",        // Task name
    4096,               // Stack size (bytes)
    NULL,               // Task parameter
    1,                  // Task priority
    &mqttTaskHandle,    // Task handle
    0                   // Core ID (0 or 1)
  );
  
  xTaskCreatePinnedToCore(
    buttonTask,         // Task function
    "Button Task",      // Task name
    4096,               // Stack size (bytes)
    NULL,               // Task parameter
    1,                  // Task priority
    &buttonTaskHandle,  // Task handle
    1                   // Core ID (0 or 1)
  );
  
  Serial.println("FreeRTOS tasks created successfully");
}

void loop() {
  // Empty loop - all work is done by FreeRTOS tasks
  vTaskDelay(pdMS_TO_TICKS(1000));
}
