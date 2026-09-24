"""4CE: the sovereignty page's API - what the workbench connects to, observed,
beside what its configuration permits, audited. Admin only throughout: the
page names processes, ports and addresses on this machine.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from open_webui.models.tools import Tools
from open_webui.utils.auth import get_admin_user
from open_webui.utils.fource_egress import watch
from open_webui.utils.plugin import get_tool_module_from_cache

log = logging.getLogger(__name__)

router = APIRouter()

# Installed by 4ce/install.py; the audit lives in the tool so chat and this
# page report from the same code.
SOVEREIGNTY_TOOL_ID = "ace_sovereignty"


@router.get("/egress")
async def get_egress(user=Depends(get_admin_user)):
    return watch.snapshot()


@router.post("/egress/canary")
async def run_canary(user=Depends(get_admin_user)):
    if not watch.running:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="The egress watch is not running.")
    return await watch.run_canary()


@router.post("/egress/reset")
async def reset_egress(user=Depends(get_admin_user)):
    watch.reset()
    return watch.snapshot()


@router.get("/audit")
async def get_audit(request: Request, user=Depends(get_admin_user)):
    try:
        module, _ = await get_tool_module_from_cache(request, SOVEREIGNTY_TOOL_ID)
    except Exception:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="The 4CE sovereignty tool is not installed. Run 4ce/install.py.",
        )
    valves = await Tools.get_tool_valves_by_id(SOVEREIGNTY_TOOL_ID)
    if hasattr(module, "Valves"):
        module.valves = module.Valves(**(valves or {}))
    findings = await module._audit()
    return {
        "checks": [{"label": label, "ok": ok, "detail": detail} for label, ok, detail in findings],
        "passed": sum(1 for _, ok, _ in findings if ok),
        "total": len(findings),
    }
