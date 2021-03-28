#!/usr/bin/python3
# -*- coding: utf-8 -*-

# continuously print VE.Direct data to stdout

import argparse, os
from vedirect import VEDirect


def print_data_callback(packet):
    print(packet)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process VE.Direct protocol')
    parser.add_argument('--port', help='Serial port')
    parser.add_argument('--timeout', help='Serial port read timeout', type=int, default='60')
    parser.add_argument('--emulate', help='emulate one of [ALL, BMV_600, BMV_700, MPPT, PHX_INVERTER]',
                    default='', type=str)
    args = parser.parse_args()
    ve = VEDirect(args.port, args.timeout, args.emulate)
    print(ve.read_data_callback(print_data_callback))
