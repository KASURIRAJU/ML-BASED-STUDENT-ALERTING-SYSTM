"""Safe faculty profile response schema."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FacultyProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_identifier: str
    first_name: str
    last_name: str
    department: str
    created_at: datetime
