from pydantic import BaseModel


class CreateTableRequest(BaseModel):
    bot_styles: list[str] | None = None


class ActionRequest(BaseModel):
    action_type: str  # fold, check, call, raise, all_in
    amount: int | None = None


class TableResponse(BaseModel):
    table_id: str
    seats: list[dict]
    community_cards: list[str]
    pot: int
    button_index: int
    current_street: int
    active_seat_index: int
    hand_number: int
    is_hand_in_progress: bool
    hero_seat_index: int
    legal_actions: list[str] = []
    waiting_for_hero: bool = False
    hand_complete: bool = False
    winner: dict | None = None
    showdown: bool = False
    pot_results: list[dict] = []
