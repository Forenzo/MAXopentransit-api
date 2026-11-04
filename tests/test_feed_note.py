"""Telling a rider the network they are being shown is not the whole one.

Written 2026-11-04 for Toronto: the City's full-network feed began serving a 22-byte empty zip, the
feed we held had expired on 31 October, and the only official dataset still publishing has no
subway. A planner that silently omits Lines 1, 2 and 4 sends somebody on a fifty-minute bus ride
where a fifteen-minute subway exists, which is worse than showing nothing — so it is served and
said out loud.
"""
from pathlib import Path

from app.cities import load_city_file
from app.feed_note import feed_warnings

NOTE = {"en": "No subway in this timetable.", "es": "Este horario no incluye el metro."}


def test_the_riders_language_wins():
    assert feed_warnings(NOTE, "es") == ["FEED_PARTIAL: Este horario no incluye el metro."]
    assert feed_warnings(NOTE, "en") == ["FEED_PARTIAL: No subway in this timetable."]


def test_a_regional_locale_still_matches_its_language():
    assert feed_warnings(NOTE, "es-419")[0].endswith("no incluye el metro.")
    assert feed_warnings(NOTE, "ES")[0].endswith("no incluye el metro.")


def test_an_unknown_language_falls_back_rather_than_going_silent():
    """Being told in the wrong language beats not being told."""
    assert feed_warnings(NOTE, "ja") == ["FEED_PARTIAL: No subway in this timetable."]
    assert feed_warnings({"pt": "Sem metrô."}, "ja") == ["FEED_PARTIAL: Sem metrô."]


def test_a_whole_feed_says_nothing():
    assert feed_warnings(None, "es") == []
    assert feed_warnings({}, "es") == []
    assert feed_warnings({"es": "   "}, "es") == []


def test_the_code_is_one_the_shipped_app_renders_verbatim():
    """`FEED_PARTIAL` is deliberately unknown to the app: its fallback prints the server's own
    sentence, so this reaches phones already installed without a release."""
    w = feed_warnings(NOTE, "es")[0]
    assert w.startswith("FEED_PARTIAL: ")
    assert w.split(":", 1)[1].strip()


class TestToronto:
    city = load_city_file(Path("cities/toronto.yaml"))

    def test_toronto_is_serving_the_surface_feed_and_says_so(self):
        assert "surfacegtfs.zip" in self.city.feeds.gtfs_static_url
        assert self.city.feeds.partial_note, "a partial feed without a note is the thing to avoid"

    def test_every_store_language_has_the_sentence(self):
        assert set(self.city.feeds.partial_note) >= {"es", "en", "fr", "pt", "it", "ms", "ar"}

    def test_the_sentence_names_what_is_missing_and_that_it_still_runs(self):
        """A rider must learn two things: the subway is absent here, and it is not absent in
        Toronto — otherwise they stay home."""
        es = self.city.feeds.partial_note["es"]
        assert "metro" in es
        assert "1, 2 y 4" in es

    def test_the_other_cities_stay_quiet(self):
        for name in ("bogota", "roma", "lisboa", "brisbane", "boston", "santiago", "casablanca",
                     "kualalumpur"):
            c = load_city_file(Path(f"cities/{name}.yaml"))
            assert not c.feeds.partial_note, name
