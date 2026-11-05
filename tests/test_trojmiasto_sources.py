"""Offline regression checks for Tricity's multi-operator graph configuration.

Run: python -m pytest tests/test_trojmiasto_sources.py -q
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_four_distinct_otp_feeds():
    graph = json.loads((ROOT / "otp/trojmiasto/build-config.json").read_text())
    feeds = graph["transitFeeds"]
    assert {f["feedId"] for f in feeds} == {"gdansk", "gdynia", "skm", "polregio"}
    assert len({f["source"] for f in feeds}) == len(feeds)
    for feed in feeds:
        assert feed["source"].endswith(f"/{feed['feedId']}-gtfs.zip")


def test_gdansk_realtime_not_applied_to_other_operators():
    router = json.loads((ROOT / "otp/trojmiasto/router-config.json").read_text())
    assert router["updaters"]
    assert {u["feedId"] for u in router["updaters"]} == {"gdansk"}


def test_tricity_city_registration_and_honest_partial_note():
    city = yaml.safe_load((ROOT / "cities/trojmiasto.yaml").read_text())
    assert city["id"] == "trojmiasto"
    assert city["timezone"] == "Europe/Warsaw"
    assert city["otp"]["feed_id"] == "gdansk"
    assert "partial_note" in city["feeds"]
    assert "incomplete" in city["feeds"]["partial_note"]["en"].lower()


def test_source_definitions_match_graph():
    source_text = (ROOT / "otp/trojmiasto/sources.env").read_text()
    for operator in ("gdansk|", "gdynia|", "skm|", "polregio|"):
        assert operator in source_text
    assert 'PRIMARY_GTFS_FEED="gdansk"' in source_text


def test_existing_single_feed_regression():
    for name in ("bogota", "toronto", "roma"):
        source = (ROOT / f"otp/{name}/sources.env").read_text()
        assert "GTFS_URL=" in source
        assert "GTFS_SOURCES=" not in source
