#include <ArduinoBLE.h>

// Define UUIDs for the BLE service and characteristic
#define SERVICE_UUID "6009359F-DF49-450E-B855-ABD71B8E44C3"
#define CHARACTERISTIC_UUID "4CDBA726-4187-4827-BADB-28EA8F906DD2"

// Ultrasonic sensor pins
const int triggerPin = 7;
const int echoPin = 6;

// BLE Service and Characteristic
BLEService parkingService(SERVICE_UUID);
BLEFloatCharacteristic distanceCharacteristic(CHARACTERISTIC_UUID, BLERead | BLENotify);

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for the serial monitor to open

  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);

  if (!initializeBLE()) {
    Serial.println("Failed to initialize BLE!");
    while (1);
  }

  Serial.println("BLE ready and waiting for connection...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    while (central.connected()) {
      float distance = measureDistance();
      distanceCharacteristic.writeValue(distance);
      Serial.print("Measured distance: ");
      Serial.println(distance);
      delay(1000); // Adjust delay as needed
    }

    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}

bool initializeBLE() {
  if (!BLE.begin()) {
    return false;
  }

  BLE.setLocalName("ParkingSensor");
  BLE.setAdvertisedService(parkingService);
  parkingService.addCharacteristic(distanceCharacteristic);
  BLE.addService(parkingService);
  BLE.advertise();

  return true;
}

float measureDistance() {
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;
  return distance;
}
