from database import db
from models import Room, Question, Session, Worksheet
from typing import List, Optional
import uuid


class RoomManager:
    """Room and exam management logic"""

    @staticmethod
    def create_exam_room(room_name: str, teacher_id: str, teacher_name: str, max_students: int = 30) -> Room:
        """Create a new exam room"""
        room = Room(
            room_name=room_name,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            max_students=max_students
        )
        return db.create_room(room)

    @staticmethod
    def get_room(room_id: str) -> Optional[Room]:
        """Get room by ID"""
        return db.get_room(room_id)

    @staticmethod
    def join_room(room_id: str, student_id: str) -> bool:
        """Add student to room"""
        return db.add_student_to_room(room_id, student_id)

    @staticmethod
    def create_question(room_id: str, title: str, description: str, allowed_languages: List[str] = None) -> Question:
        """Create a question in a room"""
        if allowed_languages is None:
            allowed_languages = ["python", "javascript", "java", "cpp"]

        question = Question(
            room_id=room_id,
            title=title,
            description=description,
            allowed_languages=allowed_languages
        )
        return db.create_question(question)

    @staticmethod
    def get_room_questions(room_id: str) -> List[Question]:
        """Get all questions in a room"""
        return db.get_room_questions(room_id)

    @staticmethod
    def get_student_worksheet(room_id: str, student_id: str, question_id: str) -> Worksheet:
        """Get or create worksheet for student"""
        return db.get_or_create_worksheet(room_id, student_id, question_id)

    @staticmethod
    def save_worksheet(worksheet: Worksheet):
        """Save worksheet code"""
        db.update_worksheet(worksheet)

    @staticmethod
    def get_room_students(room_id: str) -> List[str]:
        """Get students in room"""
        room = db.get_room(room_id)
        return room.students if room else []

    @staticmethod
    def get_student_progress(room_id: str, student_id: str) -> dict:
        """Get student's progress in all questions"""
        questions = db.get_room_questions(room_id)
        worksheets = db.get_student_worksheets(room_id, student_id)

        ws_map = {ws.question_id: ws for ws in worksheets}

        progress = {
            "total_questions": len(questions),
            "questions": []
        }

        for q in questions:
            ws = ws_map.get(q.question_id)
            progress["questions"].append({
                "question_id": q.question_id,
                "title": q.title,
                "status": ws.status if ws else "not_started",
                "submissions": ws.submission_count if ws else 0,
                "last_edited": ws.last_edited_timestamp if ws else None
            })

        return progress
