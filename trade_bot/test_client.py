from tinkoff.invest import Client, MoneyValue, Quotation
from tinkoff.invest import (
    OrderDirection, OrderType, StopOrderDirection,
    StopOrderType, StopOrderExpirationType
)
from decimal import Decimal
import pandas as pd

def decimal_to_quotation(value: Decimal):
    units = int(value)
    nano = int((value - units) * 1_000_000_000)
    return Quotation(units=units, nano=nano)

class TestTinkoffClient:
    def __init__(self, token, account_id=None):
        self.token = token
        self.account_id = account_id

        self.printlog = False
        self.filelog = True
        self.logfilename = "log.txt"

        if not self.account_id:
            self.account_id = self.get_or_create_sandbox_account()

    def get_existing_sandbox_accounts(self):
        with Client(self.token) as client:
            try:
                response = client.sandbox.get_sandbox_accounts()
                return response.accounts
            except Exception as e:
                self.log(f"❌ Ошибка получения списка sandbox счетов: {e}")
                return []

    def find_and_set_account(self):
        accounts = self.get_existing_sandbox_accounts()

        if accounts:
            self.account_id = accounts[0].id
            self.log(f"✅ Используем существующий sandbox счет: {self.account_id}")
            return "success"
        else:
            return "error"

    def get_or_create_sandbox_account(self):
        accounts = self.get_existing_sandbox_accounts()

        if accounts:
            account_id = accounts[0].id
            self.log(f"✅ Используем существующий sandbox счет: {account_id}")
            return account_id
        else:
            return self.create_sandbox_account()

    def create_sandbox_account(self):
        with Client(self.token) as client:
            try:
                response = client.sandbox.open_sandbox_account()
                self.log(f"✅ Создан новый sandbox счет: {response.account_id}")
                return response.account_id
            except Exception as e:
                self.log(f"❌ Ошибка создания sandbox счета: {e}")
                raise

    def delete_sandbox_account(self, account_id=None):
        if not account_id:
            account_id = self.account_id

        with Client(self.token) as client:
            try:
                client.sandbox.close_sandbox_account(account_id=account_id)
                self.log(f"✅ Sandbox счет {account_id} удален")
                return True
            except Exception as e:
                self.log(f"❌ Ошибка удаления sandbox счета: {e}")
                return False

    def delete_all_sandbox_accounts(self):
        accounts = self.get_existing_sandbox_accounts()
        success_count = 0

        for account in accounts:
            if self.delete_sandbox_account(account.id):
                success_count += 1

        self.log(f"✅ Удалено {success_count} из {len(accounts)} sandbox счетов")
        return success_count

    def log(self, text):
        if self.printlog:
            print(text)
        if self.filelog:
            with open(self.logfilename, "a", encoding='utf-8') as f:
                f.write(text + "\n")

    def sandbox_pay_in(self, amount, currency="rub"):
        with Client(self.token) as client:
            try:
                amount_value = MoneyValue(
                    units=int(amount),
                    nano=int((amount - int(amount)) * 1_000_000_000),
                    currency=currency.upper()
                )

                response = client.sandbox.sandbox_pay_in(
                    account_id=self.account_id,
                    amount=amount_value
                )

                balance = float(str(response.balance.units) + '.' + str(response.balance.nano).zfill(9))
                self.log(f"✅ Sandbox счет пополнен на {amount} {currency.upper()}")
                self.log(f"Текущий баланс: {balance} {currency.upper()}")
                return response

            except Exception as e:
                self.log(f"❌ Ошибка пополнения sandbox счета: {e}")
                return None

    def stop_limit_order(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_stop_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(limit_price))),
                    stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                    direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                    account_id=self.account_id,
                    stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
                    expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
                )
                self.log(f"✅ Sandbox стоп-лосс ордер создан!")
                return response
            except Exception as e:
                self.log(f"❌ Ошибка sandbox стоп-лосс ордера: {e}")
                return None

    def take_profit_order(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_stop_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(limit_price))),
                    stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                    direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                    account_id=self.account_id,
                    stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
                    expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
                )
                self.log(f"✅ Sandbox тейк-профит ордер создан!")
                return response
            except Exception as e:
                self.log(f"❌ Ошибка sandbox тейк-профит ордера: {e}")
                return None

    def create_short_position(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                )
                self.log(f"✅ Шорт-позиция создана: {lots} лотов по {price}")
                return response
            except Exception as e:
                self.log(f"❌ Ошибка создания sandbox шорт-позиции: {e}")
                return None

    def close_short_position(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                )
                self.log(f"✅ Шорт-позиция закрыта: {lots} лотов по {price}")
                return response
            except Exception as e:
                self.log(f"❌ Ошибка закрытия sandbox шорт-позиции: {e}")
                return None

    def stop_loss_short(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_stop_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(limit_price))),
                    stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                    direction=StopOrderDirection.STOP_ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
                    expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
                )
                self.log(f"✅ Стоп-лосс для шорта создан")
                return response
            except Exception as e:
                self.log(f"❌ Ошибка создания sandbox стоп-лосса для шорта: {e}")
                return None

    def take_profit_short(self, figi, lots, stop_price, limit_price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_stop_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(limit_price))),
                    stop_price=decimal_to_quotation(Decimal(str(stop_price))),
                    direction=StopOrderDirection.STOP_ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
                    expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL
                )
                self.log(f"✅ Тейк-профит для шорта создан")
                return response
            except Exception as e:
                self.log(f"❌ Ошибка создания sandbox тейк-профита для шорта: {e}")
                return None

    def buy(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET
                )
                self.log(f"✅ Sandbox покупка выполнена!")
                return True
            except Exception as e:
                self.log(f"❌ Ошибка sandbox покупки: {e}")
                return False

    def sell(self, figi, lots, price):
        with Client(self.token) as client:
            try:
                response = client.sandbox.post_sandbox_order(
                    instrument_id=figi,
                    quantity=lots,
                    price=decimal_to_quotation(Decimal(str(price))),
                    direction=OrderDirection.ORDER_DIRECTION_SELL,
                    account_id=self.account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET
                )
                self.log(f"✅ Sandbox продажа выполнена!")
                return True
            except Exception as e:
                self.log(f"❌ Ошибка sandbox продажи: {e}")
                return False

    def get_portfolio(self):
        with Client(self.token) as client:
            try:
                response = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
                return response
            except Exception as e:
                self.log(f"❌ Ошибка получения sandbox портфеля: {e}")
                return None

    def get_balances(self):
        with Client(self.token) as client:
            try:
                response = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)

                balances = {}
                for position in response.positions:
                    if position.instrument_type == 'currency':
                        currency = position.current_price.currency if position.current_price.currency else 'rub'
                        quantity = position.quantity
                        balance = float(str(quantity.units) + '.' + str(quantity.nano).zfill(9))
                        balances[currency.lower()] = balance

                return balances

            except Exception as e:
                self.log(f"❌ Ошибка получения sandbox балансов: {e}")
                return None

    def get_free_rub_balance(self):
        with Client(self.token) as client:
            portfolio = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            for pos in portfolio.positions:
                if pos.instrument_type == "currency":
                    # В sandbox currency хранится в pos.money.currency
                    if hasattr(pos, 'money') and pos.money.currency == "rub":
                        qty = float(f"{pos.quantity.units}.{str(pos.quantity.nano).zfill(9)}")
                        return qty
                    # На случай, если money нет — fallback по FIGI или имени
                    if getattr(pos, 'figi', '') == "" or "rub" in str(pos).lower():
                        qty = float(f"{pos.quantity.units}.{str(pos.quantity.nano).zfill(9)}")
                        return qty
            return 0.0

    def get_positions_market_value(self, tickers_list):
        """Возвращает рыночную стоимость всех НЕВАЛЮТНЫХ позиций с учётом знака (лонг/шорт)"""
        total = 0.0
        with Client(self.token) as client:
            portfolio = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
            for pos in portfolio.positions:
                if pos.instrument_type == "currency":
                    continue  # пропускаем валюты

                figi = pos.figi
                balance = float(f"{pos.quantity.units}.{str(pos.quantity.nano).zfill(9)}")  # может быть < 0
                current_price = float(f"{pos.current_price.units}.{str(pos.current_price.nano).zfill(9)}")

                # Находим lot_size из тикер-листа
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
                response = client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
                positions = []
                for position in response.positions:
                    if position.instrument_type != 'currency':
                        position_data = {
                            'figi': position.figi,
                            'name': getattr(position, 'name', 'N/A'),
                            'instrument_type': position.instrument_type,
                            'balance': float(str(position.quantity.units) + '.' + str(position.quantity.nano).zfill(9)),
                            'average_price': float(str(position.average_position_price.units) + '.' + str(
                                position.average_position_price.nano).zfill(9)),
                            'current_price': float(
                                str(position.current_price.units) + '.' + str(position.current_price.nano).zfill(9)),
                            'expected_yield': float(
                                str(position.expected_yield.units) + '.' + str(position.expected_yield.nano).zfill(9)),
                            'currency': position.average_position_price.currency
                        }
                        positions.append(position_data)
                return positions
            except Exception as e:
                self.log(f"❌ Ошибка получения списка sandbox позиций: {e}")
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
                from datetime import datetime, timedelta
                from tinkoff.invest import CandleInterval

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
                self.log(f"❌ Ошибка получения минутных свечей {figi}: {e}")
                return pd.DataFrame()

    def get_candles_hour(self, figi):
        with Client(self.token) as client:
            try:
                from datetime import datetime, timedelta
                from tinkoff.invest import CandleInterval

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
