#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Forked from karioja at https://github.com/karioja/vedirect
#
# 2019-01-16 JMF Modified to work with Python 3 and updated from
# https://www.sv-zanshin.com/r/manuals/victron-ve-direct-protocol.pdf

import serial
import argparse


class VEDirect:
    encoding = 'utf-8'

    error_codes = {
        0: 'No error',
        2: 'Battery voltage too high',
        17: 'Charger temperature too high',
        18: 'Charger over current',
        19: 'Charger current reversed',
        20: 'Bulk time limit exceeded',
        21: 'Current sensor issue (sensor bias/sensor broken)',
        26: 'Terminals overheated',
        33: 'Input voltage too high (solar panel)',
        34: 'Input current too high (solar panel)',
        38: 'Input shutdown (due to excessive battery voltage)',
        116: 'Factory calibration data lost',
        117: 'Invalid/incompatible firmware',
        119: 'User settings invalid'
    }

    @staticmethod
    def conv_error(code):
        return VEDirect.error_codes[int(code)]

    device_state_map = {
        0: 'not charging',
        1: 'low power',
        2: 'fault',
        3: 'charging bulk',
        4: 'charging absorption',
        5: 'charging float',
        9: 'inverting'
    }

    @staticmethod
    def conv_mode(code):
        return VEDirect.device_state_map[int(code)]

    values = {
        'LOAD': {'key': 'load'},
        'H19': {'key': 'yieldTotal', 'mx': 0.01},
        'VPV': {'key': 'panelVoltage', 'mx': 0.001},
        'ERR': {'key': 'error', 'f': conv_error},
        'FW': {'key': 'firmwareVersion', 'mx': 0.01},
        'I': {'key': 'current', 'mx': 0.001},
        'H21': {'key': 'maximumPowerToday', 'f': int},  # W
        'IL': {'key': 'loadCurrent', 'mx': 0.001},
        'PID': {'key': 'productId'},
        'H20': {'key': 'yieldToday', 'mx': 0.01},  # kWh
        'H23': {'key': 'maximumPowerYesterday', 'f': int},  # W
        'H22': {'key': 'yieldYesterday', 'mx': 0.01},  # kWh
        'HSDS': {'key': 'daySequenceNumber', 'f': int},
        'SER#': {'key': 'serialNumber'},
        'V': {'key': 'batteryVoltage', 'mx': 0.001},
        'CS': {'key': 'mode', 'f': conv_mode},
        'PPV': {'key': 'panelPower', 'f': int}
    }

    divs = {
        'batteries_hdg': ['bmv', 'SOC'],
        'batteries_bdy': ['bmv', 'V', 'I'],
        'solar_hdg': ['mppt', 'I'],
        'solar_bdy': ['mppt', 'V', 'CS', 'H20'],
        'vehicle_hdg': ['bmv', 'VS'],
        'vehicle_bdy': ['bmv', 'Relay'],
        'conv_hdg': ['conv', 'I'],
        'conv_bdy': ['conv', 'V', 'T']
    }

    units = {
        'V': 'mV',
        'VS': 'mV',
        'VM': 'mV',
        'DM': '%',
        'VPV': 'mV',
        'PPV': 'W',
        'I': 'mA',
        'IL': 'mA',
        'LOAD': '',
        'T': '°C',
        'P': 'W',
        'CE': 'mAh',
        'SOC': '%',
        'TTG': 'Minutes',
        'Alarm': '',
        'Relay': '',
        'AR': '',
        'H1': 'mAh',
        'H2': 'mAh',
        'H3': 'mAh',
        'H4': '',
        'H5': '',
        'H6': 'mAh',
        'H7': 'mV',
        'H8': 'mV',
        'H9': 'Seconds',
        'H10': '',
        'H11': '',
        'H12': '',
        'H15': 'mV',
        'H16': 'mV',
        'H17': '0.01 kWh',
        'H18': '0.01 kWh',
        'H19': '0.01 kWh',
        'H20': '0.01 kWh',
        'H21': 'W',
        'H22': '0.01 kWh',
        'H23': 'W',
        'ERR': '',
        'CS': '*',
        'BMV': '',
        'FW': '',
        'PID': '',
        'SER#': '',
        'HSDS': '',
        'MODE': '',
        'AC_OUT_V': '0.01 V',
        'AC_OUT_I': '0.1 A',
        'WARN': ''
    }

    cs = {
        '0': 'Off', '2': 'Fault', '3': 'Bulk',
        '4': 'Abs', '5': 'Float'
    }

    fmt = {
        '%': ['%', 10, 1],
        '°C': ['°C', 1, 0],
        '0.01 kWh': ['Wh', .1, 2],
        'mA': ['A', 1000, 2],
        'mAh': ['Ah', 1000, 2],
        'Minutes': ['Mins', 1, 0],
        'mV': ['V', 1000, 2],
        'Seconds': ['Secs', 1, 0],
        'W': ['W', 1, 0]
    }

    def __init__(self, serialport, emulate=False):
        """ Constructor for a Victron VEDirect serial communication session.

        Params:
            serialport (str): The name of the serial port to open
            emulate (bool): Whether or not to emulate a VEDirect device
        """
        self.serialport = serialport
        self.ser = serial.Serial(port=serialport, baudrate=19200, timeout=0)
        self.header1 = b'\r'
        self.header2 = b'\n'
        self.hexmarker = b':'
        self.delimiter = b'\t'
        self.key = b''
        self.value = b''
        self.bytes_sum = 0
        self.state = self.WAIT_HEADER1
        self.dict = {}

    (HEX, WAIT_HEADER, IN_KEY, IN_VALUE, IN_CHECKSUM) = range(5)

    def input(self, byte):
        """ Accepts a new byte and tries to finish constructing a packet.
        When a packet is complete, it will be returned as a dictionary
        """
        if byte == self.hexmarker and self.state != self.IN_CHECKSUM:
            self.state = self.HEX

        if self.state == self.WAIT_HEADER1:
            if byte == self.header1:
                self.bytes_sum += ord(byte)
                self.state = self.WAIT_HEADER2
            return None
        if self.state == self.WAIT_HEADER2:
            if byte == self.header2:
                self.bytes_sum += ord(byte)
                self.state = self.IN_KEY
            return None
        elif self.state == self.IN_KEY:
            self.bytes_sum += ord(byte)
            if byte == self.delimiter:
                if self.key == b'Checksum':
                    self.state = self.IN_CHECKSUM
                else:
                    self.state = self.IN_VALUE
            else:
                self.key += byte
            return None
        elif self.state == self.IN_VALUE:
            self.bytes_sum += ord(byte)
            if byte == self.header1:
                self.state = self.WAIT_HEADER
                self.dict[str(self.key.decode(self.encoding))] = str(
                    self.value.decode(self.encoding))
                self.key = b''
                self.value = b''
            else:
                self.value += byte
            return None
        elif self.state == self.IN_CHECKSUM:
            self.bytes_sum += ord(byte)
            self.key = b''
            self.value = b''
            self.state = self.WAIT_HEADER
            if self.bytes_sum % 256 == 0:
                self.bytes_sum = 0
                return self.dict
            else:
                print('Malformed packet')
                self.bytes_sum = 0
        elif self.state == self.HEX:
            self.bytes_sum = 0
            if byte == self.header2:
                self.state = self.WAIT_HEADER
        else:
            raise AssertionError()

    def read_data_single(self):
        """ Continue to wait until we get a single complete packet.
        """
        while True:
            byte = self.ser.read(1)
            if byte:
                packet = self.input(byte)
                if packet is not None:
                    return packet

    def read_data_single_callback(self, callbackfunction):
        """ Continue to wait until we get a single complete packet, then call the callback function with the result.
        """
        callbackfunction(self.read_data_single())

    def read_data_callback_service(self, callbackfunction):
        """ Non-blocking service to try to get one byte and see if it completes a packet.  If it does, call the
        callback function.
        """
        byte = self.ser.read(1)
        if byte:
            # got a byte
            packet = self.input(byte)
            if packet is not None:
                # made a full packet
                callbackfunction(packet)

    def read_data_callback(self, callbackfunction):
        """ Continue to wait for messages and call the callback function when we get them
        """
        while True:
            self.read_data_callback_service(callbackfunction)


def print_data_callback(data):
    print(data)


def main():
    # provide a simple entry point that streams VEDirect data to stdout
    parser = argparse.ArgumentParser(description='Read VE.Direct device and stream data to stdout')
    parser.add_argument('port', help='Serial port to read from')
    parser.add_argument('--n', help='number of packets to read (or default=0 for infinite)', default=0, type=int)
    args = parser.parse_args()
    ve = VEDirect(args.port)
    if args.n:
        for i in range(0, args.n):
            print_data_callback(ve.read_data_single())
    else:
        ve.read_data_callback(print_data_callback)


if __name__ == '__main__':
    main()