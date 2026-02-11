import requests
import streamlit as st
from .constants import BACKEND_URL
from typing import Optional, Dict, Any
import json


class APIClient:
    """API client for backend communication"""

    BASE_URL = BACKEND_URL

    @staticmethod
    def create_room(room_name: str, teacher_id: str, teacher_name: str) -> Optional[Dict]:
        """Create exam room"""
        try:
            response = requests.post(
                f"{APIClient.BASE_URL}/api/rooms/create",
                params={
                    "room_name": room_name,
                    "teacher_id": teacher_id,
                    "teacher_name": teacher_name
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to create room: {str(e)}")
            return None

    @staticmethod
    def get_room(room_id: str) -> Optional[Dict]:
        """Get room details"""
        try:
            response = requests.get(f"{APIClient.BASE_URL}/api/rooms/{room_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Room not found: {str(e)}")
            return None

    @staticmethod
    def join_room(room_id: str, student_id: str, student_name: str) -> Optional[Dict]:
        """Student joins room"""
        try:
            response = requests.post(
                f"{APIClient.BASE_URL}/api/rooms/{room_id}/join",
                params={
                    "student_id": student_id,
                    "student_name": student_name
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to join room: {str(e)}")
            return None

    @staticmethod
    def create_question(room_id: str, title: str, description: str, languages: list = None) -> Optional[Dict]:
        """Create question"""
        try:
            response = requests.post(
                f"{APIClient.BASE_URL}/api/rooms/{room_id}/questions",
                params={
                    "title": title,
                    "description": description,
                    "allowed_languages": languages or ["python", "javascript", "java", "cpp"]
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to create question: {str(e)}")
            return None

    @staticmethod
    def get_questions(room_id: str) -> Optional[Dict]:
        """Get all questions in room"""
        try:
            response = requests.get(f"{APIClient.BASE_URL}/api/rooms/{room_id}/questions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to load questions: {str(e)}")
            return None

    @staticmethod
    def get_worksheet(room_id: str, student_id: str, question_id: str) -> Optional[Dict]:
        """Get student's worksheet"""
        try:
            response = requests.get(
                f"{APIClient.BASE_URL}/api/worksheets/{room_id}/{student_id}/{question_id}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to load worksheet: {str(e)}")
            return None

    @staticmethod
    def save_code(worksheet_id: str, code: str, language: str) -> bool:
        """Auto-save code"""
        try:
            response = requests.post(
                f"{APIClient.BASE_URL}/api/worksheets/{worksheet_id}/save",
                params={
                    "code": code,
                    "language": language
                }
            )
            response.raise_for_status()
            return True
        except:
            return False

    @staticmethod
    def execute_code(worksheet_id: str, code: str, language: str, input_data: str = "") -> Optional[Dict]:
        """Execute code"""
        try:
            response = requests.post(
                f"{APIClient.BASE_URL}/api/worksheets/{worksheet_id}/execute",
                json={
                    "code": code,
                    "language": language,
                    "input_data": input_data
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "stderr": str(e)
            }

    @staticmethod
    def get_students(room_id: str) -> Optional[Dict]:
        """Get room students (Teacher)"""
        try:
            response = requests.get(f"{APIClient.BASE_URL}/api/rooms/{room_id}/students")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to load students: {str(e)}")
            return None

    @staticmethod
    def get_student_progress(room_id: str, student_id: str) -> Optional[Dict]:
        """Get student progress"""
        try:
            response = requests.get(
                f"{APIClient.BASE_URL}/api/rooms/{room_id}/student/{student_id}/progress"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return None
