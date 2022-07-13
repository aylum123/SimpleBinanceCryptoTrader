from multiprocessing import shared_memory
from statistics import mean
import pandas as pd
import time
import price_ticker
import json
import asyncio
import multiprocessing
import telegram_send
import crypto_bot

class CryptoPicker:

    TICKER_INTERVAL = 6
    BAN_SYMBOL_FROM_BUYING_DURATION = 1800
    
    @staticmethod
    def _manageDict1(dict1, keyDiff, keyPrev, keyCurr):
        prev = dict1[keyPrev]
        curr = dict1[keyCurr]
        dict1[keyDiff] = (curr / prev - 1) * 100 if prev > 0 else 0
        dict1[keyPrev] = curr
        return dict1

    @staticmethod
    def _getAllFromDictDict(dict1):
        res = {
            'symbols' : list(dict1.keys()),
            'price' : [],
            'diff' : [],
            'vol' : [],
            'volDiff' : [],
            'link' : [],
            'speed' : []
        }
        for symbol in list(dict1.keys()):
            res['price'].append(dict1[symbol]['price'])
            res['diff'].append(dict1[symbol]['diff'])
            res['vol'].append(dict1[symbol]['vol'])
            res['volDiff'].append(dict1[symbol]['volDiff'])
            res['speed'].append(dict1[symbol]['speed'])
            res['link'].append('https://www.binance.com/en/trade/' + symbol[:-4] + '_' + symbol[-4:])
        return res

    @staticmethod
    def startCryptoBot(symbol):
        cb = crypto_bot.CryptoBot()
        asyncio.get_event_loop().run_until_complete(cb.runBot(symbol))

    async def runPicker(self, symbols):
        bannedSymbols = []
        allPrices = { symbol : {
            'diff' : 0,
            'price' : 0,
            'prevPrice' : 0,
            'vol' : 0,
            'prevVol' : 0,
            'volDiff' : 0,
            'openPrice' : 0,
            'allDiff' : [],
            'speed' : 0
        } for symbol in symbols}
        shar1 = shared_memory.SharedMemory(name='telega1111', create=False, size=price_ticker.PriceTicker.SHARED_MEMORY_SIZE)
        shar1Lock = shared_memory.SharedMemory(name='telega1111Lock', create=False, size=1)

        while True:
            if shar1Lock.buf[0] != 0:
                continue
            shar1Lock.buf[0] = 1
            try:
                received = shar1.buf.tobytes().decode('utf-8').rstrip('\x00')
                if received == '':
                    shar1Lock.buf[0] = 0
                    continue
                tickerPrices = json.loads(received)
                for symbol in allPrices:
                    allPrices[symbol]['price'] = tickerPrices[symbol]['price']
                    allPrices[symbol]['vol'] = tickerPrices[symbol]['vol']
                    allPrices[symbol] = CryptoPicker._manageDict1(
                        allPrices[symbol],
                        'diff',
                        'prevPrice',
                        'price'
                    )
                    allPrices[symbol] = CryptoPicker._manageDict1(
                        allPrices[symbol],
                        'volDiff',
                        'prevVol',
                        'vol'
                    )

                    if len(allPrices[symbol]['allDiff']) < 4:
                        allPrices[symbol]['allDiff'].append(allPrices[symbol]['diff'])
                    else:
                        allPrices[symbol]['allDiff'] = [allPrices[symbol]['allDiff'][-1]]
                    allPrices[symbol]['speed'] = mean([x for x in allPrices[symbol]['allDiff']])

                    pd1 = pd.DataFrame(data=CryptoPicker._getAllFromDictDict(allPrices))
                    pd1.sort_values(by='speed', inplace=True)

                    resDf = pd1[pd1['speed'] > 0.35]#price change threshold 0.23/0.45
                    resDf = resDf[resDf['volDiff'] > 0.4]#0.7
                    resDf = resDf[resDf['diff'] > 0.1]#0.1

                if len(resDf) > 0:
                    lenResDf = 3 if len(resDf) > 2 else len(resDf)
                    sendMessage = []
                    symbolToBuyName = ''
                    for i in range(1, lenResDf + 1):
                        tempToSend = resDf.values[-i]
                        if not all([res1[0] != tempToSend[0] for res1 in bannedSymbols]):
                            continue
                        sendMessage = []
                        sendMessage.append(
                            tempToSend[0] \
                            + '\nVdiff: {:.10f}'.format(float(tempToSend[4])) \
                            + '\nspeed: {:.10f}'.format(float(tempToSend[6])) \
                            + '\nPdiff: {:.10f}'.format(float(tempToSend[2])) \
                            + '\n' + tempToSend[5])
                        allPrices[tempToSend[0]]['allDiff'] = [0]
                        symbolToBuyName = tempToSend[0]
                        break
                    
                    if symbolToBuyName != '':
                        bannedSymbols = [[res1[0], res1[1] - CryptoPicker.TICKER_INTERVAL] for res1 in bannedSymbols if res1[1] - CryptoPicker.TICKER_INTERVAL > 0]
                        bannedSymbols.append([symbolToBuyName, CryptoPicker.BAN_SYMBOL_FROM_BUYING_DURATION])
                        multiprocessing.Process(target=CryptoPicker.startCryptoBot, args=[symbolToBuyName]).start()
                        sendMessage.append('================================')
                        telegram_send.send(messages=sendMessage, silent=False, disable_web_page_preview=True)

                print('\n==================================================================\n')
                print(resDf)
                print('\n==================================================================\n')
            except Exception as e:
                print(e)
            shar1Lock.buf[0] = 0
            time.sleep(CryptoPicker.TICKER_INTERVAL)