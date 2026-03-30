"""
AI Agents Package

This package contains all AI agents for the Review Bot system.
Each agent is in its own subfolder with its implementation, states, and tests.

Available Agents:
- review_agent: Main review agent for conducting project reviews
- (Future) optimization_agent: For checklist optimization
- (Future) analytics_agent: For trend analysis and insights
"""

from app.agents.review_agent.review_agent import ReviewAgent
from app.agents.strategy_router_agent import StrategyRouter

__all__ = ["ReviewAgent", "StrategyRouter"]
