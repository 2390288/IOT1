import json
import time
import paho.mqtt.client as mqtt

DEVICE_ID = "5c690fa7-742f-4df3-b109-7425653aeb50"
client_telemetry_topic = DEVICE_ID + '/telemetry'
server_command_topic = DEVICE_ID + '/commands'  # Added
client_name = DEVICE_ID + '_temperature_server'

mqtt_client = mqtt.Client(
    client_id=client_name,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

mqtt_client.connect('test.mosquitto.org')
mqtt_client.loop_start()

def handle_telemetry(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        print(f"Message received: {payload}")
        
        # Added command logic
        command = {'led_on': payload['temperature'] > 25}  # Fixed key name
        print(f"Sending command: {command}")
        mqtt_client.publish(server_command_topic, json.dumps(command))
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")

mqtt_client.subscribe(client_telemetry_topic)
mqtt_client.on_message = handle_telemetry

try:
    print(f"Server listening on {client_telemetry_topic}")
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    mqtt_client.disconnect()
    mqtt_client.loop_stop()
    print("\nServer stopped gracefully")