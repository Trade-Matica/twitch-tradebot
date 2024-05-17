from twitchio.ext import commands
from dotenv import load_dotenv
from pybitget import Client
from pybitget.utils import random_string
from pybitget.enums import *
import os

class Bot(commands.Bot):
    def __init__(self):

        self.prefix = os.getenv("PREFIX")

        super().__init__(
            token=os.getenv("ACCESS_TOKEN"),
            prefix=self.prefix,
            initial_channels=[
                os.getenv("CHANNEL"),
            ],
        )

        self.bitget = Client(
            os.getenv("BITGET_API_KEY"),
            os.getenv("BITGET_API_SECRET"),
            os.getenv("BITGET_API_PASSPHRASE"),
            use_server_time=False,
        )

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")

    async def event_message(self, message):
        if message.echo or not message.content.startswith(self.prefix):
            return

        args = message.content[len(self.prefix) :].split()

        if args[0] != "trade" or len(args) != 6:
            return

        symbol, side, entry_price, tp_price, sl_price = args[1:6]

        if symbol not in ["BTC"]:
            return

        try:
            entry_price = float(entry_price)
            tp_price = float(tp_price)
            sl_price = float(sl_price)
        except ValueError:
            print("Invalid price format")
            return

        clean_side = self.validate_trade_parameters(
            side, entry_price, tp_price, sl_price
        )
        if clean_side is None:
            print(
                f"Invalid trade parameters: {side}, {entry_price}, {tp_price}, {sl_price}"
            )
            return

        symb = f"S{symbol}SUSDT_SUMCBL"

        if not self.validate_price(symb, entry_price, tp_price, sl_price):
            return

        self.place_order(symb, clean_side, entry_price, tp_price, sl_price)
        print(f"Trade order placed: {message.content}")

    def validate_price(self, symbol, entry_price, tp_price, sl_price):
        price = float(self.bitget.mix_get_market_price(
            symbol=symbol,
        )['data']['markPrice'])

        print("market price:", price)

        if entry_price < price * 0.99:
            print(
                f"Entry price {entry_price} is less than 1% below the market price {price}"
            )
            return False

        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)

        if risk == 0 or reward / risk < 2:
            print(f"Invalid risk-reward ratio: reward {reward}, risk {risk}")
            return False
        
        print('RR:', reward / risk)

        return True

    def validate_trade_parameters(self, side, entry_price, tp_price, sl_price):
        if side == "BUY":
            if entry_price < tp_price and sl_price < entry_price:
                return NEW_BUY
        elif side == "SELL":
            if tp_price < entry_price and entry_price < sl_price:
                return NEW_SELL
        return None

    def place_order(self, symbol, side, entry_price, tp_price, sl_price):
        try:
            placed = self.bitget.mix_place_order(
                symbol,
                "SUSDT",
                "0.001",
                side,
                "limit",
                price=entry_price,
                clientOrderId=random_string("Cuongitl"),
                presetStopLossPrice=sl_price,
                presetTakeProfitPrice=tp_price,
            )

            print(placed)
        except Exception as e:
            print(f"Failed to place order: {e}")


if __name__ == "__main__":
    load_dotenv()
    bot = Bot()
    bot.run()
