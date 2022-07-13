import time
from binance.client import Client
from binance import helpers
import telegram_send
from multiprocessing import shared_memory
import price_ticker
import json

class CryptoBot:

    TICKER_INTERVAL= 0.8
    BUY_QUANTITY_IN_USDT = 20
    SHARED_MEMORY_SIZE = 20

    def __init__(self):
        return

    async def runBot(self, symbol):
        try:
            api_key = '1Lt38xGVQCtrI58IjWetYkcRLolmJAAabzgS5EeVQt089uFyPt4tszf8D6fEIpIS'
            api_secret = 'F8x9SVYPhf1VJm4LnWoh0eRXuAhvilq30dqgGL8n3f4rI2Fzpc6ri58aiGTCJOtb'
            client = Client(api_key, api_secret)
            shm = shared_memory.SharedMemory(name='telega1111', create=False, size=price_ticker.PriceTicker.SHARED_MEMORY_SIZE)
            shm1Lock = shared_memory.SharedMemory(name='telega1111Lock', create=False, size=1)

            symbolInfo = client.get_symbol_info(symbol)
            order1 = client.order_market_buy(
                symbol=symbol,
                quoteOrderQty=CryptoBot.BUY_QUANTITY_IN_USDT
            )
            if type(order1) is not dict:
                return

            buyPrice = float(order1['fills'][0]['price'])
            sellPrice = buyPrice + buyPrice * 0.01
            order2 = None

            isLimitSellCreated = False
            if order1['status'].lower() == 'filled':
                thePrice = helpers.round_step_size(
                    float(('{:.' + str(len(symbolInfo['filters'][0]['tickSize'].split('.')[-1])) + 'f}').format(sellPrice)),
                    symbolInfo['filters'][0]['tickSize']
                )
                sellQuantity = ('{:.' + str(len(symbolInfo['filters'][2]['stepSize'].split('.')[-1])) + 'f}').format(helpers.round_step_size(
                    float(order1['fills'][0]['qty']) - float(order1['fills'][0]['commission']),
                    symbolInfo['filters'][2]['stepSize']
                ))
                if len([x for x in symbolInfo['filters'][2]['stepSize'].split('.')[-1] if x != '0']) < 1:
                    try:
                        sellQuantity = int(float(sellQuantity))
                    except Exception:
                        pass

                try:
                    order2 = client.order_limit_sell(
                        symbol=symbol,
                        quantity=sellQuantity,
                        price=('{:.' + str(len(symbolInfo['filters'][0]['tickSize'].split('.')[-1])) + 'f}').format(thePrice)
                    )
                except Exception as e3:
                    telegram_send.send(messages='Failed to sell ' + symbol + '\n' + str(e3), silent=False)

                if type(order2) is dict:
                    isLimitSellCreated = True
                time.sleep(0.5)

                while True:
                    if shm1Lock.buf[0] != 0:
                        time.sleep(0.05)
                        continue
                    shm1Lock.buf[0] = 1
                    allPrices = json.loads(shm.buf.tobytes().decode('utf-8').rstrip('\x00'))
                    shm1Lock.buf[0] = 0
                    if allPrices[symbol]['price'] <= buyPrice - buyPrice * 0.015 and isLimitSellCreated:
                        try:
                            client.cancel_order(symbol=symbol, orderId=order2['orderId'])

                            isSuccessSell = False
                            someException = ''
                        
                            order3 = client.order_market_sell(
                                symbol=symbol,
                                quantity=sellQuantity
                            )                                
                            if type(order3) is dict and order3['status'].lower() == 'filled':
                                isSuccessSell = True
                        except Exception as e:
                            someException = '\n' + type(e) + '\n' + e

                        if not isSuccessSell:
                            telegram_send.send(messages='Failed to sell ' + symbol + someException, silent=False)
                        break

                    time.sleep(CryptoBot.TICKER_INTERVAL)
        except Exception as e:
            print(e)