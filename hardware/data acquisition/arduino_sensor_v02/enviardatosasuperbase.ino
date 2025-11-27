#include <Wire.h>
#include "Adafruit_AS726x.h"
#include <BH1750.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// ========= CONFIGURA ESTO =========
const char* WIFI_SSID = "ale";
const char* WIFI_PASS = "123456789M";

const char* SUPABASE_URL = "https://lghcnblipkdoghwnhcsg.supabase.co";
// OJO: solo el path, NO vuelvas a poner el dominio aquí
const char* SUPABASE_TABLE_ENDPOINT = "/rest/v1/mediciones";

const char* SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxnaGNuYmxpcGtkb2dod25oY3NnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0MDE0NjQsImV4cCI6MjA3ODk3NzQ2NH0.h3sNqYooXOMx4l7kgL0bvpc42YcCZ4WrCNf28CxEJsA";
// ==================================

Adafruit_AS726x ams;
BH1750 lightMeter;
uint16_t sensorValues[AS726x_NUM_CHANNELS];

WiFiClientSecure client;
HTTPClient https;

void conectarWiFi() {
  Serial.print("Conectando a WiFi: ");
  Serial.println(WIFI_SSID);
WiFi.begin(WIFI_SSID, WIFI_PASS);
  WiFi.begin(WIFI_SSID);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 60) { // ~15 segundos
    delay(500);
    Serial.print(".");
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado.");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nNo se pudo conectar a WiFi.");
  }
}

void sendToSupabase(int violet, int blue, int green, int yellow,
                    int orange, int red, float lux) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado, no se envía a Supabase.");
    return;
  }

  client.setInsecure(); // NO valida certificado (simple, pero menos seguro)

  String url = String(SUPABASE_URL) + SUPABASE_TABLE_ENDPOINT;
  Serial.print("URL Supabase: ");
  Serial.println(url);

  if (!https.begin(client, url)) {
    Serial.println("Error iniciando HTTPS (https.begin falló).");
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

  Serial.print("Enviando a Supabase: ");
  Serial.println(body);

  int httpCode = https.POST(body);
  Serial.print("HTTP Code: ");
  Serial.println(httpCode);

  if (httpCode < 0) {
    Serial.print("Error en POST: ");
    Serial.println(https.errorToString(httpCode));
  }

  https.end();
}

void setup() {
  Serial.begin(115200);
  delay(2000); // pequeño delay para que dé tiempo a abrir el monitor
  Serial.println("Iniciando...");

  Wire.begin();

  conectarWiFi();

  if (!ams.begin()) {
    Serial.println("Error: no se pudo encontrar el AS7262.");
    while (1) { delay(1000); }
  }

  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Error: no se pudo iniciar el BH1750.");
    while (1) { delay(1000); }
  }

  Serial.println("AS7262 y BH1750 inicializados.");
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

  // ---- Serial para ver ----
  Serial.println("==== Lectura ====");
  Serial.print("Temp AS7262: "); Serial.print(temp); Serial.println(" °C");
  Serial.print("Violet: "); Serial.print(violet);
  Serial.print(" Blue: ");  Serial.print(blue);
  Serial.print(" Green: "); Serial.print(green);
  Serial.print(" Yellow: ");Serial.print(yellow);
  Serial.print(" Orange: ");Serial.print(orange);
  Serial.print(" Red: ");   Serial.print(red);
  Serial.println();
  Serial.print("Luz BH1750: "); Serial.print(lux); Serial.println(" lx");
  Serial.println();

  // ---- Enviar a Supabase ----
  sendToSupabase(violet, blue, green, yellow, orange, red, lux);

  delay(5000); // cada 5 segundos
}

