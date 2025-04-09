from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: Optional[str]
    username: str
    email: str

class UserInDB(User):
    password: str

class UserInTable(BaseModel):
    id: Optional[str]
    username: str
    sentadilla: int
    peso_muerto: int
    press_banca: int