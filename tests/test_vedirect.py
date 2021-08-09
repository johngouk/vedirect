import pytest
import serial
from vedirect import VEDirect


def test_basic(fake_serial):
    ser = serial.Serial()
    ve = VEDirect("BADPORT")
    pass
