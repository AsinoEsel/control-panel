import asyncio
from artnet import my_artnet, OpCode
from micropython import const
from machine import Pin, SoftSPI


from physical_elements.rfid_reader import RFIDReader


def rfid_callback(uid):
    print(uid)


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    pass
    

async def start_main_loop():
    await main_loop()


async def main_loop():
    
    asyncio.create_task(rfid_reader.run(10))        
    print("MAIN LOOP!")
    
    while True:
        "main loop alive"
        await asyncio.sleep_ms(1000)


BAUDRATE = const(100000)
RFID_CLOCK_PIN = const(18)
RFID_CS_PIN = const(5)
RFID_MOSI_PIN = const(23)
RFID_MISO_PIN = const(19)
RFID_RST_PIN = const(27)
spi = SoftSPI(baudrate=BAUDRATE, polarity=1, phase=0, sck=Pin(RFID_CLOCK_PIN), mosi=Pin(RFID_MOSI_PIN), miso=Pin(RFID_MISO_PIN))
rfid_reader = RFIDReader("RFIDReader", spi, RFID_RST_PIN, RFID_CS_PIN, rfid_callback)


my_artnet.subscribe_all(artnet_callback)


asyncio.run(start_main_loop())


print("whoops, end of main.py")
