#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;

const char* STUDENT_ID = "20225164";

String TOPIC_STATE;
String TOPIC_TELEMETRY;

#define DHT_PIN 5
#define DHT_TYPE DHT22

#define TELEMETRY_INTERVAL 5000

WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastTelemetryTime = 0;

void setupWiFi();
void setupMQTT();
void reconnectMQTT();
void publishTelemetry();

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi Connected!");
}

void setupMQTT() {
  // Build topic strings
  TOPIC_STATE = "iot_class_20251/bai6/" + String(STUDENT_ID) + "/esp32_state";
  TOPIC_TELEMETRY = "iot_class_20251/bai6/" + String(STUDENT_ID) + "/telemetry";
  
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.println("Connecting to MQTT broker...");
    
    // Create a unique client ID
    String clientId = "ESP32_" + String(STUDENT_ID) + "_" + String(random(0xffff), HEX);
    
    // When ESP32 disconnects unexpectedly, broker will publish "offline" to state topic
    if (mqttClient.connect(clientId.c_str(), 
                           TOPIC_STATE.c_str(),  // LWT topic
                           0,                      // LWT QoS
                           true,                   // LWT retain
                           "offline")) {           // LWT message
      Serial.println("MQTT Connected!");
      
      // Publish "online" status when connected
      mqttClient.publish(TOPIC_STATE.c_str(), "online", true);
      Serial.println("Published: online status");
      
    } else {
      Serial.printf("MQTT connection failed, rc=%d\n", mqttClient.state());
      Serial.println("Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void publishTelemetry() {
  // Read DHT sensor
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  // Check if reading failed
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  // Print to Serial Monitor
  Serial.printf("Temperature: %.1f °C\n", temperature);
  Serial.printf("Humidity: %.1f %%\n", humidity);
  
  // Create JSON payload
  JsonDocument doc;
  doc["temperature"] = (int)temperature;
  doc["humidity"] = (int)humidity;
  doc["mssv"] = atol(STUDENT_ID);
  
  char jsonBuffer[128];
  serializeJson(doc, jsonBuffer);
  
  // Publish to MQTT
  if (mqttClient.publish(TOPIC_TELEMETRY.c_str(), jsonBuffer)) {
    Serial.printf("Published to %s: %s\n", TOPIC_TELEMETRY.c_str(), jsonBuffer);
  } else {
    Serial.println("Failed to publish telemetry!");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  dht.begin();
  Serial.println("DHT22 sensor initialized");
  
  setupWiFi();
  
  setupMQTT();
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  unsigned long currentTime = millis();
  if (currentTime - lastTelemetryTime >= TELEMETRY_INTERVAL) {
    lastTelemetryTime = currentTime;
    publishTelemetry();
  }
}
