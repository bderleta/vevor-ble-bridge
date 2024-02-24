# Vevor BLE Bridge
# 2024 Bartosz Derleta <bartosz@derleta.com>

import paho.mqtt.client as mqtt
import logging
import platform
import json
import time
import vevor
import os

# = Configuration
# == BLE bridge
ble_mac_address = os.environ["BLE_MAC_ADDRESS"]
ble_passkey = int(os.environ["BLE_PASSKEY"]) if os.environ.get("BLE_PASSKEY") else 1234
ble_poll_interval = (
    int(os.environ["BLE_POLL_INTERVAL"]) if os.environ.get("BLE_POLL_INTERVAL") else 2
)
# == Device
device_name = os.environ["DEVICE_NAME"]
device_manufacturer = (
    os.environ["DEVICE_MANUFACTURER"]
    if os.environ.get("DEVICE_MANUFACTURER")
    else "Vevor"
)
device_model = os.environ["DEVICE_MODEL"]
device_id = "BYD-" + ble_mac_address.replace(":", "").upper()  # auto
via_device = platform.uname()[1]  # auto
# == MQTT
mqtt_host = os.environ["MQTT_HOST"] if os.environ.get("MQTT_HOST") else "127.0.0.1"
mqtt_username = os.environ.get("MQTT_USERNAME")
mqtt_password = os.environ.get("MQTT_PASSWORD")
mqtt_port = int(os.environ["MQTT_PORT"]) if os.environ.get("MQTT_PORT") else 1883
mqtt_discovery_prefix = (
    os.environ["MQTT_DISCOVERY_PREFIX"]
    if os.environ.get("MQTT_DISCOVERY_PREFIX")
    else "homeassistant"
)
mqtt_prefix = f"{os.environ['MQTT_PREFIX']}{device_id}"

client = None
logger = None
vdh = None
run = True


def init_logger():
    logger = logging.getLogger("vevor-ble-bridge")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S %z"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def init_client():
    client = mqtt.Client(client_id=device_id, clean_session=True)
    if mqtt_username and len(mqtt_username) and mqtt_password and len(mqtt_password):
        logger.info(
            f"Connecting to MQTT broker {mqtt_username}@{mqtt_host}:{mqtt_port}"
        )
        client.username_pw_set(mqtt_username, mqtt_password)
    else:
        logger.info(f"Connecting to MQTT broker {mqtt_host}:{mqtt_port}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_host, port=mqtt_port)
    return client


def get_device_conf():
    conf = {
        "name": device_name,
        "identifiers": device_id,
        "manufacturer": device_manufacturer,
        "model": device_id,
        "via_device": via_device,
        "sw": "Vevor-BLE-Bridge",
    }
    return conf


def publish_ha_config():
    start_conf = {
        "device": get_device_conf(),
        "icon": "mdi:radiator",
        "name": "Start",
        "unique_id": f"{device_id}-000",
        "command_topic": f"{mqtt_prefix}/start/cmd",
        "availability_topic": f"{mqtt_prefix}/start/av",
        "enabled_by_default": False,
    }
    client.publish(
        f"{mqtt_discovery_prefix}/button/{device_id}-000/config",
        json.dumps(start_conf),
    )

    stop_conf = {
        "device": get_device_conf(),
        "icon": "mdi:radiator-off",
        "name": "Stop",
        "unique_id": f"{device_id}-001",
        "command_topic": f"{mqtt_prefix}/stop/cmd",
        "availability_topic": f"{mqtt_prefix}/stop/av",
        "enabled_by_default": False,
    }
    client.publish(
        f"{mqtt_discovery_prefix}/button/{device_id}-001/config",
        json.dumps(stop_conf),
    )

    status_conf = {
        "device": get_device_conf(),
        "expire_after": 10,
        "name": "Status",
        "unique_id": f"{device_id}-010",
        "state_topic": f"{mqtt_prefix}/status/state",
    }
    client.publish(
        f"{mqtt_discovery_prefix}/sensor/{device_id}-010/config",
        json.dumps(status_conf),
    )

    room_temperature_conf = {
        "device": get_device_conf(),
        "expire_after": 10,
        "name": "Room temperature",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "icon": "mdi:home-thermometer",
        "unique_id": f"{device_id}-011",
        "state_topic": f"{mqtt_prefix}/room_temperature/state",
    }
    client.publish(
        f"{mqtt_discovery_prefix}/sensor/{device_id}-011/config",
        json.dumps(room_temperature_conf),
    )

    heater_temperature_conf = {
        "device": get_device_conf(),
        "expire_after": 10,
        "name": "Heater temperature",
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "icon": "mdi:thermometer-lines",
        "unique_id": f"{device_id}-012",
        "state_topic": f"{mqtt_prefix}/heater_temperature/state",
    }
    client.publish(
        f"{mqtt_discovery_prefix}/sensor/{device_id}-012/config",
        json.dumps(heater_temperature_conf),
    )

    voltage_conf = {
        "device": get_device_conf(),
        "expire_after": 10,
        "name": "Supply voltage",
        "device_class": "voltage",
        "unit_of_measurement": "V",
        "icon": "mdi:car-battery",
        "unique_id": f"{device_id}-013",
        "state_topic": f"{mqtt_prefix}/voltage/state",
    }
    client.publish(
        f"{mqtt_discovery_prefix}/sensor/{device_id}-013/config",
        json.dumps(voltage_conf),
    )

    altitude_conf = {
        "device": get_device_conf(),
        "expire_after": 10,
        "name": "Altitude",
        "device_class": "distance",
        "unit_of_measurement": "m",
        "icon": "mdi:summit",
        "unique_id": f"{device_id}-014",
        "state_topic": f"{mqtt_prefix}/altitude/state",
    }
    client.publish(
        f"{mqtt_discovery_prefix}/sensor/{device_id}-014/config",
        json.dumps(altitude_conf),
    )

    level_conf = {
        "device": get_device_conf(),
        "name": "Power level",
        "availability_topic": f"{mqtt_prefix}/level/av",
        "command_topic": f"{mqtt_prefix}/level/cmd",
        "state_topic": f"{mqtt_prefix}/level/state",
        "enabled_by_default": False,
        "icon": "mdi:speedometer",
        "unique_id": f"{device_id}-020",
        "min": 1.0,
        "max": 10.0,
        "step": 1.0,
    }
    client.publish(
        f"{mqtt_discovery_prefix}/number/{device_id}-020/config",
        json.dumps(level_conf),
    )


def on_connect(client, userdata, flags, rc):
    global run
    if rc:
        run = False
        raise RuntimeError("Cannot connect to MQTT broker (error %d)" % rc)
    logger.info("Connected to MQTT broker")
    client.subscribe(
        [
            (f"{mqtt_prefix}/start/cmd", 2),
            (f"{mqtt_prefix}/stop/cmd", 2),
            (f"{mqtt_prefix}/level/cmd", 2),
        ]
    )
    publish_ha_config()


def dispatch_result(result):
    stop_pub = False
    start_pub = False
    level_pub = False
    if result:
        logger.debug(str(result.data()))
        msg = result.running_step_msg
        if result.error:
            msg = f"{msg} ({result.error_msg})"
        client.publish(f"{mqtt_prefix}/status/state", msg)
        client.publish(f"{mqtt_prefix}/room_temperature/state", result.cab_temperature)
        if result.running_step:
            client.publish(f"{mqtt_prefix}/voltage/state", result.supply_voltage)
            client.publish(f"{mqtt_prefix}/altitude/state", result.altitude)
            client.publish(
                f"{mqtt_prefix}/heater_temperature/state", result.case_temperature
            )
            if ((result.running_mode == 0) or (result.running_mode == 1)) and (
                result.running_step < 4
            ):
                client.publish(f"{mqtt_prefix}/level/av", "online")
                client.publish(f"{mqtt_prefix}/level/state", result.set_level)
                level_pub = True
            if result.running_step == 3:
                client.publish(f"{mqtt_prefix}/stop/av", "online")
                stop_pub = True
        else:
            client.publish(f"{mqtt_prefix}/start/av", "online")
            start_pub = True
    if not stop_pub:
        client.publish(f"{mqtt_prefix}/stop/av", "offline")
    if not start_pub:
        client.publish(f"{mqtt_prefix}/start/av", "offline")
    if not level_pub:
        client.publish(f"{mqtt_prefix}/level/av", "offline")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if msg.topic == f"{mqtt_prefix}/start/cmd":
        logger.info("Received START command")
        dispatch_result(vdh.start())
    elif msg.topic == f"{mqtt_prefix}/stop/cmd":
        logger.info("Received STOP command")
        dispatch_result(vdh.stop())
    elif msg.topic == f"{mqtt_prefix}/level/cmd":
        logger.info(f"Received LEVEL={int(msg.payload)} command")
        dispatch_result(vdh.set_level(int(msg.payload)))
    logger.debug(f"{msg.topic} {str(msg.payload)}")


logger = init_logger()
client = init_client()
vdh = vevor.DieselHeater(ble_mac_address, ble_passkey)
client.loop_start()

while run:
    result = vdh.get_status()
    dispatch_result(result)
    time.sleep(ble_poll_interval)
