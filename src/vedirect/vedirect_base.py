#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Forked from nznobody at https://github.com/nznobody/vedirect
#
# Forked from karioja at https://github.com/karioja/vedirect
#
# 2019-01-16 JMF Modified for Python 3 and updated protocol from
# https://www.sv-zanshin.com/r/manuals/victron-ve-direct-protocol.pdf
'''
    VEDirectBase
    
    Superclass for all VEDirect classes
    Provides the fundamental constants and parsing logic
    The subclasses have to provide the connectivity and any other data access logic
    
    Current subclasses are
    VEDirect 
        Blocking effort, runs in CPython on RPi etc., uses serial port or open fd
    VEDirectAsyncio
        Smarter class that runs in MicroPython on ESP32 (and others maybe), uses UART

'''

import sys
import logging
from micropython import const

MICROPYTHON = True
log = logging.getLogger(__name__)
from ESPLogRecord import ESPLogRecord
log.record = ESPLogRecord()

def int_base_guess(string_val):
    return int(string_val, 0)


class VEDirectBase:
    encoding = "utf-8"

    error_codes = {
        0: "No error",
        2: "Battery voltage too high",
        17: "Charger temperature too high",
        18: "Charger over current",
        19: "Charger current reversed",
        20: "Bulk time limit exceeded",
        21: "Current sensor issue (sensor bias/sensor broken)",
        26: "Terminals overheated",
        33: "Input voltage too high (solar panel)",
        34: "Input current too high (solar panel)",
        38: "Input shutdown (due to excessive battery voltage)",
        116: "Factory calibration data lost",
        117: "Invalid/incompatible firmware",
        119: "User settings invalid",
    }

    @staticmethod
    def conv_error(code):
        return VEDirectBase.error_codes[int(code)]

    device_state_map = {
        0: "Off",
        1: "Low power",
        2: "Fault",
        3: "Bulk",
        4: "Absorption",
        5: "Float",
        6: "Storage",
        7: "Equalize (manual)",
        9: "Inverting",
        11: "Power supply",
        245: "Starting-up",
        246: "Repeated absorption",
        247: "Auto equalize / Recondition",
        248: "BatterySafe",
        252: "External Control",
    }

    @staticmethod
    def conv_mode(code):
        return VEDirectBase.device_state_map[int(code)]

    cs = {"0": "Off", "2": "Fault", "3": "Bulk", "4": "Abs", "5": "Float"}

    offReasonDecode = {
        0x000: "",
        0x001: "No input power",
        0x002: "Switched off (power switch)",
        0x004: "Switched off (device mode register)",
        0x008: "Remote input",
        0x010: "Protection active",
        0x020: "Paygo",
        0x040: "BMS",
        0x080: "Engine shutdown detection",
        0x100: "Analyzing input voltage",
    }

    capBleDecode = {
        0x001: "BLE supports switching off",
        0x002: "BLE switching off is permanent",
    }

    trackerModeDecode = {
        0x000: "Off",
        0x001: "Voltage or current limited",
        0x002: "MPPT Tracker active",
    }

    alarmReasonDecode = {
        "Low Voltage": 1 << 0,  # 1  0b00000000000001
        "High Voltage": 1 << 1,  # 2  0b00000000000010
        "Low SOC": 1 << 2,  # 4  0b00000000000100
        "Low Starter Voltage": 1 << 3,  # 8  0b00000000001000
        "High Starter Voltage": 1 << 4,  # 16  0b00000000010000
        "Low Temperature": 1 << 5,  # 32  0b00000000100000
        "High Temperature": 1 << 6,  # 64  0b00000001000000
        "Mid Voltage": 1 << 7,  # 128  0b00000010000000
        "Overload": 1 << 8,  # 256  0b00000100000000
        "DC-ripple": 1 << 9,  # 512  0b00001000000000
        "Low V AC out": 1 << 10,  # 1024  0b00010000000000
        "High C AC out": 1 << 11,  # 2048  0b00100000000000
        "Short Circuit": 1 << 12,  # 4096  0b01000000000000
        "BMS Lockout": 1 << 13,  # 8192  0b10000000000000
    }

    @staticmethod
    def lookup(key_int, lookup_list):
        if key_int in lookup_list:
            return lookup_list[key_int]
        else:
            return ""

    values = {
        "LOAD": {"key": "load"},
        "H19": {"key": "yieldTotal", "mx": 0.01},
        "VPV": {"key": "panelVoltage", "mx": 0.001},
        "ERR": {"key": "error", "f": conv_error},
        "FW": {"key": "firmwareVersion", "mx": 0.01},
        "I": {"key": "current", "mx": 0.001},
        "H21": {"key": "maximumPowerToday", "f": int},  # W
        "IL": {"key": "loadCurrent", "mx": 0.001},
        "PID": {"key": "productId"},
        "H20": {"key": "yieldToday", "mx": 0.01},  # kWh
        "H23": {"key": "maximumPowerYesterday", "f": int},  # W
        "H22": {"key": "yieldYesterday", "mx": 0.01},  # kWh
        "HSDS": {"key": "daySequenceNumber", "f": int},
        "SER#": {"key": "serialNumber"},
        "V": {"key": "batteryVoltage", "mx": 0.001},
        "CS": {"key": "mode", "f": conv_mode},
        "PPV": {"key": "panelPower", "f": int},
    }

    divs = {
        "batteries_hdg": ["bmv", "SOC"],
        "batteries_bdy": ["bmv", "V", "I"],
        "solar_hdg": ["mppt", "I"],
        "solar_bdy": ["mppt", "V", "CS", "H20"],
        "vehicle_hdg": ["bmv", "VS"],
        "vehicle_bdy": ["bmv", "Relay"],
        "conv_hdg": ["conv", "I"],
        "conv_bdy": ["conv", "V", "T"],
    }

    units = {
        "V": "mV",
        "V2": "mV",
        "V3": "mV",
        "VS": "mV",
        "VM": "mV",
        "DM": "%",
        "VPV": "mV",
        "PPV": "W",
        "I": "mA",
        "I2": "mA",
        "I3": "mA",
        "IL": "mA",
        "LOAD": "",
        "T": "°C",
        "P": "W",
        "CE": "mAh",
        "SOC": "%",
        "TTG": "Minutes",
        "Alarm": "",
        "Relay": "",
        "AR": "",
        "OR": "",
        "H1": "mAh",
        "H2": "mAh",
        "H3": "mAh",
        "H4": "",
        "H5": "",
        "H6": "mAh",
        "H7": "mV",
        "H8": "mV",
        "H9": "Seconds",
        "H10": "",
        "H11": "",
        "H12": "",
        "H15": "mV",
        "H16": "mV",
        "H17": "0.01 kWh",
        "H18": "0.01 kWh",
        "H19": "0.01 kWh",
        "H20": "0.01 kWh",
        "H21": "W",
        "H22": "0.01 kWh",
        "H23": "W",
        "ERR": "",
        "CS": "*",
        "BMV": "",
        "FW": "",
        "FWE": "",
        "PID": "",
        "SER#": "",
        "HSDS": "",
        "MODE": "",
        "AC_OUT_V": "0.01 V",
        "AC_OUT_I": "0.1 A",
        "AC_OUT_S": "VA",
        "WARN": "",
        "MPPT": "",
    }

    types = {
        "V": int,
        "VS": int,
        "VM": int,
        "DM": int,
        "VPV": int,
        "PPV": int,
        "I": int,
        "IL": int,
        "LOAD": str,
        "T": int,
        "P": int,
        "CE": int,
        "SOC": int,
        "TTG": int,
        "Alarm": str,
        "Relay": str,
        "AR": int_base_guess,
        "OR": int_base_guess,
        "H1": int,
        "H2": int,
        "H3": int,
        "H4": int,
        "H5": int,
        "H6": int,
        "H7": int,
        "H8": int,
        "H9": int,
        "H10": int_base_guess,
        "H11": int_base_guess,
        "H12": int_base_guess,
        "H13": int_base_guess,
        "H14": int_base_guess,
        "H15": int,
        "H16": int,
        "H17": int,
        "H18": int,
        "H19": int,
        "H20": int,
        "H21": int,
        "H22": int,
        "H23": int,
        "ERR": int_base_guess,
        "CS": int_base_guess,
        "BMV": str,
        "FW": str,
        "PID": str,
        "SER#": str,
        "HSDS": int_base_guess,
        "MODE": int_base_guess,
        "AC_OUT_V": int,
        "AC_OUT_I": int,
        "AC_OUT_S": int,
        "WARN": int_base_guess,
        "MPPT": int_base_guess,
    }

    @staticmethod
    def typecast(payload_dict):
        new_dict = {}
        for key, val in payload_dict.items():
            try:
                new_dict[key] = VEDirectBase.types[key](val)
            except KeyError as exc:
                log.warning("Got unknown VE key: {}, skipping...".format(key))
        return new_dict

    fmt = {
        "%": ["%", 10, 1],
        "°C": ["°C", 1, 0],
        "0.01 kWh": ["Wh", 0.1, 2],
        "mA": ["A", 1000, 2],
        "mAh": ["Ah", 1000, 2],
        "Minutes": ["Mins", 1, 0],
        "mV": ["V", 1000, 2],
        "Seconds": ["Secs", 1, 0],
        "W": ["W", 1, 0],
    }

    def __init__(self):
        """
            Constructor for a Victron VEDirect communication parser FSM

        """

        self.header1 = b"\n"
        self.header2 = b"\r"
        self.hexmarker = b":"
        self.delimiter = b"\t"
        self.key = b""
        self.value = b""
        self.bytes_sum = 0
        self.state = self.WAIT_HEADER1
        self.dict = {}

    (HEX, WAIT_HEADER1, IN_KEY, IN_VALUE, IN_CHECKSUM) = range(5)

    def _input(self, byte):
        """Accepts a new byte and tries to finish constructing a record.
        When a record is complete, it will be returned as a dictionary
        """
        log.debug("State: {}, Input: {}".format(self.state, byte))
        if byte == self.hexmarker and self.state != self.IN_CHECKSUM:
            log.debug("Changing to HEX state")
            self.state = self.HEX

        if self.state is not self.HEX:
            self.bytes_sum += ord(byte)
            log.debug("CRC: %d", self.bytes_sum)
            if byte == b"\r":
                # Ignore these, they are optional. Do count towards CRC!
                log.debug("Skipping carriage return")
                return None

        if self.state == self.WAIT_HEADER1:
            if byte == self.header1:
                log.debug("Found header1")
                self.state = self.IN_KEY
            return None
        
        elif self.state == self.IN_KEY:
            if byte == self.delimiter:
                log.debug("Found delimiter")
                if self.key == b"Checksum":
                    log.debug("Found Checksum")
                    self.state = self.IN_CHECKSUM
                else:
                    self.state = self.IN_VALUE
            else:
                self.key += byte
            return None
        
        elif self.state == self.IN_VALUE:
            if byte == self.header1:
                log.debug("Found header1, ending value read")
                try:
                    key = str(self.key.decode(self.encoding))
                    value = str(self.value.decode(self.encoding))
                    log.info("Adding entry %s:%s",key, value)
                    self.dict[key] = value
                except UnicodeError:
                    log.warning(
                        "Could not decode key {} and value {}".format(
                            self.key, self.value
                        )
                    )
                self.key = b""
                self.value = b""
                self.state = self.IN_KEY
            else:
                self.value += byte
            return None
        
        elif self.state == self.IN_CHECKSUM:
            log.debug("Checking checksum... Current %d, CRC %d",
                    self.bytes_sum % 256, ord(byte))
            self.key = b""
            self.value = b""
            self.state = self.WAIT_HEADER1
            if self.bytes_sum % 256 == 0:
                self.bytes_sum = 0
                dict_copy = self.dict.copy()
                self.dict = {}  # clear the holder - ready for a new record
                log.info("Returning record")
                return dict_copy
            else:
                # print('Malformed record')
                log.error(
                    "Malformed record, Remainder: {}".format(self.bytes_sum % 256)
                )
                self.bytes_sum = 0
        
        elif self.state == self.HEX:
            log.warning("_input is in HEX state. Current byte: {}, current value: {}".format(byte, self.value))
            self.bytes_sum = 0
            if byte == self.header2:
                self.state = self.WAIT_HEADER1
        
        else:
            raise AssertionError()
