"""Tests for backward compatibility migration of old video_time_alignment values."""

import json

import pytest

from gpstitch.models.job import RenderJobConfig, migrate_video_time_alignment


class TestMigrateVideoTimeAlignment:
    """Test the migration helper function."""

    def test_null_maps_to_auto(self):
        assert migrate_video_time_alignment(None) == "auto"

    def test_file_created_maps_to_auto(self):
        assert migrate_video_time_alignment("file-created") == "auto"

    def test_file_modified_preserved(self):
        """file-modified is still valid for SRT auto-detection pipeline."""
        assert migrate_video_time_alignment("file-modified") == "file-modified"

    def test_file_accessed_maps_to_auto(self):
        assert migrate_video_time_alignment("file-accessed") == "auto"

    def test_auto_preserved(self):
        assert migrate_video_time_alignment("auto") == "auto"

    def test_gpx_timestamps_preserved(self):
        assert migrate_video_time_alignment("gpx-timestamps") == "gpx-timestamps"

    def test_manual_preserved(self):
        assert migrate_video_time_alignment("manual") == "manual"


class TestRenderJobConfigMigration:
    """Test that RenderJobConfig migrates old alignment values on construction."""

    def test_default_is_auto(self):
        config = RenderJobConfig(session_id="s1", layout="default", output_file="/tmp/out.mp4")
        assert config.video_time_alignment == "auto"

    @pytest.mark.parametrize("old_value", ["file-created", "file-accessed"])
    def test_old_values_migrated_to_auto(self, old_value):
        config = RenderJobConfig(
            session_id="s1",
            layout="default",
            output_file="/tmp/out.mp4",
            video_time_alignment=old_value,
        )
        assert config.video_time_alignment == "auto"

    def test_file_modified_preserved(self):
        """file-modified is still valid for SRT auto-detection, not migrated."""
        config = RenderJobConfig(
            session_id="s1",
            layout="default",
            output_file="/tmp/out.mp4",
            video_time_alignment="file-modified",
        )
        assert config.video_time_alignment == "file-modified"

    def test_null_migrated_to_auto(self):
        config = RenderJobConfig(
            session_id="s1",
            layout="default",
            output_file="/tmp/out.mp4",
            video_time_alignment=None,
        )
        assert config.video_time_alignment == "auto"

    def test_new_values_preserved(self):
        for value in ("auto", "gpx-timestamps", "manual"):
            config = RenderJobConfig(
                session_id="s1",
                layout="default",
                output_file="/tmp/out.mp4",
                video_time_alignment=value,
            )
            assert config.video_time_alignment == value

    def test_old_json_job_migrated(self):
        """Simulate loading an old persisted job JSON with file-created alignment."""
        old_job_json = {
            "session_id": "old-session",
            "layout": "default-1920x1080",
            "output_file": "/tmp/out.mp4",
            "video_time_alignment": "file-created",
        }
        config = RenderJobConfig.model_validate(old_job_json)
        assert config.video_time_alignment == "auto"

    def test_old_json_job_null_alignment_migrated(self):
        """Simulate loading an old persisted job JSON with null alignment."""
        old_job_json = {
            "session_id": "old-session",
            "layout": "default-1920x1080",
            "output_file": "/tmp/out.mp4",
            "video_time_alignment": None,
        }
        config = RenderJobConfig.model_validate(old_job_json)
        assert config.video_time_alignment == "auto"

    def test_old_json_job_missing_alignment_migrated(self):
        """Simulate loading old job JSON without alignment field at all."""
        old_job_json = {
            "session_id": "old-session",
            "layout": "default-1920x1080",
            "output_file": "/tmp/out.mp4",
        }
        config = RenderJobConfig.model_validate(old_job_json)
        assert config.video_time_alignment == "auto"


class TestRenderRequestMigration:
    """Test that render API request models migrate old values."""

    def test_render_job_request_migrates_old_value(self):
        from gpstitch.api.render import RenderJobRequest

        req = RenderJobRequest(session_id="s1", video_time_alignment="file-created")
        assert req.video_time_alignment == "auto"

    def test_render_job_request_migrates_null(self):
        from gpstitch.api.render import RenderJobRequest

        req = RenderJobRequest(session_id="s1", video_time_alignment=None)
        assert req.video_time_alignment == "auto"

    def test_render_job_request_default_is_auto(self):
        from gpstitch.api.render import RenderJobRequest

        req = RenderJobRequest(session_id="s1")
        assert req.video_time_alignment == "auto"

    def test_batch_render_request_migrates_old_value(self):
        from gpstitch.api.render import BatchRenderRequest

        req = BatchRenderRequest(
            files=[{"video_path": "/tmp/video.mp4"}],
            video_time_alignment="file-accessed",
        )
        assert req.video_time_alignment == "auto"

    def test_batch_render_request_migrates_null(self):
        from gpstitch.api.render import BatchRenderRequest

        req = BatchRenderRequest(
            files=[{"video_path": "/tmp/video.mp4"}],
            video_time_alignment=None,
        )
        assert req.video_time_alignment == "auto"

    def test_batch_render_request_preserves_new_values(self):
        from gpstitch.api.render import BatchRenderRequest

        req = BatchRenderRequest(
            files=[{"video_path": "/tmp/video.mp4"}],
            video_time_alignment="manual",
        )
        assert req.video_time_alignment == "manual"


class TestJobManagerLoadMigration:
    """Test that old persisted jobs load correctly with migration."""

    def test_full_old_job_json_loads(self):
        """Full Job JSON with old alignment value loads and migrates correctly."""
        from gpstitch.models.job import Job

        old_job_data = {
            "id": "test-job-123",
            "type": "render",
            "status": "completed",
            "config": {
                "session_id": "old-session",
                "layout": "default-1920x1080",
                "output_file": "/tmp/out.mp4",
                "video_time_alignment": "file-created",
            },
            "created_at": "2025-01-01T00:00:00Z",
            "progress": {"percent": 100},
        }
        job = Job.model_validate(old_job_data)
        assert job.config.video_time_alignment == "auto"
        assert job.config.time_offset_seconds == 0

    def test_full_old_job_json_roundtrip(self):
        """Job serialized and deserialized preserves migrated value."""
        from gpstitch.models.job import Job

        old_job_data = {
            "id": "test-job-456",
            "type": "render",
            "status": "pending",
            "config": {
                "session_id": "s1",
                "layout": "default-1920x1080",
                "output_file": "/tmp/out.mp4",
                "video_time_alignment": "file-accessed",
            },
            "created_at": "2025-06-01T12:00:00Z",
            "progress": {"percent": 0},
        }
        job = Job.model_validate(old_job_data)
        assert job.config.video_time_alignment == "auto"

        # Re-serialize and re-load
        job_json = json.loads(job.model_dump_json())
        job2 = Job.model_validate(job_json)
        assert job2.config.video_time_alignment == "auto"
