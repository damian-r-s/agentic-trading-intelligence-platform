from langgraph.graph import END, START, StateGraph

from src.agents.tools.nodes.correlation import correlation_node
from src.agents.tools.nodes.liquidity import liquidity_node
from src.agents.tools.nodes.market_regime import market_regime_node
from src.agents.tools.nodes.momentum import momentum_node
from src.agents.tools.nodes.portfolio_snapshot import portfolio_snapshot_node
from src.agents.tools.nodes.risk_metrics import risk_metrics_node
from src.agents.tools.nodes.technical_analysis import technical_analysis_node
from src.agents.tools.nodes.news_sentiment import sentiment_node
from src.agents.tools.nodes.strategy import strategy_node
from src.agents.tools.nodes.critic import critic_node
from src.agents.tools.nodes.decision_report import decision_report_node

from src.agents.tools.state import TradingDecisionState

def _build_graph() -> StateGraph:
    graph = StateGraph(TradingDecisionState)

    graph.add_node("portfolio_snapshot", portfolio_snapshot_node)
    graph.add_node("risk_metrics",       risk_metrics_node)
    graph.add_node("technical_analysis", technical_analysis_node)
    graph.add_node("market_regime",      market_regime_node)
    graph.add_node("momentum",           momentum_node)
    graph.add_node("liquidity",          liquidity_node)
    graph.add_node("correlation",        correlation_node)    
    graph.add_node("news_sentiment",     sentiment_node)
    graph.add_node("strategy",           strategy_node)
    graph.add_node("critic",             critic_node)
    graph.add_node("decision_report",    decision_report_node)

    # portfolio_snapshot must run first — all parallel nodes read portfolio data
    graph.add_edge(START, "portfolio_snapshot")

    # fan-out: seven nodes run in parallel after portfolio is ready
    for node in ("risk_metrics", 
                 "technical_analysis", 
                 "market_regime", 
                 "momentum", 
                 "liquidity", 
                 "correlation", 
                 "news_sentiment"):
        graph.add_edge("portfolio_snapshot", node)
        graph.add_edge(node, "strategy")
        
    # fan-in: strategy waits for all seven nodes above before running
    graph.add_edge("strategy", "critic")
    graph.add_edge("critic", "decision_report")
    graph.add_edge("decision_report", END)

    return graph

_compiled_graph = _build_graph().compile()

def run_trading_analysis(symbol: str) -> TradingDecisionState:
    return _compiled_graph.invoke({"symbol": symbol})