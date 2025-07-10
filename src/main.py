import logging
from micropython import const

from vedirect.vedirect_new import VEDirect

#machine.freq(240000000) # Juice things up a bit

#           ADJUST LOG LEVEL HERE->vvvvvv, values are DEBUG, INFO, WARNING, ERROR, FATAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)06d %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)
port = 1 # Number of UART
timeout = 2000
logger.debug("Initialising VEDirect instance")
port = open('newfile',mode='rb')
print(type(port))
ve = VEDirect(port, timeout)
#ve.read_data_callback(print_data_callback, 1000)
logger.debug("Calling VEDirect.read()")
print(ve.read_data_single(flush=False))
print(ve.read_data_single(flush=False))

from vedirect.vedirect_asyncio_new import VEDirectAsyncio



