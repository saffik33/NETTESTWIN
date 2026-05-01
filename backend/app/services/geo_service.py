"""IP geolocation service with in-memory cache for traceroute map."""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Simple in-memory cache: IP -> GeoLocation
_cache: dict[str, "GeoLocation | None"] = {}

GEO_API_URL = "https://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,isp,as,query"
BATCH_API_URL = "https://ip-api.com/batch?fields=status,country,city,lat,lon,isp,as,query"


@dataclass
class GeoLocation:
    ip: str
    lat: float
    lon: float
    city: str | None
    country: str | None
    isp: str | None
    asn: str | None


def _is_private_ip(ip: str) -> bool:
    """Check if an IP is in a private/reserved range."""
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    try:
        first, second = int(parts[0]), int(parts[1])
    except ValueError:
        return True

    if first == 10:
        return True
    if first == 172 and 16 <= second <= 31:
        return True
    if first == 192 and second == 168:
        return True
    if first == 127:
        return True
    if first == 169 and second == 254:
        return True
    return False


async def geolocate_ip(ip: str) -> GeoLocation | None:
    """Look up geolocation for a single IP. Returns None for private IPs or failures."""
    if _is_private_ip(ip):
        return None

    if ip in _cache:
        return _cache[ip]

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(GEO_API_URL.format(ip=ip))
            data = resp.json()

        if data.get("status") == "success":
            geo = GeoLocation(
                ip=data["query"],
                lat=data["lat"],
                lon=data["lon"],
                city=data.get("city"),
                country=data.get("country"),
                isp=data.get("isp"),
                asn=data.get("as"),
            )
            _cache[ip] = geo
            return geo

        _cache[ip] = None
        return None
    except Exception as e:
        logger.debug("Geolocation failed for %s: %s", ip, e)
        _cache[ip] = None
        return None


async def geolocate_batch(ips: list[str]) -> dict[str, GeoLocation | None]:
    """Batch geolocate multiple IPs. Uses cache and batch API."""
    result: dict[str, GeoLocation | None] = {}
    uncached = []

    for ip in ips:
        if _is_private_ip(ip):
            result[ip] = None
        elif ip in _cache:
            result[ip] = _cache[ip]
        else:
            uncached.append(ip)

    if not uncached:
        return result

    # ip-api.com allows batch of up to 100 IPs
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                BATCH_API_URL,
                json=[{"query": ip} for ip in uncached[:100]],
            )
            batch_data = resp.json()

        for item in batch_data:
            ip = item.get("query", "")
            if item.get("status") == "success":
                geo = GeoLocation(
                    ip=ip,
                    lat=item["lat"],
                    lon=item["lon"],
                    city=item.get("city"),
                    country=item.get("country"),
                    isp=item.get("isp"),
                    asn=item.get("as"),
                )
                _cache[ip] = geo
                result[ip] = geo
            else:
                _cache[ip] = None
                result[ip] = None
    except Exception as e:
        logger.warning("Batch geolocation failed: %s", e)
        for ip in uncached:
            result[ip] = None

    return result
