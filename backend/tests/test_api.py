from datetime import UTC, datetime, timedelta

MB = 1024 * 1024


async def test_upload_returns_metadata(upload):
    response = await upload(b"hello", "hello.txt", expires_hours=1, max_downloads=3)

    assert response.status_code == 200
    body = response.json()
    assert len(body["short_code"]) == 6
    assert body["original_name"] == "hello.txt"
    assert body["file_size"] == 5
    assert body["max_downloads"] == 3
    assert body["expires_at"] is not None


async def test_upload_roundtrip_returns_same_content(client, upload):
    code = (await upload(b"payload", "data.bin")).json()["short_code"]

    response = await client.get(f"/api/download/{code}")

    assert response.status_code == 200
    assert response.content == b"payload"
    assert "data.bin" in response.headers["content-disposition"]


async def test_zero_expiry_and_zero_limit_mean_unlimited(upload):
    body = (await upload(expires_hours=0, max_downloads=0)).json()

    assert body["expires_at"] is None
    assert body["max_downloads"] is None


async def test_upload_larger_than_limit_is_rejected(upload, app):
    response = await upload(b"x" * (MB + 1))

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()
    assert list(app.state.settings.upload_dir.iterdir()) == []


async def test_upload_at_exact_limit_is_accepted(upload):
    response = await upload(b"x" * MB)

    assert response.status_code == 200


async def test_filename_cannot_contain_path(upload, app):
    response = await upload(b"x", filename="../../evil.txt")

    assert response.status_code == 200
    assert response.json()["original_name"] == "evil.txt"
    stored = [p.name for p in app.state.settings.upload_dir.iterdir()]
    assert len(stored) == 1
    assert "evil" not in stored[0]


async def test_info_does_not_count_as_download(client, upload):
    code = (await upload()).json()["short_code"]

    await client.get(f"/api/info/{code}")
    info = (await client.get(f"/api/info/{code}")).json()

    assert info["download_count"] == 0
    assert info["original_name"] == "hello.txt"


async def test_download_increments_counter(client, upload):
    code = (await upload()).json()["short_code"]

    await client.get(f"/api/download/{code}")
    info = (await client.get(f"/api/info/{code}")).json()

    assert info["download_count"] == 1


async def test_unknown_code_returns_404(client):
    assert (await client.get("/api/info/nope00")).status_code == 404
    assert (await client.get("/api/download/nope00")).status_code == 404


async def test_expired_file_returns_410(client, upload, update_record):
    code = (await upload()).json()["short_code"]
    await update_record(code, expires_at=datetime.now(UTC) - timedelta(minutes=1))

    for endpoint in ("info", "download"):
        response = await client.get(f"/api/{endpoint}/{code}")
        assert response.status_code == 410
        assert response.json()["detail"] == "File has expired"


async def test_download_limit_is_enforced(client, upload):
    code = (await upload(max_downloads=2)).json()["short_code"]

    assert (await client.get(f"/api/download/{code}")).status_code == 200
    assert (await client.get(f"/api/download/{code}")).status_code == 200
    blocked = await client.get(f"/api/download/{code}")

    assert blocked.status_code == 410
    assert blocked.json()["detail"] == "Download limit reached"
    assert (await client.get(f"/api/info/{code}")).status_code == 410


async def test_missing_file_on_disk_returns_404(client, upload, app):
    code = (await upload()).json()["short_code"]
    for path in app.state.settings.upload_dir.iterdir():
        path.unlink()

    response = await client.get(f"/api/download/{code}")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found on disk"
