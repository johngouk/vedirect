# !/usr/bin/python
# -*- coding: utf-8 -*-

# An emulator for a Victron MPPT solar charge controller.
# sends output to a port.
#
# Deeply horrible hack of the original flexible script to simulate MPPT on ESP32
# Only works on MPy/ESP32 with model 'MPPT', sph, n hardcoded because no arguments!
# Used to connect to target EPS32 running VEDirectAsyncio to test it before integration test
# 2025 JDG
#
# To re-route the port to another one for testing, Use `socat` to create linked virtual serial ports with:
# socat -d -d PTY,raw,echo=0,link=/tmp/vmodem0 PTY,raw,echo=0,link=/tmp/vmodem1
# https://github.com/karioja/vedirect
#
# Or, use `pty` as in:
# http://allican.be/blog/2017/01/15/python-dummy-serial-port.html
#
# The code below originated from https://github.com/karioja/vedirect
#
# 2020 JMF

import os, time
import logging

from machine import UART
    
logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

model_default = "MPPT"


class VEDirectDeviceEmulator:
    models = ["ALL", "BMV_600", "BMV_700", "MPPT", "PHX_INVERTER"]
    data = {
        "ALL": {
            "V": "12800",
            "V2": "12802",
            "V3": "12803",
            "VS": "12200",
            "VM": "1280",
            "DM": "120",
            "VPV": "3350",
            "PPV": "130",
            "I": "15000",
            "IL": "1500",
            "LOAD": "ON",
            "T": "25",
            "P": "130",
            "CE": "13500",
            "SOC": "876",
            "TTG": "45",
            "Alarm": "OFF",
            "Relay": "OFF",
            "AR": "1000001",
            "OR": "0x00000000",
            "H1": "55000",
            "H2": "15000",
            "H3": "13000",
            "H4": "230",
            "H5": "12",
            "H6": "234000",
            "H7": "11000",
            "H8": "14800",
            "H9": "7200",
            "H10": "45",
            "H11": "5",
            "H12": "0",
            "H13": "0",
            "H14": "0",
            "H15": "11500",
            "H16": "14800",
            "H17": "34",
            "H18": "45",
            "H19": "456",
            "H20": "45",
            "H21": "300",
            "H22": "45",
            "H23": "350",
            "ERR": "0",
            "CS": "5",
            "BMV": "702",
            "FW": "1.19",
            "PID": "0x204",
            "SER#": "HQ141112345",
            "HSDS": "0",
            "MODE": "2",
            "AC_OUT_V": "23000",
            "AC_OUT_I": "50",
            "WARN": "1",
            "MPPT": "2",
        },
        "BMV_600": {
            "V": "12800",
            "VS": "12800",
            "I": "15000",
            "CE": "13500",
            "SOC": "876",
            "TTG": "45",
            "Alarm": "OFF",
            "Relay": "OFF",
            "AR": "1",
            "H1": "55000",
            "H2": "15000",
            "H3": "13000",
            "H4": "230",
            "H5": "12",
            "H6": "234000",
            "H7": "11000",
            "H8": "14800",
            "H9": "7200",
            "H10": "45",
            "H11": "5",
            "H12": "0",
            "H13": "0",
            "H14": "0",
            "H15": "11500",
            "H16": "14800",
            "BMV": "702",
            "FW": "1.19",
        },
        "BMV_700": {
            "V": "12800",
            "VS": "12800",
            "VM": "1280",
            "DM": "120",
            "I": "15000",
            "T": "25",
            "P": "130",
            "CE": "13500",
            "SOC": "876",
            "TTG": "45",
            "Alarm": "OFF",
            "Relay": "OFF",
            "AR": "1",
            "H1": "55000",
            "H2": "15000",
            "H3": "13000",
            "H4": "230",
            "H5": "12",
            "H6": "234000",
            "H7": "11000",
            "H8": "14800",
            "H9": "7200",
            "H10": "45",
            "H11": "5",
            "H12": "0",
            "H15": "11500",
            "H16": "14800",
            "H17": "34",
            "H18": "45",
            "BMV": "702",
            "FW": "1.19",
            "PID": "0x204",
        },
        "MPPT": {
            "V": "12800",
            "VPV": "3350",
            "PPV": "130",
            "I": "15000",
            "IL": "1500",
            "LOAD": "ON",
            "Relay": "OFF",
            "H19": "456",
            "H20": "45",
            "H21": "300",
            "H22": "45",
            "H23": "350",
            "ERR": "0",
            "CS": "5",
            "FW": "1.19",
            "PID": "0xA042",
            "SER#": "HQ141112345",
            "HSDS": "0",
            "MPPT": "2",
        },
        "PHX_INVERTER": {
            "AR": "1",
            "CS": "5",
            "FW": "1.19",
            "PID": "0xA201",
            "SER#": "HQ141112345",
            "MODE": "2",
            "AC_OUT_V": "23000",
            "AC_OUT_I": "50",
            "WARN": "1",
        },
    }

    def __init__(self, serialport, model="ALL"):
        """
        Constructor for Victron VEDirect device emulator.

        Args:
            serialport (machine.UART): UART to write to 
            model (str): one of ['ALL', 'BMV_600', 'BMV_700', 'MPPT', 'PHX_INVERTER']
        """
        self.serialport = serialport
        self.model = model
        # Serial port is a UART
        self.ser = serialport
        self.ser.init(19200)
        self.writer = self.ser.write

    def record_to_bytes(self, datadict):
        result = list()
        for key in self.data[self.model]:
            result.append(ord("\r"))
            result.append(ord("\n"))
            result.extend([ord(i) for i in key])
            result.append(ord("\t"))
            result.extend([ord(i) for i in datadict[key]])
        # checksum
        result.append(ord("\r"))
        result.append(ord("\n"))
        result.extend([ord(i) for i in "Checksum"])
        result.append(ord("\t"))
        result.append((256 - (sum(result) % 256)) % 256)
        return result

    def send_record(self):
        record = self.get_bytes()
        log.info(f"Sending: {record[:10]}...")
        self.writer(record)

    def get_record(self):
        return self.data[self.model]

    def get_bytes(self):
        return bytes(self.record_to_bytes(self.get_record()))

    def send_records(self, n=-1, samples_per_hour=720.0):
        """Send n records"""
        sleep_seconds = 3600.0 / float(samples_per_hour)
        while n != 0:
            self.send_record()
            time.sleep(sleep_seconds)
            if n != 0:
                n = n - 1


def main():
    destination = "uart"
    model = 'MPPT'
    n = -1
    sph = 3600
    u = 1
    tx = 14
    rx = 13
    uart = UART(u, tx=tx, rx=rx)
    output = uart
        
    print(f"VEDirect emulator running. Writing to {destination}{u} rx {rx} tx {tx}")
    VEDirectDeviceEmulator(output, model).send_records(samples_per_hour=sph)


if __name__ == "__main__":
    main()
