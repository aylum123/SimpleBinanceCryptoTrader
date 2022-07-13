import os
import asyncio
from multiprocessing import shared_memory
import multiprocessing
import price_ticker
import crypto_picker

def startPriceTicker(symbols):
    pt = price_ticker.PriceTicker()
    asyncio.get_event_loop().run_until_complete(pt.runTicker(symbols))

def startCryptoPicker(symbols):
    cp = crypto_picker.CryptoPicker()
    asyncio.get_event_loop().run_until_complete(cp.runPicker(symbols))

if __name__ == '__main__':

    symbols = None
    with open(os.path.dirname(os.path.realpath(__file__)) + '\\symbols2.txt', 'r') as f:
        symbols = [line1.replace('\n', '').replace('_', '') for line1 in f.readlines() if line1 != '' and line1 != '\n']

    shar1 = shared_memory.SharedMemory(name='telega1111', create=True, size=price_ticker.PriceTicker.SHARED_MEMORY_SIZE)
    shar1Lock = shared_memory.SharedMemory(name='telega1111Lock', create=True, size=1)
    shar1Lock.buf[0] = 0
    multiprocessing.Process(target=startPriceTicker, args=[symbols]).start()
    multiprocessing.Process(target=startCryptoPicker, args=[symbols]).start()
    
    while True:
        pass