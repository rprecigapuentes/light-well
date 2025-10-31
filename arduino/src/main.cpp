/***************************************************************************
  Combined AS7262 + BH1750 Logger
  - Reads 6 spectral channels (AS7262)
  - Reads ambient light in lux (BH1750)
  - Outputs raw CSV line for each measurement

  CSV order:
  temp, violet, blue, green, yellow, orange, red, lux
***************************************************************************/

#include <Wire.h>
#include "Adafruit_AS726x.h"
#include <BH1750.h>

// Create sensor objects
Adafruit_AS726x as7262;
BH1750 lightMeter(0x23);  // default address (ADDR pin to GND)

// Buffer to hold AS7262 raw values
uint16_t sensorValues[AS726x_NUM_CHANNELS];

void setup() {
  Serial.begin(115200);
  while(!Serial);

  // Initialize I2C
  Wire.begin();  // A4 = SDA, A5 = SCL on Arduino Uno

  pinMode(LED_BUILTIN, OUTPUT);

  // Initialize AS7262
  if(!as7262.begin()){
    Serial.println("Error: could not connect to AS7262 (check wiring).");
    while(1);
  }

  // Initialize BH1750 in continuous high-res mode
  if(lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)){
    Serial.println("BH1750 ready");
  } else {
    Serial.println("Error: could not initialize BH1750 (check wiring).");
    while(1);
  }

  Serial.println("Sensors initialized. Starting measurements...");
}

void loop() {
  // Start AS7262 measurement
  as7262.startMeasurement();

  // Wait until data ready
  while(!as7262.dataReady()){
    delay(5);
  }

  // Read AS7262 raw channels
  as7262.readRawValues(sensorValues);

  // Read AS7262 temperature (°C)
  uint8_t temp = as7262.readTemperature();

  // Read BH1750 light (lux)
  float lux = lightMeter.readLightLevel();

  // Print CSV line: temp, violet, blue, green, yellow, orange, red, lux
  Serial.print(temp); Serial.print(",");
  Serial.print(sensorValues[AS726x_VIOLET]); Serial.print(",");
  Serial.print(sensorValues[AS726x_BLUE]); Serial.print(",");
  Serial.print(sensorValues[AS726x_GREEN]); Serial.print(",");
  Serial.print(sensorValues[AS726x_YELLOW]); Serial.print(",");
  Serial.print(sensorValues[AS726x_ORANGE]); Serial.print(",");
  Serial.print(sensorValues[AS726x_RED]); Serial.print(",");
  Serial.println(lux, 2);  // print with 2 decimal places

  delay(1000); // wait 1 second between measurements
}
