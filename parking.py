import time
import struct
import threading
from bluepy import btle
import RPi.GPIO as GPIO
import sys

# Define GPIO pins for the LED and buzzer
LED_PIN = 27
BUZZER_PIN = 17

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

def cleanup_pins():
    GPIO.cleanup([LED_PIN, BUZZER_PIN])

class CustomNotificationHandler(btle.DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleNotification(self, cHandle, data):
        try:
            distance = struct.unpack('f', data)[0]
            print(f"Notification received: {distance} cm")
            interval = calculate_interval(distance)
            print(f"Calculated Interval: {interval}; Distance: {distance}")
            led_controller.update_interval(interval)
        except Exception as e:
            print(f"Notification handling error: {e}")

class LEDController:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self.blink_interval = None

    def _run(self):
        while not self._stop_event.is_set():
            if self.blink_interval is None:
                set_led_state(False)
                set_buzzer_state(False)
                time.sleep(0.1)
            else:
                set_led_state(True)
                set_buzzer_state(True)
                time.sleep(self.blink_interval)
                set_led_state(False)
                set_buzzer_state(False)
                time.sleep(self.blink_interval)

    def start(self):
        if not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def update_interval(self, interval):
        self.blink_interval = interval

def set_led_state(state):
    GPIO.output(LED_PIN, state)

def set_buzzer_state(state):
    GPIO.output(BUZZER_PIN, state)

def calculate_interval(distance):
    if distance < 0:
        return None
    if distance < 5:
        return 0.2
    if distance < 10:
        return 0.5
    if distance < 15:
        return 1.0
    return 2.0

def connect_to_device(device_address):
    print(f"Attempting to connect to {device_address}...")
    try:
        peripheral = btle.Peripheral(device_address)
        peripheral.setDelegate(CustomNotificationHandler())
        print("Connection established.")
        return peripheral
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def receive_data(peripheral):
    try:
        print("Waiting for notifications...")

        service_uuid = btle.UUID("6009359F-DF49-450E-B855-ABD71B8E44C3")
        characteristic_uuid = btle.UUID("4CDBA726-4187-4827-BADB-28EA8F906DD2")

        service = peripheral.getServiceByUUID(service_uuid)
        characteristic = service.getCharacteristics(characteristic_uuid)[0]

        setup_data = b"\x01\x00"
        peripheral.writeCharacteristic(characteristic.getHandle() + 1, setup_data, withResponse=True)

        while True:
            if peripheral.waitForNotifications(1.0):
                continue
            print("No notifications. Waiting...")
    except btle.BTLEDisconnectError as e:
        set_led_state(False)
        set_buzzer_state(False)
        print(f"Disconnected from device: {e}")
        print("Reconnecting in 5 seconds...")
        time.sleep(5)
        return None

if __name__ == "__main__":
    try:
        led_controller = LEDController()
        led_controller.start()
        
        # Device address can be passed as a command-line argument
        if len(sys.argv) > 1:
            device_address = sys.argv[1]
        else:
            print("Usage: python script.py <device_address>")
            sys.exit(1)

        peripheral = connect_to_device(device_address)
        if peripheral:
            receive_data(peripheral)
    finally:
        cleanup_pins()
        led_controller.stop()
