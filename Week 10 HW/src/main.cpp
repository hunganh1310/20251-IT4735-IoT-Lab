#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>

// Pin definitions
#define RESET_BUTTON_PIN 0  // Nút BOOT trên ESP32

// Access Point configuration
const char* ap_ssid = "ESP32_Config";
const char* ap_password = "12345678";

// Stored WiFi credentials
String stored_ssid = "";
String stored_password = "";

// Double reset detection
#define RESET_TIMEOUT 3000
#define RESET_FLAG_KEY "reset_flag"

// Objects
Preferences preferences;
WebServer server(80);
bool isAPMode = false;

// HTML page for WiFi configuration
const char* htmlPage = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESP32 WiFi Config</title>
  <style>
    body { font-family: Arial; text-align: center; margin: 50px; background: #f0f0f0; }
    .container { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { color: #333; }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    button { background: #4CAF50; color: white; padding: 14px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }
    button:hover { background: #45a049; }
  </style>
</head>
<body>
  <div class="container">
    <h1>ESP32 WiFi Setup</h1>
    <form action="/save" method="POST">
      <input type="text" name="ssid" placeholder="WiFi SSID" required>
      <input type="password" name="password" placeholder="WiFi Password">
      <button type="submit">Save & Connect</button>
    </form>
  </div>
</body>
</html>
)rawliteral";

// HTML page for success
const char* successPage = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Success</title>
  <style>
    body { font-family: Arial; text-align: center; margin: 50px; background: #f0f0f0; }
    .container { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: auto; }
    h1 { color: #4CAF50; }
  </style>
</head>
<body>
  <div class="container">
    <h1>WiFi Saved!</h1>
    <p>ESP32 will restart and connect to your network.</p>
    <p>Please wait...</p>
  </div>
</body>
</html>
)rawliteral";

// Handle root page
void handleRoot() {
  server.send(200, "text/html", htmlPage);
}

// Handle save WiFi credentials
void handleSave() {
  String newSSID = server.arg("ssid");
  String newPassword = server.arg("password");

  Serial.println("\n=== Saving WiFi Credentials ===");
  Serial.printf("SSID: %s\n", newSSID.c_str());
  Serial.println("Password: ****");

  // Save to Preferences
  preferences.begin("wifi", false);
  preferences.putString("ssid", newSSID);
  preferences.putString("password", newPassword);
  preferences.end();

  Serial.println("Credentials saved to Preferences!");

  server.send(200, "text/html", successPage);
  
  delay(2000);
  ESP.restart();
}

// Start Access Point mode
void startAPMode() {
  isAPMode = true;
  
  Serial.println("\n=== Starting Access Point Mode ===");
  
  WiFi.disconnect(true);
  delay(100);
  
  WiFi.mode(WIFI_AP);
  delay(100);
  
  bool apStarted = WiFi.softAP(ap_ssid, ap_password);
  
  if (apStarted) {
    Serial.println("AP Started Successfully!");
  } else {
    Serial.println("AP Failed to Start!");
    return;
  }
  
  delay(500);  // Wait for AP to stabilize
  
  IPAddress IP = WiFi.softAPIP();
  Serial.printf("AP SSID: %s\n", ap_ssid);
  Serial.printf("AP Password: %s\n", ap_password);
  Serial.printf("AP IP Address: %s\n", IP.toString().c_str());

  // Setup web server routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/save", HTTP_POST, handleSave);
  server.onNotFound([]() {
    server.send(404, "text/plain", "Not Found");
  });
  server.begin();
  
  Serial.println("Web Server started!");
  Serial.printf("Connect to WiFi '%s' and open http://%s\n", ap_ssid, IP.toString().c_str());
}

// Connect to WiFi using stored credentials
bool connectToWiFi() {
  Serial.println("\n=== Connecting to WiFi ===");
  Serial.printf("SSID: %s\n", stored_ssid.c_str());

  WiFi.mode(WIFI_STA);
  WiFi.begin(stored_ssid.c_str(), stored_password.c_str());

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi!");
    Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
    return true;
  } else {
    Serial.println("\nFailed to connect!");
    return false;
  }
}

// Clear saved WiFi credentials (call this to reset)
void clearWiFiCredentials() {
  preferences.begin("wifi", false);
  preferences.clear();
  preferences.end();
  Serial.println("WiFi credentials cleared!");
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  delay(1000);
  
  Serial.println();
  Serial.println("ESP32 Starting...");
  Serial.println("\n========================================");
  Serial.println("   ESP32 WiFi Manager with Preferences");
  Serial.println("========================================");

  // === DOUBLE RESET DETECTION ===
  // Nhấn nút RESET 2 lần trong 3 giây để xóa WiFi
  preferences.begin("system", false);
  bool resetFlag = preferences.getBool(RESET_FLAG_KEY, false);
  
  if (resetFlag) {
    // Lần reset thứ 2 - Xóa WiFi!
    Serial.println("\n*** DOUBLE RESET DETECTED! ***");
    Serial.println("Clearing WiFi credentials...");
    preferences.putBool(RESET_FLAG_KEY, false);
    preferences.end();
    
    clearWiFiCredentials();
    
    Serial.println("WiFi cleared! Restarting...");
    delay(1000);
    ESP.restart();
  } else {
    // Lần reset thứ 1 - Đặt cờ và chờ
    preferences.putBool(RESET_FLAG_KEY, true);
    preferences.end();
    
    Serial.println("Press RESET again within 3 seconds to clear WiFi...");
    delay(RESET_TIMEOUT);
    
    // Hết thời gian chờ - Xóa cờ
    preferences.begin("system", false);
    preferences.putBool(RESET_FLAG_KEY, false);
    preferences.end();
    Serial.println("Continuing normal boot...");
  }

  // Load WiFi credentials from Preferences
  preferences.begin("wifi", true); // Read-only mode
  stored_ssid = preferences.getString("ssid", "");
  stored_password = preferences.getString("password", "");
  preferences.end();

  Serial.printf("Stored SSID: %s\n", stored_ssid.c_str());

  // Check if SSID is saved
  if (stored_ssid.length() == 0) {
    Serial.println("No SSID saved. Starting AP mode...");
    startAPMode();
  } else {
    Serial.println("SSID found. Attempting to connect...");
    if (!connectToWiFi()) {
      Serial.println("Connection failed. Starting AP mode...");
      startAPMode();
    }
  }
}

void loop() {
  // If in AP mode, handle web server
  if (isAPMode) {
    server.handleClient();
    return;
  }

  // Normal operation mode - WiFi connected
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi is connected. Running normal operation...");
    // Thêm code xử lý của bạn ở đây
  } else {
    Serial.println("WiFi Disconnected! Reconnecting...");
    WiFi.begin(stored_ssid.c_str(), stored_password.c_str());
  }

  delay(5000);
}
