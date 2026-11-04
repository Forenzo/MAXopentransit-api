"""A sentence a rider sees when the feed we are serving is not the whole network.

Written 2026-11-04 for Toronto. The City's "TTC Routes and Schedules" dataset started serving a
22-byte empty zip that morning, the feed we were holding had expired on 31 October, and the only
official dataset still publishing — "Surface Routes and Schedules for BusTime" — carries 208 bus
routes, 16 streetcar routes and the island ferry, and **no subway**.

Between a planner that shows nothing and one that silently omits Lines 1, 2 and 4, neither is
acceptable: the second confidently sends somebody on a fifty-minute bus ride where a fifteen-minute
subway exists. So the partial feed is served *and said out loud*, on every plan, in the rider's own
language.

It rides the existing warning channel on purpose. `FEED_PARTIAL` is a code the shipped app does not
know, and its fallback renders the server's own sentence verbatim — so this reaches phones that are
already installed, with no release.
"""


def feed_warnings(note: dict[str, str] | None, locale: str) -> list[str]:
    """`["FEED_PARTIAL: <sentence>"]`, or nothing when this city's feed is whole.

    The sentence comes from the city's own configuration because only that file can know what is
    missing; the app cannot translate a fact it does not have. `locale` picks the language, falling
    back to the feed's `en` text and then to whatever single language was written.
    """
    if not note:
        return []
    lang = (locale or "en").split("-")[0].lower()
    text = note.get(lang) or note.get("en") or next(iter(note.values()), "")
    text = text.strip()
    return [f"FEED_PARTIAL: {text}"] if text else []
