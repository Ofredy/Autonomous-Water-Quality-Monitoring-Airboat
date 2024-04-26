/*
 * arduino_function.cpp
 *
 *  Created on: Jan 8, 2024
 *      Author: danie
 */
#include "cpp_header.h"
#include "Arduino.h"
#include "DFRobot_ESP_PH.h"
#include "EEPROM.h"



 //PH Variables
DFRobot_ESP_PH ph;
#define ESPADC 4096.0   //the esp Analog Digital Conversion value
#define ESPVOLTAGE 3300 //the esp voltage supply value
#define PH_PIN 34		//the esp gpio data pin number
float voltage = 25;

//Turbidity variable
int sensorPin = 39;  //36 FOR ESP

//TDS variables
#define TdsSensorPin 33
#define VREF 5             // analog reference voltage(Volt) of the ADC
#define SCOUNT  30            // sum of sample point
int analogBuffer[SCOUNT];     // store the analog value in the array, read from ADC
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;
int copyIndex = 0;
float averageVoltage = 0;
float tdsValue = 0;



// median filtering algorithm for TDS sensor
int getMedianNum(int bArray[], int iFilterLen) {
    int bTab[iFilterLen];
    for (byte i = 0; i < iFilterLen; i++)
        bTab[i] = bArray[i];
    int i, j, bTemp;
    for (j = 0; j < iFilterLen - 1; j++) {
        for (i = 0; i < iFilterLen - j - 1; i++) {
            if (bTab[i] > bTab[i + 1]) {
                bTemp = bTab[i];
                bTab[i] = bTab[i + 1];
                bTab[i + 1] = bTemp;
            }
        }
    }
    if ((iFilterLen & 1) > 0) {
        bTemp = bTab[(iFilterLen - 1) / 2];
    }
    else {
        bTemp = (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
    }
    return bTemp;
}
int getMeanNum(int bArray[], int iFilterLen) {
    int sum = 0;
    for (byte i = 0; i < iFilterLen; i++) {
        sum += bArray[i];
    }
    return sum / iFilterLen;
}

extern "C" void TDS_setup_function();
void TDS_setup_function() {
    Serial.begin(115200);
    pinMode(TdsSensorPin, INPUT);
}
extern "C" float TDS_function(float temperature);
float TDS_function(float temperature) {
    // TDS sensor
    int sensorValue = analogRead(TdsSensorPin);
    static int analogBuffer[SCOUNT] = {0};
    static int analogBufferIndex = 0;
    static float averageVoltage = 0.0;
    static float tdsValue = 0.0;

    // Store the sensor value in the buffer
//    analogBuffer[analogBufferIndex] = sensorValue;
//    analogBufferIndex = (analogBufferIndex + 1) % SCOUNT; // Circular buffer index update

    // Calculate average voltage from the buffer
    float sum = 0.0;
    for (int i = 0; i < SCOUNT; i++) {
    	analogBuffer[i] = analogRead(TdsSensorPin);
       sum += analogBuffer[i];
    }
    //averageVoltage = getMedianNum(analogBuffer, SCOUNT) * (float)VREF / 4096.0;
  averageVoltage = (sum / SCOUNT) * (float)VREF / 4096.0;

    // Temperature compensation formula: fFinalResult(25^C) = fFinalResult(current)/(1.0+0.02*(fTP-25.0))
    float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);

    // Temperature compensation
    float compensatedVoltage = averageVoltage / compensationCoefficient;

    // Convert voltage to TDS value
    tdsValue = (133.42 * compensatedVoltage * compensatedVoltage * compensatedVoltage - 255.86 * compensatedVoltage * compensatedVoltage + 857.39 * compensatedVoltage) * 0.5;

    return tdsValue;
}


extern "C" void PH_setup_function();
void PH_setup_function() {
    Serial.begin(115200);
    EEPROM.begin(32);//needed to permit storage of calibration value in eeprom
    ph.begin();
}
extern "C" float PH_function(float temperature);
float PH_function(float temperature) {
    //PH sensor
    static unsigned long timepoint = millis();
    if (millis() - timepoint > 1000U) //time interval: 1s
    {
        timepoint = millis();
        //voltage = rawPinValue / esp32ADC * esp32Vin
        voltage = analogRead(PH_PIN) / ESPADC * ESPVOLTAGE; // read the voltage
//        Serial.print("voltage:");
//        Serial.println(voltage, 4);
//
//
//        Serial.print("temperature:");
//        Serial.print(temperature, 1);
//        Serial.println("^C");

        phValue = ph.readPH(voltage, temperature); // convert voltage to pH with temperature compensation
//        Serial.print("pH:");
//        Serial.println(phValue, 4);
    }
    ph.calibration(voltage, temperature); // calibration process by Serail CMD
    return phValue;
}
extern "C" void Turbidity_setup_function();
void Turbidity_setup_function() {
    Serial.begin(115200);
}
extern "C" float Turbidity_function();
float Turbidity_function() {

    //Turbidity sensor
    int sensorValue = analogRead(sensorPin);
//    Serial.println(sensorValue);
    turbidity = map(sensorValue, 0, 4095, 100, 0);
//    Serial.println(turbidity);
    return turbidity;

}





