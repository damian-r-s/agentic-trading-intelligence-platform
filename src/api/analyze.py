from fastapi import APIRouter, HTTPException, Query
from fastapi import Depends

from src.api.auth import get_current_user

from src.agents.tools.graph import run_trading_analysis
from src.exchanges.binance.client import (
    BinanceAPIError,
    BinanceClientError,
    BinanceConfigurationError,
    BinanceNetworkError,
    BinanceResponseError,
    BinanceTimeoutError,
)

router = APIRouter(tags=["agent"], dependencies=[Depends(get_current_user)])

@router.get("/agent/analyze")
async def analyze(symbol: str = Query(default="BTCUSDT")):
    try:
        return run_trading_analysis(symbol.upper())
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
