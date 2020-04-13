import os, pty
import threading
from vedirect.vedirect_emulator import VEDirectEmulator
from vedirect.vedirect import VEDirect
import unittest


class TestVEDirect(unittest.TestCase):

    def cb_function(self, data):
        self.data = data

    def test_v_mppt(self):
        """ Test with an MPPT emulator on a fake serial port """
        master, slave = pty.openpty()  # open the pseudoterminal
        s_name = os.ttyname(slave)  # translate the slave fd to a filename

        # Set up the slave (IoT device client) to listen for data from the (master) device
        vedir = VEDirect(s_name)
        thread_slave = threading.Thread(target=vedir.read_data_single_callback, args=[self.cb_function])
        thread_slave.start()

        # Create a separate device emulator thread that connects to the master port
        vede = VEDirectEmulator(master, model='MPPT')
        thread_master = threading.Thread(target=vede.send_packet)
        thread_master.start()

        # Wait a maximum of 5 seconds for the IoT device client to finish (it getting one packet)
        thread_slave.join(timeout=5)

        self.assertDictEqual(self.data, VEDirectEmulator.data['MPPT'])


if __name__ == '__main__':
    unittest.main()
