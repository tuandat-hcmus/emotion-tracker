from pydantic import BaseModel, Field


class SeedDemoDataRequest(BaseModel):
    days: int = Field(default=30, ge=7, le=90)
    email: str = "demo@example.com"
    password: str = Field(default="demo123456", min_length=8)
    reset: bool = False


class SeedDemoDataResponse(BaseModel):
    user_id: str
    email: str
    days: int
    entry_count: int
    weekly_wrapup_id: str
    monthly_wrapup_id: str
    reset_applied: bool


class ResetDemoDataRequest(BaseModel):
    email: str = "demo@example.com"


class ResetDemoDataResponse(BaseModel):
    email: str
    removed_user: bool
