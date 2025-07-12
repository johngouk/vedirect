import logging
from micropython import const
import asyncio

from vedirect.vedirect_asyncio import VEDirectAsyncio

#machine.freq(240000000) # Juice things up a bit

async def loop(ve):
    e = ve.getEvent()
    while True:
        await e.wait()
        e.clear()
        record = ve.getRecord()
        print("event:",record)

def printRecord(record):
    print("callback:",record)

#           ADJUST LOG LEVEL HERE->vvvvvv, values are DEBUG, INFO, WARNING, ERROR, FATAL
logging.basicConfig(level=logging.WARNING, format='%(asctime)s.%(msecs)06d %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)
port = 1 # Number of UART
timeout = 2000
rx = 14
tx = 13
logger.debug("Initialising VEDirectAsyncio instance: uart: %d rx: %d tx: %d",port,rx,tx)
#port = open('newfile',mode='rb')
#print(type(port))
#ve = VEDirect(port, timeout)
ve = VEDirectAsyncio(uartId=1,tx=19,rx=18, callback=printRecord)
#ve.read_data_callback(print_data_callback, 1000)
#logger.debug("Calling VEDirect.read()")
#print(ve.read_data_single(flush=False))
#print(ve.read_data_single(flush=False))

#from vedirect.vedirect_asyncio_new import VEDirectAsynciotry:
    # start the main async tasks
try:
    asyncio.run(loop(ve))
finally:
    # reset and start a new event loop for the task scheduler
    asyncio.new_event_loop()

