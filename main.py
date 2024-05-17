from twitchio.ext import commands
from dotenv import load_dotenv
from pybitget import Client
from pybitget.utils import random_string
from pybitget.enums import *
import os

__MIN_RR__ = 2.0
__MIN_PC_PRICE__ = 0.99
__ORDER_VALUE__ = 0.618 * 125  # order_cost * laverage | = 0.001 BTC


class Bot(commands.Bot):
    def __init__(self):
        load_dotenv()

        self.prefix = os.getenv("PREFIX")

        super().__init__(
            token=os.getenv("ACCESS_TOKEN"),
            prefix=self.prefix,
            initial_channels=[os.getenv("CHANNEL")],
        )

        self.bitget = Client(
            os.getenv("BITGET_API_KEY"),
            os.getenv("BITGET_API_SECRET"),
            os.getenv("BITGET_API_PASSPHRASE"),
            use_server_time=False,
        )

        self.maker_fee = float(os.getenv("MAKER_FEE"))
        self.taker_fee = float(os.getenv("TAKER_FEE"))

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")

    async def event_message(self, message):
        if message.echo or not message.content.startswith(self.prefix):
            return

        args = message.content[len(self.prefix) :].split()

        if args[0] != "trade" or len(args) < 5:
            return

        symbol, side, tp_price, sl_price = args[1:5]
        entry_price = None

        if len(args) == 6:
            entry_price = args[5]

        if symbol not in ["BTC"]:
            return

        try:
            tp_price = float(tp_price)
            sl_price = float(sl_price)
            if entry_price:
                entry_price = float(entry_price)
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

        if entry_price and not self.validate_price(
            symb, entry_price, tp_price, sl_price
        ):
            return

        if not self.is_trade_profitable(symb, side, entry_price, tp_price):
            print("Trade is not profitable after fees.")
            return

        self.place_order(symb, clean_side, entry_price, tp_price, sl_price)
        print(f"Trade order placed: {message.content}")

    def validate_price(self, symbol, entry_price, tp_price, sl_price):
        price = float(
            self.bitget.mix_get_market_price(symbol=symbol)["data"]["markPrice"]
        )

        if entry_price == None:
            entry_price = price

        print("market price:", price)

        if entry_price < price * __MIN_PC_PRICE__:
            print(
                f"Entry price {entry_price} is less than 1% below the market price {price}"
            )
            return False

        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)

        if risk == 0 or reward / risk < __MIN_RR__:
            print(f"Invalid risk-reward ratio: reward {reward}, risk {risk}")
            return False

        print("RR:", reward / risk)

        return True

    def validate_trade_parameters(self, side, entry_price, tp_price, sl_price):
        if side == "BUY":
            if entry_price is None or (
                entry_price < tp_price and sl_price < entry_price
            ):
                return NEW_BUY
        elif side == "SELL":
            if entry_price is None or (
                tp_price < entry_price and entry_price < sl_price
            ):
                return NEW_SELL
        return None

    def is_trade_profitable(self, symbol, side, entry_price: float, tp_price: float):
        entry_fee = 0

        if entry_price is None:
            entry_price = float(
                (self.bitget.mix_get_market_price(symbol=symbol)["data"]["markPrice"])
            )
            entry_fee = entry_price * self.taker_fee
        else:
            entry_fee = entry_price * self.maker_fee

        if side == "BUY":
            exit_fee = tp_price * self.maker_fee
            total_fee = entry_fee + exit_fee
            position_size = __ORDER_VALUE__ / entry_price
            profit = (tp_price - entry_price - total_fee) * position_size

        elif side == "SELL":
            exit_fee = tp_price * self.maker_fee
            total_fee = entry_fee + exit_fee
            position_size = __ORDER_VALUE__ / entry_price
            profit = (entry_price - tp_price - total_fee) * position_size

        print("Expected profits:", profit)
        return profit > 0

    def calculate_order_size(self, price):
        return __ORDER_VALUE__ / price

    def place_order(self, symbol, side, entry_price, tp_price, sl_price):
        try:
            if entry_price:
                order_type = "limit"
                order_size = self.calculate_order_size(entry_price)
            else:
                order_type = "market"
                market_price = float(
                    self.bitget.mix_get_market_price(symbol=symbol)["data"]["markPrice"]
                )
                order_size = self.calculate_order_size(market_price)

            print(order_size)
            placed = self.bitget.mix_place_order(
                symbol,
                "SUSDT",
                str(order_size),
                side,
                order_type,
                price=entry_price if entry_price else None,
                clientOrderId=random_string("Cuongitl"),
                presetStopLossPrice=sl_price,
                presetTakeProfitPrice=tp_price,
            )

            print(placed)
        except Exception as e:
            print(f"Failed to place order: {e}")


if __name__ == "__main__":
    bot = Bot()
    bot.run()
