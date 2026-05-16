from fastapi import APIRouter, HTTPException

from src.exchanges.binance.client import (
    BinanceAPIError,
    BinanceClientError,
    BinanceConfigurationError,
    BinanceNetworkError,
    BinanceResponseError,
    BinanceTimeoutError,
)
from src.exchanges.binance.service import create_binance_portfolio_service

router = APIRouter()


@router.get("/portfolio")
async def portfolio():
    try:
        service = create_binance_portfolio_service()

        return service.get_portfolio_snapshot()
    except BinanceConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except BinanceAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.payload,
        ) from exc
    except BinanceTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except BinanceNetworkError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except BinanceResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "status_code": exc.status_code,
                "payload": exc.payload,
            },
        ) from exc
    except BinanceClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
