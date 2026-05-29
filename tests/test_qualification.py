from unittest.mock import AsyncMock, patch

import pytest


QUALIFY_PAYLOAD = {
    "creator_bio": "Professional cricket analyst with 8 years of match analysis experience.",
    "platform": "youtube",
    "followers": 500000,
    "recent_posts": [
        "IPL match analysis and player performance breakdown",
        "Fitness routines for cricketers",
    ],
    "creator_id": None,
}


@pytest.mark.asyncio
async def test_submit_qualification_creates_pending_job(client):
    with patch("app.api.v1.qualification.run_qualification_job", new_callable=AsyncMock) as mock_task:
        response = await client.post("/api/v1/qualify", json=QUALIFY_PAYLOAD)

    assert response.status_code == 202
    data = response.json()
    assert data["job_id"]
    assert data["status"] == "PENDING"
    assert data["creator_id"] is None
    assert data["result"] is None
    assert data["error_message"] is None
    assert data["prompt_tokens"] is None
    assert data["completion_tokens"] is None
    assert data["total_tokens"] is None
    mock_task.assert_awaited_once_with(data["job_id"])


@pytest.mark.asyncio
async def test_get_qualification_job(client):
    with patch("app.api.v1.qualification.run_qualification_job", new_callable=AsyncMock):
        create_response = await client.post("/api/v1/qualify", json=QUALIFY_PAYLOAD)

    job_id = create_response.json()["job_id"]

    response = await client.get(f"/api/v1/qualify/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "PENDING"
    assert data["creator_id"] is None


@pytest.mark.asyncio
async def test_submit_qualification_rejects_unknown_creator_id(client):
    payload = {**QUALIFY_PAYLOAD, "creator_id": "missing-creator-id"}

    with patch("app.api.v1.qualification.run_qualification_job", new_callable=AsyncMock) as mock_task:
        response = await client.post("/api/v1/qualify", json=payload)

    assert response.status_code == 404
    assert "missing-creator-id" in response.json()["detail"]
    mock_task.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_qualification_job_not_found(client):
    response = await client.get("/api/v1/qualify/missing-job-id")

    assert response.status_code == 404
