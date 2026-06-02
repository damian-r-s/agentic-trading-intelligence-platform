import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

@dataclass(frozen=True)
class FinBertServiceSettings:
    url: str = "http://localhost:8001"

def get_finbert_service_settings() -> FinBertServiceSettings:
    return FinBertServiceSettings(
        url=os.getenv("FINBERT_URL", "http://localhost:8001")
    )

@dataclass(frozen=True)
class BinanceSettings:
    api_key: str
    api_secret: str
    base_url: str = "https://api.binance.com"
    recv_window: int = 5000

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)


def get_binance_settings() -> BinanceSettings:
    return BinanceSettings(
        api_key=os.getenv("BINANCE_API_KEY", ""),
        api_secret=os.getenv("BINANCE_API_SECRET", ""),
        base_url=os.getenv("BINANCE_BASE_URL", "https://api.binance.com"),
        recv_window=int(os.getenv("BINANCE_RECV_WINDOW", "5000")),
    )

@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:3b"

def get_ollama_settings() -> OllamaSettings:
    return OllamaSettings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
    )
@dataclass(frozen=True)
class NewsSettings:
    news_api_key: str

def get_news_settings() -> NewsSettings:
    return NewsSettings(
        news_api_key=os.getenv("NEWS_API_KEY", "")
    )


@dataclass(frozen=True)
class FinBertSettings:
    model: str = "ProsusAI/finbert"


def get_finbert_settings() -> FinBertSettings:
    return FinBertSettings(
        model=os.getenv("FINBERT_MODEL", "ProsusAI/finbert"),
    )