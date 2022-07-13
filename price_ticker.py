import time
import json
from binance import BinanceSocketManager
from binance.client import Client
from multiprocessing import shared_memory

class PriceTicker:

    TICKER_INTERVAL = 0.01
    SHARED_MEMORY_SIZE = 20000

    def __init__(self):
        api_key = ''
        api_secret = ''
        self.client = Client(api_key, api_secret)
        self.allPrices = {}

    async def runTicker(self, symbols):
        try:
            self.allPrices = {symbol : {'price' : 0, 'vol' : 0} for symbol in symbols}
            bm = BinanceSocketManager(self.client)
            multSock = bm.multiplex_socket([symbol.lower() + '@ticker' for symbol in symbols])
            sharedMem = shared_memory.SharedMemory(name='telega1111', create=False, size=PriceTicker.SHARED_MEMORY_SIZE)
            sharedMemLock = shared_memory.SharedMemory(name='telega1111Lock', create=False, size=1)

            async with multSock as tickerStream:
                while True:
                    try:
                        if sharedMemLock.buf[0] != 0:
                            continue
                        sharedMemLock.buf[0] = 1                    
                        res = await tickerStream.recv()
                        if res['data']['s'] in self.allPrices:
                            try:
                                self.allPrices[res['data']['s']]['price'] = float(res['data']['c'])
                                self.allPrices[res['data']['s']]['vol'] = float(res['data']['q'])
                            except:
                                self.allPrices[res['data']['s']]['price'] = 0
                                self.allPrices[res['data']['s']]['vol'] = 0

                            strToSend = json.dumps(self.allPrices).encode('utf-8')
                            sharedMem.buf[:] = bytes((b'\x00')*len(sharedMem.buf))
                            sharedMem.buf[:len(strToSend)] = strToSend
                    except Exception as e2:
                        print(e2)
                    sharedMemLock.buf[0] = 0
                    time.sleep(PriceTicker.TICKER_INTERVAL)

            await self.client.close_connection()
        except Exception as e:
            print('EXCEPTION11111: ' + str(e))