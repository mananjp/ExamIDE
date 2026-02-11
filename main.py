from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from code_executor import CodeExecutor


# ============================================================================
# DATA MODELS
# ============================================================================

class Room(BaseModel):
    room_id: str
    room_code: str
    room_name: str
    teacher_name: str
    language: str
    students: List[str] = []
    student_names: Dict[str, str] = {}  # NEW: Map student_id to student_name
    questions: List[Dict] = []
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


# ============================================================================
# DATABASE (In-Memory)
# ============================================================================

class Database:
    def __init__(self):
        self.rooms = {}
        self.questions = {}
        self.worksheets = {}
        self.sessions = {}
        self.student_names = {}  # NEW: Track student names globally

    def create_room(self, room_name: str, teacher_name: str, language: str) -> Room:
        room_id = str(uuid.uuid4())
        room_code = str(uuid.uuid4())[:6].upper()

        room = Room(
            room_id=room_id,
            room_code=room_code,
            room_name=room_name,
            teacher_name=teacher_name,
            language=language,
            students=[],
            student_names={},
            questions=[]
        )

        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def join_room(self, room_code: str, student_name: str) -> dict:
        for room in self.rooms.values():
            if room.room_code == room_code:
                student_id = str(uuid.uuid4())
                room.students.append(student_id)
                room.student_names[student_id] = student_name  # NEW: Store student name
                self.student_names[student_id] = student_name  # Also store globally
                return {
                    "room_id": room.room_id,
                    "student_id": student_id,
                    "student_name": student_name
                }
        return None

    def create_question(self, room_id: str, question_text: str, language: str) -> dict:
        room = self.rooms.get(room_id)
        if not room:
            return None

        question_id = str(uuid.uuid4())
        question = {
            "question_id": question_id,
            "question_text": question_text,
            "language": language
        }

        room.questions.append(question)
        self.questions[question_id] = question

        return question

    def get_questions(self, room_id: str) -> List[dict]:
        room = self.rooms.get(room_id)
        if room:
            return room.questions
        return []

    def create_worksheet(self, room_id: str, student_id: str, question_id: str, language: str) -> Worksheet:
        worksheet_id = str(uuid.uuid4())

        worksheet = Worksheet(
            worksheet_id=worksheet_id,
            room_id=room_id,
            student_id=student_id,
            question_id=question_id,
            language=language,
            status="working",
            last_updated=datetime.now().isoformat()
        )

        self.worksheets[worksheet_id] = worksheet
        return worksheet

    def get_worksheet(self, worksheet_id: str) -> Optional[Worksheet]:
        return self.worksheets.get(worksheet_id)

    def save_worksheet(self, worksheet_id: str, code: str) -> bool:
        worksheet = self.worksheets.get(worksheet_id)
        if worksheet:
            worksheet.code = code
            worksheet.last_updated = datetime.now().isoformat()
            return True
        return False

    def get_student_worksheets(self, room_id: str, student_id: str) -> Dict:
        """Get all worksheets for a specific student in a room"""
        student_worksheets = {}
        for ws_id, ws in self.worksheets.items():
            if ws.room_id == room_id and ws.student_id == student_id:
                student_worksheets[ws_id] = {
                    "code": ws.code,
                    "language": ws.language,
                    "status": ws.status,
                    "last_updated": ws.last_updated,
                    "question_id": ws.question_id
                }
        return student_worksheets

    # ========================================================================
    # STEP 3: GET STUDENT CODES WITH NAMES (UPDATED)
    # ========================================================================

    def get_student_codes_with_names(self, room_id: str) -> Dict:
        """
        Get all student codes in a room with student NAMES
        Returns: {student_id: {name, code, language, status, last_updated, question_id}}
        """
        room = self.rooms.get(room_id)
        if not room:
            return {}

        # Collect all student codes with their names
        student_codes = {}

        for student_id in room.students:
            # Get student name from room mapping
            student_name = room.student_names.get(student_id, "Unknown Student")

            # Get all worksheets for this student
            student_worksheets = self.get_student_worksheets(room_id, student_id)

            if student_worksheets:
                # Get the most recently updated worksheet
                latest_ws_id = None
                latest_ws = None
                latest_time = None

                for ws_id, ws_data in student_worksheets.items():
                    ws_time = ws_data.get("last_updated", "")
                    if latest_time is None or ws_time > latest_time:
                        latest_time = ws_time
                        latest_ws_id = ws_id
                        latest_ws = ws_data

                if latest_ws:
                    student_codes[student_id] = {
                        "student_name": student_name,  # NEW: Include student name
                        "code": latest_ws.get("code", ""),
                        "language": latest_ws.get("language", "python"),
                        "status": latest_ws.get("status", "working"),
                        "last_updated": latest_ws.get("last_updated", ""),
                        "question_id": latest_ws.get("question_id", "")
                    }
            else:
                # Student hasn't written any code yet
                student_codes[student_id] = {
                    "student_name": student_name,  # NEW: Include student name
                    "code": "",
                    "language": "python",
                    "status": "idle",
                    "last_updated": "",
                    "question_id": ""
                }

        return student_codes


# ============================================================================
# INITIALIZE APP
# ============================================================================

app = FastAPI(title="Online Exam IDE API")
db = Database()
code_executor = CodeExecutor()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============================================================================
# ROOM ENDPOINTS
# ============================================================================

@app.post("/api/rooms/create")
async def create_room(data: dict):
    """Create a new exam room"""
    room = db.create_room(
        room_name=data.get("room_name"),
        teacher_name=data.get("teacher_name"),
        language=data.get("language", "Python")
    )

    return {
        "room_id": room.room_id,
        "room_code": room.room_code,
        "room_name": room.room_name,
        "teacher_name": room.teacher_name
    }


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details"""
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return {
        "room_id": room.room_id,
        "room_code": room.room_code,
        "room_name": room.room_name,
        "teacher_name": room.teacher_name,
        "students": room.students,
        "student_names": room.student_names,  # NEW: Return student names mapping
        "questions": room.questions,
        "language": room.language
    }


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, data: dict):
    """Join an existing room"""
    result = db.join_room(room_code, data.get("student_name"))
    if not result:
        raise HTTPException(status_code=404, detail="Room not found")

    return result


# ============================================================================
# QUESTION ENDPOINTS
# ============================================================================

@app.post("/api/rooms/{room_id}/questions")
async def create_question(room_id: str, data: dict):
    """Create a question in a room"""
    question = db.create_question(
        room_id=room_id,
        question_text=data.get("question_text"),
        language=data.get("language", "Python")
    )

    if not question:
        raise HTTPException(status_code=404, detail="Room not found")

    return question


@app.get("/api/rooms/{room_id}/questions")
async def get_questions(room_id: str):
    """Get all questions in a room"""
    questions = db.get_questions(room_id)
    return {"questions": questions}


# ============================================================================
# WORKSHEET ENDPOINTS
# ============================================================================

@app.get("/api/worksheets/{room_id}/{student_id}/{question_id}")
async def get_worksheet(room_id: str, student_id: str, question_id: str):
    """Get or create a worksheet"""
    # Find existing worksheet or create new
    worksheets = [ws for ws in db.worksheets.values()
                  if ws.room_id == room_id and ws.student_id == student_id and ws.question_id == question_id]

    if worksheets:
        ws = worksheets[0]
    else:
        # Get language from question
        question = db.questions.get(question_id)
        language = question.get("language", "Python") if question else "Python"
        ws = db.create_worksheet(room_id, student_id, question_id, language)

    return {
        "worksheet_id": ws.worksheet_id,
        "code": ws.code,
        "language": ws.language,
        "status": ws.status,
        "last_updated": ws.last_updated
    }


@app.post("/api/worksheets/{worksheet_id}/save")
async def save_worksheet(worksheet_id: str, data: dict):
    """Save worksheet code"""
    success = db.save_worksheet(worksheet_id, data.get("code", ""))

    if not success:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    return {"success": True, "message": "Code saved"}


# ============================================================================
# CODE EXECUTION ENDPOINT
# ============================================================================

@app.post("/api/execute")
async def execute_code(data: dict):
    """Execute code"""
    code = data.get("code")
    language = data.get("language", "python").lower()

    result = code_executor.execute(code, language)

    return result


# ============================================================================
# STEP 3: LIVE CODE MONITOR ENDPOINT (UPDATED WITH STUDENT NAMES)
# ============================================================================

@app.get("/api/rooms/{room_id}/student-codes")
async def get_student_codes(room_id: str):
    """
    Get all student codes in a room with student NAMES
    Used for Step 3: Live Code Monitor
    Returns student name, code, status, and more!
    """
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Get student codes with names
    student_codes = db.get_student_codes_with_names(room_id)

    return {
        "room_id": room_id,
        "student_codes": student_codes,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)