#VE Direct Code

- `main.py` - a test script to be loaded onto an ESP32 that uses the VEDirectAsyncio class to receive VEDirect messages over a serial port. This works in conjunction with another ESP32 running `main.py` from the `/tests` directory, which generates VEDirect messages and sends them. Yes, it's a two-chip problem!
- `/vedirect` - source directory