from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import (
    McpServerCreate,
    McpServerResponse,
    McpServerUpdate,
    McpStatsResponse,
)
from app.services.mcp_service import McpService

router = APIRouter()
mcp_service = McpService()


@router.get("/mcp/servers", response_model=list[McpServerResponse])
async def list_mcp_servers(db: AsyncSession = Depends(get_db)):
    return await mcp_service.list_servers(db)


@router.get("/mcp/stats", response_model=McpStatsResponse)
async def get_mcp_stats(db: AsyncSession = Depends(get_db)):
    return await mcp_service.get_stats(db)


@router.post("/mcp/servers", response_model=McpServerResponse)
async def create_mcp_server(payload: McpServerCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await mcp_service.create_server(db, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/mcp/servers/{server_id}", response_model=McpServerResponse)
async def update_mcp_server(
    server_id: str,
    payload: McpServerUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await mcp_service.update_server(db, server_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="mcp server not found")
    return updated


@router.delete("/mcp/servers/{server_id}")
async def delete_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await mcp_service.delete_server(db, server_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="mcp server not found")
    return {"success": True}


@router.post("/mcp/servers/{server_id}/probe", response_model=McpServerResponse)
async def probe_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    probed = await mcp_service.probe_server(db, server_id)
    if not probed:
        raise HTTPException(status_code=404, detail="mcp server not found")
    return probed


@router.post("/mcp/probe-all", response_model=list[McpServerResponse])
async def probe_all_mcp_servers(db: AsyncSession = Depends(get_db)):
    return await mcp_service.probe_all(db)
