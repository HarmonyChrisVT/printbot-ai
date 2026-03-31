"""
PrintBot AI - Health Monitor Agent
=====================================
Watches all agent logs for errors, reports them to the Master Orchestrator
via the Intelligence Bus, and logs a daily summary of issues found and fixed.

Schedule: Every 5 minutes (passive watch). Daily summary at 00:00 UTC.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from database.models import AgentLog, SystemEvent, get_session
from agents.intelligence_bus import bus

logger = logging.getLogger(__name__)

# How often to scan for new errors (seconds)
SCAN_INTERVAL = 300  # 5 minutes

# Error threshold — alert if any agent has this many errors in one scan window
ERROR_ALERT_THRESHOLD = 3


class HealthMonitorAgent:
    """
    Watches AgentLog for errors across all agents.
    Publishes health signals to the Intelligence Bus.
    Writes a daily summary SystemEvent.
    """

    def __init__(self, db_session):
        self.session = db_session
        self.running = False
        self._last_scan_at: datetime = datetime.utcnow() - timedelta(seconds=SCAN_INTERVAL)
        self._last_daily_summary_date: str = ""  # YYYY-MM-DD
        # Tracks cumulative per-agent error counts since last daily summary
        self._daily_error_counts: Dict[str, int] = {}
        self._daily_fix_counts: Dict[str, int] = {}

    async def run(self):
        self.running = True
        logger.info("HealthMonitorAgent started")
        print("🏥 Health Monitor Agent started")

        while self.running:
            try:
                await self._scan_errors()
                await self._maybe_daily_summary()
                await asyncio.sleep(SCAN_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"HealthMonitorAgent error: {e}")
                await asyncio.sleep(60)

    def stop(self):
        self.running = False
        print("🛑 Health Monitor Agent stopped")

    # ── Error scan ─────────────────────────────────────────────────────────────

    async def _scan_errors(self):
        """Scan AgentLog for errors since last scan and publish to bus."""
        now = datetime.utcnow()
        since = self._last_scan_at

        try:
            errors: List[AgentLog] = (
                self.session.query(AgentLog)
                .filter(
                    AgentLog.status == "error",
                    AgentLog.created_at >= since,
                )
                .order_by(AgentLog.created_at.desc())
                .all()
            )

            # Also count recent successes (used to infer "fixed" items)
            recent_successes: List[AgentLog] = (
                self.session.query(AgentLog)
                .filter(
                    AgentLog.status == "success",
                    AgentLog.created_at >= since,
                )
                .all()
            )
        except Exception as e:
            logger.warning(f"HealthMonitor: DB query failed: {e}")
            self._last_scan_at = now
            return

        # Group errors by agent
        errors_by_agent: Dict[str, List[AgentLog]] = {}
        for err in errors:
            errors_by_agent.setdefault(err.agent_name, []).append(err)

        # Group successes by agent (for "fixed" heuristic)
        successes_by_agent: Dict[str, int] = {}
        for suc in recent_successes:
            successes_by_agent[suc.agent_name] = successes_by_agent.get(suc.agent_name, 0) + 1

        total_errors = len(errors)
        healthy_agents = []
        sick_agents = []

        for agent_name, agent_errors in errors_by_agent.items():
            count = len(agent_errors)
            latest = agent_errors[0]

            # Accumulate daily totals
            self._daily_error_counts[agent_name] = (
                self._daily_error_counts.get(agent_name, 0) + count
            )

            # Publish per-agent error signal to bus
            bus.publish(
                "health_monitor",
                f"{agent_name}_error_count",
                count,
            )
            bus.emit_flow(
                "health_monitor",
                "master_orchestrator",
                f"⚠️  {agent_name}: {count} error(s) in last 5 min — "
                f"latest: {latest.action} | {_truncate(latest.details)}",
                {"agent": agent_name, "count": count, "action": latest.action},
            )
            sick_agents.append(agent_name)

            if count >= ERROR_ALERT_THRESHOLD:
                logger.warning(
                    f"HealthMonitor ALERT: {agent_name} had {count} errors in last 5 min"
                )
                print(
                    f"🚨 Health Monitor: {agent_name} has {count} errors in last 5 min — "
                    f"latest: {latest.action}"
                )

        # Track fixes (agents that had errors before but now have successes)
        for agent_name, suc_count in successes_by_agent.items():
            if agent_name in errors_by_agent:
                self._daily_fix_counts[agent_name] = (
                    self._daily_fix_counts.get(agent_name, 0) + suc_count
                )

        # Agents with zero errors
        all_known = set(self.session.query(AgentLog.agent_name).distinct().all())
        all_known = {r[0] for r in all_known}
        healthy_agents = [a for a in all_known if a not in errors_by_agent]

        # Publish overall health summary to bus
        bus.publish("health_monitor", "total_errors_last_5min", total_errors)
        bus.publish("health_monitor", "sick_agents", sick_agents)
        bus.publish("health_monitor", "healthy_agents", healthy_agents)

        if total_errors == 0:
            print(f"✅ Health Monitor: All clear — no errors in last 5 min")
        else:
            print(
                f"⚠️  Health Monitor: {total_errors} error(s) across "
                f"{len(sick_agents)} agent(s): {', '.join(sick_agents)}"
            )

        self._last_scan_at = now

    # ── Daily summary ──────────────────────────────────────────────────────────

    async def _maybe_daily_summary(self):
        """Write a daily summary SystemEvent at midnight UTC."""
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        if today_str == self._last_daily_summary_date:
            return
        # Only trigger after midnight transitions (not on first run)
        if self._last_daily_summary_date == "":
            self._last_daily_summary_date = today_str
            return

        await self._write_daily_summary(self._last_daily_summary_date)
        self._last_daily_summary_date = today_str
        # Reset accumulators for the new day
        self._daily_error_counts = {}
        self._daily_fix_counts = {}

    async def _write_daily_summary(self, date_str: str):
        """Persist a daily health summary to SystemEvent."""
        total_errors = sum(self._daily_error_counts.values())
        total_fixes = sum(self._daily_fix_counts.values())

        lines = [f"Health Monitor Daily Summary — {date_str}"]
        lines.append(f"Total errors detected: {total_errors}")
        lines.append(f"Total agent recoveries (success after error): {total_fixes}")

        if self._daily_error_counts:
            lines.append("Errors by agent:")
            for agent, count in sorted(
                self._daily_error_counts.items(), key=lambda x: x[1], reverse=True
            ):
                fixes = self._daily_fix_counts.get(agent, 0)
                lines.append(f"  {agent}: {count} errors, {fixes} recoveries")
        else:
            lines.append("No errors detected — all agents healthy all day ✅")

        summary_text = "\n".join(lines)
        print(f"\n📋 {summary_text}\n")
        logger.info(summary_text)

        try:
            event = SystemEvent(
                event_type="health_monitor_daily_summary",
                severity="info" if total_errors == 0 else "warning",
                message=f"Health summary {date_str}: {total_errors} errors, {total_fixes} recoveries",
                details={
                    "date": date_str,
                    "total_errors": total_errors,
                    "total_fixes": total_fixes,
                    "errors_by_agent": self._daily_error_counts,
                    "fixes_by_agent": self._daily_fix_counts,
                    "full_summary": summary_text,
                },
            )
            self.session.add(event)
            self.session.commit()
        except Exception as e:
            logger.error(f"HealthMonitor: failed to write daily summary: {e}")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _truncate(obj: Any, max_len: int = 120) -> str:
    text = str(obj) if obj is not None else ""
    return text[:max_len] + ("…" if len(text) > max_len else "")
