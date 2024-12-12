#include "HX711.h"
#include <Preferences.h>

constexpr uint8_t pinData  = 2;
constexpr uint8_t pinClock = 18;

HX711 loadcell;

float conversionFactor;
float calibratedForce;

Preferences preferences;

constexpr int numReadings = 10;
float readings[numReadings] = {0};
int readIndex = 0;
float total = 0;
float average = 0;
constexpr float alpha = 0.94;
float lastValidForce = 0;

bool isCalibrated = false;

void setup() {
  Serial.begin(115200);

  loadcell.begin(pinData, pinClock);
  loadcell.tare();
  preferences.begin("HX711", false);
  conversionFactor = preferences.getFloat("conversionFactor", 1.0);
  calibratedForce = preferences.getFloat("calibratedForce", 0.0);

  if (fabs(conversionFactor) < 1E-10) {
    conversionFactor = 1.0;
    preferences.putFloat("conversionFactor", conversionFactor);
  }

  loadcell.set_scale(conversionFactor);

  // Verifica se a calibração foi salva
  if (calibratedForce != 0.0) {
    isCalibrated = true;
    lastValidForce = calibratedForce;
  }
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 's') {
      conversionFactor = Serial.parseFloat();
      loadcell.set_scale(conversionFactor);
      preferences.putFloat("conversionFactor", conversionFactor);
      isCalibrated = true;
      saveCalibrationForce();
    }

    if (cmd == 'g') {
      Serial.print("<2,");
      Serial.print(loadcell.get_scale(), 5);
      Serial.println(">");
    }
  }

  float time = millis() * 1E-3;
  float force = -loadcell.get_units(2);

  total -= readings[readIndex];
  readings[readIndex] = force;
  total += readings[readIndex];
  readIndex = (readIndex + 1) % numReadings;

  average = total / numReadings;
  float smoothedForce = alpha * force + (1.0 - alpha) * lastValidForce;

  if (abs(force - average) > 0.1) {
    smoothedForce = force;
  }

  if (abs(smoothedForce - lastValidForce) > 0.100) {
    lastValidForce = smoothedForce;
  }

  if (isCalibrated && lastValidForce < 0) {
    lastValidForce = 0;
  }

  Serial.print("<1,");
  Serial.print(time, 3);
  Serial.print(",");
  Serial.print(lastValidForce, 4);
  Serial.println(">");

  delay(12);
}

void saveCalibrationForce() {
  preferences.putFloat("calibratedForce", lastValidForce);
}