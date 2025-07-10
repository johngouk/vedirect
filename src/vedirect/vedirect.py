#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Forked from karioja at https://github.com/karioja/vedirect
#
# 2019-01-16 JMF Modified for Python 3 and updated protocol from
# https://www.sv-zanshin.com/r/manuals/victron-ve-direct-protocol.pdf


import sys
import logging
from micropython import const

MICROPYTHON = True
log = logging.getLogger(__name__)
from ESPLogRecord import ESPLogRecord
log.record = ESPLogRecord()

from machine import UART

from vedirect.vedirect_base import VEDirectBase

class VEDirect(VEDirectBase):

    def __init__(self, serialport, timeout=60):
        """Constructor for a Victron VEDirect serial communication session.

        Params:
            serialport (int): The number of the UART to open OR
                an already opened interface that adheres the serial interface
            timeout (float): Read timeout value (seconds)
        """
        super().__init__()
        log.debug("serialport is %s", type(serialport))
        if isinstance(serialport, int):
            log.debug(const("VEDirect init opening UART %d"), serialport)
            self.serialport = serialport
            self.ser = UART(int(serialport), 19200, timeout=timeout)  # E.g. for fipy 0,1, or 2
            #self.ser.init(baudrate=19200, timeout_chars=10)
        else:
            log.debug(
                const("VEDirect init using passed in serial port: %s"),str(serialport)
            )
            self.serialport = str(serialport)
            self.ser = serialport

    def read(self):
        """
        Check for input buffer, process if present, return record if complete. 
        """
        if hasattr(self.ser, '__any__'):
            input_buf_len = self.ser.any()
        else:
            input_buf_len = -1
        log.debug("Input buffer %d chars",input_buf_len)
        if input_buf_len:
            input_buf = self.ser.read(input_buf_len)
            log.debug("Input: %d bytes read",len(input_buf))
            for byte in input_buf:
                record = self._input(byte.to_bytes(1, sys.byteorder))
                if record is not None:
                    record = self.typecast(record)
                    self._buff_records.append(record)
        try:
            log.debug("Returning records")
            return self._buff_records.pop()
        except IndexError:
            return None

    def read_data_single(self, flush=True, timeout=None):
        """Wait until we get a single complete record, then return it. Optional timeout in ms"""
        timer = None
        if flush and not MICROPYTHON:
            self.ser.flushInput()
        if timeout and MICROPYTHON and Timer:
            timer = Timer.Chrono()
            timer.start()
        while True:
            if timer and timer.read_ms() > timeout:
                log.debug("Timed out")
                return None
            byte = self.ser.read(1)
            if byte:
                # log.debug("Read: {}".format(byte))
                # got a byte (didn't time out)
                record = self._input(byte)
                if record is not None:
                    return self.typecast(record)


def main():
    # provide a simple entry point that streams data from a VEDirect device to stdout
    parser = argparse.ArgumentParser(
        description="Read VE.Direct device and stream data to stdout"
    )
    parser.add_argument("--port", help="Serial port to read from", type=str, default="")
    parser.add_argument(
        "--n",
        help="number of records to read (or default=-1 for infinite)",
        default=-1,
        type=int,
    )
    parser.add_argument(
        "--timeout", help="Serial port read timeout, seconds", type=int, default="60"
    )
    parser.add_argument(
        "--loglevel",
        help="logging level - one of [DEBUG, INFO, WARNING, ERROR, CRITICAL]",
        default="ERROR",
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel.upper())
    if not args.port:
        print("Must specify a port to listen.")
        raise ValueError("Must give a port")
    ve = VEDirect(args.port, args.timeout)
    ve.read_data_callback(print_data_callback, args.n)


if __name__ == "__main__" and not MICROPYTHON:
    main()
