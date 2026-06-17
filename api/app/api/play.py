from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.database import get_db
from app.models.user import User
from app.services.poker_engine.game_manager import game_manager
from app.schemas.game import ActionRequest, TableResponse

router = APIRouter()


@router.post("/tables")
def create_table(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    table = game_manager.create_table(user_id, user.display_name)
    return {"table_id": table.table_id, "table": table.to_dict(user_id)}


@router.post("/tables/{table_id}/start")
def start_hand(
    table_id: str,
    user_id: int = Depends(get_current_user_id),
):
    if table_id not in game_manager.tables:
        raise HTTPException(status_code=404, detail="Table not found")
    table = game_manager.start_hand(table_id)
    legal = game_manager.get_legal_actions(table_id, user_id)
    d = table.to_dict(user_id)
    d["legal_actions"] = legal
    return d


@router.post("/tables/{table_id}/action")
def action(
    table_id: str,
    req: ActionRequest,
    user_id: int = Depends(get_current_user_id),
):
    result = game_manager.apply_hero_action(table_id, user_id, req.action_type, req.amount)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/tables/{table_id}")
def get_table(
    table_id: str,
    user_id: int = Depends(get_current_user_id),
):
    if table_id not in game_manager.tables:
        raise HTTPException(status_code=404, detail="Table not found")
    table = game_manager.tables[table_id]
    legal = game_manager.get_legal_actions(table_id, user_id)
    d = table.to_dict(user_id)
    d["legal_actions"] = legal
    return d
