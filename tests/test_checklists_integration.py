import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Checklist, ChecklistItem

pytestmark = pytest.mark.asyncio

# -----------------------------------------------------------------------------
# 1. POST /api/checklists/{id}/clone-to-project/{pid}
# -----------------------------------------------------------------------------

async def test_clone_checklist_happy_path(
    async_client: AsyncClient,
    db_session: AsyncSession,
    create_test_user,
    project_factory,
    checklist_factory,
    item_factory
):
    """Happy path: clones items, sets is_global=False, source_checklist_id matches."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    global_chk = await checklist_factory(is_global=True, name="Global Blueprint")
    await item_factory(checklist_id=global_chk.id, item_code="1.1", question="Q1", weight=1.0)
    await item_factory(checklist_id=global_chk.id, item_code="1.2", question="Q2", weight=2.0)

    res = await async_client.post(
        f"/api/checklists/{global_chk.id}/clone-to-project/{project.id}",
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_global"] is False
    assert data["source_checklist_id"] == global_chk.id
    assert data["project_id"] == project.id
    assert data["item_count"] == 2

    # Verify DB explicitly
    result = await db_session.execute(select(Checklist).where(Checklist.id == data["id"]))
    cloned_chk = result.scalar_one()
    assert cloned_chk.is_global is False
    assert cloned_chk.source_checklist_id == global_chk.id


async def test_clone_checklist_404_not_found(
    async_client: AsyncClient,
    create_test_user,
    project_factory
):
    """404 if source checklist not found."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)

    res = await async_client.post(
        f"/api/checklists/99999/clone-to-project/{project.id}",
        headers=headers
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


async def test_clone_checklist_400_already_project_checklist(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory
):
    """400 if source is already a project checklist."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    project_chk = await checklist_factory(is_global=False, project_id=project.id)

    res = await async_client.post(
        f"/api/checklists/{project_chk.id}/clone-to-project/{project.id}",
        headers=headers
    )
    assert res.status_code == 400
    assert "global" in res.json()["detail"].lower()


async def test_clone_checklist_403_wrong_project_owner(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory
):
    """403 if project belongs to another user (non-admin)."""
    user1, _ = await create_test_user(role="reviewer")
    user2, headers2 = await create_test_user(role="reviewer")  # Attacker

    project = await project_factory(owner_id=user1.id)
    global_chk = await checklist_factory(is_global=True)

    res = await async_client.post(
        f"/api/checklists/{global_chk.id}/clone-to-project/{project.id}",
        headers=headers2
    )
    assert res.status_code == 403


# -----------------------------------------------------------------------------
# 2. POST /api/checklists/{id}/items + PUT + DELETE
# -----------------------------------------------------------------------------

async def test_items_crud_403_on_global_checklist(
    async_client: AsyncClient,
    create_test_user,
    checklist_factory
):
    """403 when targeting a global checklist."""
    user, headers = await create_test_user(role="admin")
    global_chk = await checklist_factory(is_global=True)

    res = await async_client.post(
        f"/api/checklists/{global_chk.id}/items",
        json={"item_code": "1", "question": "Q", "weight": 1.0},
        headers=headers
    )
    assert res.status_code == 403
    assert "global" in res.json()["detail"].lower()


async def test_items_crud_workflow(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory
):
    """add item appears in GET response, edit changes fields, delete removes item."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    chk = await checklist_factory(is_global=False, project_id=project.id)

    # ADD
    add_payload = {
        "item_code": "NEW.1",
        "question": "Is CRUD working?",
        "weight": 2.5,
        "is_required": True,
        "area": "Testing"
    }
    res_add = await async_client.post(f"/api/checklists/{chk.id}/items", json=add_payload, headers=headers)
    assert res_add.status_code == 200
    item_id = res_add.json()["id"]

    # Verify via GET
    res_get = await async_client.get(f"/api/checklists/{chk.id}?include_items=true", headers=headers)
    items = res_get.json().get("items", [])
    assert any(i["id"] == item_id and i["question"] == "Is CRUD working?" for i in items)

    # EDIT
    edit_payload = {
        "item_code": "NEW.1",
        "question": "Updated Question",
        "weight": 3.0,
        "is_required": False
    }
    res_edit = await async_client.put(f"/api/checklists/{chk.id}/items/{item_id}", json=edit_payload, headers=headers)
    assert res_edit.status_code == 200
    assert res_edit.json()["question"] == "Updated Question"

    # DELETE
    res_del = await async_client.delete(f"/api/checklists/{chk.id}/items/{item_id}", headers=headers)
    assert res_del.status_code == 200

    # Verify removal
    res_get_after = await async_client.get(f"/api/checklists/{chk.id}?include_items=true", headers=headers)
    items_after = res_get_after.json().get("items", [])
    assert not any(i["id"] == item_id for i in items_after)


# -----------------------------------------------------------------------------
# 3. POST /api/checklists/{id}/sync-from-global
# -----------------------------------------------------------------------------

async def test_sync_add_new_only(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory,
    item_factory
):
    """add_new_only: only adds missing items, does not touch existing."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    
    global_chk = await checklist_factory(is_global=True)
    await item_factory(checklist_id=global_chk.id, item_code="1.1", question="Global 1.1", weight=1.0)
    await item_factory(checklist_id=global_chk.id, item_code="2.1", question="New Global 2.1", weight=2.0)

    proj_chk = await checklist_factory(is_global=False, project_id=project.id, source_checklist_id=global_chk.id)
    
    # Project has modified 1.1, missing 2.1
    await item_factory(checklist_id=proj_chk.id, item_code="1.1", question="Modified Local 1.1", weight=5.0)

    res = await async_client.post(
        f"/api/checklists/{proj_chk.id}/sync-from-global",
        json={"strategy": "add_new_only"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["added"] == 1
    assert data["updated"] == 0

    res_get = await async_client.get(f"/api/checklists/{proj_chk.id}?include_items=true", headers=headers)
    items = res_get.json()["items"]
    assert len(items) == 2
    
    # Existing item untouched
    item_11 = next(i for i in items if i["item_code"] == "1.1")
    assert item_11["question"] == "Modified Local 1.1"
    assert item_11["weight"] == 5.0
    
    # New item added
    item_21 = next(i for i in items if i["item_code"] == "2.1")
    assert item_21["question"] == "New Global 2.1"


async def test_sync_add_and_update(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory,
    item_factory
):
    """add_and_update: updates changed items + adds missing."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    
    global_chk = await checklist_factory(is_global=True)
    await item_factory(checklist_id=global_chk.id, item_code="1.1", question="Global 1.1 Updated", weight=2.0)
    await item_factory(checklist_id=global_chk.id, item_code="2.1", question="New Global 2.1", weight=2.0)

    proj_chk = await checklist_factory(is_global=False, project_id=project.id, source_checklist_id=global_chk.id)
    await item_factory(checklist_id=proj_chk.id, item_code="1.1", question="Old Local 1.1", weight=1.0)

    res = await async_client.post(
        f"/api/checklists/{proj_chk.id}/sync-from-global",
        json={"strategy": "add_and_update"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["added"] == 1
    assert data["updated"] == 1

    res_get = await async_client.get(f"/api/checklists/{proj_chk.id}?include_items=true", headers=headers)
    items = res_get.json()["items"]
    
    item_11 = next(i for i in items if i["item_code"] == "1.1")
    assert item_11["question"] == "Global 1.1 Updated"
    assert item_11["weight"] == 2.0


async def test_sync_full_reset(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory,
    item_factory
):
    """full_reset: replaces all items with global copy."""
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    
    global_chk = await checklist_factory(is_global=True)
    await item_factory(checklist_id=global_chk.id, item_code="NEW.G", question="Global Only")

    proj_chk = await checklist_factory(is_global=False, project_id=project.id, source_checklist_id=global_chk.id)
    await item_factory(checklist_id=proj_chk.id, item_code="LOCAL.1", question="Local Only - Will be wiped")

    res = await async_client.post(
        f"/api/checklists/{proj_chk.id}/sync-from-global",
        json={"strategy": "full_reset"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["added"] == 1

    res_get = await async_client.get(f"/api/checklists/{proj_chk.id}?include_items=true", headers=headers)
    items = res_get.json()["items"]

    assert len(items) == 1
    assert items[0]["item_code"] == "NEW.G"


async def test_sync_403_wrong_project_owner(
    async_client: AsyncClient,
    create_test_user,
    project_factory,
    checklist_factory,
    item_factory
):
    """403 when a non-owner tries to sync another user's project checklist."""
    owner, _ = await create_test_user(role="reviewer")
    attacker, attacker_headers = await create_test_user(role="reviewer")

    project = await project_factory(owner_id=owner.id)
    global_chk = await checklist_factory(is_global=True)
    await item_factory(checklist_id=global_chk.id, item_code="1.1", question="Q1")

    proj_chk = await checklist_factory(
        is_global=False, project_id=project.id, source_checklist_id=global_chk.id
    )

    res = await async_client.post(
        f"/api/checklists/{proj_chk.id}/sync-from-global",
        json={"strategy": "add_new_only"},
        headers=attacker_headers,
    )
    assert res.status_code == 403
