This bot allows your viewers to trade Bitcoin on your account by using a simple chat command.

Usage:
To place a trade, use the following command in chat:
    - !trade <symbol> <SIDE> <TP_PRICE> <SL_PRICE> [ENTRY_PRICE]

Parameters:
    - <symbol>: The trading symbol, e.g., BTC.
    - <SIDE>: The side of the trade, either BUY or SELL.
    - <TP_PRICE>: The take profit price.
    - <SL_PRICE>: The stop loss price.
    - [ENTRY_PRICE]: The entry price (optional for market orders).

Example:
To place a limit order:
    - !trade BTC BUY 65000 64900 64910

To place a market order:
    - !trade BTC BUY 64500 64300

Requirements:
    - Minimum Risk Reward Ratio: The trade must have a minimum risk-reward ratio of 2:1.
    - Order Price Range: For limit orders, the entry price must be within 1% of the current market price.
    - Order Value: The order value is dynamically calculated to ensure the trade size fits the specified USDT amount.
