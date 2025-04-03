# -*- coding: utf-8 -*-
import os
import glob
import time
import paho.mqtt.client as mqtt
import json
from gpiozero import LED

DEVICE_ID = "5c690fa7-742f-4df3-b109-7425653aeb50"  
client_name = DEVICE_ID + '_temperature_client'
client_telemetry_topic = DEVICE_ID + '/telemetry'
server_command_topic = DEVICE_ID + '/commands'

# LED setup (assuming green LED on GPIO17)
led = LED(17)

# MQTT Client Setup
mqtt_client = mqtt.Client(client_name)
mqtt_client.connect('test.mosquitto.org')
mqtt_client.loop_start()
print("MQTT connected!")

# DS18B20 Sensor Setup
device_file = None

def sensor_setup():
    global device_file
    os.system('sudo modprobe w1-gpio')
    os.system('sudo modprobe w1-therm')
    
    base_dir = '/sys/bus/w1/devices/'
    device_folders = glob.glob(base_dir + '28*')
    
    if not device_folders:
        raise Exception("DS18B20 sensor not found")
    
    device_folder = device_folders[0]
    device_file = device_folder + '/w1_slave'

def read_temp_raw():
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        return lines
    except Exception as e:
        print(f"Read error: {e}")
        return []

def read_temperature():
    lines = read_temp_raw()
    while not lines or 'YES' not in lines[0]:
        time.sleep(0.2)
        lines = read_temp_raw()
    
    temp_pos = lines[1].find('t=')
    if temp_pos != -1:
        temp_str = lines[1][temp_pos+2:]
        temp_c = float(temp_str) / 1000.0
        return round(temp_c, 2)

def handle_command(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        print(f"Command received: {payload}")
        if payload['led_on']:
            led.on()
        else:
            led.off()
    except Exception as e:
        print(f"Command error: {str(e)}")

# Subscribe to commands
mqtt_client.subscribe(server_command_topic)
mqtt_client.on_message = handle_command

try:
    sensor_setup()
    print("Temperature monitoring started. Press Ctrl+C to exit")
    
    while True:
        try:
            temp_c = read_temperature()
            print(f"Current temperature: {temp_c}\u00b0C")
            
            # Publish telemetry ONLY
            telemetry = {'temperature': temp_c}
            mqtt_client.publish(client_telemetry_topic, json.dumps(telemetry))
            
            time.sleep(3)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            time.sleep(5)

except KeyboardInterrupt:
    led.off()
    mqtt_client.loop_stop()
    print("\nProgram terminated")

except Exception as e:
    print(f"Fatal error: {str(e)}")
    led.off()
    mqtt_client.loop_stop()
