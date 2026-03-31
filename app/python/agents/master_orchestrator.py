"""
PrintBot AI - Master Orchestrator Agent
========================================
The "boss" agent that sits above all other agents.

Responsibilities:
  • Every 5 minutes: gather store health metrics from the database
  • Determine the current SystemMode (DESIGN / SELL / OUTREACH / FULFILLMENT)
  • Set priority queues — which agents work hardest in which mode
  • Publish agent-override parameters to the IntelligenceBus
  • Derive cross-agent intelligence from DB data and share it via the bus
    (Design → Content Writer, Social → Affiliate, Competitor Spy → Pricing …)
  • Log every decision to SystemEvent for audit trail
  • Expose get_status() for the dashboard API endpoint
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import sqlalchemy as sa

from config.settings import config
from database.models import (
    Product, Design, Order, Sale, SocialPost,
    TrendData, AgentLog, SystemEvent, CompetitorPrice,
)
from agents.intelligence_bus import IntelligenceBus, StoreMetrics, SystemMode, bus

logger = logging.getLogger(__name__)

# ── Decision thresholds ───────────────────────────────────────────────────────
MIN_PRODUCTS_TO_SELL       = 3   # need this many approved products before SELL_MODE
FULFILLMENT_BACKLOG_URGENT = 5   # paid orders unfulfilled → FULFILLMENT_MODE
OUTREACH_THRESHOLD_DAYS    = 7   # products exist but 0 orders in N days → OUTREACH


class MasterOrchestrator:
    """
    Master Orchestrator — evaluated every 5 minutes.
    Holds references to all agent instances; can read their .running flag.
    Does NOT import agent modules (avoids circular imports) — receives them
    as a plain dict from the main orchestrator.
    """

    EVAL_INTERVAL = 300  # seconds between evaluations

    # Expected maximum idle time per agent before it's considered stuck (seconds).
    # If an agent has no log entry newer than this, the orchestrator will reassign
    # it a high-priority task from the current mode's queue.
    AGENT_IDLE_TIMEOUT: Dict[str, int] = {
        "design":               1800 * 2,   # 30-min interval × 2
        "pricing":              7200 * 2,   # 2-hr interval × 2
        "social":               21600 * 2,  # 6-hr interval × 2
        "fulfillment":          300 * 3,    # 5-min interval × 3
        "b2b":                  3600 * 2,
        "customer_engagement":  3600 * 2,
        "competitor_spy":       7200 * 2,
        "affiliate":            86400 * 2,
        "content_writer":       1800 * 2,
        "customer_service":     60 * 3,
        "inventory_prediction": 86400 * 2,
    }

    # ── Priority queues per mode (front = highest priority) ───────────────────
    PRIORITY_QUEUES: Dict[SystemMode, List[str]] = {
        SystemMode.DESIGN_MODE: [
            "design", "content_writer", "pricing",
            "competitor_spy", "inventory_prediction",
            "social", "affiliate", "customer_engagement",
            "b2b", "fulfillment", "customer_service",
        ],
        SystemMode.SELL_MODE: [
            "social", "affiliate", "customer_engagement", "b2b",
            "pricing", "content_writer", "competitor_spy",
            "fulfillment", "customer_service",
            "design", "inventory_prediction",
        ],
        SystemMode.OUTREACH_MODE: [
            "social", "affiliate", "b2b", "customer_engagement",
            "pricing", "content_writer", "competitor_spy",
            "fulfillment", "customer_service",
            "design", "inventory_prediction",
        ],
        SystemMode.FULFILLMENT_MODE: [
            "fulfillment", "customer_service", "customer_engagement",
            "social", "pricing", "affiliate", "b2b",
            "content_writer", "competitor_spy",
            "design", "inventory_prediction",
        ],
    }

    # ── Interval multipliers per mode (< 1.0 = work faster, > 1.0 = slow down) ─
    INTERVAL_MULTIPLIERS: Dict[SystemMode, Dict[str, float]] = {
        SystemMode.DESIGN_MODE: {
            "design": 0.5, "content_writer": 0.6, "pricing": 0.7,
            "social": 1.5, "affiliate": 2.0, "b2b": 2.0,
            "fulfillment": 2.0,
        },
        SystemMode.SELL_MODE: {
            "social": 0.4, "affiliate": 0.4, "customer_engagement": 0.5,
            "b2b": 0.5, "pricing": 0.6, "content_writer": 0.7,
            "design": 3.0, "inventory_prediction": 1.5,
        },
        SystemMode.OUTREACH_MODE: {
            "social": 0.3, "affiliate": 0.3, "b2b": 0.4,
            "customer_engagement": 0.4, "pricing": 0.6,
            "design": 4.0, "fulfillment": 2.0,
        },
        SystemMode.FULFILLMENT_MODE: {
            "fulfillment": 0.3, "customer_service": 0.4,
            "customer_engagement": 0.5,
            "social": 2.0, "design": 5.0, "b2b": 3.0,
        },
    }

    # ── Collaboration task descriptions per mode ───────────────────────────────
    COLLABORATION_TASKS: Dict[SystemMode, Dict[str, str]] = {
        SystemMode.DESIGN_MODE: {
            "design":               "Scanning trends & generating AI designs",
            "content_writer":       "Writing SEO descriptions for new designs",
            "pricing":              "Setting competitive launch prices",
            "competitor_spy":       "Researching competitor product gaps",
            "social":               "Building initial brand presence",
            "affiliate":            "Standby — waiting for products",
            "b2b":                  "Standby — waiting for products",
            "fulfillment":          "Standby — no orders yet",
            "customer_service":     "Ready for first customers",
            "inventory_prediction": "Baseline forecasting",
            "customer_engagement":  "Warming up email sequences",
        },
        SystemMode.SELL_MODE: {
            "social":               "Posting products — maximum reach",
            "affiliate":            "Activating affiliate network",
            "customer_engagement":  "Running retention & upsell campaigns",
            "b2b":                  "Pitching bulk & corporate orders",
            "pricing":              "Dynamic competitor-based repricing",
            "content_writer":       "A/B testing product descriptions",
            "competitor_spy":       "Monitoring competitor responses",
            "fulfillment":          "Processing & shipping orders",
            "customer_service":     "Handling customer inquiries",
            "design":               "Standby — sufficient products",
            "inventory_prediction": "Forecasting restock needs",
        },
        SystemMode.OUTREACH_MODE: {
            "social":               "Aggressive posting — 3× normal frequency",
            "affiliate":            "Recruiting new affiliates urgently",
            "b2b":                  "Cold outreach to bulk buyers",
            "customer_engagement":  "Re-engagement & abandoned cart recovery",
            "pricing":              "Promotional pricing to attract first sales",
            "content_writer":       "Creating viral & SEO-optimised content",
            "competitor_spy":       "Identifying competitor weaknesses to exploit",
            "fulfillment":          "Ready to ship on first order",
            "customer_service":     "Proactive outreach to inquiries",
            "design":               "Paused — focus is on selling existing products",
            "inventory_prediction": "Standby",
        },
        SystemMode.FULFILLMENT_MODE: {
            "fulfillment":          "URGENT: processing all pending orders",
            "customer_service":     "Handling order-related inquiries",
            "customer_engagement":  "Sending shipping & tracking updates",
            "social":               "Maintaining minimal presence",
            "pricing":              "Monitoring for anomalies",
            "affiliate":            "Tracking commissions",
            "b2b":                  "Paused during backlog clearance",
            "design":               "Paused — fulfillment is primary",
            "competitor_spy":       "Passive monitoring only",
            "inventory_prediction": "Assessing stock after backlog clears",
            "content_writer":       "Paused",
        },
    }

    def __init__(self, db_session, agents: Dict[str, Any]):
        self.session     = db_session
        self.agents      = agents          # {name: agent_instance}
        self.bus         = bus             # shared singleton
        self.running     = False
        self.current_mode: SystemMode = SystemMode.DESIGN_MODE
        self.last_eval:   Optional[datetime] = None
        self.eval_count:  int = 0

    # ── Main loop ─────────────────────────────────────────────────────────────

    async def run(self):
        self.running = True
        logger.info("MasterOrchestrator started — monitoring all agents every 5 min")
        await self._evaluate()          # immediate first evaluation
        while self.running:
            try:
                await asyncio.sleep(self.EVAL_INTERVAL)
                await self._evaluate()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MasterOrchestrator error: {e}")
                await asyncio.sleep(60)

    def stop(self):
        self.running = False

    # ── Evaluation cycle ──────────────────────────────────────────────────────

    async def _evaluate(self):
        metrics    = self._gather_metrics()
        self.bus.metrics = metrics

        new_mode   = self._determine_mode(metrics)
        changed    = new_mode != self.current_mode
        self.current_mode = new_mode

        strategy   = self._build_strategy(metrics, new_mode, changed)
        queue      = self.PRIORITY_QUEUES[new_mode]

        # Push to bus
        self.bus.set_mode(new_mode, strategy, queue)

        # Override agent intervals
        self._apply_overrides(new_mode)

        # Share cross-agent intelligence
        self._share_intelligence(metrics)

        # Set collaboration task descriptions
        for agent, task in self.COLLABORATION_TASKS.get(new_mode, {}).items():
            self.bus.set_collaboration(agent, task)

        # Detect idle agents and reassign them work
        self._reassign_idle_agents(new_mode)

        # Decide and log
        decision = {
            "at":           datetime.utcnow().isoformat(),
            "mode":         str(new_mode),
            "mode_label":   new_mode.replace("_", " ").title(),
            "strategy":     strategy,
            "mode_changed": changed,
            "metrics": {
                "approved_products":  metrics.approved_products,
                "orders_today":       metrics.total_orders_today,
                "orders_week":        metrics.total_orders_week,
                "revenue":            round(metrics.total_revenue, 2),
                "backlog":            metrics.fulfillment_backlog,
            },
        }
        self.bus.log_decision(decision)

        if changed:
            self._log_system_event(
                f"Mode changed → {new_mode}: {strategy}",
                severity="info",
            )
            logger.info(f"MasterOrchestrator MODE CHANGE → {new_mode}")

        self.last_eval  = datetime.utcnow()
        self.eval_count += 1
        logger.info(f"MasterOrchestrator [{new_mode}] eval #{self.eval_count}: {strategy[:80]}")

    # ── Metrics ───────────────────────────────────────────────────────────────

    def _gather_metrics(self) -> StoreMetrics:
        now     = datetime.utcnow()
        today   = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        try:
            approved = self.session.query(Product).filter(
                Product.is_active == True,
                Product.is_approved == True,
            ).count()

            total_p = self.session.query(Product).filter(
                Product.is_active == True
            ).count()

            pending_d = self.session.query(Design).filter(
                Design.status == "pending"
            ).count()

            orders_today = self.session.query(Order).filter(
                Order.created_at >= today
            ).count()

            orders_week = self.session.query(Order).filter(
                Order.created_at >= week_ago
            ).count()

            revenue = self.session.query(
                sa.func.sum(Sale.revenue)
            ).scalar() or 0.0

            backlog = self.session.query(Order).filter(
                Order.fulfillment_status.in_(["unfulfilled", "partial"]),
                Order.financial_status == "paid",
            ).count()

            posts_today = self.session.query(SocialPost).filter(
                SocialPost.posted_at >= today,
                SocialPost.status == "posted",
            ).count()

        except Exception as e:
            logger.warning(f"MasterOrchestrator metric query error: {e}")
            return StoreMetrics()

        return StoreMetrics(
            total_products=total_p,
            approved_products=approved,
            pending_designs=pending_d,
            total_orders_today=orders_today,
            total_orders_week=orders_week,
            total_revenue=float(revenue),
            fulfillment_backlog=backlog,
            social_posts_today=posts_today,
        )

    # ── Mode determination ────────────────────────────────────────────────────

    def _determine_mode(self, m: StoreMetrics) -> SystemMode:
        # Paid-order backlog is always the most urgent signal
        if m.fulfillment_backlog >= FULFILLMENT_BACKLOG_URGENT:
            return SystemMode.FULFILLMENT_MODE
        # Not enough products → design first
        if m.approved_products < MIN_PRODUCTS_TO_SELL:
            return SystemMode.DESIGN_MODE
        # Products exist but no sales traction → outreach
        if m.approved_products >= MIN_PRODUCTS_TO_SELL and m.total_orders_week == 0:
            return SystemMode.OUTREACH_MODE
        # Products + orders = normal selling mode
        return SystemMode.SELL_MODE

    # ── Strategy narrative ────────────────────────────────────────────────────

    def _build_strategy(self, m: StoreMetrics, mode: SystemMode, changed: bool) -> str:
        narratives = {
            SystemMode.DESIGN_MODE: (
                f"Store has {m.approved_products}/{MIN_PRODUCTS_TO_SELL} minimum products. "
                "Design Agent is primary. All other agents on standby until product threshold is met."
            ),
            SystemMode.SELL_MODE: (
                f"{m.approved_products} products live · {m.total_orders_today} orders today · "
                f"${m.total_revenue:,.2f} lifetime revenue. "
                "Social, Affiliate & B2B agents are primary — selling is the #1 mission."
            ),
            SystemMode.OUTREACH_MODE: (
                f"{m.approved_products} products ready but 0 orders in 7 days. "
                "All agents pivoted to aggressive customer acquisition — Social at 3× frequency."
            ),
            SystemMode.FULFILLMENT_MODE: (
                f"URGENT: {m.fulfillment_backlog} paid orders awaiting fulfilment. "
                "Fulfillment Agent is primary — customer experience and reputation first."
            ),
        }
        prefix = "⚡ MODE CHANGE: " if changed else ""
        return prefix + narratives.get(mode, "Evaluating store health…")

    # ── Overrides ─────────────────────────────────────────────────────────────

    def _apply_overrides(self, mode: SystemMode):
        multipliers = self.INTERVAL_MULTIPLIERS.get(mode, {})
        queue       = self.PRIORITY_QUEUES[mode]
        for agent_name, mult in multipliers.items():
            self.bus.set_override(
                agent_name,
                interval_multiplier=mult,
                priority=queue.index(agent_name) if agent_name in queue else 99,
                mode=str(mode),
            )

    # ── Cross-agent intelligence sharing ─────────────────────────────────────

    def _share_intelligence(self, m: StoreMetrics):
        """Derive intelligence from the DB and route it between agents via the bus."""

        # ── Design → Content Writer & SEO ────────────────────────────────────
        try:
            recent_trends = (
                self.session.query(TrendData)
                .filter(TrendData.design_created == True)
                .order_by(TrendData.collected_at.desc())
                .limit(5)
                .all()
            )
            if recent_trends:
                keywords = [t.keyword for t in recent_trends]
                self.bus.publish("design", "latest_keywords", keywords)
                self.bus.publish("master", "seo_keywords_from_design", keywords)
                self.bus.emit_flow(
                    "design", "content_writer",
                    f"{len(keywords)} trend keywords ready for SEO: {', '.join(keywords[:3])}…",
                    keywords,
                )
        except Exception as e:
            logger.debug(f"Intelligence: design→content_writer: {e}")

        # ── Social → Affiliate & B2B ─────────────────────────────────────────
        try:
            top_post = (
                self.session.query(SocialPost)
                .filter(SocialPost.status == "posted")
                .order_by(
                    (SocialPost.likes + SocialPost.comments * 3 + SocialPost.shares * 5).desc()
                )
                .first()
            )
            if top_post:
                engagement = (top_post.likes + top_post.comments + top_post.shares)
                self.bus.publish("social", "top_post_engagement", engagement)
                self.bus.publish("social", "top_hashtags", top_post.hashtags or [])
                self.bus.emit_flow(
                    "social", "affiliate",
                    f"Top post: {engagement} engagements — route affiliates to this content",
                    {"post_id": top_post.id, "engagement": engagement},
                )
                self.bus.emit_flow(
                    "social", "b2b",
                    f"Social proof available: {engagement} engagements on top post",
                )
        except Exception as e:
            logger.debug(f"Intelligence: social→affiliate: {e}")

        # ── Competitor Spy → Pricing ─────────────────────────────────────────
        try:
            lowest = (
                self.session.query(sa.func.min(CompetitorPrice.price))
                .scalar()
            )
            if lowest:
                self.bus.publish("competitor_spy", "lowest_competitor_price", float(lowest))
                self.bus.publish("master", "competitor_price_floor", float(lowest))
                self.bus.emit_flow(
                    "competitor_spy", "pricing",
                    f"Competitor floor detected at ${lowest:.2f} — adjust margins",
                    {"floor_price": float(lowest)},
                )
        except Exception as e:
            logger.debug(f"Intelligence: competitor_spy→pricing: {e}")

        # ── Fulfillment → Customer Engagement ────────────────────────────────
        if m.fulfillment_backlog > 0:
            self.bus.emit_flow(
                "fulfillment", "customer_engagement",
                f"{m.fulfillment_backlog} orders shipping — trigger tracking update emails",
                {"backlog": m.fulfillment_backlog},
            )

        # ── Master → All: broadcast store health ─────────────────────────────
        self.bus.publish("master", "approved_products",   m.approved_products)
        self.bus.publish("master", "orders_today",        m.total_orders_today)
        self.bus.publish("master", "revenue",             round(m.total_revenue, 2))
        self.bus.publish("master", "current_mode",        str(self.current_mode))
        self.bus.publish("master", "fulfillment_backlog", m.fulfillment_backlog)

    # ── Idle agent detection & reassignment ──────────────────────────────────

    def _reassign_idle_agents(self, mode: SystemMode):
        """
        Check every running agent's last AgentLog entry.
        If an agent hasn't logged anything within its AGENT_IDLE_TIMEOUT window,
        flag it as idle, increase its interval multiplier to 0.1 (run ASAP),
        and emit a directive to the bus so the agent picks up work immediately.
        """
        now = datetime.utcnow()
        queue = self.PRIORITY_QUEUES[mode]
        idle_agents = []

        for agent_name, agent_obj in self.agents.items():
            if not agent_obj.running:
                continue  # stopped agents are not "idle"

            timeout = self.AGENT_IDLE_TIMEOUT.get(agent_name, 3600)

            try:
                last_log = (
                    self.session.query(AgentLog)
                    .filter(AgentLog.agent_name == agent_name)
                    .order_by(AgentLog.created_at.desc())
                    .first()
                )
                last_active = last_log.created_at if last_log else None
            except Exception as e:
                logger.debug(f"Idle check: DB error for {agent_name}: {e}")
                last_active = None

            if last_active is None or (now - last_active).total_seconds() > timeout:
                idle_agents.append(agent_name)
                priority = queue.index(agent_name) if agent_name in queue else 99
                # Push interval multiplier close to 0 so the agent's next sleep
                # expires immediately and it runs its next cycle without waiting
                self.bus.set_override(
                    agent_name,
                    interval_multiplier=0.1,
                    priority=priority,
                    mode=str(mode),
                )
                self.bus.set_collaboration(
                    agent_name,
                    f"[REASSIGNED — idle > {timeout//60}m] "
                    + self.COLLABORATION_TASKS.get(mode, {}).get(agent_name, "Execute primary task"),
                )
                self.bus.emit_flow(
                    "master_orchestrator",
                    agent_name,
                    f"IDLE ALERT: {agent_name} has been inactive for >{timeout//60} min — "
                    f"resuming immediately under {mode} mode",
                    {"idle_agent": agent_name, "timeout_min": timeout // 60},
                )
                elapsed = int((now - last_active).total_seconds() // 60) if last_active else "never"
                logger.warning(
                    f"MasterOrchestrator: {agent_name} IDLE (last active: {elapsed} min ago) — reassigned"
                )
                print(
                    f"♻️  Orchestrator: {agent_name} idle ({elapsed} min) — reassigning under {mode}"
                )

        if idle_agents:
            self.bus.publish("master", "idle_agents", idle_agents)
            self._log_system_event(
                f"Idle agents reassigned: {', '.join(idle_agents)}",
                severity="warning",
            )
        else:
            self.bus.publish("master", "idle_agents", [])

    # ── DB logging ────────────────────────────────────────────────────────────

    def _log_system_event(self, message: str, severity: str = "info"):
        try:
            event = SystemEvent(
                event_type="orchestrator_decision",
                severity=severity,
                message=message,
                details={
                    "mode":       str(self.current_mode),
                    "eval_count": self.eval_count,
                },
            )
            self.session.add(event)
            self.session.commit()
        except Exception as e:
            logger.error(f"Failed to log orchestrator event: {e}")

    # ── API status (dashboard) ────────────────────────────────────────────────

    def get_status(self) -> Dict:
        snap = self.bus.snapshot()
        return {
            "running":          self.running,
            "eval_count":       self.eval_count,
            "last_eval_at":     self.last_eval.isoformat() if self.last_eval else None,
            "next_eval_in":     max(0, self.EVAL_INTERVAL - (
                datetime.utcnow() - self.last_eval
            ).seconds) if self.last_eval else 0,
            **snap,  # mode, strategy, priority_queue, metrics, flows, decisions …
        }
