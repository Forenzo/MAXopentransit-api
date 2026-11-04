"""Streaming stop_times.txt without dropping rows.

The file can be 500 MB, so unquoted lines take a fast `split(",")` path. That path used to *skip*
any line containing a quote, on the assumption that quotes in stop_times are rare. Toronto's surface
feed quotes `stop_headsign` on every row: on 2026-11-04 the scan read 0 of its 2.7 M rows and
reported success, which would have left the city with no service windows and no stop→route index.
"""
import io
import zipfile


def _zip(stop_times: str) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("stop_times.txt", stop_times)
    return zipfile.ZipFile(buf)


HEAD = "trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign\r\n"
TRIP2ROUTE = {"t1": "r1", "t2": "r2"}


def scan(body: str):
    from app.gtfs_static import _scan_stop_times
    return _scan_stop_times(_zip(HEAD + body), TRIP2ROUTE)


def test_plain_rows_are_read():
    stops, span = scan("t1,07:00:00,07:00:00,s1,1,\r\nt1,07:10:00,07:10:00,s2,2,\r\n")
    assert stops == {"s1": {"r1"}, "s2": {"r1"}}
    assert span == {"t1": ("07:00:00", "07:10:00")}


def test_a_quoted_field_on_every_row_is_not_silently_dropped():
    """Toronto's feed, in miniature. This is the regression."""
    stops, span = scan('t1,07:43:00,07:43:00,s1,1,"43 KENNEDY KENNEDY STN"\r\n'
                       't1,08:12:00,08:12:00,s2,2,"43 KENNEDY KENNEDY STN"\r\n')
    assert stops == {"s1": {"r1"}, "s2": {"r1"}}
    assert span == {"t1": ("07:43:00", "08:12:00")}


def test_a_comma_inside_a_quoted_field_does_not_shift_the_columns():
    """The reason the fast path cannot simply split: the headsign carries its own comma."""
    stops, span = scan('t1,09:00:00,09:00:00,s9,1,"KENNEDY, VIA EGLINTON"\r\n')
    assert stops == {"s9": {"r1"}}
    assert span == {"t1": ("09:00:00", "09:00:00")}


def test_quoted_and_plain_rows_mix_in_one_file():
    stops, span = scan('t1,07:00:00,07:00:00,s1,1,\r\n'
                       't2,08:00:00,08:00:00,s2,1,"GO WEST"\r\n'
                       't2,08:30:00,08:30:00,s3,2,"GO WEST"\r\n')
    assert stops == {"s1": {"r1"}, "s2": {"r2"}, "s3": {"r2"}}
    assert span == {"t1": ("07:00:00", "07:00:00"), "t2": ("08:00:00", "08:30:00")}


def test_a_trip_the_feed_does_not_declare_is_ignored():
    stops, span = scan('tX,07:00:00,07:00:00,s1,1,"x"\r\n')
    assert stops == {} and span == {}


def test_a_short_row_is_still_skipped():
    """Truncated lines have nothing to take; only *quoted* ones were being lost."""
    stops, _ = scan("t1,07:00:00\r\n")
    assert stops == {}


def test_a_single_digit_hour_is_padded_so_times_compare():
    stops, span = scan('t1,7:05:00,7:05:00,s1,1,"a"\r\nt1,19:00:00,19:00:00,s2,2,"a"\r\n')
    assert span == {"t1": ("07:05:00", "19:00:00")}
