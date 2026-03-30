from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from code_executor import CodeExecutor
from database import Database
from models import Room, Question, Worksheet, ExecutionResult, TestCase, SubmissionResult
from report_generator import generate_exam_report

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("WARNING: MONGO_URI not found in .env")

# ============================================================================
# INITIALIZE APP
# ============================================================================

app = FastAPI(title="Online Exam IDE API",docs_url="/docs", redoc_url="/redoc")
# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database
db = Database(MONGO_URI)
code_executor = CodeExecutor()

# Max score per question (each question is worth this many points)
MAX_SCORE_PER_QUESTION = 100


# ============================================================================
# HELPER: Room expiry check
# ============================================================================

async def check_room_active(room_id: str) -> dict:
    """Check if room exists and is active. Auto-expire if time is up."""
    room = await db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.get("status") == "expired":
        raise HTTPException(status_code=403, detail="This exam has ended. Room is no longer accessible.")
    
    if db.is_room_expired(room):
        await db.expire_room(room_id)
        raise HTTPException(status_code=403, detail="This exam has ended. Room code has been revoked.")
    
    return room


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
    room_name = data.get("room_name")
    teacher_name = data.get("teacher_name")
    language = data.get("language", "Python")
    duration_minutes = int(data.get("duration", 30))
    start_time = data.get("start_time") # ISO String
    
    room = await db.create_room(
        room_name=room_name,
        teacher_name=teacher_name,
        language=language,
        duration_minutes=duration_minutes,
        start_time=start_time
    )
    
    return {
        "room_id": room["room_id"],
        "room_code": room["room_code"],
        "room_name": room["room_name"],
        "teacher_name": room["teacher_name"],
        "duration_minutes": room["duration_minutes"],
        "start_time": room["start_time"],
        "end_time": room["end_time"]
    }


@app.post("/api/rooms/{room_id}/report_violation")
async def report_violation(room_id: str, data: dict):
    """Report a student violation (tab switch, etc.)"""
    student_id = data.get("student_id")
    
    room = await db.get_room(room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    if student_id:
        current_flags = room.get("student_red_flags", {}).get(student_id, 0)
        new_flags = current_flags + 1
        await db.update_red_flags(room_id, student_id, new_flags)
        
        return {"success": True, "new_count": new_flags}
    
    return {"success": False}


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details. Auto-detects and marks expired rooms."""
    room = await db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Auto-expire if time is up (but still return data for teacher to view)
    status = room.get("status", "active")
    if status != "expired" and db.is_room_expired(room):
        await db.expire_room(room_id)
        status = "expired"

    return {
        "room_id": room["room_id"],
        "room_code": room["room_code"],
        "room_name": room["room_name"],
        "teacher_name": room["teacher_name"],
        "students": room.get("students", []),
        "student_names": room.get("student_names", {}),
        "questions": room.get("questions", []),
        "language": room.get("language"),
        "duration_minutes": room.get("duration_minutes"),
        "start_time": room.get("start_time"),
        "end_time": room.get("end_time"),
        "student_red_flags": room.get("student_red_flags", {}),
        "status": status
    }


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, data: dict):
    """Join an existing room. BLOCKED if room is expired."""
    result = await db.join_room(room_code, data.get("student_name"))
    if not result:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if db.join_room returned an error (expired room)
    if "error" in result and result["error"] == "expired":
        raise HTTPException(status_code=403, detail=result["detail"])

    return result


# ============================================================================
# QUESTION ENDPOINTS
# ============================================================================

@app.post("/api/rooms/{room_id}/questions")
async def create_question(room_id: str, data: dict):
    """Create a question in a room, with optional test cases."""
    question = await db.create_question(
        room_id=room_id,
        question_text=data.get("question_text"),
        language=data.get("language", "Python"),
        test_cases=data.get("test_cases", [])
    )

    if not question:
        raise HTTPException(status_code=404, detail="Room not found")

    return question


@app.get("/api/rooms/{room_id}/questions")
async def get_questions(room_id: str):
    """
    Get all questions in a room.
    Hidden test cases are filtered out for student consumption.
    """
    questions = await db.get_questions(room_id)
    
    filtered_questions = []
    for q in questions:
        filtered_q = {
            "question_id": q["question_id"],
            "question_text": q["question_text"],
            "language": q.get("language", "Python"),
            "test_cases": [
                tc for tc in q.get("test_cases", [])
                if not tc.get("is_hidden", False)
            ],
            "total_test_cases": len(q.get("test_cases", [])),
            "hidden_test_cases_count": len([
                tc for tc in q.get("test_cases", [])
                if tc.get("is_hidden", False)
            ])
        }
        filtered_questions.append(filtered_q)
    
    return {"questions": filtered_questions}


@app.get("/api/rooms/{room_id}/questions/full")
async def get_questions_full(room_id: str):
    """Get all questions including hidden test cases (for teacher use)."""
    questions = await db.get_questions(room_id)
    return {"questions": questions}


# ============================================================================
# WORKSHEET ENDPOINTS
# ============================================================================

@app.get("/api/worksheets/{room_id}/{student_id}/{question_id}")
async def get_worksheet(room_id: str, student_id: str, question_id: str):
    """Get or create a worksheet"""
    ws = await db.get_worksheet(room_id, student_id, question_id)

    if ws:
        pass
    else:
        room = await db.get_room(room_id)
        language = "Python" # Default
        if room:
            for q in room.get("questions", []):
                if q["question_id"] == question_id:
                    language = q.get("language", "Python")
                    break
        
        ws = await db.create_worksheet(room_id, student_id, question_id, language)

    return {
        "worksheet_id": ws["worksheet_id"],
        "code": ws["code"],
        "language": ws["language"],
        "status": ws["status"],
        "last_updated": ws["last_updated"]
    }


@app.post("/api/worksheets/{worksheet_id}/save")
async def save_worksheet(worksheet_id: str, data: dict):
    """Save worksheet code. BLOCKED if room is expired."""
    # Check if the worksheet's room is still active
    ws = await db.get_worksheet_by_id(worksheet_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    
    room = await db.get_room(ws["room_id"])
    if room and (room.get("status") == "expired" or db.is_room_expired(room)):
        if room.get("status") != "expired":
            await db.expire_room(room["room_id"])
        raise HTTPException(status_code=403, detail="Exam has ended. Cannot save code.")

    success = await db.save_worksheet(worksheet_id, data.get("code", ""))

    if not success:
        return {"success": True, "message": "Code saved (no changes)"}

    return {"success": True, "message": "Code saved"}


# ============================================================================
# CODE EXECUTION ENDPOINT
# ============================================================================

@app.post("/api/execute")
async def execute_code(data: dict):
    """Execute code (freeform run, no test case checking)"""
    code = data.get("code")
    language = data.get("language", "python").lower()

    result = code_executor.execute(code, language)

    return result


# ============================================================================
# SUBMISSION / AUTO-JUDGE ENDPOINT  (WITH SCORING)
# ============================================================================

@app.post("/api/submit")
async def submit_solution(data: dict):
    """
    Submit a solution for judging against all test cases.
    Returns per-case results AND a score.
    
    Score = (passed_cases / total_cases) * MAX_SCORE_PER_QUESTION
    
    BLOCKED if room is expired.
    """
    code = data.get("code", "")
    language = data.get("language", "python").lower()
    room_id = data.get("room_id")
    question_id = data.get("question_id")
    student_id = data.get("student_id")

    if not all([code, room_id, question_id, student_id]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Security: check room is active
    room = await db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.get("status") == "expired" or db.is_room_expired(room):
        if room.get("status") != "expired":
            await db.expire_room(room_id)
        raise HTTPException(status_code=403, detail="Exam has ended. Cannot submit solutions.")

    # Get the question with ALL test cases (including hidden)
    question = await db.get_question(room_id, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    test_cases = question.get("test_cases", [])
    if not test_cases:
        raise HTTPException(status_code=400, detail="No test cases defined for this question")

    # Run code against each test case
    results = []
    passed_count = 0
    has_error = False

    for i, tc in enumerate(test_cases):
        tc_result = code_executor.execute_with_test_case(
            code=code,
            language=language,
            input_data=tc.get("input_data", ""),
            expected_output=tc.get("expected_output", "")
        )

        is_hidden = tc.get("is_hidden", False)

        case_result = {
            "case_number": i + 1,
            "is_hidden": is_hidden,
            "passed": tc_result["passed"],
            "status": tc_result["status"],
        }

        # For example (visible) test cases, show full details
        if not is_hidden:
            case_result["input_data"] = tc.get("input_data", "")
            case_result["expected_output"] = tc_result["expected_output"]
            case_result["actual_output"] = tc_result["actual_output"]

        if tc_result.get("error"):
            case_result["error"] = tc_result["error"] if not is_hidden else "Runtime Error"
            has_error = True

        if tc_result["passed"]:
            passed_count += 1

        results.append(case_result)

    # Determine overall verdict
    total = len(test_cases)
    if passed_count == total:
        overall = "Accepted"
    elif has_error:
        overall = "Runtime Error"
    else:
        overall = "Wrong Answer"

    # Calculate score
    score = (passed_count / total) * MAX_SCORE_PER_QUESTION if total > 0 else 0

    submission_result = {
        "question_id": question_id,
        "total_cases": total,
        "passed_cases": passed_count,
        "results": results,
        "overall": overall,
        "score": round(score, 1),
        "max_score": MAX_SCORE_PER_QUESTION,
        "submitted_at": datetime.now().isoformat()
    }

    # Save submission result to worksheet
    try:
        ws = await db.get_worksheet(room_id, student_id, question_id)
        if ws:
            await db.save_worksheet(ws["worksheet_id"], code)
            await db.save_submission_result(ws["worksheet_id"], submission_result)
    except Exception as e:
        print(f"Warning: Could not save submission result: {e}")

    return submission_result


# ============================================================================
# SCORES ENDPOINT
# ============================================================================

@app.get("/api/rooms/{room_id}/scores")
async def get_room_scores(room_id: str):
    """
    Get aggregated scores for all students in a room.
    Returns per-student, per-question scores based on their best submission.
    """
    room = await db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    questions = room.get("questions", [])
    students = room.get("students", [])
    student_names = room.get("student_names", {})
    student_red_flags = room.get("student_red_flags", {})

    # Get all worksheets for the room
    all_worksheets = await db.get_all_worksheets_for_room(room_id)

    # Build lookup: (student_id, question_id) -> best submission
    ws_lookup = {}
    for ws in all_worksheets:
        key = (ws["student_id"], ws["question_id"])
        ws_lookup[key] = ws

    scores_data = []
    for sid in students:
        student_entry = {
            "student_id": sid,
            "student_name": student_names.get(sid, "Unknown"),
            "red_flags": student_red_flags.get(sid, 0),
            "questions": [],
            "total_score": 0,
            "max_total": len(questions) * MAX_SCORE_PER_QUESTION
        }

        for q in questions:
            qid = q["question_id"]
            ws = ws_lookup.get((sid, qid))

            best_score = 0
            status = "not_attempted"

            if ws and ws.get("submission_results"):
                # Find best submission score
                for sub in ws["submission_results"]:
                    sub_score = sub.get("score", 0)
                    if sub_score > best_score:
                        best_score = sub_score
                    if sub.get("overall") == "Accepted":
                        status = "accepted"
                    elif status != "accepted":
                        status = "attempted"

            student_entry["questions"].append({
                "question_id": qid,
                "score": best_score,
                "max_score": MAX_SCORE_PER_QUESTION,
                "status": status
            })
            student_entry["total_score"] += best_score

        scores_data.append(student_entry)

    # Sort by total score descending
    scores_data.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "room_id": room_id,
        "room_name": room.get("room_name"),
        "max_score_per_question": MAX_SCORE_PER_QUESTION,
        "total_questions": len(questions),
        "total_students": len(students),
        "scores": scores_data
    }


# ============================================================================
# PDF REPORT ENDPOINT
# ============================================================================

@app.get("/api/rooms/{room_id}/report")
async def generate_report(room_id: str):
    """
    Generate and download a PDF exam report with scores and violations.
    Uses ReportLab library.
    """
    room = await db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    questions = room.get("questions", [])
    students = room.get("students", [])
    student_names = room.get("student_names", {})
    student_red_flags = room.get("student_red_flags", {})

    # Get all worksheets for scoring
    all_worksheets = await db.get_all_worksheets_for_room(room_id)

    ws_lookup = {}
    for ws in all_worksheets:
        key = (ws["student_id"], ws["question_id"])
        ws_lookup[key] = ws

    # Build scores data for report
    scores_data = []
    for sid in students:
        student_entry = {
            "student_id": sid,
            "student_name": student_names.get(sid, "Unknown"),
            "red_flags": student_red_flags.get(sid, 0),
            "questions": [],
            "total_score": 0,
            "max_total": len(questions) * MAX_SCORE_PER_QUESTION
        }

        for q in questions:
            qid = q["question_id"]
            ws = ws_lookup.get((sid, qid))

            best_score = 0
            status = "not_attempted"

            if ws and ws.get("submission_results"):
                for sub in ws["submission_results"]:
                    sub_score = sub.get("score", 0)
                    if sub_score > best_score:
                        best_score = sub_score
                    if sub.get("overall") == "Accepted":
                        status = "accepted"
                    elif status != "accepted":
                        status = "attempted"

            student_entry["questions"].append({
                "question_id": qid,
                "score": best_score,
                "max_score": MAX_SCORE_PER_QUESTION,
                "status": status
            })
            student_entry["total_score"] += best_score

        scores_data.append(student_entry)

    # Sort by total score descending
    scores_data.sort(key=lambda x: x["total_score"], reverse=True)

    # Generate PDF
    pdf_bytes = generate_exam_report(
        room_data=room,
        scores_data=scores_data,
        questions=questions
    )

    # Return as downloadable PDF
    filename = f"exam_report_{room.get('room_name', 'report').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ============================================================================
# LIVE CODE MONITOR ENDPOINT
# ============================================================================

@app.get("/api/rooms/{room_id}/student-codes")
async def get_student_codes(room_id: str):
    """Get all student codes in a room with student NAMES"""
    room = await db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    student_codes = await db.get_student_codes_with_names(room_id)

    return {
        "room_id": room_id,
        "student_codes": student_codes,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)