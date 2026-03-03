from tinkoff.invest import Client, MoneyValue, Quotation
from tinkoff.invest import (
    PostStopOrderRequest, StopOrderDirection, StopOrderType, StopOrderExpirationType,
    PostOrderRequest, OrderDirection, OrderType, GetCandlesRequest, CandleInterval
)
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd

def decimal_to_quotation(value: Decimal):
    units = int(value)
    nano = int((value - units) * 1_000_000_000)
    return Quotation(units=units, nano=nano)

class TinkoffClient:
    def __init__(self, token, account_id=None):
        self.token = token
        self.account_id = account_id

        self.printlog = False
        self.filelog = True
        self.logfilename = "log.txt"

        if not self.account_id:
            self.account_id = self.get_account_id()

    def get_account_id(self):
        with Client(self.token) as client:
            accounts = client.users.get_accounts()
            if not accounts.accounts:
                raise ValueError("Не найдено доступных счетов")
            return accounts.accounts[0].id


    def log(self, text):
        if self.printlog:
            print(text)
        if self.filelog:
            with open(self.logfilename, "a", encoding='utf-8') as f:
                f.write(text+"\n")

    def check_short_availability(self, figi):
        with Client(self.token) as client:
            try:
                instrument_response = client.instruments.get_instrument_by(id_type=1, id=figi)
                instrument = instrument_response.instrument
                return getattr(instrument, 'short_enabled_flag', False)
            except Exception as e:
                self.log(f"❌ Ошибка проверки доступности шорт-продажи: {e}")
                return False

    def stop_limit_order(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            request = PostStopOrderRequest(
                instrument_id=figi,
                quantity=lots,
                price=decimal_to_quotation(Decimal(str(limit_price))),
                stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                account_id=self.account_id,
                stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
                expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
            )

            response = client.stop_orders.post_stop_order(request=request)

    def take_profit_order(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            request = PostStopOrderRequest(
                instrument_id=figi,
                quantity=lots,
                price=decimal_to_quotation(Decimal(str(limit_price))),
                stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                account_id=self.account_id,
                stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
                expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
            )

            response = client.stop_orders.post_stop_order(request=request)

    def create_short_position(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                request = PostOrderRequest(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                )
                response = client.orders.post_order(request=request)
            except Exception as e:
                self.log(f"❌ Ошибка создания шорт-позиции: {e}")

    def close_short_position(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                request = PostOrderRequest(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                )
                response = client.orders.post_order(request=request)
            except Exception as e:
                self.log(f"❌ Ошибка закрытия шорт-позиции: {e}")

    def stop_loss_short(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            try:
                request = PostStopOrderRequest(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(limit_price))),
                    stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                    direction=StopOrderDirection.STOP_ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
                    expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
                )

                response = client.stop_orders.post_stop_order(request=request)
            except Exception as e:
                self.log(f"❌ Ошибка создания стоп-лосса для шорта: {e}")

    def take_profit_short(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            try:
                request = PostStopOrderRequest(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(limit_price))),
                    stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                    direction=StopOrderDirection.STOP_ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
                    expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
                )
                response = client.stop_orders.post_stop_order(request=request)
            except Exception as e:
                self.log(f"❌ Ошибка создания тейк-профита для шорта: {e}")

    def buy(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                request = PostOrderRequest(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET
                )
                response = client.orders.post_order(request=request)
                return True
            except Exception as e:
                self.log(f"❌ Ошибка покупки: {e}")
                return False

    def sell(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                request = PostOrderRequest(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET
                )
                response = client.orders.post_order(request=request)
                return True
            except Exception as e:
                self.log(f"❌ Ошибка продажи: {e}")
                return False

    def get_portfolio(self):
        with Client(self.token) as client:
            try:
                response = client.operations.get_portfolio(account_id=self.account_id)
                return response
            except Exception as e:
                self.log(f"❌ Ошибка получения портфеля: {e}")
                return None

    def get_portfolio_summary(self):
        with Client(self.token) as client:
            try:
                response = client.operations.get_portfolio(account_id=self.account_id)

                portfolio_summary = {
                    'total_amount_shares': float(
                        str(response.total_amount_shares.units) + '.' + str(response.total_amount_shares.nano).zfill(
                            9)),
                    'total_amount_bonds': float(
                        str(response.total_amount_bonds.units) + '.' + str(response.total_amount_bonds.nano).zfill(9)),
                    'total_amount_etf': float(
                        str(response.total_amount_etf.units) + '.' + str(response.total_amount_etf.nano).zfill(9)),
                    'total_amount_currencies': float(str(response.total_amount_currencies.units) + '.' + str(
                        response.total_amount_currencies.nano).zfill(9)),
                    'total_amount_futures': float(
                        str(response.total_amount_futures.units) + '.' + str(response.total_amount_futures.nano).zfill(
                            9)),
                    'expected_yield': float(
                        str(response.expected_yield.units) + '.' + str(response.expected_yield.nano).zfill(9)),
                    'positions': []
                }

                for position in response.positions:
                    position_info = {
                        'figi': position.figi,
                        'instrument_type': position.instrument_type,
                        'quantity': float(str(position.quantity.units) + '.' + str(position.quantity.nano).zfill(9)),
                        'average_price': float(str(position.average_position_price.units) + '.' + str(
                            position.average_position_price.nano).zfill(9)),
                        'expected_yield': float(
                            str(position.expected_yield.units) + '.' + str(position.expected_yield.nano).zfill(9)),
                        'current_price': float(
                            str(position.current_price.units) + '.' + str(position.current_price.nano).zfill(9)),
                        'currency': position.average_position_price.currency
                    }
                    portfolio_summary['positions'].append(position_info)

                return portfolio_summary

            except Exception as e:
                self.log(f"❌ Ошибка получения сводки портфеля: {e}")
                return None

    def get_balances(self):
        with Client(self.token) as client:
            try:
                response = client.operations.get_portfolio(account_id=self.account_id)

                balances = {}
                for position in response.positions:
                    # Проверяем, что это валюта
                    if position.instrument_type == 'currency':
                        currency = position.current_price.currency if position.current_price.currency else 'rub'
                        # Получаем количество валюты
                        quantity = position.quantity
                        balance = float(str(quantity.units) + '.' + str(quantity.nano).zfill(9))
                        balances[currency.lower()] = balance

                return balances

            except Exception as e:
                self.log(f"❌ Ошибка получения балансов: {e}")
                return None

    def get_free_rub_balance(self):
        with Client(self.token) as client:
            portfolio = client.operations.get_portfolio(account_id=self.account_id)
            for pos in portfolio.positions:
                if pos.instrument_type == "currency":
                    # В реальном счёте валюта имеет currency в current_price или отдельно
                    currency = getattr(pos, 'currency', None)
                    if not currency and hasattr(pos, 'current_price'):
                        currency = getattr(pos.current_price, 'currency', None)
                    if currency == "rub":
                        qty = float(f"{pos.quantity.units}.{str(pos.quantity.nano).zfill(9)}")
                        return qty
            return 0.0

    def get_positions_market_value(self, tickers_list):
        """Возвращает рыночную стоимость всех НЕВАЛЮТНЫХ позиций с учётом знака (лонг/шорт)"""
        total = 0.0
        with Client(self.token) as client:
            portfolio = client.operations.get_portfolio(account_id=self.account_id)
            for pos in portfolio.positions:
                if pos.instrument_type == "currency":
                    continue

                figi = pos.figi
                balance = float(f"{pos.quantity.units}.{str(pos.quantity.nano).zfill(9)}")  # может быть < 0
                current_price = float(f"{pos.current_price.units}.{str(pos.current_price.nano).zfill(9)}")

                lot_size = 1
                for f, t, n, l in tickers_list:
                    if f == figi:
                        lot_size = l
                        break

                position_value = balance * current_price * lot_size
                total += position_value
        return total

    def get_currency_balance(self, currency="rub"):
        balances = self.get_balances()
        if balances and currency in balances:
            return balances[currency]
        return 0.0

    def get_positions_list(self):
        with Client(self.token) as client:
            try:
                response = client.operations.get_portfolio(account_id=self.account_id)

                positions = []
                for position in response.positions:
                    # Пропускаем валютные позиции
                    if position.instrument_type == 'currency':
                        continue

                    # Получаем актуальную цену
                    current_price = 0.0
                    if position.current_price:
                        current_price = float(str(position.current_price.units) + '.' +
                                              str(position.current_price.nano).zfill(9))

                    # Получаем среднюю цену покупки
                    avg_price = 0.0
                    if position.average_position_price:
                        avg_price = float(str(position.average_position_price.units) + '.' +
                                          str(position.average_position_price.nano).zfill(9))

                    # Получаем количество лотов
                    quantity = 0.0
                    if position.quantity:
                        quantity = float(str(position.quantity.units) + '.' +
                                         str(position.quantity.nano).zfill(9))

                    # Получаем P&L
                    pnl = 0.0
                    if position.expected_yield:
                        pnl = float(str(position.expected_yield.units) + '.' +
                                    str(position.expected_yield.nano).zfill(9))

                    position_data = {
                        'figi': position.figi,
                        'name': getattr(position, 'name', 'N/A'),
                        'instrument_type': position.instrument_type,
                        'balance': quantity,
                        'average_price': avg_price,
                        'current_price': current_price,
                        'expected_yield': pnl,
                        'currency': position.current_price.currency if position.current_price else 'rub'
                    }
                    positions.append(position_data)

                return positions

            except Exception as e:
                self.log(f"❌ Ошибка получения списка позиций: {e}")
                return None

    def get_order_book(self, figi: str, depth: int = 10):
        """
        Получает стакан по FIGI.
        Возвращает: {'bids': [(price, qty), ...], 'asks': [(price, qty), ...]}
        """
        from tinkoff.invest import GetOrderBookRequest
        with Client(self.token) as client:
            try:
                response = client.market_data.get_order_book(
                    instrument_id=figi,
                    depth=depth
                )
                bids = [
                    (
                        float(str(b.price.units) + '.' + str(b.price.nano).zfill(9)),
                        b.quantity
                    )
                    for b in response.bids
                ]
                asks = [
                    (
                        float(str(a.price.units) + '.' + str(a.price.nano).zfill(9)),
                        a.quantity
                    )
                    for a in response.asks
                ]
                return {"bids": bids, "asks": asks}
            except Exception as e:
                self.log(f"❌ Ошибка получения стакана для {figi}: {e}")
                return {"bids": [], "asks": []}

    def get_candles_min(self, figi):
        with Client(self.token) as client:
            try:
                response = client.market_data.get_candles(
                    instrument_id=figi,
                    from_=datetime.now() - timedelta(days=1),
                    to=datetime.now(),
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN
                )

                data = []
                for candle in response.candles:
                    data.append({
                        'time': candle.time,
                        'open': float(str(candle.open.units) + '.' + str(candle.open.nano).zfill(9)),
                        'high': float(str(candle.high.units) + '.' + str(candle.high.nano).zfill(9)),
                        'low': float(str(candle.low.units) + '.' + str(candle.low.nano).zfill(9)),
                        'close': float(str(candle.close.units) + '.' + str(candle.close.nano).zfill(9)),
                        'volume': candle.volume
                    })
                return pd.DataFrame(data)
            except Exception as e:
                self.log(f"❌ Ошибка получения свечей {figi}: {e}")
                return pd.DataFrame()

    def get_candles_hour(self, figi):
        with Client(self.token) as client:
            try:
                response = client.market_data.get_candles(
                    instrument_id=figi,
                    from_=datetime.now() - timedelta(days=7),
                    to=datetime.now(),
                    interval=CandleInterval.CANDLE_INTERVAL_HOUR
                )

                data = []
                for candle in response.candles:
                    data.append({
                        'time': candle.time,
                        'open': float(str(candle.open.units) + '.' + str(candle.open.nano).zfill(9)),
                        'high': float(str(candle.high.units) + '.' + str(candle.high.nano).zfill(9)),
                        'low': float(str(candle.low.units) + '.' + str(candle.low.nano).zfill(9)),
                        'close': float(str(candle.close.units) + '.' + str(candle.close.nano).zfill(9)),
                        'volume': candle.volume
                    })
                return pd.DataFrame(data)
            except Exception as e:
                self.log(f"❌ Ошибка получения часовых свечей {figi}: {e}")
                return pd.DataFrame()