"""The approved Police/Meta vocabulary reaches only authorized gallery content."""

import uuid

from app.local.upgrades import POLICE, SOCIAL
from app.models import WorkspaceMember
from app.security import create_access_token
from app.social_features.models import Publication, PublicationTerm
from sqlalchemy import delete, select, update

EXPECTED = {
    POLICE: {
        "categories": {
            "Active arrest warrants": ("Órdenes de captura vigentes", 5),
            "Missing persons": ("Personas desaparecidas", 4),
            "No warrants or criminal history": ("Sin órdenes ni antecedentes", 7),
            "Audiovisual material": ("Material audiovisual", 3),
        },
        "tags": {
            "Active arrest warrant": ("Orden de captura vigente", 5),
            "No recorded criminal history": ("Sin antecedentes registrados", 16),
            "Active judicial proceedings": ("Proceso judicial activo", 2),
            "No active proceedings": ("Sin procesos activos", 14),
            "Active search order": ("Orden de búsqueda vigente", 4),
            "No active arrest warrants": ("Sin órdenes de captura", 11),
            "Observation video": ("Video de observación", 3),
        },
    },
    SOCIAL: {
        "categories": {
            "Introductions": ("Presentaciones", 3),
            "Social content": ("Contenido social", 3),
        },
        "tags": {
            "Personal introduction": ("Presentación personal", 3),
            "Community": ("Comunidad", 3),
            "Video": ("Video", 3),
            "Everyday life": ("Vida cotidiana", 3),
        },
    },
}


def authorization(evaluation, workspace):
    accounts = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    account = next(row for row in accounts if row["workspace_id"] == str(workspace))
    identifier = uuid.UUID(account["id"])
    return identifier, {
        "Authorization": "Bearer "
        + create_access_token(identifier, evaluation.app.state.settings)
    }


def test_approved_terms_and_counts_are_the_actual_gallery_filters(evaluation):
    for workspace, expected in EXPECTED.items():
        _, headers = authorization(evaluation, workspace)
        scoped = {"workspace_id": str(workspace)}
        response = evaluation.get(
            "/v1/gallery/filter-options", headers=headers, params=scoped
        )
        assert response.status_code == 200
        options = response.json()
        catalog = evaluation.get(
            f"/v1/groups/{workspace}/publication-catalog", headers=headers
        )
        assert catalog.status_code == 200
        for field, vocabulary in expected.items():
            terms = {row["name"]: row for row in options[field]}
            assert set(terms) == set(vocabulary)
            assert {
                row["name"] for row in catalog.json()[field] if row["active"]
            } == set(vocabulary)
            for name, (spanish, count) in vocabulary.items():
                term = terms[name]
                assert term["active"] and term["workspace_id"] == str(workspace)
                assert term["display_text"]["name"] == {
                    "source": name,
                    "en": name,
                    "es": spanish,
                }
                query = "category_ids" if field == "categories" else "tag_ids"
                result = evaluation.get(
                    "/v1/gallery/page",
                    headers=headers,
                    params={
                        **scoped,
                        query: term["id"],
                        "limit": 30,
                    },
                )
                assert result.status_code == 200
                items = result.json()["items"]
                assert len(items) == count, name
                assert all(item["workspace_id"] == str(workspace) for item in items)
                if field == "categories":
                    assert all(item["category"]["id"] == term["id"] for item in items)
                else:
                    assert all(
                        term["id"] in {tag["id"] for tag in item["tags"]}
                        for item in items
                    )
        assert (
            evaluation.get("/v1/gallery/filter-options", headers=headers).json()
            == options
        )
        foreign = SOCIAL if workspace == POLICE else POLICE
        assert (
            evaluation.get(
                "/v1/gallery/filter-options",
                headers=headers,
                params={"workspace_id": str(foreign)},
            ).status_code
            == 403
        )
        with evaluation.app.state.database.session_factory() as db:
            foreign_tag = db.scalar(
                select(PublicationTerm.id).where(
                    PublicationTerm.workspace_id == foreign,
                    PublicationTerm.kind == "tag",
                    PublicationTerm.active.is_(True),
                )
            )
        assert (
            evaluation.get(
                "/v1/gallery/page",
                headers=headers,
                params={"tag_ids": str(foreign_tag)},
            ).json()["items"]
            == []
        )


def test_hidden_content_and_removed_membership_do_not_leave_filter_options(evaluation):
    account, headers = authorization(evaluation, POLICE)
    with evaluation.app.state.database.session_factory() as db:
        db.execute(
            update(Publication)
            .where(
                Publication.workspace_id == POLICE,
                Publication.source_ref.like("security:pexels-%"),
            )
            .values(hidden=True)
        )
        db.commit()
    result = evaluation.get(
        "/v1/gallery/filter-options",
        headers=headers,
        params={"workspace_id": str(POLICE)},
    )
    assert result.status_code == 200
    assert "Audiovisual material" not in {
        row["name"] for row in result.json()["categories"]
    }
    assert "Observation video" not in {row["name"] for row in result.json()["tags"]}
    with evaluation.app.state.database.session_factory() as db:
        db.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == POLICE,
                WorkspaceMember.user_id == account,
            )
        )
        db.commit()
    assert (
        evaluation.get(
            "/v1/gallery/filter-options",
            headers=headers,
            params={"workspace_id": str(POLICE)},
        ).status_code
        == 403
    )
    assert evaluation.get("/v1/gallery/filter-options", headers=headers).json() == {
        "categories": [],
        "tags": [],
        "owners": [],
    }
    assert evaluation.get("/v1/gallery/page", headers=headers).json()["items"] == []
