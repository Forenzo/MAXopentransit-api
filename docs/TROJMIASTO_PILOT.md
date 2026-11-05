# Trójmiasto multi-feed pilot

**Status:** Graph input integration committed; end-to-end runtime validation pending.
The routing graph now includes four *independent* GTFS inputs:
- ZTM Gdańsk — `gdansk`
- ZKM Gdynia — `gdynia`
- SKM Trójmiasto — `skm`
- POLREGIO — `polregio`

Unlike rewriting every source identifier into one ZIP, separate OTP `feedId` namespaces preserve source trip IDs. The ZTM Gdańsk GTFS-RT updaters are explicitly scoped to `gdansk` and must be validated against current feed trip IDs. Other operators currently have timetable-based routing without verified live feeds. The API static ingest still reads `data/trojmiasto/trojmiasto-gtfs.zip`, which the preparation step copies from the Gdańsk feed: stop searches, routes and component metadata therefore remain **incomplete** for other operators. Do not expose this pilot as a fully supported production city.

## Required dependencies and graph build

On macOS with Docker, Python 3.12+, JDK 21+, and sufficient free RAM/storage:

```sh
git checkout feature/poland-metro-regions
make venv
make up
make graph CITY=trojmiasto
CITY=trojmiasto make otp
cp .env.example .env
make dev
curl http://localhost:8001/v1/cities/trojmiasto
```

The graph build fetches all four zip archives and validates core GTFS tables before replacing cached copies. Source definitions are in `otp/trojmiasto/sources.env`, and OTP's `transitFeeds` entries are in `otp/trojmiasto/build-config.json`. Existing single-feed cities continue to use the original `GTFS_URL` setting. **No live graph has yet been built in this branch**.

## Issues before public deployment

1. POLREGIO publishes **national** GTFS, which increases graph size substantially and may introduce out-of-region itineraries; implement spatial pruning after inspecting actual stop and service coverage. Do not trim stop_times blindly: it can invalidate train itineraries and stop_sequence semantics.
2. Extend FastAPI static ingestion to index all four feeds, preserve operator identities and distinguish duplicate route/stop/trip IDs. Preserve the source-to-feed namespace in returned IDs.
3. Verify links and ZIP service-date ranges on each production refresh; Gdynia's URL is HTTP and may need a vetted HTTPS mirror or server allowlist.
4. Verify GTFS-Realtime trip update matching for Gdańsk and implement the required 12-minute delay / cancellation journey re-evaluation in the mobile client. Other operators need trusted live data or explicit timetable-only indicators.
5. Test real journeys and realistic walking transfers between Gdańsk Wrzeszcz, Sopot, Gdynia Główna, Rumia and Wejherowo; compare all operators with no operator preference.
6. Tune walking as a **soft preference**: less walking for similar ETAs without a user-selected fixed cap; document OTP internal search limits and avoid dangerous unbounded computation.
7. Verify licensing and display correct attributions; POLREGIO specifically requires a source notice and liability disclaimer.

This is committed code, not a functioning deployed service or APK.
