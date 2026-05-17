from fastapi import APIRouter, HTTPException, Query

from src.exchanges.binance.client import (
    BinanceAPIError,
    BinanceClientError,
    BinanceConfigurationError,
    BinanceNetworkError,
    BinanceResponseError,
    BinanceTimeoutError,
)
from src.exchanges.binance.market_data import KlineInterval, create_binance_market_data_service

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/{symbol}/candles")
async def candles(
    symbol: str,
    interval: KlineInterval = Query(default="1h"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    OHLCV candles for the given symbol.
    Example: /market-data/BTCUSDT/candles?interval=4h&limit=200
    """
    try:
        service = create_binance_market_data_service()
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "candles": service.get_klines(symbol.upper(), interval, limit),
        }
    except BinanceConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except BinanceAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload) from exc
    except BinanceTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except BinanceNetworkError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except BinanceResponseError as exc:
        raise HTTPException(status_code=502, detail={"message": str(exc), "payload": exc.payload}) from exc
    except BinanceClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{symbol}/order-book")
async def order_book(
    symbol: str,
    depth: int = Query(default=50, ge=5, le=5000),
):
    """
    Order book (bid/ask) for the given symbol.
    Includes spread, mid-price, and total depth on both sides.
    Example: /market-data/BTCUSDT/order-book?depth=20
    """
    try:
        service = create_binance_market_data_service()
        return service.get_order_book(symbol.upper(), depth)
    except BinanceConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except BinanceAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload) from exc
    except BinanceTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except BinanceNetworkError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except BinanceResponseError as exc:
        raise HTTPException(status_code=502, detail={"message": str(exc), "payload": exc.payload}) from exc
    except BinanceClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{symbol}/stats")
async def stats_24h(symbol: str):
    """
    24h statistics: price change, high/low, volume, trade count.
    Example: /market-data/BTCUSDT/stats
    """
    try:
        service = create_binance_market_data_service()
        return service.get_24h_stats(symbol.upper())
    except BinanceConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except BinanceAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload) from exc
    except BinanceTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except BinanceNetworkError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except BinanceResponseError as exc:
        raise HTTPException(status_code=502, detail={"message": str(exc), "payload": exc.payload}) from exc
    except BinanceClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
