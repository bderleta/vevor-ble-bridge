# Vevor BLE Bridge
# 2024 Bartosz Derleta <bartosz@derleta.com>

import os
from bluepy.btle import Peripheral, DefaultDelegate, Scanner
import threading
import time
import random
import math
import struct
import sys


def _u8tonumber(e):
    return (e + 256) if (e < 0) else e


def _UnsignToSign(e):
    if e > 32767.5:
        e = e | -65536
    return e


class _DieselHeaterNotification:
    _error_strings = (
        "No fault",
        "Startup failure",
        "Lack of fuel",
        "Supply voltage overrun",
        "Outlet sensor fault",
        "Inlet sensor fault",
        "Pulse pump fault",
        "Fan fault",
        "Ignition unit fault",
        "Overheating",
        "Overheat sensor fault",
    )
    _error_strings_alt = (
        "No fault",
        "Supply voltage overrun",
        None,
        "Ignition unit fault",
        "Pulse pump fault",
        "Overheating",
        "Fan fault",
        None,
        "Lack of fuel",
        "Overheat sensor fault",
        "Startup failure",
    )
    _running_step_strings = (
        "Standby",  # "Heating", # Stand-by
        "Self-test",  # "Run Self-test", # Self-test
        "Ignition",  # "Ignition Preparation", # Ignition
        "Running",  # "Stable Combustion", # Running
        "Cooldown",  # "Shutdown Cooling" # Cooldown
    )

    def __init__(self, je):
        # print("< " + je.hex(' ', 1))
        fb = _u8tonumber(je[0])
        sb = _u8tonumber(je[1])
        if (170 == fb) and (85 == sb):
            self.running_state = _u8tonumber(je[3])  # Is running at all?
            self.error = _u8tonumber(je[4])
            self.error_msg = self._error_strings[self.error]
            self.running_step = _u8tonumber(je[5])  # Detailed state when running
            self.running_step_msg = self._running_step_strings[self.running_step]
            self.altitude = _u8tonumber(je[6]) + 256 * _u8tonumber(je[7])
            self.running_mode = _u8tonumber(je[8])  # Temperature / Level mode
            match self.running_mode:
                case 0:
                    self.set_level = _u8tonumber(je[10]) + 1
                    self.set_temperature = None
                case 1:
                    self.set_level = _u8tonumber(je[9])
                    self.set_temperature = None
                case 2:
                    self.set_temperature = _u8tonumber(je[9])
                    self.set_level = _u8tonumber(je[10]) + 1
                case _:
                    raise RuntimeError("Unrecognized running mode")
            self.supply_voltage = (256 * _u8tonumber(je[12]) + _u8tonumber(je[11])) / 10
            self.case_temperature = _UnsignToSign(256 * je[14] + je[13])
            self.cab_temperature = _UnsignToSign(256 * je[16] + je[15])
            self.md = 1
        elif (170 == fb) and (102 == sb):
            self.running_state = _u8tonumber(je[3])
            self.error = _u8tonumber(je[17])
            self.error_msg = self._error_strings_alt[self.error]
            self.running_step = _u8tonumber(je[5])
            self.running_step_msg = self._running_step_strings[self.running_step]
            self.altitude = _u8tonumber(je[6]) + 256 * _u8tonumber(je[7])
            self.running_mode = _u8tonumber(je[8])
            match self.running_mode:
                case 0:
                    self.set_level = _u8tonumber(je[10]) + 1
                    self.set_temperature = None
                case 1:
                    self.set_level = _u8tonumber(je[9])
                    self.set_temperature = None
                case 2:
                    self.set_temperature = _u8tonumber(je[9])
                    self.set_level = _u8tonumber(je[10]) + 1
                case _:
                    raise RuntimeError("Unrecognized running mode")
            self.supply_voltage = (256 * _u8tonumber(je[12]) + _u8tonumber(je[11])) / 10
            self.case_temperature = _UnsignToSign(256 * je[14] + je[13])
            self.cab_temperature = _UnsignToSign(256 * je[16] + je[15])
            self.md = 3
        elif (170 == fb) and (136 == sb):
            raise RuntimeError("Unsupported payload (todo)")
        else:
            raise RuntimeError("Unrecognized payload")

    def data(self):
        return vars(self)


class _DieselHeaterDelegate(DefaultDelegate):
    def __init__(self, parent):
        self.parent = parent

    def handleNotification(self, cHandle, data):
        self.parent._last_notification = _DieselHeaterNotification(data)


class DieselHeater:
    _service_uuid = "0000ffe0-0000-1000-8000-00805f9b34fb"
    _characteristic_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"
    _last_notification = None

    def __init__(self, mac_address: str, passkey: int):
        self.mac_address = mac_address
        self.passkey = passkey
        self.peripheral = Peripheral(mac_address, "public")
        self.service = self.peripheral.getServiceByUUID(self._service_uuid)
        if self.service is None:
            raise RuntimeError("Requested service is not supported by peripheral")
        self.characteristic = self.service.getCharacteristics(
            self._characteristic_uuid
        )[0]
        if self.characteristic is None:
            raise RuntimeError("Requested characteristic is not supported by service")
        self.peripheral.setDelegate(_DieselHeaterDelegate(self))

    def _send_command(self, command: int, argument: int, n: int):
        o = bytearray([0xAA, n % 256, 0, 0, 0, 0, 0, 0])
        if 136 == n:
            o[2] = random.randint(0, 255)
            o[3] = random.randint(0, 255)
        else:  # 85
            o[2] = math.floor(self.passkey / 100)
            o[3] = self.passkey % 100
        o[4] = command % 256
        o[5] = argument % 256
        o[6] = math.floor(argument / 256)
        o[7] = o[2] + o[3] + o[4] + o[5] + o[6]
        # print("> " + o.hex(' ', 1))
        self._last_notification = None
        response = self.characteristic.write(
            o, withResponse=True
        )  # returns sth like "{'rsp': ['wr']}"
        if self.peripheral.waitForNotifications(1) and self._last_notification:
            return self._last_notification
        return None

    def get_status(self):
        # todo: mode 136
        return self._send_command(1, 0, 85)

    def start(self):
        return self._send_command(3, 1, 85)

    def stop(self):
        return self._send_command(3, 0, 85)

    def set_level(self, level):
        if (level < 1) or (level > 36):
            raise RuntimeError("Invalid level")
        return self._send_command(4, level, 85)
        
    def set_mode(self, mode):
        if (mode < 1) or (mode > 2):
            raise RuntimeError("Invalid mode")
        return self._send_command(2, mode, 85)    
