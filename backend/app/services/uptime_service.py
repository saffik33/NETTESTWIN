"""Lightweight uptime monitoring: periodic ping probes + outage detection."""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ws_manager import ws_manager
from app.database import AsyncSessionLocal
from app.models.uptime import OutageEvent, UptimeProbe

logger = logging.getLogger(__name__)

PROBE_INTERVAL = 30  # seconds
PROBE_TARGET = "8.8.8.8"
OUTAGE_THRESHOLD = 2  # consecutive failures to declare outage

_running = False
_task: asyncio.Task | None = None
_consecutive_failures = 0
_current_outage_id: int | None = None


async def _ping_probe(target: str) -> tuple[bool, float | None]:
    """Single ICMP probe. Returns (is_up, latency_ms)."""
    try:
        process = await asyncio.create_subprocess_exec(
            "ping", "-n", "1", "-w", "3000", target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5)
        output = stdout.decode("utf-8", errors="replace")

        if process.returncode == 0 and "TTL=" in output.upper():
            import re
            match = re.search(r"time[=<]([\d.]+)\s*ms", output, re.IGNORECASE)
            latency = float(match.group(1)) if match else None
            return True, latency
        return False, None
    except Exception:
        return False, None


async def _probe_loop() -> None:
    """Main probe loop running every PROBE_INTERVAL seconds."""
    global _consecutive_failures, _current_outage_id

    while _running:
        try:
            is_up, latency = await _ping_probe(PROBE_TARGET)

            async with AsyncSessionLocal() as db:
                probe = UptimeProbe(
                    is_up=is_up,
                    latency_ms=latency,
                    target=PROBE_TARGET,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(probe)

                if not is_up:
                    _consecutive_failures += 1
                    if _consecutive_failures >= OUTAGE_THRESHOLD and _current_outage_id is None:
                        # Start new outage
                        outage = OutageEvent(
                            started_at=datetime.now(timezone.utc),
                            resolved=False,
                        )
                        db.add(outage)
                        await db.commit()
                        await db.refresh(outage)
                        _current_outage_id = outage.id
                        logger.warning("Outage detected (id=%d)", outage.id)
                        await ws_manager.broadcast({
                            "type": "outage_started",
                            "payload": {"outage_id": outage.id},
                        })
                else:
                    if _current_outage_id is not None:
                        # Resolve outage
                        outage = await db.get(OutageEvent, _current_outage_id)
                        if outage:
                            outage.ended_at = datetime.now(timezone.utc)
                            outage.duration_seconds = int(
                                (outage.ended_at - outage.started_at).total_seconds()
                            )
                            outage.resolved = True
                            logger.info(
                                "Outage %d resolved after %d seconds",
                                _current_outage_id,
                                outage.duration_seconds,
                            )
                            await ws_manager.broadcast({
                                "type": "outage_resolved",
                                "payload": {
                                    "outage_id": _current_outage_id,
                                    "duration_seconds": outage.duration_seconds,
                                },
                            })
                        _current_outage_id = None
                    _consecutive_failures = 0

                await db.commit()
        except Exception as e:
            logger.error("Uptime probe error: %s", e, exc_info=True)

        await asyncio.sleep(PROBE_INTERVAL)


def start_uptime_monitor() -> None:
    """Start the background uptime monitoring loop."""
    global _running, _task
    if _running:
        return
    _running = True
    _task = asyncio.get_event_loop().create_task(_probe_loop())
    logger.info("Uptime monitor started (every %ds)", PROBE_INTERVAL)


def stop_uptime_monitor() -> None:
    """Stop the background uptime monitoring loop."""
    global _running, _task
    _running = False
    if _task and not _task.done():
        _task.cancel()
    _task = None
    logger.info("Uptime monitor stopped")


async def get_uptime_stats(db: AsyncSession, period: str = "24h") -> dict:
    """Calculate uptime statistics for a given period."""
    period_map = {"1h": 1 / 24, "24h": 1, "7d": 7, "30d": 30}
    days = period_map.get(period, 1)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total probes and successful probes
    result = (await db.execute(
        select(
            func.count().label("total"),
            func.sum(func.cast(UptimeProbe.is_up, Integer)).label("up_count"),
            func.avg(UptimeProbe.latency_ms).label("avg_latency"),
        ).where(UptimeProbe.timestamp >= since)
    )).one()

    total = result.total or 0
    up_count = result.up_count or 0
    uptime_pct = round((up_count / total * 100), 2) if total > 0 else None

    # Outage events
    outages = (await db.execute(
        select(OutageEvent)
        .where(OutageEvent.started_at >= since)
        .order_by(OutageEvent.started_at.desc())
    )).scalars().all()

    total_downtime = sum(o.duration_seconds or 0 for o in outages if o.resolved)

    return {
        "period": period,
        "uptime_pct": uptime_pct,
        "total_probes": total,
        "successful_probes": up_count,
        "avg_probe_latency_ms": round(result.avg_latency, 2) if result.avg_latency else None,
        "outage_count": len(outages),
        "total_downtime_seconds": total_downtime,
        "outages": [
            {
                "id": o.id,
                "started_at": o.started_at.isoformat(),
                "ended_at": o.ended_at.isoformat() if o.ended_at else None,
                "duration_seconds": o.duration_seconds,
                "resolved": o.resolved,
            }
            for o in outages
        ],
    }


async def get_probe_history(db: AsyncSession, limit: int = 120) -> list[dict]:
    """Get recent probe results for visualization."""
    result = await db.execute(
        select(UptimeProbe)
        .order_by(UptimeProbe.timestamp.desc())
        .limit(limit)
    )
    probes = result.scalars().all()
    return [
        {
            "is_up": p.is_up,
            "latency_ms": p.latency_ms,
            "timestamp": p.timestamp.isoformat(),
        }
        for p in reversed(probes)
    ]
