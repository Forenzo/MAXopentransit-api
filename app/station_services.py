"""Servicios en la estación: split the OSM POI layer into facilities that belong to the
station and services that are merely nearby — so the app never calls a street-corner
pharmacy "en la estación".

Validated against Bogotá (2026-11, 3,288 POIs vs 156 troncal stations): only 4 POIs sit
within 25 m of any station and 23 within 50 m; the median POI is 758 m away. There is no
"inside" cluster to separate by distance. The one honest "station facility" signal is a
tag: 30 POIs are TransMilenio-operated bike parking ("Cicloparqueadero Estación …"), all
tagged on operator/name. So the "en la estación" bucket is decided by the tag, not by a
distance guess; everything else is a smooth gradient presented as "cerca, a X min". See
REFERENCE-APPS.md (TransMi App appendix).
"""
from .geo import haversine_m

WALK_M_PER_MIN = 80.0  # ~1.33 m/s, OTP's default walking speed

# A facility that is part of the station itself. TransMilenio brands its station bike
# parking as operator "TransMilenio" / name "Cicloparqueadero Estación …". Matched on the
# tag, never on distance — distance only confirms it is THIS station's, not another's.
_FACILITY_TOKENS = ("transmilenio", "cicloparqueadero estaci")


def is_station_facility(props: dict) -> bool:
    blob = f"{props.get('operator') or ''} {props.get('name') or ''}".lower()
    return any(tok in blob for tok in _FACILITY_TOKENS)


def _walk_minutes(metres: float) -> int:
    return max(1, round(metres / WALK_M_PER_MIN))


def _decorate(feat: dict, dist: float) -> dict:
    props = {**(feat.get("properties") or {}),
             "distanceMeters": round(dist), "walkMinutes": _walk_minutes(dist)}
    return {**feat, "properties": props}


def station_services(feats: list[dict], lat: float, lon: float, *,
                     at_station_m: float = 150.0, nearby_m: float = 400.0,
                     limit: int = 40) -> tuple[list[dict], list[dict]]:
    """(atStation, nearby), each sorted by distance.

    A POI is `atStation` only when its tag marks it as a station facility AND it is within
    `at_station_m` of this station (a facility tagged TransMilenio but further away belongs
    to a different station, so it falls through to `nearby`). `nearby` holds everything else
    within `nearby_m`, nearest first, capped at `limit`. Membership is exclusive.
    """
    at: list[tuple[float, dict]] = []
    near: list[tuple[float, dict]] = []
    for f in feats:
        coords = (f.get("geometry") or {}).get("coordinates") or [None, None]
        flon, flat = coords[0], coords[1]
        if flon is None or flat is None:
            continue
        d = haversine_m(lat, lon, flat, flon)
        if is_station_facility(f.get("properties") or {}) and d <= at_station_m:
            at.append((d, _decorate(f, d)))
        elif d <= nearby_m:
            near.append((d, _decorate(f, d)))
    at.sort(key=lambda x: x[0])
    near.sort(key=lambda x: x[0])
    return [e for _, e in at], [e for _, e in near[:limit]]
