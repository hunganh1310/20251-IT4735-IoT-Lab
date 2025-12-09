#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>

#define LED1_PIN 2
#define LED2_PIN 4

TaskHandle_t led1TaskHandle = NULL;
TaskHandle_t led2TaskHandle = NULL;
TaskHandle_t serialTaskHandle = NULL;

// LED blinking periods (in milliseconds)
volatile uint32_t led1Period = 500;
volatile uint32_t led2Period = 800;

// LED enable/disable flags
volatile bool led1Enabled = true;
volatile bool led2Enabled = true;

// Semaphores for protecting shared resources
SemaphoreHandle_t led1Mutex = NULL;
SemaphoreHandle_t led2Mutex = NULL;

// Function prototypes
void led1Task(void *parameter);
void led2Task(void *parameter);
void serialTask(void *parameter);
void processSerialCommand(String command);

// Task 1: Control LED 1 blinking
void led1Task(void *parameter) {
  while (true) {
    if (xSemaphoreTake(led1Mutex, portMAX_DELAY) == pdTRUE) {
      bool enabled = led1Enabled;
      uint32_t period = led1Period;
      xSemaphoreGive(led1Mutex);
      
      if (enabled) {
        digitalWrite(LED1_PIN, HIGH);
        vTaskDelay(pdMS_TO_TICKS(period / 2));
        digitalWrite(LED1_PIN, LOW);
        vTaskDelay(pdMS_TO_TICKS(period / 2));
      } else {
        // If disabled, turn off LED and wait
        digitalWrite(LED1_PIN, LOW);
        vTaskDelay(pdMS_TO_TICKS(100));
      }
    }
  }
}

// Task 2: Control LED 2 blinking
void led2Task(void *parameter) {
  while (true) {
    if (xSemaphoreTake(led2Mutex, portMAX_DELAY) == pdTRUE) {
      bool enabled = led2Enabled;
      uint32_t period = led2Period;
      xSemaphoreGive(led2Mutex);
      
      if (enabled) {
        digitalWrite(LED2_PIN, HIGH);
        vTaskDelay(pdMS_TO_TICKS(period / 2));
        digitalWrite(LED2_PIN, LOW);
        vTaskDelay(pdMS_TO_TICKS(period / 2));
      } else {
        // If disabled, turn off LED and wait
        digitalWrite(LED2_PIN, LOW);
        vTaskDelay(pdMS_TO_TICKS(100));
      }
    }
  }
}

// Task 3: Handle Serial commands
void serialTask(void *parameter) {
  Serial.println("Commands: LED <1|2> <period|ON|OFF>");
  
  String inputBuffer = "";
  
  while (true) {
    if (Serial.available() > 0) {
      char inChar = Serial.read();
      
      if (inChar == '\n' || inChar == '\r') {
        if (inputBuffer.length() > 0) {
          inputBuffer.trim();
          processSerialCommand(inputBuffer);
          inputBuffer = "";
        }
      } else {
        inputBuffer += inChar;
      }
    }
    
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

// Process Serial commands
void processSerialCommand(String command) {
  command.toUpperCase();
  command.trim();
  
  // Parse command: "LED X Y"
  if (command.startsWith("LED ")) {
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (secondSpace == -1) {
      Serial.println("Error: Invalid format");
      return;
    }
    
    String ledNumStr = command.substring(firstSpace + 1, secondSpace);
    String valueStr = command.substring(secondSpace + 1);
    
    ledNumStr.trim();
    valueStr.trim();
    
    int ledNum = ledNumStr.toInt();
    
    if (ledNum != 1 && ledNum != 2) {
      Serial.println("Error: LED must be 1 or 2");
      return;
    }
    
    // Check if value is ON/OFF or a period value
    if (valueStr == "ON") {
      if (ledNum == 1) {
        if (xSemaphoreTake(led1Mutex, portMAX_DELAY) == pdTRUE) {
          led1Enabled = true;
          xSemaphoreGive(led1Mutex);
          Serial.println("LED1 ON");
        }
      } else {
        if (xSemaphoreTake(led2Mutex, portMAX_DELAY) == pdTRUE) {
          led2Enabled = true;
          xSemaphoreGive(led2Mutex);
          Serial.println("LED2 ON");
        }
      }
    } 
    else if (valueStr == "OFF") {
      if (ledNum == 1) {
        if (xSemaphoreTake(led1Mutex, portMAX_DELAY) == pdTRUE) {
          led1Enabled = false;
          xSemaphoreGive(led1Mutex);
          Serial.println("LED1 OFF");
        }
      } else {
        if (xSemaphoreTake(led2Mutex, portMAX_DELAY) == pdTRUE) {
          led2Enabled = false;
          xSemaphoreGive(led2Mutex);
          Serial.println("LED2 OFF");
        }
      }
    } 
    else {
      // Try to parse as period value
      int period = valueStr.toInt();
      
      if (period <= 0) {
        Serial.println("Error: Invalid period");
        return;
      }
      
      if (ledNum == 1) {
        if (xSemaphoreTake(led1Mutex, portMAX_DELAY) == pdTRUE) {
          led1Period = period;
          xSemaphoreGive(led1Mutex);
          Serial.printf("LED1: %dms\n", period);
        }
      } else {
        if (xSemaphoreTake(led2Mutex, portMAX_DELAY) == pdTRUE) {
          led2Period = period;
          xSemaphoreGive(led2Mutex);
          Serial.printf("LED2: %dms\n", period);
        }
      }
    }
  } else {
    Serial.println("Error: Unknown command");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nFreeRTOS LED Control");
  
  // Initialize LED pins
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  
  // Create mutexes for protecting shared resources
  led1Mutex = xSemaphoreCreateMutex();
  led2Mutex = xSemaphoreCreateMutex();
  
  if (led1Mutex == NULL || led2Mutex == NULL) {
    Serial.println("Mutex error!");
    return;
  }
  
  // Create FreeRTOS tasks
  BaseType_t result1 = xTaskCreatePinnedToCore(
    led1Task,           // Task function
    "LED1 Task",        // Task name
    2048,               // Stack size (bytes)
    NULL,               // Task parameter
    2,                  // Task priority
    &led1TaskHandle,    // Task handle
    0                   // Core ID (0 or 1)
  );
  
  BaseType_t result2 = xTaskCreatePinnedToCore(
    led2Task,           // Task function
    "LED2 Task",        // Task name
    2048,               // Stack size (bytes)
    NULL,               // Task parameter
    2,                  // Task priority
    &led2TaskHandle,    // Task handle
    0                   // Core ID (0 or 1)
  );
  
  BaseType_t result3 = xTaskCreatePinnedToCore(
    serialTask,         // Task function
    "Serial Task",      // Task name
    4096,               // Stack size (bytes)
    NULL,               // Task parameter
    1,                  // Task priority (lower than LED tasks)
    &serialTaskHandle,  // Task handle
    1                   // Core ID (0 or 1)
  );
  
  if (result1 == pdPASS && result2 == pdPASS && result3 == pdPASS) {
    Serial.println("Ready!");
  } else {
    Serial.println("Task creation failed!");
  }
}

void loop() {
  // Empty loop - all work is done by FreeRTOS tasks
  vTaskDelay(pdMS_TO_TICKS(1000));
}
