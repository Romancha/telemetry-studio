"""Contract tests for gopro_overlay library APIs used by patches.

These tests verify that the gopro_overlay library exposes the APIs our patches
depend on. If the library changes, these tests will fail BEFORE the patches
silently break at runtime.
"""

import inspect

import pytest


class TestLoadingModuleContract:
    """Verify gopro_overlay.loading API that gpx_patches.py depends on."""

    def test_load_external_exists(self):
        from gopro_overlay.loading import load_external

        assert callable(load_external)

    def test_load_external_signature(self):
        """load_external must accept (filepath, units) — our patch replaces it."""
        from gopro_overlay.loading import load_external

        sig = inspect.signature(load_external)
        params = list(sig.parameters.keys())
        assert len(params) >= 2, f"Expected at least 2 params, got {params}"
        assert params[0] == "filepath", f"First param should be 'filepath', got '{params[0]}'"
        assert params[1] == "units", f"Second param should be 'units', got '{params[1]}'"


class TestTimeseriesContract:
    """Verify Timeseries/Entry APIs that gpx_patches.py depends on."""

    def test_entry_accepts_custom_kwargs(self):
        """Entry must accept arbitrary kwargs like iso, fnum, ev, ct for DJI metrics."""
        from datetime import datetime

        from gopro_overlay.point import Point
        from gopro_overlay.timeseries import Entry
        from gopro_overlay.units import units

        entry = Entry(
            datetime(2024, 1, 1),
            point=Point(69.0, 35.0),
            alt=units.Quantity(100.0, units.m),
            iso=units.Quantity(100),
            fnum=units.Quantity(2.8),
            ev=units.Quantity(0.0),
            ct=units.Quantity(5500),
            shutter=units.Quantity(0.001),
            focal_len=units.Quantity(24.0),
        )

        assert entry.iso is not None
        assert entry.fnum is not None
        assert entry.ev is not None
        assert entry.ct is not None
        assert entry.shutter is not None
        assert entry.focal_len is not None

    def test_timeseries_preserves_custom_entry_attrs(self):
        """Timeseries.add() + .get() must preserve custom attributes on Entry."""
        from datetime import datetime

        from gopro_overlay.point import Point
        from gopro_overlay.timeseries import Entry, Timeseries
        from gopro_overlay.units import units

        ts = Timeseries()
        dt = datetime(2024, 1, 1, 12, 0, 0)
        entry = Entry(
            dt,
            point=Point(69.0, 35.0),
            alt=units.Quantity(100.0, units.m),
            iso=units.Quantity(200),
            fnum=units.Quantity(1.7),
        )
        ts.add(entry)

        retrieved = ts.get(ts.min)
        assert retrieved.iso is not None
        assert retrieved.fnum is not None

    def test_timeseries_has_min_max_get(self):
        """Timeseries must expose .min, .max, .get() — used by patched load."""
        from datetime import datetime

        from gopro_overlay.point import Point
        from gopro_overlay.timeseries import Entry, Timeseries
        from gopro_overlay.units import units

        ts = Timeseries()
        entry = Entry(
            datetime(2024, 1, 1),
            point=Point(0, 0),
            alt=units.Quantity(0, units.m),
        )
        ts.add(entry)

        assert ts.min is not None
        assert ts.max is not None
        assert callable(ts.get)
        assert ts.get(ts.min) is not None


class TestMetricAccessorContract:
    """Verify gopro_overlay.layout_xml API that metric_patches.py depends on."""

    def test_metric_accessor_from_exists(self):
        from gopro_overlay.layout_xml import metric_accessor_from

        assert callable(metric_accessor_from)

    def test_known_metric_returns_callable(self):
        """Standard metrics like 'speed' must return a callable accessor."""
        from gopro_overlay.layout_xml import metric_accessor_from

        accessor = metric_accessor_from("speed")
        assert callable(accessor)

    def test_unknown_metric_raises_oserror(self):
        """Unknown metrics must raise OSError — our patch catches this to add custom metrics."""
        # Reset the patch to test the original function behavior
        from gopro_overlay import layout_xml

        # Save current state
        current_fn = layout_xml.metric_accessor_from
        was_patched = getattr(layout_xml, "_ts_metric_patched", False)

        # If patched, we need to get the original from the closure
        # Our patch wraps the original, so unknown metrics go through _original first
        # which raises OSError, then we check _custom_accessors.
        # For a truly unknown metric, the patched version also raises OSError.
        # So we can test with a metric name that neither original nor patch knows.
        with pytest.raises(OSError):
            current_fn("__nonexistent_metric_9999__")

    def test_accessor_callable_signature(self):
        """Accessor must accept a single entry argument."""
        from gopro_overlay.layout_xml import metric_accessor_from

        accessor = metric_accessor_from("speed")
        sig = inspect.signature(accessor)
        params = list(sig.parameters.keys())
        assert len(params) >= 1, f"Accessor should accept at least 1 param, got {params}"
