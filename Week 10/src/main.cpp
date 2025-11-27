#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// Pin definitions
#define DHT_PIN       13
#define DHT_TYPE      DHT22
#define PIR_PIN       14
#define LED_PIN       2

// Ngưỡng nhiệt độ (°C) - LED sáng khi nhiệt độ vượt ngưỡng
#define TEMP_THRESHOLD  30.0

// Thời gian tắt đèn nền LCD sau khi không có chuyển động (ms)
#define BACKLIGHT_TIMEOUT  10000

// LCD I2C address (thường là 0x27 hoặc 0x3F)
#define LCD_ADDRESS  0x27
#define LCD_COLS     16
#define LCD_ROWS     2

// Objects
LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLS, LCD_ROWS);
DHT dht(DHT_PIN, DHT_TYPE);

// Variables
unsigned long lastSensorRead = 0;
unsigned long sensorInterval = 2000;  // Đọc cảm biến mỗi 2 giây
unsigned long lastMotionTime = 0;
bool backlightOn = true;
bool lastMotionState = false;

void setup() {
  Serial.begin(115200);
  Serial.println("\n========================================");
  Serial.println("  ESP32 + DHT22 + PIR + LCD + LED");
  Serial.println("========================================");
  Serial.print("Temperature threshold: ");
  Serial.print(TEMP_THRESHOLD);
  Serial.println(" C");
  Serial.print("Backlight timeout: ");
  Serial.print(BACKLIGHT_TIMEOUT / 1000);
  Serial.println(" seconds");
  Serial.println("----------------------------------------\n");
  
  // Khởi tạo chân
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Khởi tạo I2C
  Wire.begin(21, 22);  // SDA=21, SCL=22
  
  // Khởi tạo LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Initializing...");
  
  // Khởi tạo DHT22
  dht.begin();
  
  // Đợi cảm biến ổn định
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready!");
  Serial.println("System initialized successfully!\n");
  
  lastMotionTime = millis();
  delay(1000);
  lcd.clear();
}

void readAndDisplaySensor() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (!isnan(temperature) && !isnan(humidity)) {
    // Hiển thị lên LCD
    lcd.setCursor(0, 0);
    lcd.print("Temp: ");
    lcd.print(temperature, 1);
    lcd.print((char)223);  // Ký tự độ
    lcd.print("C   ");
    
    lcd.setCursor(0, 1);
    lcd.print("Hum:  ");
    lcd.print(humidity, 1);
    lcd.print("%   ");
    
    // Log qua Serial
    Serial.print("[SENSOR] Temp: ");
    Serial.print(temperature, 1);
    Serial.print(" C | Humidity: ");
    Serial.print(humidity, 1);
    Serial.print("% | ");
    
    // Kiểm tra ngưỡng nhiệt độ và điều khiển LED
    if (temperature > TEMP_THRESHOLD) {
      digitalWrite(LED_PIN, HIGH);
      Serial.print("LED: ON (Temp > ");
      Serial.print(TEMP_THRESHOLD);
      Serial.println(" C)");
    } else {
      digitalWrite(LED_PIN, LOW);
      Serial.print("LED: OFF (Temp <= ");
      Serial.print(TEMP_THRESHOLD);
      Serial.println(" C)");
    }
  } else {
    lcd.setCursor(0, 0);
    lcd.print("Sensor Error!   ");
    lcd.setCursor(0, 1);
    lcd.print("                ");
    Serial.println("[ERROR] Failed to read DHT22 sensor!");
  }
}

void handleMotionSensor() {
  bool motionDetected = digitalRead(PIR_PIN) == HIGH;
  
  if (motionDetected) {
    lastMotionTime = millis();
    
    if (!backlightOn) {
      lcd.backlight();
      backlightOn = true;
      Serial.println("[PIR] Motion detected! Backlight ON");
    }
    
    if (!lastMotionState) {
      Serial.println("[PIR] Motion detected!");
      lastMotionState = true;
    }
  } else {
    if (lastMotionState) {
      Serial.println("[PIR] No motion");
      lastMotionState = false;
    }
    
    // Kiểm tra timeout để tắt đèn nền
    if (backlightOn && (millis() - lastMotionTime >= BACKLIGHT_TIMEOUT)) {
      lcd.noBacklight();
      backlightOn = false;
      Serial.println("[PIR] No motion for 10s. Backlight OFF");
    }
  }
}

void loop() {
  // Xử lý cảm biến chuyển động
  handleMotionSensor();
  
  // Đọc và hiển thị cảm biến định kỳ
  if (millis() - lastSensorRead >= sensorInterval) {
    lastSensorRead = millis();
    readAndDisplaySensor();
  }
  
  delay(100);
}
