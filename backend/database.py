
import motor.motor_asyncio
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models import Room, Question, Worksheet, ExecutionResult

import certifi

class Database:
    def __init__(self, uri: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            uri,
            tlsCAFile=certifi.where()
        )
        self.db = self.client.exam_ide_db
        self.rooms_collection = self.db.rooms
        self.questions_collection = self.db.questions
        self.worksheets_collection = self.db.worksheets

    async def create_room(
        self,
        room_name: str,
        teacher_name: str,
        language: str,
        duration_minutes: int,
        start_time: Optional[str] = None
    ) -> dict:
        room_id = str(uuid.uuid4())
        room_code = str(uuid.uuid4())[:6].upper()

        # Calculate end time if start time is provided
        end_time: Optional[str] = None
        if start_time and duration_minutes:
            try:
                # Normalize and parse start_time
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = start_dt + timedelta(minutes=duration_minutes)
                end_time = end_dt.isoformat()
            except Exception:
                # If parsing fails, just leave end_time as None
                end_time = None

        room_doc = {
            "room_id": room_id,
            "room_code": room_code,
            "room_name": room_name,
            "teacher_name": teacher_name,
            "language": language,
            "duration_minutes": duration_minutes,
            "start_time": start_time,
            "end_time": end_time,
            "students": [],
            "student_names": {},
            "student_red_flags": {},
            "questions": [],
            "status": "active",
            "created_at": datetime.now(),
        }

        await self.rooms_collection.insert_one(room_doc)
        room_doc.pop("_id", None)  # Remove Mongo ID
        return room_doc

    async def get_room(self, room_id: str) -> Optional[dict]:
        room = await self.rooms_collection.find_one({"room_id": room_id}, {"_id": 0})
        return room

    async def get_room_by_code(self, room_code: str) -> Optional[dict]:
        room = await self.rooms_collection.find_one({"room_code": room_code}, {"_id": 0})
        return room

    def is_room_expired(self, room: dict) -> bool:
        """Check if a room's exam time has ended."""
        end_time_str = room.get("end_time")
        if not end_time_str:
            return False
        try:
            end_dt = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            # Compare as naive if needed
            now = datetime.now(end_dt.tzinfo) if end_dt.tzinfo else datetime.now()
            return now > end_dt
        except Exception:
            return False

    async def expire_room(self, room_id: str):
        """Mark a room as expired."""
        await self.rooms_collection.update_one(
            {"room_id": room_id},
            {"$set": {"status": "expired"}}
        )

    async def join_room(self, room_code: str, student_name: str) -> Optional[dict]:
        room = await self.get_room_by_code(room_code)
        if not room:
            return None

        # Security: reject joins if room is expired
        if room.get("status") == "expired" or self.is_room_expired(room):
            # Auto-mark as expired in DB if not already
            if room.get("status") != "expired":
                await self.expire_room(room["room_id"])
            return {"error": "expired", "detail": "This exam has ended. Room code is no longer valid."}

        # Security: reject joins if exam has already started
        start_time_str = room.get("start_time")
        if start_time_str:
            try:
                start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                now = datetime.now(start_dt.tzinfo) if start_dt.tzinfo else datetime.now()
                if now > start_dt:
                    return {"error": "started", "detail": "Exam has already started. Late entries are not allowed."}
            except Exception:
                pass

        # Integrity: ensure student name is unique within the room
        student_name_lower = student_name.strip().lower()
        existing_names = room.get("student_names", {})
        for existing_id, existing_name in existing_names.items():
            if existing_name.strip().lower() == student_name_lower:
                return {"error": "name_taken", "detail": "Name already taken. Please use your full name or add an initial."}

        room_id = room["room_id"]
        student_id = str(uuid.uuid4())
        
        # Update room with new student
        await self.rooms_collection.update_one(
            {"room_id": room_id},
            {
                "$push": {"students": student_id},
                "$set": {f"student_names.{student_id}": student_name}
            }
        )
        
        return {
            "room_id": room_id,
            "student_id": student_id,
            "student_name": student_name
        }

    async def create_question(
        self,
        room_id: str,
        question_text: str,
        language: str,
        test_cases: Optional[List[dict]] = None
    ) -> Optional[dict]:
        """Create a question with optional test cases (example + hidden)."""
        room = await self.get_room(room_id)
        if not room:
            return None

        question_id = str(uuid.uuid4())

        # Build test case list with generated IDs
        processed_test_cases = []
        if test_cases:
            for tc in test_cases:
                processed_test_cases.append({
                    "test_id": tc.get("test_id", str(uuid.uuid4())),
                    "input_data": tc.get("input_data", ""),
                    "expected_output": tc.get("expected_output", ""),
                    "is_hidden": tc.get("is_hidden", False)
                })

        question = {
            "question_id": question_id,
            "question_text": question_text,
            "language": language,
            "test_cases": processed_test_cases
        }

        # Embed question in room document
        await self.rooms_collection.update_one(
            {"room_id": room_id},
            {"$push": {"questions": question}}
        )
        
        # Also store in separate collection for direct lookups
        await self.questions_collection.insert_one(question.copy())
        if "_id" in question:
            question.pop("_id")
        
        return question

    async def get_questions(self, room_id: str) -> List[dict]:
        room = await self.get_room(room_id)
        if room:
            return room.get("questions", [])
        return []

    async def get_question(self, room_id: str, question_id: str) -> Optional[dict]:
        """Get a single question by ID (includes hidden test cases for judging)."""
        room = await self.get_room(room_id)
        if not room:
            return None
        for q in room.get("questions", []):
            if q["question_id"] == question_id:
                return q
        return None

    async def create_worksheet(self, room_id: str, student_id: str, question_id: str, language: str) -> dict:
        worksheet_id = str(uuid.uuid4())

        worksheet = {
            "worksheet_id": worksheet_id,
            "room_id": room_id,
            "student_id": student_id,
            "question_id": question_id,
            "code": "",
            "language": language,
            "status": "working",
            "last_updated": datetime.now().isoformat(),
            "submission_results": []  # track submission history
        }

        await self.worksheets_collection.insert_one(worksheet)
        worksheet.pop("_id")
        return worksheet

    async def get_worksheet(self, room_id: str, student_id: str, question_id: str) -> Optional[dict]:
        ws = await self.worksheets_collection.find_one({
            "room_id": room_id,
            "student_id": student_id,
            "question_id": question_id
        }, {"_id": 0})
        return ws
        
    async def get_worksheet_by_id(self, worksheet_id: str) -> Optional[dict]:
         ws = await self.worksheets_collection.find_one({"worksheet_id": worksheet_id}, {"_id": 0})
         return ws

    async def save_worksheet(self, worksheet_id: str, code: str) -> bool:
        result = await self.worksheets_collection.update_one(
            {"worksheet_id": worksheet_id},
            {
                "$set": {
                    "code": code,
                    "last_updated": datetime.now().isoformat()
                }
            }
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def save_submission_result(self, worksheet_id: str, submission_result: dict) -> bool:
        """Save a submission result to the worksheet's history."""
        result = await self.worksheets_collection.update_one(
            {"worksheet_id": worksheet_id},
            {
                "$push": {"submission_results": submission_result},
                "$set": {
                    "status": "accepted" if submission_result.get("overall") == "Accepted" else "attempted",
                    "last_updated": datetime.now().isoformat()
                }
            }
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def get_student_worksheets(self, room_id: str, student_id: str) -> Dict:
        cursor = self.worksheets_collection.find({"room_id": room_id, "student_id": student_id})
        student_worksheets = {}
        async for ws in cursor:
            student_worksheets[ws["worksheet_id"]] = {
                "code": ws["code"],
                "language": ws["language"],
                "status": ws["status"],
                "last_updated": ws["last_updated"],
                "question_id": ws["question_id"]
            }
        return student_worksheets
        
    async def update_red_flags(self, room_id: str, student_id: str, count: int):
         await self.rooms_collection.update_one(
            {"room_id": room_id},
            {"$set": {f"student_red_flags.{student_id}": count}}
        )

    async def get_student_codes_with_names(self, room_id: str) -> Dict:
        room = await self.get_room(room_id)
        if not room:
            return {}

        student_codes = {}
        students = room.get("students", [])
        student_names = room.get("student_names", {})
        student_red_flags = room.get("student_red_flags", {})

        for student_id in students:
            student_name = student_names.get(student_id, "Unknown Student")
            
            # Get latest worksheet
            cursor = self.worksheets_collection.find({"room_id": room_id, "student_id": student_id}).sort("last_updated", -1).limit(1)
            latest_ws = None
            async for ws in cursor:
                latest_ws = ws
            
            if latest_ws:
                student_codes[student_id] = {
                    "student_name": student_name,
                    "red_flags": student_red_flags.get(student_id, 0),
                    "code": latest_ws.get("code", ""),
                    "language": latest_ws.get("language", "python"),
                    "status": latest_ws.get("status", "working"),
                    "last_updated": latest_ws.get("last_updated", ""),
                    "question_id": latest_ws.get("question_id", "")
                }
            else:
                student_codes[student_id] = {
                    "student_name": student_name,
                    "red_flags": student_red_flags.get(student_id, 0),
                    "code": "",
                    "language": "python",
                    "status": "idle",
                    "last_updated": "",
                    "question_id": ""
                }
        
        return student_codes

    async def get_all_worksheets_for_room(self, room_id: str) -> list:
        """Get all worksheets for a room (for scoring/report)."""
        cursor = self.worksheets_collection.find({"room_id": room_id}, {"_id": 0})
        worksheets = []
        async for ws in cursor:
            worksheets.append(ws)
        return worksheets
