from src.exchanges.binance.market_data import BinanceMarketDataService


class FakeMarketClient:
    def get_klines(self, symbol, interval, limit):
        return [
            [
                1700000000000, "40000", "41000", "39500", "40500", "100.5",
                1700003600000, "4050000", 500, "60.3", "2432100", "0",
            ]
        ]

    def get_order_book(self, symbol, limit):
        return {
            "lastUpdateId": 12345,
            "bids": [["40000.00", "1.5"], ["39999.00", "2.0"]],
            "asks": [["40001.00", "0.8"], ["40002.00", "1.2"]],
        }

    def get_24h_ticker(self, symbol):
        return {
            "symbol": "BTCUSDT",
            "priceChange": "1500.00",
            "priceChangePercent": "3.90",
            "lastPrice": "40000.00",
            "highPrice": "41000.00",
            "lowPrice": "38500.00",
            "volume": "25000.00",
            "quoteVolume": "987500000.00",
            "openPrice": "38500.00",
            "count": 350000,
            "weightedAvgPrice": "39500.00",
        }


def make_service():
    return BinanceMarketDataService(FakeMarketClient())


def test_klines_returns_one_normalized_candle():
    candles = make_service().get_klines("BTCUSDT", "1h", 1)

    assert len(candles) == 1


def test_kline_fields_are_named_correctly():
    candle = make_service().get_klines("BTCUSDT", "1h", 1)[0]

    assert candle["open_time"] == 1700000000000
    assert candle["open"] == "40000"
    assert candle["high"] == "41000"
    assert candle["low"] == "39500"
    assert candle["close"] == "40500"
    assert candle["volume"] == "100.5"
    assert candle["close_time"] == 1700003600000
    assert candle["quote_volume"] == "4050000"
    assert candle["trade_count"] == 500
    assert candle["taker_buy_volume"] == "60.3"
    assert candle["taker_buy_quote_volume"] == "2432100"


def test_order_book_best_bid_and_ask():
    book = make_service().get_order_book("BTCUSDT", 5)

    assert book["best_bid"] == "40000"
    assert book["best_ask"] == "40001"


def test_order_book_spread():
    book = make_service().get_order_book("BTCUSDT", 5)

    assert book["spread"] == "1"
    assert book["spread_pct"] == "0.0025"
    assert book["mid_price"] == "40000.5"


def test_order_book_depth_is_sum_of_quantities():
    book = make_service().get_order_book("BTCUSDT", 5)

    # bids: 1.5 + 2.0 = 3.5
    assert book["bid_depth"] == "3.5"
    # asks: 0.8 + 1.2 = 2
    assert book["ask_depth"] == "2"


def test_order_book_preserves_levels():
    book = make_service().get_order_book("BTCUSDT", 5)

    assert book["symbol"] == "BTCUSDT"
    assert book["last_update_id"] == 12345
    assert len(book["bids"]) == 2
    assert len(book["asks"]) == 2
    assert book["bids"][0] == {"price": "40000.00", "quantity": "1.5"}
    assert book["asks"][0] == {"price": "40001.00", "quantity": "0.8"}


def test_24h_stats_fields():
    stats = make_service().get_24h_stats("BTCUSDT")

    assert stats["symbol"] == "BTCUSDT"
    assert stats["price_change"] == "1500.00"
    assert stats["price_change_pct"] == "3.90"
    assert stats["last_price"] == "40000.00"
    assert stats["high"] == "41000.00"
    assert stats["low"] == "38500.00"
    assert stats["volume"] == "25000.00"
    assert stats["quote_volume"] == "987500000.00"
    assert stats["open_price"] == "38500.00"
    assert stats["trade_count"] == 350000
    assert stats["weighted_avg_price"] == "39500.00"
