# flash_arbitrage

My attempt at an arbitrage bot on algorand leveraging algofi's flashloans
depending on the price difference, I borrow, buy high and sell low in different exchanges

to begin, create a new .env file, put in MNEMONIC="Your mnemonic phrase, without commas",
start the price bot, it will continualy check the prices of the worth of 1 usdc in algo and when there is a price difference of up to 2 decimals, 
it calls the flashswap function.

NOTE this is my first attempt and it may not work the way I intend it to, might even loose money, so thread with caution
