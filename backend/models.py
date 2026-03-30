from pydantic import BaseModel
from typing import List, Optional, Dict

class TestCase(BaseModel):
    test_id: str
    input_data: str          # stdin input to feed the program
    expected_output: str     # expected stdout output (stripped for comparison)
    is_hidden: bool = False  # True = hidden from students, used only for judging

class Room(BaseModel):
    room_id: str
    room_code: str
    room_name: str
    teacher_name: str
    language: str
    duration_minutes: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    students: List[str] = []
    student_names: Dict[str, str] = {}
    student_red_flags: Dict[str, int] = {}
    questions: List[dict] = []
    status: str = "active"

class Question(BaseModel):
    question_id: str
    question_text: str
    language: str
    test_cases: List[TestCase] = []

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

class SubmissionResult(BaseModel):
    question_id: str
    total_cases: int
    passed_cases: int
    results: List[dict] = []  # per-case verdict details
    overall: str              # "Accepted" / "Wrong Answer" / "Runtime Error" / "Compilation Error"