#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Forked from karioja at https://github.com/karioja/vedirect
#
# 2019-01-16 JMF Modified for Python 3 and updated protocol from
# https://www.sv-zanshin.com/r/manuals/victron-ve-direct-protocol.pdf
'''

    VEDirectAsyncio
    
    Class to read data over a serial port from a Victron device that uses the VE:Direct
    protocol
    
    VEDirectAsyncio(uart=<pre-initialised UART object>, # This...
                    uartId=<ESP32 UART Id>, rx=<RX Pin Number, tx=<TX Pin number>, # or this!
                    callback=<callback for record completion>) # Optional
                    
    getEvent()
        returns an asyncio.Event which can be waited on to be alerted for a record completion.
        Call Event.clear() when notified

    getRecord()
        returns the completed record if called after Event completes and record available,
        otherwise None
        
    
'''


import sys
import logging
from micropython import const

MICROPYTHON = True
log = logging.getLogger(__name__)
from ESPLogRecord import ESPLogRecord
log.record = ESPLogRecord()

from machine import UART

from .vedevice import VEDirectBase

class VEDirectAsyncio(VEDirectBase):

    def __init__(self, uart=None, uartId=None, rx=None, tx=None, callback=None):
        super().__init()

        self._uart = uart
        self._uartId = uartId
        self._rx = rx
        self._tx = tx
        self._callback = callback
        self._recordReady = asyncio.Event()
        self._recordQ = deque((),2,True) # Somewhere to put records, only 2 secs worth!
        if (uart is not None) and (uartId == None):
            # We have a previously opened UART to use...
            log.info("Using UART provided")
            self._uart.init(baudrate=19200) # We assume you've used the pins you want to
        elif (uartId is not None) and (rx is not None) and (tx is not None):
            # We have to open our own UART
            log.info("Opening UART %s, rx %d tx %d", uartId, rx, tx)
            self._uart = UART(uartid)
            self._uart.init(baudrate=19200, rx=rx. tx=tx) # We assume you've used the pins you want to
        else:
            # Get your act together guys, work with me here!
            log.error("You're having a laugh, I need either a UART or a set of UART parameters!")
            raise Exception("You're having a laugh, I need either a UART or a set of UART parameters!")
        self._run = asyncio.create_task(self._go())  # Thread runs forever

    def getRecord(self):
        '''
            Return a record to the caller, if present, otherwise None
        '''
        try:
            return self._recordQ.pop()
        except IndexError:
            return None
    
    def getEvent(self):
        '''
            Return the "record arrived" Event for the caller to wait on
            The caller must call Event.clear() when it receives the Event
        '''
        return self._recordReady
    
    async def _go(self):
        '''
            Loops checking port for any input
        '''
        while True:
            while self._uart.any(): # Any data on the serial port??
                byte = self._uart.read(1) # OK, read a byte
                if byte:
                    log.debug("Read: 0x%02x", byte)
                    # got a byte (didn't time out)
                    record = self._input(byte)
                    if record is not None:
                        self._recordQ.appendleft(record) # Let the IndexError exception happen
                        if self._callback is not None: # User wants a callback
                            self._callback(record)
                        self._recordReady.set() # Tell the Event people
            # Hang around for some more data to arrive
            # 19200 baud, 10 bits/char (8, 1 parity, 1 stop) => 2000 chars/sec
            # Records are sent 1/sec, maybe 250 chars/record => 125ms transmit per record
            # Let's try 250msec, which means we shouldn't miss any
            await asyncio.sleep_ms(250)

