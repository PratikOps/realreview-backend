from pydantic import BaseModel
from datetime import datetime

class ImageCreate(BaseModel):
    uploader: str
    location: str

class ImageOut(BaseModel):
    id: int
    filename: str
    uploader: str
    location: str
    timestamp: datetime
    url: str  # 👈 add this line

    class Config:
        orm_mode = True
