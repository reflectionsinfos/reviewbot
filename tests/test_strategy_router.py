from types import SimpleNamespace

from app.services.autonomous_review.strategy_router import StrategyConfig, StrategyRouter


def test_strategy_router_defaults_to_llm_analysis_for_documentation_items():
    router = StrategyRouter()
    item = SimpleNamespace(
        id=101,
        area="Technical Documentation",
        question="Are HLD and LLD available for all key modules and services?",
    )

    config = router.route(item)

    assert config.strategy == "llm_analysis"
    assert "HLD" in config.context_keywords or "LLD" in config.context_keywords


def test_strategy_router_uses_reviewer_override_before_default_llm():
    override = StrategyConfig(strategy="human_required", skip_reason="Manual review only")
    router = StrategyRouter(db_rules={202: override})
    item = SimpleNamespace(
        id=202,
        area="Security Architecture",
        question="Are security reviews and tests planned and tracked?",
    )

    config = router.route(item)

    assert config.strategy == "human_required"
    assert config.skip_reason == "Manual review only"
