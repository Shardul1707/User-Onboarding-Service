from pydantic import BaseModel
from datetime import datetime

class UserRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

class UserResponse(BaseModel):
    status: str
    message: str
    verification: str
    user_id: str

class UserDetailsResponse(BaseModel):
    status: str
    message: str = None
    email: str = None
    first_name: str = None
    last_name: str = None
    verification_state: str = None
    user_id: str = None
    created_on: datetime = None