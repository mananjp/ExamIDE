import json
import os
from typing import Dict, List, Optional
from models import Room, Question, Worksheet, Session
import sqlite3


class InMemoryDB:
    """Simple in-memory database for college project"""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.questions: Dict[str, Question] = {}
        self.worksheets: Dict[str, Worksheet] = {}
        self.sessions: Dict[str, Session] = {}

    # ROOM OPERATIONS
    def create_room(self, room: Room) -> Room:
        self.rooms[room.room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_all_rooms(self) -> List[Room]:
        return list(self.rooms.values())

    def add_student_to_room(self, room_id: str, student_id: str) -> bool:
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if student_id not in room.students and len(room.students) < room.max_students:
                room.students.append(student_id)
                return True
        return False

    # QUESTION OPERATIONS
    def create_question(self, question: Question) -> Question:
        self.questions[question.question_id] = question
        # Add to room's questions list
        if question.room_id in self.rooms:
            self.rooms[question.room_id].questions.append(question.question_id)
        return question

    def get_question(self, question_id: str) -> Optional[Question]:
        return self.questions.get(question_id)

    def get_room_questions(self, room_id: str) -> List[Question]:
        room = self.rooms.get(room_id)
        if not room:
            return []
        return [self.questions.get(qid) for qid in room.questions if qid in self.questions]

    # WORKSHEET OPERATIONS
    def get_or_create_worksheet(self, room_id: str, student_id: str, question_id: str) -> Worksheet:
        key = f"{room_id}:{student_id}:{question_id}"

        if key not in self.worksheets:
            worksheet = Worksheet(
                room_id=room_id,
                student_id=student_id,
                question_id=question_id
            )
            self.worksheets[key] = worksheet

        return self.worksheets[key]

    def update_worksheet(self, worksheet: Worksheet):
        key = f"{worksheet.room_id}:{worksheet.student_id}:{worksheet.question_id}"
        self.worksheets[key] = worksheet

    def get_student_worksheets(self, room_id: str, student_id: str) -> List[Worksheet]:
        return [
            ws for ws in self.worksheets.values()
            if ws.room_id == room_id and ws.student_id == student_id
        ]

    def get_worksheet_by_id(self, worksheet_id: str) -> Optional[Worksheet]:
        for ws in self.worksheets.values():
            if ws.worksheet_id == worksheet_id:
                return ws
        return None

    # SESSION OPERATIONS
    def create_session(self, session: Session) -> Session:
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    def get_room_sessions(self, room_id: str) -> List[Session]:
        return [s for s in self.sessions.values() if s.room_id == room_id]

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]


# Global database instance
db = InMemoryDB()
