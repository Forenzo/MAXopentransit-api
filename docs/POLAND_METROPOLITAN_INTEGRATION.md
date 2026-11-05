# Poland metropolitan integrations — implementation plan

Status: design specification (not yet implemented)
Branch: `feature/poland-metro-regions`

## Regions

### `trojmiasto` — Tricity, Pomerania
- Treat Gdańsk, Gdynia, Sopot and practical neighbouring service areas as one metropolitan routing region.
- Combine ZTM Gdańsk, ZKM Gdynia, SKM and POLREGIO passenger schedules, including services operating over the PKM corridor.
- Do not count PKM infrastructure as a separate train operator or import duplicate trips.
- Verify authoritative GTFS feed URLs, permissions, update cadence, agency IDs, and GTFS-RT coverage before configuring production ingestion.

### `gzm` — Górnośląsko-Zagłębiowska Metropolia
- Treat Katowice and the wider GZM travel area as one metropolitan routing region.
- Include ZTM GZM buses, Tramwaje Śląskie trams, Tychy trolleybuses, Koleje Śląskie and POLREGIO.
- Verify timetable, realtime, and rail source coverage; de-duplicate shared trips between imported feeds.
- Include pedestrian connectivity across municipal boundaries and transfer stops.

## Routing behavior shared by both regions

1. Optimize for the fastest **practical door-to-door arrival**, independent of operator. Consider access and egress walks, wait time, changes, and current delay information.
2. Prefer **less walking** among journeys with broadly similar arrival times. Never impose a user-visible fixed walking-distance cap; allow longer walks where necessary or where they meaningfully improve arrival time. Underlying OTP computational limits may still apply and must be documented and tested.
3. Cancelled planned service: immediately seek alternate journeys.
4. Predicted delay **>= 12 minutes**: trigger re-evaluation, **not unconditional switching**.
5. Under 12 minutes: re-evaluate earlier if a transfer becomes infeasible or a materially better alternative emerges.
6. If no better alternative exists, retain the journey and update the ETA; suppress route-switch oscillation.
7. Never infer cancellation or punctuality solely from missing realtime data; show freshness and fall back to published schedules transparently.
8. Save origin/destination commutes and recalculate practical route at journey time. Do not require locking a specific rail/bus line.

## Engineering milestones

- [ ] Audit city YAML schema, OTP graph build scripts, API region registry and mobile city selection.
- [ ] Document authoritative feed URLs, provenance, rights, refresh cadence, realtime availability and station coverage for each operator.
- [ ] Build a repeatable feed pipeline with stable agency/trip IDs, collision handling, validation, and duplicate train removal.
- [ ] Add city YAML and OSM extraction/geofence definitions for Tricity; test cross-operator itineraries.
- [ ] Add GZM region and validate bus/tram/trolleybus/rail journeys and inter-municipal walking transfers.
- [ ] Verify walking preference settings against OTP routing behavior with reproducible fixtures.
- [ ] Implement or verify mobile active-journey monitoring, >=12-minute delay triggers, cancellation and missed-transfer rerouting, and notification throttling.
- [ ] Add tests for missing/stale realtime data, schedule rollover, calendar exceptions, and both metropolitan boundaries.
- [ ] Build and test Android app against a deployed API; consider upstream PRs only after validation.

## Architecture notes

The API README describes `cities/<city>.yaml` city configuration, per-city OTP graphs, and FastAPI normalization. Multiple operators may need preprocessing and/or multiple GTFS archives before graph build; do not presume an arbitrary URL list works without testing. Use separate region graphs, shared routing policy, and deterministic feed ingestion. 
