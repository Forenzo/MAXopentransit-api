# Trójmiasto phase 1 (ZTM Gdańsk pilot)

This is an **incomplete first build**, NOT full Tricity routing. The YAML includes a visible `FEED_PARTIAL` warning until Gdynia, SKM and POLREGIO feeds can be integrated. Never ship it as full-area coverage.

## Inputs

- [ZTM Gdańsk GTFS](https://www.transit.land/data/feeds/f-ztm~gdansk), CC BY 4.0; operator download URL is used in config.
- [ZTM Gdańsk GTFS-RT](https://www.transit.land/data/feeds/f-u3tm-ztm~gdansk~rt), positions and trip updates. HTTP access must be checked from the server; network policies may block it.
- [Geofabrik Pomorskie](https://download.geofabrik.de/europe/poland/pomorskie.html), OpenStreetMap extract. Respect OpenStreetMap attribution.

## Build and test (macOS)

Requires Python >=3.12, Docker, Java >=21 and enough free disk/RAM.

```sh
make venv
make up
make graph CITY=trojmiasto
CITY=trojmiasto make otp
cp .env.example .env
make dev
curl 'http://localhost:8001/v1/cities'
curl 'http://localhost:8001/v1/cities/trojmiasto'
```

Run a cross-town Gdańsk route through `/v1/cities/trojmiasto/plan` with valid coordinates and verify the result, route modes, display warning and walking paths. Inspect `/health` and `/v1/cities/trojmiasto/health` for feed freshness and graph matching.

## Before enabling as a public metro region

1. Build a multi-operator GTFS acquisition and import pipeline and validate referential integrity and calendar coverage.
2. Add ZKM Gdynia feed, SKM Trójmiasto and POLREGIO without duplicate rail trips (PKM is infrastructure, not a separate passenger operator).
3. Ensure real-time feed trip IDs match the graph/merged static IDs; otherwise disable OTP realtime updaters rather than incorrectly attributing delays.
4. Test missing feeds, stale RT, transfers at Gdańsk Wrzeszcz, Gdynia Główna, Sopot, Rumia, and Wejherowo; inspect OSM transfer footpaths.
5. Implement 12-minute delay-triggered **re-evaluation** in the mobile journey monitor, retaining an existing route when no better alternative exists.
6. Apply shortest-practical-walking preference, with no user-configured hard distance cap, using measured generalized-cost tuning rather than simply claiming that the default OTP policy does it.

No APK, hosted API, or trip validation is claimed at this stage.
