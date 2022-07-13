# SimpleBinanceCryptoTrader

Binance trading bot

I just wrote this code, did debug so it's kind of works. The code definitely has some flaws. But this is it. From my exprerience this bot keeps balance the same :)

This code every 6 seconds takes difference in price of some cryptocurrencies, calculates speed. Then the bot picks one (last in sorted list) crypto, buys it, places limit sell +1% of buying prince. Also watcher for every bought crypto running in it's own procces. If price of bought crypto drops to -1.5% from buying, bot cancells limit sell and places market sell. Forgot to exit the process if limit sell is filled.

Also the bot can send message to telegram. It sends position it bought and should send some Exceptions from code.
