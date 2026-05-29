import pytest


@pytest.mark.asyncio
async def test_create_creator(client):
    response = await client.post("/api/v1/creators", json={
        "name": "Virat Sharma",
        "platform": "instagram",
        "followers": 150000,
        "bio": "Cricket enthusiast and fitness coach",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Virat Sharma"
    assert data["state"] == "DISCOVERED"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_creator(client):
    create_resp = await client.post("/api/v1/creators", json={
        "name": "Test Creator",
        "platform": "youtube",
        "followers": 50000,
    })
    creator_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/creators/{creator_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == creator_id


@pytest.mark.asyncio
async def test_get_creator_not_found(client):
    response = await client.get("/api/v1/creators/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_creators(client):
    for i in range(3):
        await client.post("/api/v1/creators", json={
            "name": f"Creator {i}",
            "platform": "instagram",
            "followers": 1000 * i,
        })
    response = await client.get("/api/v1/creators")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_list_creators_filter_by_state(client):
    await client.post("/api/v1/creators", json={"name": "C1", "platform": "instagram", "followers": 100})
    response = await client.get("/api/v1/creators?state=DISCOVERED")
    assert response.status_code == 200
    assert all(c["state"] == "DISCOVERED" for c in response.json())


@pytest.mark.asyncio
async def test_state_transition_valid(client):
    create_resp = await client.post("/api/v1/creators", json={
        "name": "Transition Creator",
        "platform": "twitter",
        "followers": 200000,
    })
    creator_id = create_resp.json()["id"]

    patch_resp = await client.patch(f"/api/v1/creators/{creator_id}/state", json={
        "new_state": "QUALIFIED",
        "notes": "Meets all criteria",
    })
    assert patch_resp.status_code == 200
    assert patch_resp.json()["state"] == "QUALIFIED"


@pytest.mark.asyncio
async def test_state_transition_invalid(client):
    create_resp = await client.post("/api/v1/creators", json={
        "name": "Bad Transition Creator",
        "platform": "instagram",
        "followers": 5000,
    })
    creator_id = create_resp.json()["id"]

    # DISCOVERED → ONBOARDED is not allowed
    patch_resp = await client.patch(f"/api/v1/creators/{creator_id}/state", json={
        "new_state": "ONBOARDED",
    })
    assert patch_resp.status_code == 422


@pytest.mark.asyncio
async def test_creator_history(client):
    create_resp = await client.post("/api/v1/creators", json={
        "name": "History Creator",
        "platform": "youtube",
        "followers": 75000,
    })
    creator_id = create_resp.json()["id"]

    await client.patch(f"/api/v1/creators/{creator_id}/state", json={"new_state": "QUALIFIED"})
    await client.patch(f"/api/v1/creators/{creator_id}/state", json={"new_state": "OUTREACH_PENDING"})

    history_resp = await client.get(f"/api/v1/creators/{creator_id}/history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) == 2
    assert history[0]["from_state"] == "DISCOVERED"
    assert history[0]["to_state"] == "QUALIFIED"
    assert history[1]["from_state"] == "QUALIFIED"
    assert history[1]["to_state"] == "OUTREACH_PENDING"


@pytest.mark.asyncio
async def test_terminal_state_cannot_transition(client):
    create_resp = await client.post("/api/v1/creators", json={
        "name": "Terminal Creator",
        "platform": "instagram",
        "followers": 10000,
    })
    creator_id = create_resp.json()["id"]

    # Walk to REJECTED
    await client.patch(f"/api/v1/creators/{creator_id}/state", json={"new_state": "REJECTED"})

    # Try to transition again from terminal state
    patch_resp = await client.patch(f"/api/v1/creators/{creator_id}/state", json={"new_state": "QUALIFIED"})
    assert patch_resp.status_code == 422
