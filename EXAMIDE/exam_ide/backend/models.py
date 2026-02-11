from pydantic import BaseModel
from typing import List, Optional

class Room(BaseModel):
    room_id: str
    room_code: str
    room_name: str
    teacher_name: str
    language: str
    students: List[str] = []
    questions: List[dict] = []
    status: str = "active"

class Question(BaseModel):
    question_id: str
    question_text: str
    language: str

class Worksheet(BaseModel):
    worksheet_id: str
    room_id: str
    student_id: str
    question_id: str
    code: str = ""
    language: str
    status: str = "working"
    last_updated: str

class ExecutionResult(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None

class CodeExecutionRequest(BaseModel):
    code: str
    language: str