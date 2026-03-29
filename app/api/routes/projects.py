"""
Projects API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from datetime import datetime
import logging
import re
import json

from pydantic import BaseModel

from app.db.session import get_db
from app.models import Project, Checklist, ChecklistItem, User
from app.services.checklist_parser import parse_excel_checklist
from app.api.routes.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class ProjectWithChecklistsCreate(BaseModel):
    """Request model for creating a project with checklists"""
    name: str
    domain: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    stakeholders: Optional[Dict] = None
    status: str = "active"
    checklist_ids: Optional[List[int]] = []
    checklist_names: Optional[Dict[str, str]] = None


@router.get("/")
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """List all projects with pagination"""
    query = select(Project)

    if status:
        query = query.where(Project.status == status)

    # Get total count for pagination metadata
    total_query = select(func.count()).select_from(Project)
    if status:
        total_query = total_query.where(Project.status == status)
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    return {
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "domain": p.domain,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in projects
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
            "has_more": skip + limit < total
        }
    }


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get project details"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "name": project.name,
        "domain": project.domain,
        "description": project.description,
        "tech_stack": project.tech_stack,
        "stakeholders": project.stakeholders,
        "status": project.status,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None
    }


@router.post("/")
async def create_project(
    name: str = Form(..., min_length=1, max_length=200),
    domain: str = Form(None, max_length=100),
    description: str = Form(None, max_length=2000),
    tech_stack: str = Form(None),
    stakeholders: str = Form(None),
    status: str = Form("active"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project with validation"""
    # Validate project name
    if not name or len(name.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Project name cannot be empty"
        )

    # Validate status
    valid_statuses = ["active", "completed", "on_hold"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    # Parse JSON fields
    try:
        tech_stack_list = json.loads(tech_stack) if tech_stack else None
        stakeholders_dict = json.loads(stakeholders) if stakeholders else None
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON format in tech_stack or stakeholders: {str(e)}"
        )

    project = Project(
        name=name.strip(),
        domain=domain.strip() if domain else None,
        description=description.strip() if description else None,
        tech_stack=tech_stack_list,
        stakeholders=stakeholders_dict,
        status=status
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Project created: {project.name} (ID: {project.id})")

    return {
        "message": "Project created successfully",
        "project_id": project.id,
        "name": project.name
    }


@router.post("/create-with-checklists")
async def create_project_with_checklists(
    req: ProjectWithChecklistsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project and clone one or more global checklists into it in a single transaction.
    """
    try:
        # Validate project name
        if not req.name or len(req.name.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Project name cannot be empty"
            )

        # Validate status
        valid_statuses = ["active", "completed", "on_hold"]
        if req.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Create the project
        project = Project(
            name=req.name.strip(),
            domain=req.domain.strip() if req.domain else None,
            description=req.description.strip() if req.description else None,
            tech_stack=req.tech_stack,
            stakeholders=req.stakeholders,
            status=req.status,
            owner_id=current_user.id
        )

        db.add(project)
        await db.flush()  # Get project ID without committing

        # Clone checklists
        checklists_cloned = []

        for checklist_id in req.checklist_ids or []:
            # Load the global checklist with items
            result = await db.execute(
                select(Checklist)
                .options(selectinload(Checklist.items))
                .where(Checklist.id == checklist_id)
            )
            source_checklist = result.scalar_one_or_none()

            if not source_checklist:
                logger.warning(f"Checklist ID {checklist_id} not found, skipping")
                continue

            if not source_checklist.is_global:
                logger.warning(f"Checklist ID {checklist_id} is not global, skipping")
                continue

            # Determine the name for the cloned checklist
            checklist_name = (
                req.checklist_names.get(str(checklist_id), "").strip()
                if req.checklist_names and req.checklist_names.get(str(checklist_id))
                else source_checklist.name
            )
            if not checklist_name:
                checklist_name = source_checklist.name

            # Create the cloned checklist
            new_checklist = Checklist(
                name=checklist_name,
                type=source_checklist.type,
                version=source_checklist.version,
                project_id=project.id,
                is_global=False,
                source_checklist_id=source_checklist.id
            )
            db.add(new_checklist)
            await db.flush()  # Get checklist ID

            # Deep-copy all items
            items_count = 0
            for item in source_checklist.items:
                new_item = ChecklistItem(
                    checklist_id=new_checklist.id,
                    item_code=item.item_code,
                    area=item.area,
                    question=item.question,
                    category=item.category,
                    weight=item.weight,
                    is_review_mandatory=item.is_review_mandatory,
                    expected_evidence=item.expected_evidence,
                    suggested_for_domains=item.suggested_for_domains,
                    order=item.order
                )
                db.add(new_item)
                items_count += 1

            checklists_cloned.append({
                "id": new_checklist.id,
                "name": new_checklist.name,
                "type": new_checklist.type,
                "item_count": items_count
            })

            logger.info(
                f"Cloned checklist '{source_checklist.name}' (ID: {checklist_id}) "
                f"to project '{project.name}' (ID: {project.id}) as '{new_checklist.name}'"
            )

        await db.commit()
        await db.refresh(project)

        logger.info(
            f"Project created with checklists: {project.name} (ID: {project.id}), "
            f"owner: {current_user.email}, checklists cloned: {len(checklists_cloned)}"
        )

        return {
            "project_id": project.id,
            "name": project.name,
            "checklists_cloned": checklists_cloned
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating project with checklists: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/upload-checklist")
async def upload_checklist(
    project_id: int,
    file: UploadFile = File(..., description="Excel checklist file (.xlsx)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload Excel checklist file for a project.
    Parses the file and creates checklist items in database.
    """
    import tempfile
    import os
    
    # Validate file type
    allowed_extensions = [".xlsx", ".xlsm"]
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 25MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        logger.info(f"Uploading checklist for project {project_id}: {file.filename}")
        
        # Parse the Excel file
        parsed_data = await parse_excel_checklist(tmp_path)
        
        if not parsed_data.get("checklists"):
            raise HTTPException(
                status_code=400,
                detail="No valid checklists found in Excel file"
            )

        # Create checklists and items
        created_checklists = []

        for checklist_type, items in parsed_data.get("checklists", {}).items():
            if not items:
                logger.warning(f"No items found for checklist type: {checklist_type}")
                continue
                
            checklist = Checklist(
                name=f"{checklist_type.title()} Check List",
                type=checklist_type,
                project_id=project_id,
                is_global=False
            )

            db.add(checklist)
            await db.flush()  # Get checklist ID

            # Add items
            for idx, item_data in enumerate(items):
                item = ChecklistItem(
                    checklist_id=checklist.id,
                    item_code=item_data.get("item_code", str(idx + 1)),
                    area=item_data.get("area", "General"),
                    question=item_data.get("question"),
                    category=item_data.get("category", checklist_type),
                    weight=item_data.get("weight", 1.0),
                    is_review_mandatory=item_data.get("is_review_mandatory", item_data.get("is_required", True)),
                    expected_evidence=item_data.get("expected_evidence"),
                    order=idx
                )
                db.add(item)

            created_checklists.append({
                "id": checklist.id,
                "type": checklist_type,
                "items_count": len(items)
            })

        await db.commit()
        
        logger.info(
            f"Checklist uploaded successfully for project {project_id}. "
            f"Created {len(created_checklists)} checklists"
        )

        return {
            "message": "Checklist uploaded and parsed successfully",
            "project_id": project_id,
            "checklists": created_checklists,
            "statistics": parsed_data.get("statistics")
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error parsing checklist: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing checklist: {str(e)}"
        )

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.put("/{project_id}")
async def update_project(
    project_id: int,
    name: Optional[str] = Form(None, min_length=1, max_length=200),
    domain: Optional[str] = Form(None, max_length=100),
    description: Optional[str] = Form(None, max_length=2000),
    status: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Update project details with validation"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate status if provided
    if status is not None:
        valid_statuses = ["active", "completed", "on_hold"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        project.status = status

    # Update fields if provided
    if name is not None:
        project.name = name.strip()
    if domain is not None:
        project.domain = domain.strip()
    if description is not None:
        project.description = description.strip()

    project.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(project)
    
    logger.info(f"Project updated: {project.name} (ID: {project.id})")

    return {
        "message": "Project updated successfully",
        "project_id": project.id
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_name = project.name
    await db.delete(project)
    await db.commit()
    
    logger.info(f"Project deleted: {project_name} (ID: {project_id})")

    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/checklists")
async def get_project_checklists(
    project_id: int,
    include_items: bool = Query(False, description="Include checklist items in response"),
    db: AsyncSession = Depends(get_db)
):
    """Get all checklists for a project"""
    # Verify project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await db.execute(
        select(Checklist)
        .where(Checklist.project_id == project_id)
        .options(selectinload(Checklist.items))
    )
    checklists = result.scalars().all()

    response = {
        "project_id": project_id,
        "project_name": project.name,
        "checklists": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "version": c.version,
                "items_count": len(c.items),
                "source_checklist_id": c.source_checklist_id,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in checklists
        ],
        "total": len(checklists)
    }
    
    # Optionally include items
    if include_items:
        for i, checklist in enumerate(checklists):
            response["checklists"][i]["items"] = [
                {
                    "id": item.id,
                    "item_code": item.item_code,
                    "area": item.area,
                    "question": item.question,
                    "category": item.category,
                    "weight": item.weight,
                    "is_review_mandatory": item.is_review_mandatory
                }
                for item in checklist.items
            ]
    
    return response

@router.get("/templates")
async def list_templates(
    db: AsyncSession = Depends(get_db)
):
    """
    List available global checklist templates.
    These are templates stored in the database that can be applied to projects.
    """
    result = await db.execute(
        select(Checklist).where(Checklist.is_global == True)
    )
    templates = result.scalars().all()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "type": t.type,
                "version": t.version,
                "items_count": len(t.items),
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in templates
        ],
        "total": len(templates)
    }


@router.post("/{project_id}/use-template/{template_id}")
async def use_template_for_project(
    project_id: int,
    template_id: int,
):
    """Deprecated — use POST /api/checklists/{template_id}/clone-to-project/{project_id} instead."""
    raise HTTPException(
        status_code=410,
        detail=(
            "This endpoint is deprecated. Use "
            f"POST /api/checklists/{template_id}/clone-to-project/{project_id} instead. "
            "The new endpoint requires authentication and tracks the source template for sync."
        )
    )
