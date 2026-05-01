"""Real-time bandwidth monitoring using psutil network counters."""

import asyncio
import logging
import time
from datetime import datetime, timezone

import psutil

from app.core.ws_manager import ws_manager

logger = logging.getLogger(__name__)

POLL_INTERVAL = 1.5  # seconds between samples
_running = False
_task: asyncio.Task | None = None


def _get_interface_stats() -> dict[str, dict]:
    """Get per-interface bytes sent/received."""
    counters = psutil.net_io_counters(pernic=True)
    result = {}
    for name, stats in counters.items():
        # Skip loopback
        if name.lower().startswith("loopback") or name.lower() == "lo":
            continue
        result[name] = {
            "bytes_sent": stats.bytes_sent,
            "bytes_recv": stats.bytes_recv,
        }
    return result


async def _bandwidth_loop() -> None:
    """Poll network counters and broadcast throughput over WebSocket."""
    prev_stats = await asyncio.to_thread(_get_interface_stats)
    prev_time = time.monotonic()

    while _running:
        try:
            await asyncio.sleep(POLL_INTERVAL)

            current_stats = await asyncio.to_thread(_get_interface_stats)
            current_time = time.monotonic()
            elapsed = current_time - prev_time

            if elapsed <= 0:
                prev_stats = current_stats
                prev_time = current_time
                continue

            interfaces = {}
            total_download_mbps = 0.0
            total_upload_mbps = 0.0

            for name in current_stats:
                if name not in prev_stats:
                    continue
                bytes_recv_diff = current_stats[name]["bytes_recv"] - prev_stats[name]["bytes_recv"]
                bytes_sent_diff = current_stats[name]["bytes_sent"] - prev_stats[name]["bytes_sent"]

                dl_mbps = round((bytes_recv_diff * 8) / (elapsed * 1_000_000), 3)
                ul_mbps = round((bytes_sent_diff * 8) / (elapsed * 1_000_000), 3)

                # Only include interfaces with any traffic
                if dl_mbps > 0 or ul_mbps > 0 or name in prev_stats:
                    interfaces[name] = {
                        "download_mbps": dl_mbps,
                        "upload_mbps": ul_mbps,
                    }
                    total_download_mbps += dl_mbps
                    total_upload_mbps += ul_mbps

            if ws_manager.active_connections:
                await ws_manager.broadcast({
                    "type": "bandwidth_update",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "total_download_mbps": round(total_download_mbps, 3),
                        "total_upload_mbps": round(total_upload_mbps, 3),
                        "interfaces": interfaces,
                    },
                })

            prev_stats = current_stats
            prev_time = current_time
        except Exception as e:
            logger.error("Bandwidth monitor error: %s", e, exc_info=True)


def start_bandwidth_monitor() -> None:
    """Start the background bandwidth monitoring loop."""
    global _running, _task
    if _running:
        return
    _running = True
    _task = asyncio.get_event_loop().create_task(_bandwidth_loop())
    logger.info("Bandwidth monitor started (every %.1fs)", POLL_INTERVAL)


def stop_bandwidth_monitor() -> None:
    """Stop the background bandwidth monitoring loop."""
    global _running, _task
    _running = False
    if _task and not _task.done():
        _task.cancel()
    _task = None
    logger.info("Bandwidth monitor stopped")
