import datetime as dt
import unittest
from unime_prenota import next_target

UTC = dt.timezone.utc

class SchedulingTests(unittest.TestCase):
    def test_winter_offset(self):
        now = dt.datetime(2026, 1, 15, 6, tzinfo=UTC)
        self.assertEqual(next_target("08:00:00", now=now), dt.datetime(2026, 1, 15, 7, tzinfo=UTC))

    def test_summer_offset(self):
        now = dt.datetime(2026, 7, 15, 5, tzinfo=UTC)
        self.assertEqual(next_target("08:00:00", now=now), dt.datetime(2026, 7, 15, 6, tzinfo=UTC))

    def test_next_day(self):
        now = dt.datetime(2026, 1, 15, 8, tzinfo=UTC)
        self.assertEqual(next_target("08:00:00", now=now), dt.datetime(2026, 1, 16, 7, tzinfo=UTC))

    def test_spring_gap(self):
        now = dt.datetime(2026, 3, 29, 0, tzinfo=UTC)
        self.assertEqual(next_target("02:30:00", now=now), dt.datetime(2026, 3, 30, 0, 30, tzinfo=UTC))

    def test_autumn_repeated_time(self):
        now = dt.datetime(2026, 10, 25, 0, 45, tzinfo=UTC)
        self.assertEqual(next_target("02:30:00", now=now), dt.datetime(2026, 10, 25, 1, 30, tzinfo=UTC))

if __name__ == "__main__":
    unittest.main()
