"""
PrintBot AI - Agent Intelligence Bus
=====================================
Shared in-memory state for real-time agent-to-agent communication.

Agents WRITE:  bus.publish("design", "latest_keywords", [...])
Agents READ:   bus.get("design", "latest_keywords")
Orchestrator:  bus.set_mode() / bus.set_override() / bus.log_decision()
Dashboard:     bus.snapshot()
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ── System modes ──────────────────────────────────────────────────────────────

class SystemMode(str, Enum):
    DESIGN_MODE      = "design"       # Too few products — generate first
    SELL_MODE        = "sell"         # Products exist — pivot all to selling
    OUTREACH_MODE    = "outreach"     # Products exist but 0 orders — acquire customers
    FULFILLMENT_MODE = "fulfillment"  # Paid-order backlog — ship first


MODE_LABELS = {
    SystemMode.DESIGN_MODE:      "Design & Build",
    SystemMode.SELL_MODE:        "Sell & Scale",
    SystemMode.OUTREACH_MODE:    "Aggressive Outreach",
    SystemMode.FULFILLMENT_MODE: "Fulfillment First",
}

MODE_COLORS = {
    SystemMode.DESIGN_MODE:      "blue",
    SystemMode.SELL_MODE:        "green",
    SystemMode.OUTREACH_MODE:    "orange",
    SystemMode.FULFILLMENT_MODE: "red",
}


# ── Metric snapshot ───────────────────────────────────────────────────────────

@dataclass
class StoreMetrics:
    total_products:     int   = 0
    approved_products:  int   = 0
    pending_designs:    int   = 0
    total_orders_today: int   = 0
    total_orders_week:  int   = 0
    total_revenue:      float = 0.0
    fulfillment_backlog: int  = 0
    social_posts_today: int   = 0
    collected_at: datetime = field(default_factory=datetime.utcnow)


# ── Intelligence flow (agent → agent message) ─────────────────────────────────

@dataclass
class IntelligenceFlow:
    from_agent:   str
    to_agent:     str
    signal:       str       # e.g. "3 new trend keywords"
    data:         Any       = None
    published_at: datetime  = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "from":  self.from_agent,
            "to":    self.to_agent,
            "signal": self.signal,
            "at":    self.published_at.isoformat(),
        }


# ── Singleton bus ─────────────────────────────────────────────────────────────

class IntelligenceBus:
    """
    Module-level singleton shared by every agent and the MasterOrchestrator.
    Thread-safe enough for asyncio single-event-loop usage.
    """
    _instance: Optional["IntelligenceBus"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.mode: SystemMode             = SystemMode.DESIGN_MODE
        self.metrics: StoreMetrics        = StoreMetrics()
        self.strategy_summary: str        = "Master Orchestrator initialising…"
        self.priority_queue: List[str]    = []
        self.insights: Dict[str, Dict[str, Any]] = {}   # agent → {key: value}
        self.overrides: Dict[str, Dict[str, Any]] = {}  # agent → runtime params
        self.decisions: List[Dict]        = []           # rolling last-50 decisions
        self.flows: List[IntelligenceFlow] = []          # agent↔agent messages
        self.last_updated: datetime       = datetime.utcnow()
        self.agent_collaboration: Dict[str, str] = {}   # agent → current task desc

    # ── Write (agents call these) ─────────────────────────────────────────────

    def publish(self, agent: str, key: str, value: Any):
        """Agent publishes a piece of intelligence for others to read."""
        if agent not in self.insights:
            self.insights[agent] = {}
        self.insights[agent][key] = value
        self.insights[agent]["_updated"] = datetime.utcnow().isoformat()

    def emit_flow(self, from_agent: str, to_agent: str, signal: str, data: Any = None):
        """Record an intelligence flow between two agents (shown on dashboard)."""
        flow = IntelligenceFlow(from_agent, to_agent, signal, data)
        self.flows.insert(0, flow)
        if len(self.flows) > 100:
            self.flows.pop()

    def set_collaboration(self, agent: str, task: str):
        """Agent declares what it is currently doing (shown on dashboard)."""
        self.agent_collaboration[agent] = task

    # ── Write (MasterOrchestrator calls these) ───────────────────────────────

    def set_mode(self, mode: SystemMode, strategy: str, queue: List[str]):
        self.mode = mode
        self.strategy_summary = strategy
        self.priority_queue = queue
        self.last_updated = datetime.utcnow()

    def set_override(self, agent: str, **kwargs):
        """Override an agent's runtime parameters (interval_multiplier, etc.)."""
        self.overrides[agent] = {**self.overrides.get(agent, {}), **kwargs}

    def log_decision(self, decision: Dict):
        self.decisions.insert(0, decision)
        if len(self.decisions) > 50:
            self.decisions.pop()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get(self, agent: str, key: str, default: Any = None) -> Any:
        return self.insights.get(agent, {}).get(key, default)

    def get_override(self, agent: str, key: str, default: Any = None) -> Any:
        return self.overrides.get(agent, {}).get(key, default)

    # ── Snapshot (API / dashboard) ────────────────────────────────────────────

    def snapshot(self) -> Dict:
        m = self.metrics
        return {
            "mode":           str(self.mode),
            "mode_label":     MODE_LABELS.get(self.mode, self.mode),
            "mode_color":     MODE_COLORS.get(self.mode, "gray"),
            "strategy":       self.strategy_summary,
            "priority_queue": self.priority_queue,
            "metrics": {
                "total_products":     m.total_products,
                "approved_products":  m.approved_products,
                "pending_designs":    m.pending_designs,
                "orders_today":       m.total_orders_today,
                "orders_week":        m.total_orders_week,
                "revenue":            round(m.total_revenue, 2),
                "fulfillment_backlog": m.fulfillment_backlog,
                "social_posts_today": m.social_posts_today,
            },
            "agent_insights": {
                agent: {k: v for k, v in data.items() if not k.startswith("_")}
                for agent, data in self.insights.items()
            },
            "agent_collaboration": self.agent_collaboration,
            "intelligence_flows": [f.to_dict() for f in self.flows[:20]],
            "recent_decisions":   self.decisions[:10],
            "last_updated":       self.last_updated.isoformat(),
        }


# Module-level singleton — import this everywhere
bus = IntelligenceBus()
