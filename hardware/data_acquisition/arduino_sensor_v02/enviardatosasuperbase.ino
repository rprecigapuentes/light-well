#include <Wire.h>
#include "Adafruit_AS726x.h"
#include <BH1750.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// ========= CONFIGURE THIS =========
// Replace these values with your own credentials before flashing.
// Never commit real credentials to version control.
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

const char* SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co";
// NOTE: path only — do NOT include the domain here
const char* SUPABASE_TABLE_ENDPOINT = "/rest/v1/mediciones";

const char* SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY";
// ==================================

Adafruit_AS726x ams;
BH1750 lightMeter;
uint16_t sensorValues[AS726x_NUM_CHANNELS];

WiFiClientSecure client;
HTTPClient https;

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 60) { // ~15 seconds
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi.");
  }
}

void sendToSupabase(int violet, int blue, int green, int yellow,
                    int orange, int red, float lux) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, skipping Supabase upload.");
    return;
  }

  client.setInsecure(); // skips TLS certificate validation (simple but less secure)

  String url = String(SUPABASE_URL) + SUPABASE_TABLE_ENDPOINT;
  Serial.print("Supabase URL: ");
  Serial.println(url);

  if (!https.begin(client, url)) {
    Serial.println("Error starting HTTPS (https.begin failed).");
    return;
  }

  https.addHeader("Content-Type", "application/json");
  https.addHeader("apikey", SUPABASE_ANON_KEY);
  https.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
  https.addHeader("Prefer", "return=minimal");

  String body = "{";
  body += "\"violet\":" + String(violet) + ",";
  body += "\"blue\":"   + String(blue) + ",";
  body += "\"green\":"  + String(green) + ",";
  body += "\"yellow\":" + String(yellow) + ",";
  body += "\"orange\":" + String(orange) + ",";
  body += "\"red\":"    + String(red) + ",";
  body += "\"lux\":"    + String(lux, 2);
  body += "}";

  Serial.print("Sending to Supabase: ");
  Serial.println(body);

  int httpCode = https.POST(body);
  Serial.print("HTTP Code: ");
  Serial.println(httpCode);

  if (httpCode < 0) {
    Serial.print("POST error: ");
    Serial.println(https.errorToString(httpCode));
  }

  https.end();
}

void setup() {
  Serial.begin(115200);
  delay(2000); // short delay to allow the serial monitor to open
  Serial.println("Starting up...");

  Wire.begin();

  connectWiFi();

  if (!ams.begin()) {
    Serial.println("Error: AS7262 sensor not found.");
    while (1) { delay(1000); }
  }

  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Error: BH1750 sensor failed to initialize.");
    while (1) { delay(1000); }
  }

  Serial.println("AS7262 and BH1750 initialized.");
}

void loop() {
  // ---- AS7262 ----
  uint8_t temp = ams.readTemperature();
  ams.startMeasurement();
  while (!ams.dataReady()) {
    delay(5);
  }
  ams.readRawValues(sensorValues);

  int violet = sensorValues[AS726x_VIOLET];
  int blue   = sensorValues[AS726x_BLUE];
  int green  = sensorValues[AS726x_GREEN];
  int yellow = sensorValues[AS726x_YELLOW];
  int orange = sensorValues[AS726x_ORANGE];
  int red    = sensorValues[AS726x_RED];

  // ---- BH1750 ----
  float lux = lightMeter.readLightLevel();

  // ---- Serial output ----
  Serial.println("==== Reading ====");
  Serial.print("Temp AS7262: "); Serial.print(temp); Serial.println(" C");
  Serial.print("Violet: "); Serial.print(violet);
  Serial.print(" Blue: ");  Serial.print(blue);
  Serial.print(" Green: "); Serial.print(green);
  Serial.print(" Yellow: ");Serial.print(yellow);
  Serial.print(" Orange: ");Serial.print(orange);
  Serial.print(" Red: ");   Serial.print(red);
  Serial.println();
  Serial.print("BH1750 lux: "); Serial.print(lux); Serial.println(" lx");
  Serial.println();

  // ---- Upload to Supabase ----
  sendToSupabase(violet, blue, green, yellow, orange, red, lux);

  delay(5000); // sample every 5 seconds
}
