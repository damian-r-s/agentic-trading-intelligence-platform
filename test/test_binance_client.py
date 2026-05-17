import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest
import requests as requests_lib

from src.core.config import BinanceSettings
from src.exchanges.binance.client import (
    BinanceAPIError,
    BinanceAuthenticationError,
    BinanceClient,
    BinanceConfigurationError,
    BinanceNetworkError,
    BinanceRateLimitError,
    BinanceResponseError,
    BinanceTimeoutError,
    extract_error_message,
    parse_response_payload,
    raise_api_error,
)

SETTINGS = BinanceSettings(
    api_key="test-key",
    api_secret="test-secret",
    base_url="https://api.binance.com",
    recv_window=5000,
)

FIXED_TIMESTAMP = 1700000000000

def make_client():
    return BinanceClient(SETTINGS)

def fake_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("not json")
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def test_raises_configuration_error_when_api_key_empty():
    with pytest.raises(BinanceConfigurationError):
        BinanceClient(BinanceSettings(api_key="", api_secret="secret"))


def test_raises_configuration_error_when_api_secret_empty():
    with pytest.raises(BinanceConfigurationError):
        BinanceClient(BinanceSettings(api_key="key", api_secret=""))


def test_client_constructs_when_credentials_present():
    client = make_client()
    assert client.settings == SETTINGS


# ---------------------------------------------------------------------------
# Public endpoints — happy path and routing
# ---------------------------------------------------------------------------

@patch("requests.get")
def test_get_klines_hits_correct_path_and_params(mock_get):
    mock_get.return_value = fake_response(json_data=[["data"]])

    make_client().get_klines("BTCUSDT", "1h", 100)

    call_kwargs = mock_get.call_args
    assert call_kwargs[0][0] == "https://api.binance.com/api/v3/klines"
    assert call_kwargs[1]["params"]["symbol"] == "BTCUSDT"
    assert call_kwargs[1]["params"]["interval"] == "1h"
    assert call_kwargs[1]["params"]["limit"] == 100


@patch("requests.get")
def test_get_order_book_hits_correct_path_and_params(mock_get):
    mock_get.return_value = fake_response(json_data={"bids": [], "asks": []})

    make_client().get_order_book("ETHUSDT", 50)

    call_kwargs = mock_get.call_args
    assert call_kwargs[0][0] == "https://api.binance.com/api/v3/depth"
    assert call_kwargs[1]["params"]["symbol"] == "ETHUSDT"
    assert call_kwargs[1]["params"]["limit"] == 50


@patch("requests.get")
def test_get_24h_ticker_with_symbol(mock_get):
    mock_get.return_value = fake_response(json_data={"symbol": "BTCUSDT"})

    make_client().get_24h_ticker("BTCUSDT")

    assert mock_get.call_args[1]["params"]["symbol"] == "BTCUSDT"


@patch("requests.get")
def test_get_24h_ticker_without_symbol_sends_no_params(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_24h_ticker()

    assert mock_get.call_args[1]["params"] is None


@patch("requests.get")
def test_get_ticker_prices_encodes_symbols_as_json(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_ticker_prices(["BTCUSDT", "ETHUSDT"])

    raw = mock_get.call_args[1]["params"]["symbols"]
    assert json.loads(raw) == ["BTCUSDT", "ETHUSDT"]


@patch("requests.get")
def test_get_exchange_info_hits_correct_path(mock_get):
    mock_get.return_value = fake_response(json_data={"symbols": []})

    make_client().get_exchange_info()

    assert mock_get.call_args[0][0] == "https://api.binance.com/api/v3/exchangeInfo"


@patch("requests.get")
def test_public_get_returns_json_payload(mock_get):
    payload = [{"open": "100"}]
    mock_get.return_value = fake_response(json_data=payload)

    result = make_client().get_klines("BTCUSDT", "1h", 1)

    assert result == payload


# ---------------------------------------------------------------------------
# Public endpoints — network errors
# ---------------------------------------------------------------------------

@patch("requests.get", side_effect=requests_lib.Timeout)
def test_public_get_raises_timeout(_):
    with pytest.raises(BinanceTimeoutError):
        make_client().get_klines("BTCUSDT", "1h", 1)


@patch("requests.get", side_effect=requests_lib.ConnectionError)
def test_public_get_raises_network_error_on_connection_error(_):
    with pytest.raises(BinanceNetworkError):
        make_client().get_exchange_info()


@patch("requests.get", side_effect=requests_lib.RequestException("oops"))
def test_public_get_raises_network_error_on_generic_request_exception(_):
    with pytest.raises(BinanceNetworkError):
        make_client().get_exchange_info()


@patch("requests.get")
def test_public_get_raises_api_error_on_4xx(mock_get):
    mock_get.return_value = fake_response(
        status_code=400,
        json_data={"code": -1100, "msg": "Bad request"},
    )

    with pytest.raises(BinanceAPIError):
        make_client().get_klines("BTCUSDT", "1h", 1)


@patch("requests.get")
def test_public_get_raises_response_error_on_non_json_2xx(mock_get):
    mock_get.return_value = fake_response(status_code=200, text="plaintext")

    with pytest.raises(BinanceResponseError):
        make_client().get_klines("BTCUSDT", "1h", 1)


# ---------------------------------------------------------------------------
# Signed endpoints — routing and authentication headers
# ---------------------------------------------------------------------------

@patch("requests.get")
def test_signed_get_sends_api_key_header(mock_get):
    mock_get.return_value = fake_response(json_data={})

    make_client().get_account_info()

    assert mock_get.call_args[1]["headers"]["X-MBX-APIKEY"] == "test-key"


@patch("requests.get")
def test_signed_get_includes_recv_window_and_timestamp(mock_get):
    mock_get.return_value = fake_response(json_data={})

    make_client().get_account_info()

    params = mock_get.call_args[1]["params"]
    assert params["recvWindow"] == 5000
    assert isinstance(params["timestamp"], int)
    assert params["timestamp"] > 0


@patch("requests.get")
def test_signed_get_signature_matches_hmac(mock_get):
    mock_get.return_value = fake_response(json_data={})

    with patch.object(BinanceClient, "_timestamp_ms", return_value=FIXED_TIMESTAMP):
        make_client().get_account_info()

    params = mock_get.call_args[1]["params"]
    sig = params.pop("signature")

    expected = hmac.new(
        b"test-secret",
        urlencode(params).encode(),
        hashlib.sha256,
    ).hexdigest()

    assert sig == expected


@patch("requests.get")
def test_get_my_trades_sends_symbol(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_my_trades("BTCUSDT")

    assert mock_get.call_args[1]["params"]["symbol"] == "BTCUSDT"
    assert mock_get.call_args[0][0].endswith("/api/v3/myTrades")


@patch("requests.get")
def test_get_open_orders_with_symbol(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_open_orders("ETHUSDT")

    assert mock_get.call_args[1]["params"]["symbol"] == "ETHUSDT"


@patch("requests.get")
def test_get_open_orders_without_symbol_omits_symbol_param(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_open_orders()

    assert "symbol" not in mock_get.call_args[1]["params"]


@patch("requests.get")
def test_get_trade_fee_with_symbol(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_trade_fee("BTCUSDT")

    assert mock_get.call_args[1]["params"]["symbol"] == "BTCUSDT"


@patch("requests.get")
def test_get_trade_fee_without_symbol_omits_symbol_param(mock_get):
    mock_get.return_value = fake_response(json_data=[])

    make_client().get_trade_fee()

    assert "symbol" not in mock_get.call_args[1]["params"]


# ---------------------------------------------------------------------------
# Signed endpoints — error mapping
# ---------------------------------------------------------------------------

@patch("requests.get")
def test_signed_get_raises_authentication_error_on_401(mock_get):
    mock_get.return_value = fake_response(status_code=401, json_data={"code": -2014, "msg": "Invalid key"})

    with pytest.raises(BinanceAuthenticationError):
        make_client().get_account_info()


@patch("requests.get")
def test_signed_get_raises_authentication_error_on_403(mock_get):
    mock_get.return_value = fake_response(status_code=403, json_data={"code": -2015, "msg": "Forbidden"})

    with pytest.raises(BinanceAuthenticationError):
        make_client().get_account_info()


@patch("requests.get")
def test_signed_get_raises_rate_limit_error_on_429(mock_get):
    mock_get.return_value = fake_response(status_code=429, json_data={"code": -1003, "msg": "Too many"})

    with pytest.raises(BinanceRateLimitError):
        make_client().get_account_info()


@patch("requests.get")
def test_signed_get_raises_rate_limit_error_on_418(mock_get):
    mock_get.return_value = fake_response(status_code=418, json_data={"code": -1003, "msg": "Banned"})

    with pytest.raises(BinanceRateLimitError):
        make_client().get_account_info()


@patch("requests.get")
def test_signed_get_raises_generic_api_error_on_other_4xx(mock_get):
    mock_get.return_value = fake_response(status_code=400, json_data={"code": -1100, "msg": "Bad param"})

    with pytest.raises(BinanceAPIError):
        make_client().get_account_info()


@patch("requests.get", side_effect=requests_lib.Timeout)
def test_signed_get_raises_timeout(_):
    with pytest.raises(BinanceTimeoutError):
        make_client().get_account_info()


@patch("requests.get", side_effect=requests_lib.ConnectionError)
def test_signed_get_raises_network_error_on_connection_error(_):
    with pytest.raises(BinanceNetworkError):
        make_client().get_account_info()


# ---------------------------------------------------------------------------
# parse_response_payload
# ---------------------------------------------------------------------------

def test_parse_response_payload_returns_json_on_success():
    resp = fake_response(status_code=200, json_data={"key": "val"})

    assert parse_response_payload(resp) == {"key": "val"}


def test_parse_response_payload_returns_text_on_4xx_non_json():
    resp = fake_response(status_code=400, text="Bad request")

    assert parse_response_payload(resp) == "Bad request"


def test_parse_response_payload_raises_response_error_on_2xx_non_json():
    resp = fake_response(status_code=200, text="not json")

    with pytest.raises(BinanceResponseError) as exc_info:
        parse_response_payload(resp)

    assert exc_info.value.status_code == 200


# ---------------------------------------------------------------------------
# raise_api_error
# ---------------------------------------------------------------------------

def test_raise_api_error_401_raises_authentication_error():
    with pytest.raises(BinanceAuthenticationError):
        raise_api_error(401, {"code": -2014, "msg": "bad key"})


def test_raise_api_error_403_raises_authentication_error():
    with pytest.raises(BinanceAuthenticationError):
        raise_api_error(403, {})


def test_raise_api_error_429_raises_rate_limit_error():
    with pytest.raises(BinanceRateLimitError):
        raise_api_error(429, {})


def test_raise_api_error_418_raises_rate_limit_error():
    with pytest.raises(BinanceRateLimitError):
        raise_api_error(418, {})


def test_raise_api_error_400_raises_api_error():
    with pytest.raises(BinanceAPIError):
        raise_api_error(400, {"code": -1100, "msg": "bad param"})


def test_raise_api_error_500_raises_api_error():
    with pytest.raises(BinanceAPIError):
        raise_api_error(500, "server error")


# ---------------------------------------------------------------------------
# extract_error_message
# ---------------------------------------------------------------------------

def test_extract_error_message_with_code_and_msg():
    assert extract_error_message({"code": -1100, "msg": "Bad param"}) == "-1100: Bad param"


def test_extract_error_message_dict_without_code():
    assert extract_error_message({"message": "something went wrong"}) == "something went wrong"


def test_extract_error_message_non_dict_string():
    assert extract_error_message("raw error") == "raw error"


def test_extract_error_message_non_dict_other():
    assert extract_error_message(42) == "42"


def test_extract_error_message_dict_with_neither_msg_nor_message():
    result = extract_error_message({"code": -9999})
    assert "-9999" in result
