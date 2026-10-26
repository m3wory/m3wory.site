from datetime import UTC, datetime, timedelta

from app.services.cleanup import cleanup_files


async def run_cleanup(app) -> int:
    return await cleanup_files(app.state.session_factory, app.state.storage)


async def test_cleanup_removes_expired_files_from_db_and_disk(client, upload, update_record, app):
    code = (await upload()).json()["short_code"]
    await update_record(code, expires_at=datetime.now(UTC) - timedelta(hours=1))

    removed = await run_cleanup(app)

    assert removed == 1
    assert list(app.state.settings.upload_dir.iterdir()) == []
    assert (await client.get(f"/api/info/{code}")).status_code == 404


async def test_cleanup_removes_files_with_exhausted_downloads(client, upload, app):
    code = (await upload(max_downloads=1)).json()["short_code"]
    await client.get(f"/api/download/{code}")

    assert await run_cleanup(app) == 1
    assert list(app.state.settings.upload_dir.iterdir()) == []


async def test_cleanup_keeps_active_files(upload, app):
    await upload(expires_hours=24, max_downloads=5)
    await upload(expires_hours=0, max_downloads=0)

    assert await run_cleanup(app) == 0
    assert len(list(app.state.settings.upload_dir.iterdir())) == 2
