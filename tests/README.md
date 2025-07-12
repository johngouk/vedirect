#VEDirect tests
These are some test drivers for the VEDirect classes.
 - newfile - a file with two VE:Direct records in used to test the VEDirect class in CPython on my laptop
 - main.py - main to be uploaded to ESP32 to send VE:Direct messages over a serial ink to the ESP32 running the VE:Direct code
 - vedirect_device_emulator_ESP_.py - the actual test code, which has been copied to main.py so it can be uploaded; no Rename facility in Thonny
 - vedirect_device_emulator_orig_.py - the original test code, which runs in CPython, and I modified to read from a text file