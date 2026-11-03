"""Updates must preserve the integrity of existing workplace histories."""

from test_workspace_imports import batch, setup_source


def test_person_cannot_be_withdrawn_leaving_active_clinical_records(
    client, auth_headers
):
    ws, _, headers = setup_source(client, auth_headers)
    payload = batch()
    prescription = {
        **payload["records"][0],
        "external_id": "rx1",
        "kind": "prescription",
        "related_ids": ["patient1"],
    }
    payload["records"].append(prescription)
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=payload
        ).status_code
        == 200
    )
    withdrawal = batch(2, "withdraw-person", "deleted")
    response = client.post("/v1/integrations/imports", headers=headers, json=withdrawal)
    assert response.status_code == 422, response.text
    assert "rx1" in response.text
    visible = client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json()
    assert len(visible) == 2 and all(row["version"] == 1 for row in visible)
    withdrawal["records"].append({**prescription, "version": 2, "status": "deleted"})
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=withdrawal
        ).status_code
        == 200
    )
    assert client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json() == []


def test_medication_comparison_rejects_blank_observations_and_untyped_source(
    client, auth_headers
):
    ws, _, headers = setup_source(client, auth_headers)
    payload = batch()
    payload["records"][0]["data"]["allergies_reviewed_at"] = "2026-11-01T12:00:00Z"
    payload["records"].append(
        {
            **payload["records"][0],
            "external_id": "rx1",
            "kind": "prescription",
            "related_ids": ["patient1"],
            "data": {
                "ingredient": 123,
                "concentration": "10 mg",
                "state": "active",
                "valid_from": "2026-11-01T00:00:00Z",
                "valid_until": "2026-12-01T00:00:00Z",
            },
        }
    )
    imported = client.post(
        "/v1/integrations/imports", headers=headers, json=payload
    ).json()["records"]
    path = f"/v1/workspaces/{ws}/records/{imported[0]['id']}/medication-check"
    comparison = {
        "prescription_id": imported[1]["id"],
        "observed_ingredient": "123",
        "observed_concentration": "10 mg",
        "patient_confirmed": True,
        "checked_at": "2026-11-02T12:00:00Z",
    }
    response = client.post(path, headers=auth_headers, json=comparison)
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"
    assert "ingredient" in response.json()["missing"]
    for field in ("observed_ingredient", "observed_concentration"):
        response = client.post(
            path, headers=auth_headers, json={**comparison, field: "  "}
        )
        assert response.status_code == 422


def test_incomplete_allergy_is_missing_evidence_not_a_match(client, auth_headers):
    ws, _, headers = setup_source(client, auth_headers)
    payload = batch()
    person = payload["records"][0]
    person["data"]["allergies_reviewed_at"] = "2026-11-01T12:00:00Z"
    payload["records"] += [
        {
            **person,
            "external_id": "rx",
            "kind": "prescription",
            "related_ids": ["patient1"],
            "data": {
                "ingredient": "DEMO",
                "concentration": "10 mg",
                "state": "active",
                "valid_from": "2026-11-01T00:00:00Z",
                "valid_until": "2026-12-01T00:00:00Z",
            },
        },
        {
            **person,
            "external_id": "allergy",
            "kind": "allergy",
            "related_ids": ["patient1"],
            "data": {},
        },
    ]
    rows = client.post(
        "/v1/integrations/imports", headers=headers, json=payload
    ).json()["records"]
    response = client.post(
        f"/v1/workspaces/{ws}/records/{rows[0]['id']}/medication-check",
        headers=auth_headers,
        json={
            "prescription_id": rows[1]["id"],
            "observed_ingredient": "DEMO",
            "observed_concentration": "10 mg",
            "patient_confirmed": True,
            "checked_at": "2026-11-02T12:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"
    assert "allergy_substance" in response.json()["missing"]
    assert rows[2]["id"] in response.json()["source_record_ids"]
