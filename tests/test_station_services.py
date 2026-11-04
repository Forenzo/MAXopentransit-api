"""Servicios en la estación.

The feature exists because of a validation the user asked for before building: in Bogotá almost
nothing is physically inside a TransMilenio station, so labelling a nearby street POI "en la
estación" would be wrong. The split is therefore by tag, not by distance — these tests pin that
distinction, especially that a very close but untagged POI is NOT called a station facility.
"""
from app.station_services import is_station_facility, station_services

# A real troncal station coordinate (Calle 100) and a pharmacy ~40 m away.
STATION = (4.6860, -74.0540)


def _poi(dlat: float, dlon: float, ptype: str = "pharmacy", **props) -> dict:
    return {"type": "Feature",
            "geometry": {"type": "Point", "coordinates": [STATION[1] + dlon, STATION[0] + dlat]},
            "properties": {"type": ptype, **props}}


def test_tagged_bike_parking_close_is_at_station():
    at, near = station_services([_poi(0.0002, 0.0, "bike_parking", operator="TransMilenio")],
                                *STATION)
    assert len(at) == 1 and not near
    assert at[0]["properties"]["type"] == "bike_parking"


def test_close_but_untagged_pharmacy_is_nearby_not_at_station():
    """The whole point: a pharmacy 20 m from the vestibule is 'cerca', never 'en la estación'."""
    at, near = station_services([_poi(0.00018, 0.0)], *STATION)  # ~20 m
    assert at == []
    assert len(near) == 1
    assert near[0]["properties"]["type"] == "pharmacy"


def test_tagged_facility_far_away_belongs_to_another_station():
    """Tagged TransMilenio but 300 m off: not THIS station's facility -> falls through to nearby."""
    at, near = station_services([_poi(0.0027, 0.0, "bike_parking", operator="TransMilenio")],
                                *STATION, at_station_m=150.0, nearby_m=400.0)
    assert at == []
    assert len(near) == 1


def test_beyond_radius_is_dropped():
    at, near = station_services([_poi(0.01, 0.0)], *STATION, nearby_m=400.0)  # ~1.1 km
    assert at == [] and near == []


def test_nearby_sorted_by_distance_and_decorated():
    feats = [_poi(0.003, 0.0, "atm"), _poi(0.0005, 0.0, "atm"), _poi(0.0015, 0.0, "atm")]
    _, near = station_services(feats, *STATION, nearby_m=500.0)
    d = [p["properties"]["distanceMeters"] for p in near]
    assert d == sorted(d)
    assert all("walkMinutes" in p["properties"] and p["properties"]["walkMinutes"] >= 1 for p in near)


def test_limit_applies_to_nearby():
    feats = [_poi(0.0005 + i * 0.0001, 0.0, "atm") for i in range(10)]
    _, near = station_services(feats, *STATION, nearby_m=800.0, limit=3)
    assert len(near) == 3


def test_facility_tag_matches_operator_or_name():
    assert is_station_facility({"operator": "TransMilenio"})
    assert is_station_facility({"name": "Cicloparqueadero Estación Banderas"})
    assert not is_station_facility({"name": "Droguería La Rebaja"})
    assert not is_station_facility({})
