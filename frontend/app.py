import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
from datetime import datetime
import time

# ============================================================================
# STEP 4: CODE TEMPLATES CONFIGURATION
# ============================================================================

# Python Templates (8 templates)
PYTHON_TEMPLATES = {
    "Simple Function": '''def greet(name):
    """A simple greeting function"""
    print(f"Hello, {name}!")

greet("World")''',

    " Function with Math": '''def add_numbers(a, b):
    """Add two numbers and return result"""
    result = a + b
    print(f"{a} + {b} = {result}")
    return result

add_numbers(5, 10)''',

    " For Loop": '''fruits = ["apple", "banana", "orange"]

for fruit in fruits:
    print(f"I like {fruit}")''',

    " If-Else": '''age = 20

if age >= 18:
    print("You are an adult")
else:
    print("You are a minor")''',

    " List Operations": '''numbers = [1, 2, 3, 4, 5]

# Add element
numbers.append(6)

# Remove element
numbers.remove(3)

# Print all
for num in numbers:
    print(num)''',

    " While Loop": '''count = 0

while count < 5:
    print(f"Count: {count}")
    count += 1''',

    " List Comprehension": '''# Create a list of squares
squares = [x**2 for x in range(5)]
print(squares)

# Filter even numbers
numbers = [x for x in range(10) if x % 2 == 0]
print(numbers)''',

    "Dictionary": '''student = {
    "name": "John",
    "age": 20,
    "grade": "A"
}

print(student["name"])
print(student["grade"])'''
}

# JavaScript Templates (5 templates)
JAVASCRIPT_TEMPLATES = {
    " Simple Function": '''function greet(name) {
  console.log(`Hello, ${name}!`);
}

greet("World");''',

    " Function with Math": '''function addNumbers(a, b) {
  let result = a + b;
  console.log(`${a} + ${b} = ${result}`);
  return result;
}

addNumbers(5, 10);''',

    " For Loop": '''let fruits = ["apple", "banana", "orange"];

for (let i = 0; i < fruits.length; i++) {
  console.log(`I like ${fruits[i]}`);
}''',

    " If-Else": '''let age = 20;

if (age >= 18) {
  console.log("You are an adult");
} else {
  console.log("You are a minor");
}''',

    " Array Operations": '''let numbers = [1, 2, 3, 4, 5];

// Add element
numbers.push(6);

// Remove element
numbers.splice(2, 1);

// Print all
for (let num of numbers) {
  console.log(num);
}'''
}

# ============================================================================
# CONFIGURATION
# ============================================================================

# The URL used by Streamlit (server) to contact FastAPI (server)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# The URL used by the browser (client JS) to contact the unified Nginx proxy
PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "")


# ============================================================================
# API CLIENT
# ============================================================================

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session_id = None
        self.role = None

    def create_room(self, room_name: str, teacher_name: str, language: str = "Python", duration: int = 30,
                    start_time: str = None):
        """Create a new exam room"""
        payload = {
            "room_name": room_name,
            "teacher_name": teacher_name,
            "language": language,
            "duration": duration,
            "session_id": self.session_id
        }
        if start_time:
            payload["start_time"] = start_time

        response = requests.post(
            f"{self.base_url}/api/rooms/create",
            json=payload
        )
        return response.json()

    def join_room(self, room_code: str, student_name: str):
        """Join an existing exam room"""
        response = requests.post(
            f"{self.base_url}/api/rooms/{room_code}/join",
            json={
                "student_name": student_name,
                "session_id": self.session_id
            }
        )
        return response.json()

    def get_room(self, room_id: str):
        """Get room details"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}")
        return response.json()

    def create_question(self, room_id: str, question_text: str, language: str, test_cases: list = None):
        """Create a question in the room with optional test cases"""
        payload = {
            "question_text": question_text,
            "language": language,
        }
        if test_cases:
            payload["test_cases"] = test_cases
        
        response = requests.post(
            f"{self.base_url}/api/rooms/{room_id}/questions",
            json=payload
        )
        return response.json()

    def get_questions(self, room_id: str):
        """Get all questions in a room (hidden test cases filtered out)"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/questions")
        return response.json()

    def get_questions_full(self, room_id: str):
        """Get all questions including hidden test cases (teacher use)"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/questions/full")
        return response.json()

    def get_worksheet(self, room_id: str, student_id: str, question_id: str):
        """Get student's worksheet"""
        response = requests.get(
            f"{self.base_url}/api/worksheets/{room_id}/{student_id}/{question_id}"
        )
        return response.json()

    def save_code(self, worksheet_id: str, code: str):
        """Save student code"""
        response = requests.post(
            f"{self.base_url}/api/worksheets/{worksheet_id}/save",
            json={"code": code}
        )
        return response.json()

    def execute_code(self, code: str, language: str):
        """Execute code and get output"""
        response = requests.post(
            f"{self.base_url}/api/execute",
            json={
                "code": code,
                "language": language
            }
        )
        return response.json()

    def submit_solution(self, code: str, language: str, room_id: str, question_id: str, student_id: str):
        """Submit solution for auto-judging against all test cases"""
        response = requests.post(
            f"{self.base_url}/api/submit",
            json={
                "code": code,
                "language": language,
                "room_id": room_id,
                "question_id": question_id,
                "student_id": student_id
            }
        )
        return response.json()

    def get_student_codes(self, room_id: str):
        """Get all student codes with NAMES in the room (Live Monitor)"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/student-codes")
        return response.json()

    def get_scores(self, room_id: str):
        """Get aggregated scores for all students"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/scores")
        return response.json()

    def download_report(self, room_id: str):
        """Download PDF exam report. Returns raw bytes."""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/report")
        if response.status_code == 200:
            return response.content
        return None

    def report_violation(self, room_id: str, student_id: str):
        """Report a security violation"""
        try:
            requests.post(
                f"{self.base_url}/api/rooms/{room_id}/report_violation",
                json={"student_id": student_id}
            )
        except:
            pass


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def teacher_page(api_client):
    """Teacher dashboard"""
    st.title("📋 Teacher Dashboard")

    # Sidebar for room creation
    with st.sidebar:
        st.header("Create Exam Room")
        room_name = st.text_input("Exam/Assignment Name")
        teacher_name = st.text_input("Your Name")
        language = st.selectbox("Programming Language", ["Python", "JavaScript", "Java", "C++"])

        # Duration and Start Time
        duration = st.slider("Duration (minutes)", 5, 180, 60, step=5)

        start_option = st.radio("Start Time", ["Start Now", "Schedule for Later"])
        start_time_iso = None

        if start_option == "Schedule for Later":
            exam_date = st.date_input("Exam Date", min_value=datetime.now().date())
            exam_time = st.time_input("Exam Time", value=datetime.now().time())
            if exam_date and exam_time:
                start_dt = datetime.combine(exam_date, exam_time)
                start_time_iso = start_dt.isoformat()
        else:
            start_time_iso = datetime.now().isoformat()

        if st.button("Create Exam Room", key="create_room"):
            if room_name and teacher_name:
                result = api_client.create_room(room_name, teacher_name, language, duration, start_time_iso)
                if "room_id" in result:
                    st.session_state.room_id = result["room_id"]
                    st.session_state.room_code = result["room_code"]
                    st.success(f"Room created! Code: {result['room_code']}")
                else:
                    st.error(f"Error: {result.get('detail', 'Unknown error')}")

    # Display current room
    if "room_id" in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🔑 Room Code: `{st.session_state.room_code}`")
        with col2:
            st.info(f"🆔 Room ID: `{st.session_state.room_id}`")

        # ================================================================
        # CREATE QUESTION WITH TEST CASES
        # ================================================================
        with st.expander("📝 Create New Question", expanded=True):
            question_text = st.text_area("Question Text", height=100, 
                                          placeholder="Write your coding question here...\ne.g., Write a function that reads two integers from stdin and prints their sum.")
            question_lang = st.selectbox("Language", ["Python", "JavaScript", "Java", "C++"], key="q_lang")

            st.divider()
            st.subheader("🧪 Test Cases")
            st.caption("Add example test cases (visible to students) and hidden test cases (used for judging only).")

            # Dynamic test case management using session state
            if "test_cases_draft" not in st.session_state:
                st.session_state.test_cases_draft = []

            # Show existing draft test cases
            cases_to_remove = []
            for idx, tc in enumerate(st.session_state.test_cases_draft):
                with st.container():
                    tc_col1, tc_col2, tc_col3 = st.columns([3, 3, 1])
                    with tc_col1:
                        tc["input_data"] = st.text_area(
                            f"Input (Test Case {idx + 1})",
                            value=tc.get("input_data", ""),
                            key=f"tc_input_{idx}",
                            height=80,
                            placeholder="e.g., 5 10"
                        )
                    with tc_col2:
                        tc["expected_output"] = st.text_area(
                            f"Expected Output (Test Case {idx + 1})",
                            value=tc.get("expected_output", ""),
                            key=f"tc_output_{idx}",
                            height=80,
                            placeholder="e.g., 15"
                        )
                    with tc_col3:
                        tc["is_hidden"] = st.checkbox(
                            "Hidden?",
                            value=tc.get("is_hidden", False),
                            key=f"tc_hidden_{idx}",
                            help="Hidden test cases are NOT shown to students"
                        )
                        if st.button("🗑️", key=f"tc_remove_{idx}"):
                            cases_to_remove.append(idx)

                    # Visual indicator
                    badge = "🔒 Hidden" if tc.get("is_hidden") else "👁️ Visible"
                    st.caption(f"Test Case {idx + 1} — {badge}")
                    st.divider()

            # Remove marked test cases
            if cases_to_remove:
                for idx in sorted(cases_to_remove, reverse=True):
                    st.session_state.test_cases_draft.pop(idx)
                st.rerun()

            # Add new test case button
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                if st.button("➕ Add Example Test Case", key="add_example_tc"):
                    st.session_state.test_cases_draft.append({
                        "input_data": "",
                        "expected_output": "",
                        "is_hidden": False
                    })
                    st.rerun()
            with col_add2:
                if st.button("➕ Add Hidden Test Case", key="add_hidden_tc"):
                    st.session_state.test_cases_draft.append({
                        "input_data": "",
                        "expected_output": "",
                        "is_hidden": True
                    })
                    st.rerun()

            # Summary
            example_count = sum(1 for tc in st.session_state.test_cases_draft if not tc.get("is_hidden"))
            hidden_count = sum(1 for tc in st.session_state.test_cases_draft if tc.get("is_hidden"))
            st.info(f"📊 **{example_count}** example test case(s) | **{hidden_count}** hidden test case(s)")

            # Submit question
            if st.button("✅ Add Question", key="add_question"):
                if question_text:
                    # Validate test cases
                    valid_test_cases = [
                        tc for tc in st.session_state.test_cases_draft
                        if tc.get("expected_output", "").strip()  # at least expected output must exist
                    ]
                    
                    result = api_client.create_question(
                        st.session_state.room_id,
                        question_text,
                        question_lang,
                        test_cases=valid_test_cases if valid_test_cases else None
                    )
                    
                    if "question_id" in result:
                        st.success(f"✅ Question created with {len(valid_test_cases)} test case(s)!")
                        st.session_state.test_cases_draft = []  # Reset draft
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('detail', 'Unknown error')}")
                else:
                    st.warning("Please enter a question text!")

        # ================================================================
        # ROOM OVERVIEW
        # ================================================================
        try:
            room = api_client.get_room(st.session_state.room_id)
            room_status = room.get("status", "active")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Connected Students", len(room.get("students", [])))
            with col2:
                st.metric("Questions", len(room.get("questions", [])))
            with col3:
                if room_status == "expired":
                    st.metric("Status", "🔴 Expired")
                else:
                    st.metric("Status", "✅ Active")

            # Expired room banner
            if room_status == "expired":
                st.warning("⏰ **This exam has ended.** Room code is revoked — no new students can join or submit.")

            # Questions list with test case details
            if room.get("questions"):
                st.subheader("📋 Questions")
                for i, q in enumerate(room["questions"]):
                    tc_list = q.get("test_cases", [])
                    example_tc = [tc for tc in tc_list if not tc.get("is_hidden")]
                    hidden_tc = [tc for tc in tc_list if tc.get("is_hidden")]
                    
                    with st.expander(f"Q{i+1}: {q.get('question_text', 'N/A')[:80]}..."):
                        st.write(f"**{q.get('question_text', 'N/A')}**")
                        st.write(f"Language: `{q.get('language', 'Python')}`")
                        st.write(f"Test Cases: **{len(example_tc)}** example, **{len(hidden_tc)}** hidden")
                        
                        if example_tc:
                            st.write("**👁️ Example Test Cases:**")
                            for j, tc in enumerate(example_tc):
                                st.markdown(f"**Case {j+1}:** Input: `{tc.get('input_data', '')}` → Expected: `{tc.get('expected_output', '')}`")
                        
                        if hidden_tc:
                            st.write("**🔒 Hidden Test Cases:**")
                            for j, tc in enumerate(hidden_tc):
                                st.markdown(f"**Case {j+1}:** Input: `{tc.get('input_data', '')}` → Expected: `{tc.get('expected_output', '')}`")

            # ================================================================
            # SCORES & REPORT SECTION
            # ================================================================
            st.divider()
            st.subheader("📊 Student Scores")

            try:
                scores_response = api_client.get_scores(st.session_state.room_id)
                scores_list = scores_response.get("scores", [])

                if scores_list:
                    # Build scoreboard table
                    q_list = room.get("questions", [])
                    scoreboard_data = []
                    for rank, s in enumerate(scores_list, 1):
                        row = {
                            "Rank": rank,
                            "Student": s.get("student_name", "Unknown"),
                        }
                        for qi, qs in enumerate(s.get("questions", [])):
                            score = qs.get("score", 0)
                            max_s = qs.get("max_score", 100)
                            status = qs.get("status", "not_attempted")
                            icon = "✅" if status == "accepted" else ("📝" if status == "attempted" else "—")
                            row[f"Q{qi+1}"] = f"{icon} {score:.0f}/{max_s:.0f}"
                        
                        total = s.get("total_score", 0)
                        max_total = s.get("max_total", 0)
                        pct = (total / max_total * 100) if max_total > 0 else 0
                        row["Total"] = f"{total:.0f}/{max_total:.0f}"
                        row["Percentage"] = f"{pct:.1f}%"
                        row["Violations"] = f"🚩 {s.get('red_flags', 0)}" if s.get('red_flags', 0) > 0 else "✅ 0"
                        scoreboard_data.append(row)

                    st.dataframe(scoreboard_data, use_container_width=True, hide_index=True)
                else:
                    st.info("No submissions yet.")
            except Exception as e:
                st.error(f"Error loading scores: {e}")

            # Download report button
            st.divider()
            st.subheader("📄 Generate PDF Report")
            st.caption("Download a comprehensive PDF report with scores, violations, and exam statistics.")
            
            if st.button("📥 Download Exam Report (PDF)", key="download_report", use_container_width=True):
                with st.spinner("Generating PDF report..."):
                    pdf_bytes = api_client.download_report(st.session_state.room_id)
                if pdf_bytes:
                    st.download_button(
                        label="💾 Save Report",
                        data=pdf_bytes,
                        file_name=f"exam_report_{room.get('room_name', 'report').replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key="save_report_btn"
                    )
                    st.success("✅ Report generated! Click 'Save Report' above to download.")
                else:
                    st.error("Failed to generate report.")

        except Exception as e:
            st.error(f"Error loading room: {e}")

        # ====================================================================
        # LIVE CODE MONITOR
        # ====================================================================

        st.divider()
        st.subheader("👁️ Live Student Monitor")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader("📺 Live Code Monitor")

        # CLASSROOM STATUS TABLE
        try:
            detailed_data = api_client.get_student_codes(st.session_state.room_id)
            student_codes_map = detailed_data.get("student_codes", {})
            student_ids_list = room.get("students", [])

            if student_ids_list:
                status_data = []
                for sid in student_ids_list:
                    s_info = student_codes_map.get(sid, {})
                    nm = room.get("student_names", {}).get(sid, "Unknown")
                    flgs = s_info.get("red_flags", 0)
                    sts = s_info.get("status", "idle")
                    last_up = s_info.get("last_updated", "")
                    if last_up:
                        last_up = last_up.split("T")[1][:8]

                    status_icon = "🟩" if sts == "working" else ("✅" if sts == "accepted" else "🔴")
                    flag_icon = "🚩" if flgs > 0 else "✅"

                    status_data.append({
                        "Student Name": nm,
                        "Status": f"{status_icon} {sts}",
                        "Violations": f"{flag_icon} {flgs}",
                        "Last Active": last_up,
                        "ID": sid
                    })

                st.info("**Classroom Overview**")
                st.dataframe(
                    status_data,
                    column_config={
                        "Student Name": st.column_config.TextColumn("Student Name", width="medium"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "Violations": st.column_config.TextColumn("Violations (Red Flags)", width="small"),
                        "Last Active": st.column_config.TextColumn("Last Active", width="small"),
                        "ID": st.column_config.TextColumn("Student ID", width="small")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Waiting for students to join...")

        except Exception as ex:
            st.error(f"Error loading classroom status: {ex}")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            # Get student names from room
            room = api_client.get_room(st.session_state.room_id)
            student_names_map = room.get("student_names", {})
            student_ids = room.get("students", [])

            student_display = []

            try:
                detailed_data = api_client.get_student_codes(st.session_state.room_id)
                student_codes_map = detailed_data.get("student_codes", {})
            except:
                student_codes_map = {}

            for sid in student_ids:
                name = student_names_map.get(sid, f"Student ({sid[:8]}...)")
                s_data = student_codes_map.get(sid, {})
                flags = s_data.get("red_flags", 0)

                flag_str = f" ({flags})" if flags > 0 else ""
                display_name = f"{name}{flag_str}"

                student_display.append({"id": sid, "name": display_name})

            if student_display:
                selected_idx = st.selectbox(
                    "Select Student to Monitor",
                    range(len(student_display)),
                    format_func=lambda i: student_display[i]["name"],
                    key="monitor_student"
                )
                selected_student_id = student_display[selected_idx]["id"]
                selected_student_name = student_display[selected_idx]["name"]
            else:
                st.info("No students connected yet")
                selected_student_id = None
                selected_student_name = None

        with col2:
            auto_refresh = st.checkbox("☑️ Auto Refresh", value=True, key="auto_refresh")
        with col3:
            refresh_interval = st.slider("Interval (sec)", 1, 10, 2, key="refresh_interval")

        # Live code display area
        if selected_student_id:
            st.write(f"**Monitoring:** {selected_student_name}")

            code_placeholder = st.empty()
            status_placeholder = st.empty()

            while auto_refresh:
                try:
                    student_codes_response = api_client.get_student_codes(st.session_state.room_id)

                    if student_codes_response and "student_codes" in student_codes_response:
                        student_data = student_codes_response["student_codes"].get(selected_student_id, {})

                        code = student_data.get("code", "")
                        student_name = student_data.get("student_name", "Unknown")
                        language = student_data.get("language", "python").lower()
                        status = student_data.get("status", "idle")
                        last_updated = student_data.get("last_updated", "")
                        red_flags = student_data.get("red_flags", 0)

                        with code_placeholder.container():
                            if red_flags > 0:
                                st.error(
                                    f"🔴 **VIOLATION ALERT**: This student has left the exam window {red_flags} times!")

                            if code.strip():
                                st.code(code, language=language)
                            else:
                                st.info("⌛ Waiting for student to start coding...")

                        with status_placeholder.container():
                            col1, col2, col3 = st.columns(3)

                            if status == "idle":
                                status_icon = ""
                            elif status == "working":
                                status_icon = "🟩"
                            elif status == "accepted":
                                status_icon = "✅"
                            else:
                                status_icon = "🔴"

                            with col1:
                                st.write(f"**Status:** {status_icon} {status.upper()}")
                            with col2:
                                st.write(f"**Language:** {language.upper()}")

                            if last_updated:
                                time_str = last_updated.split('T')[1][:8] if 'T' in last_updated else last_updated
                                with col3:
                                    st.write(f"**Updated:** {time_str}")

                    time.sleep(refresh_interval)
                    st.rerun()

                except Exception as e:
                    st.error(f"Error fetching code: {e}")
                    break
    else:
        st.info("📌 Create a room using the sidebar to get started!")


def student_page(api_client):
    """Student workspace — LeetCode / HackerRank style split-pane layout"""

    # Sidebar for room joining
    with st.sidebar:
        st.header("Join Exam Room")
        room_code = st.text_input("Room Code")
        student_name = st.text_input("Your Name")

        if st.button("Join Room", key="join_room"):
            if room_code and student_name:
                try:
                    result = api_client.join_room(room_code, student_name)
                    if "room_id" in result:
                        st.session_state.room_id = result["room_id"]
                        st.session_state.student_id = result["student_id"]
                        st.session_state.student_name = student_name
                        st.success("Room joined!")
                    else:
                        st.error(f"Error: {result.get('detail', 'Unknown error')}")
                except requests.exceptions.HTTPError as e:
                    if e.response and e.response.status_code == 403:
                        st.error("🔴 This exam has ended. The room code is no longer valid.")
                    else:
                        st.error(f"Error: {e}")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "room_id" not in st.session_state:
        st.title("💻 Online Exam IDE")
        st.info("📌 Join a room using the sidebar to get started!")
        return

    # ================================================================
    # ROOM & TIMING CHECKS
    # ================================================================
    try:
        room = api_client.get_room(st.session_state.room_id)
        start_time_str = room.get("start_time")
        end_time_str = room.get("end_time")

        now = datetime.now()
        start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
        end_time = datetime.fromisoformat(end_time_str) if end_time_str else None

        if start_time and now < start_time:
            st.warning(f"Exam has not started yet. Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.metric("Time until start", str(start_time - now).split('.')[0])
            if st.button("Refresh Status"):
                st.rerun()
            return

        if end_time and now > end_time:
            st.error("Exam has ended. You can no longer submit code.")
            st.metric("Exam Ended", end_time.strftime('%Y-%m-%d %H:%M:%S'))
            return

    except Exception as e:
        st.error(f"Error checking exam status: {e}")
        return

    # ================================================================
    # BLOCKED STUDENT CHECK
    # ================================================================
    blocked_students = room.get("blocked_students", [])
    student_id = st.session_state.student_id
    my_flags = room.get("student_red_flags", {}).get(student_id, 0)

    if student_id in blocked_students or my_flags > 3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%);
            border: 3px solid #ef4444;
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            margin: 40px auto;
            max-width: 700px;
            box-shadow: 0 0 60px rgba(239, 68, 68, 0.4);
        ">
            <div style="font-size: 80px; margin-bottom: 20px;">🚫</div>
            <h1 style="color: #ffffff; font-size: 42px; margin-bottom: 10px; font-weight: 800;">
                EXAM ACCESS BLOCKED
            </h1>
            <p style="color: #fca5a5; font-size: 20px; margin-bottom: 30px;">
                You have been permanently blocked from this exam due to <strong>repeated security violations</strong>.
            </p>
            <div style="
                background: rgba(0,0,0,0.3);
                border-radius: 12px;
                padding: 20px;
                margin: 20px auto;
                max-width: 400px;
            ">
                <p style="color: #f87171; font-size: 28px; font-weight: 700; margin: 0;">
                    Your Score: 0 / 100
                </p>
                <p style="color: #fca5a5; font-size: 16px; margin-top: 8px;">
                    Violations recorded: """ + str(my_flags) + """
                </p>
            </div>
            <p style="color: #d1d5db; font-size: 14px; margin-top: 20px;">
                This action is final. Contact your teacher if you believe this is an error.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ================================================================
    # SECURITY SCRIPT & EXAM HEADER
    # ================================================================
    if end_time:
        time_left = end_time - now

        st_room_id = st.session_state.room_id
        st_student_id = st.session_state.student_id

        security_script = f"""
        <script>
        const targetWindow = window.parent;
        const targetDocument = targetWindow.document;

        let violationCount = {my_flags};

        function reportViolation() {{
            violationCount++;
            fetch("{PUBLIC_BACKEND_URL}/api/rooms/{st_room_id}/report_violation", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify({{
                    "student_id": "{st_student_id}"
                }})
            }}).then(r => r.json()).then(data => {{
                if (data.blocked) {{
                    showOverlay('<h1 style="font-size: 60px;">🚫 BLOCKED</h1><h2 style="font-size: 30px;">You have been permanently blocked from this exam.</h2><p style="font-size: 22px;">Your score is now 0. Contact your teacher.</p>', true);
                    // Disable click-to-dismiss for blocked overlay
                    var overlay = targetDocument.getElementById('security-overlay');
                    if (overlay) overlay.onclick = null;
                    // Force reload after a short delay so the server-side block kicks in
                    setTimeout(() => {{ targetWindow.location.reload(); }}, 3000);
                }}
            }}).catch(e => console.error(e));
        }}

        function requestFullScreen() {{
            var elem = targetDocument.documentElement;
            if (elem.requestFullscreen) {{
                elem.requestFullscreen().catch(err => {{
                    console.log("Error attempting to enable full-screen mode: " + err.message);
                }});
            }} else if (elem.webkitRequestFullscreen) {{
                elem.webkitRequestFullscreen();
            }} else if (elem.msRequestFullscreen) {{
                elem.msRequestFullscreen();
            }}
        }}

        function showOverlay(message, isRed = true) {{
            var overlay = targetDocument.getElementById('security-overlay');
            if (!overlay) {{
                overlay = targetDocument.createElement('div');
                overlay.id = 'security-overlay';
                overlay.style.position = 'fixed';
                overlay.style.top = '0';
                overlay.style.left = '0';
                overlay.style.width = '100vw';
                overlay.style.height = '100vh';
                overlay.style.zIndex = '999999';
                overlay.style.color = 'white';
                overlay.style.display = 'flex';
                overlay.style.justifyContent = 'center';
                overlay.style.alignItems = 'center';
                overlay.style.flexDirection = 'column';

                overlay.onclick = function() {{
                    overlay.style.display = 'none';
                    targetDocument.title = "Online Exam IDE";
                    requestFullScreen();
                }};

                targetDocument.body.appendChild(overlay);
            }}

            overlay.style.backgroundColor = isRed ? 'rgba(255, 0, 0, 0.98)' : 'rgba(0, 0, 0, 0.9)';
            overlay.innerHTML = message;
            overlay.style.display = 'flex';
        }}

        targetDocument.addEventListener('contextmenu', event => {{
            event.preventDefault();
            event.stopPropagation();
            reportViolation();
            showOverlay('<h1 style="font-size: 50px;"> VIOLATION</h1><h2 style="font-size: 30px;">Right-click is forbidden!</h2><p style="font-size: 20px;">Return and CLICK HERE to resume.</p>');
            return false;
        }}, true);

        targetDocument.addEventListener('keydown', function(e) {{
            if (e.ctrlKey || e.altKey || e.metaKey) {{
                e.preventDefault();
                e.stopPropagation();
                reportViolation();
                showOverlay('<h1 style="font-size: 50px;"> VIOLATION</h1><h2 style="font-size: 30px;">Keyboard shortcuts are forbidden!</h2><p style="font-size: 20px;">Return and CLICK HERE to resume.</p>');
                return false;
            }}
            if (e.keyCode >= 112 && e.keyCode <= 123) {{
                 e.preventDefault();
                 e.stopPropagation();
                 reportViolation();
                 showOverlay('<h1 style="font-size: 50px;"> VIOLATION</h1><h2 style="font-size: 30px;">Function keys are forbidden!</h2><p style="font-size: 20px;">Return and CLICK HERE to resume.</p>');
                 return false;
            }}
        }}, true);

        ['copy', 'cut', 'paste'].forEach(e => {{
            targetDocument.addEventListener(e, function(event) {{
                event.preventDefault();
                event.stopPropagation();
                reportViolation();
                let action = e.toUpperCase();
                showOverlay('<h1 style="font-size: 50px;"> VIOLATION</h1><h2 style="font-size: 30px;">' + action + ' is forbidden!</h2><p style="font-size: 20px;">Return and CLICK HERE to resume.</p>');
                return false;
            }}, true);
        }});

        targetWindow.addEventListener('blur', function() {{
           targetDocument.title = " EXAM WARNING: COME BACK!";
           reportViolation();
           showOverlay('<h1 style="font-size: 50px;"> VIOLATION</h1><h2 style="font-size: 30px;">You left the exam window!</h2><p style="font-size: 20px;">Return and CLICK HERE to resume.</p>');
        }});

        function handleFullscreenChange() {{
            if (!targetDocument.fullscreenElement && !targetDocument.webkitFullscreenElement && !targetDocument.msFullscreenElement) {{
                reportViolation();
                showOverlay('<h1 style="font-size: 40px;"> FULLSCREEN REQUIRED</h1><h2 style="font-size: 25px;">You cannot leave fullscreen mode.</h2><p style="font-size: 20px;">CLICK HERE to return to fullscreen.</p>', true);
            }}
        }}

        targetDocument.addEventListener('fullscreenchange', handleFullscreenChange);
        targetDocument.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        targetDocument.addEventListener('mozfullscreenchange', handleFullscreenChange);
        targetDocument.addEventListener('MSFullscreenChange', handleFullscreenChange);

        const style = targetDocument.createElement('style');
        style.innerHTML = `
            [data-testid="stSidebar"] {{ display: none !important; }}
            [data-testid="stToolbar"] {{ visibility: hidden !important; }}
            header {{ visibility: hidden !important; }}
        `;
        targetDocument.head.appendChild(style);

        setInterval(function() {{
             if (!targetDocument.fullscreenElement && !targetDocument.webkitFullscreenElement && !targetDocument.msFullscreenElement) {{
                 var overlay = targetDocument.getElementById('security-overlay');
                 if (!overlay || overlay.style.display == 'none') {{
                     showOverlay('<h1 style="font-size: 40px;"> FULLSCREEN REQUIRED</h1><h2 style="font-size: 25px;">You cannot leave fullscreen mode.</h2><p style="font-size: 20px;">CLICK HERE to return to fullscreen.</p>', true);
                 }}
             }}
        }}, 1000);

        setTimeout(requestFullScreen, 500);
        console.log("Security script loaded and attached to parent");
        </script>
        """
        components.html(security_script, height=0, width=0)

        # ================================================================
        # TOP BAR: Timer + Violations + Fullscreen
        # ================================================================
        top_col1, top_col2, top_col3, top_col4 = st.columns([2, 1, 1, 1])
        with top_col1:
            st.markdown(f"**💻 {st.session_state.student_name}** — *{room.get('room_name', 'Exam')}*")
        with top_col2:
            st.metric("⏱ Time Left", str(time_left).split('.')[0])
        with top_col3:
            violation_color = "🔴" if my_flags > 0 else "🟢"
            st.metric(f"{violation_color} Violations", f"{my_flags} / 3")
        with top_col4:
            st.markdown("""
            <button onclick="parent.document.documentElement.requestFullscreen()" style="
                background-color: #FF4B4B; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
                font-weight: bold;
                font-size: 13px;">
                🖥️ Fullscreen
            </button>
            """, unsafe_allow_html=True)

        if st.button("🔄 Refresh", key="refresh_timer"):
            st.rerun()

    # ================================================================
    # QUESTION + SPLIT-PANE IDE LAYOUT
    # ================================================================
    try:
        questions = api_client.get_questions(st.session_state.room_id)
        question_list = questions.get("questions", [])

        if not question_list:
            st.info("No questions available yet. Ask your teacher to create some!")
            return

        # Question tab selector (like LeetCode problem tabs)
        question_names = [f"Q{i+1}: {q.get('question_text', 'Question')[:50]}..." for i, q in enumerate(question_list)]
        selected_q_idx = st.selectbox("📋 Select Problem", range(len(question_names)),
                                      format_func=lambda i: question_names[i], label_visibility="collapsed")
        selected_question = question_list[selected_q_idx]
        question_id = selected_question.get("question_id")
        language = selected_question.get("language", "Python").lower()

        st.markdown("---")

        # ================================================================
        # SPLIT PANE: LEFT (Problem) | RIGHT (Code Editor)
        # ================================================================
        left_col, right_col = st.columns([1, 1], gap="medium")

        # ========================
        # LEFT PANEL: Problem
        # ========================
        with left_col:
            st.markdown("### 📝 Problem Statement")
            st.markdown(f"""
            <div style="
                background: rgba(30, 36, 46, 0.6);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 16px;
                line-height: 1.7;
            ">
                {selected_question['question_text']}
            </div>
            """, unsafe_allow_html=True)

            # Example Test Cases
            example_test_cases = selected_question.get("test_cases", [])
            hidden_count = selected_question.get("hidden_test_cases_count", 0)

            if example_test_cases or hidden_count > 0:
                st.markdown("### 🧪 Test Cases")

                if example_test_cases:
                    for j, tc in enumerate(example_test_cases):
                        st.markdown(f"**Example {j+1}:**")
                        tc_left, tc_right = st.columns(2)
                        with tc_left:
                            input_display = tc.get("input_data", "(no input)")
                            st.code(input_display if input_display else "(no input)", language="text")
                        with tc_right:
                            st.code(tc.get("expected_output", ""), language="text")

                if hidden_count > 0:
                    st.info(f"🔒 **{hidden_count}** hidden test case(s) will be used for final judging.")

            # ================================================================
            # SUBMISSION RESULTS (shown in left panel, like LeetCode)
            # ================================================================
            if "last_submission" in st.session_state and st.session_state.last_submission:
                submission = st.session_state.last_submission

                st.markdown("---")
                st.markdown("### 📊 Submission Results")

                overall = submission.get("overall", "Unknown")
                passed = submission.get("passed_cases", 0)
                total = submission.get("total_cases", 0)
                score = submission.get("score", 0)
                max_score = submission.get("max_score", 100)

                # Verdict banner
                if overall == "Accepted":
                    st.success(f"🎉 **{overall}** — All {total} test case(s) passed! Score: **{score:.0f}/{max_score:.0f}**")
                elif overall == "Wrong Answer":
                    st.error(f"❌ **{overall}** — {passed}/{total} passed. Score: **{score:.0f}/{max_score:.0f}**")
                elif overall == "Runtime Error":
                    st.error(f"💥 **{overall}** — {passed}/{total} passed. Score: **{score:.0f}/{max_score:.0f}**")
                else:
                    st.warning(f"⚠️ **{overall}** — {passed}/{total} passed. Score: **{score:.0f}/{max_score:.0f}**")

                # Per-case results
                case_results = submission.get("results", [])
                for cr in case_results:
                    case_num = cr.get("case_number", "?")
                    is_hidden = cr.get("is_hidden", False)
                    case_passed = cr.get("passed", False)
                    case_status = cr.get("status", "")

                    icon = "✅" if case_passed else "❌"

                    if is_hidden:
                        st.write(f"{icon} **Hidden Test Case {case_num}**: {case_status}")
                    else:
                        with st.expander(f"{icon} Test Case {case_num}: {case_status}", expanded=not case_passed):
                            tc_col1, tc_col2, tc_col3 = st.columns(3)
                            with tc_col1:
                                st.markdown("**Input:**")
                                st.code(cr.get("input_data", "(no input)"), language="text")
                            with tc_col2:
                                st.markdown("**Expected:**")
                                st.code(cr.get("expected_output", ""), language="text")
                            with tc_col3:
                                st.markdown("**Your Output:**")
                                actual = cr.get("actual_output", "")
                                if cr.get("error"):
                                    st.code(cr.get("error", ""), language="text")
                                else:
                                    st.code(actual if actual else "(no output)", language="text")

        # ========================
        # RIGHT PANEL: Code Editor
        # ========================
        with right_col:
            # Language badge
            lang_icons = {"python": "🐍", "javascript": "🟨", "java": "☕", "c++": "⚙️"}
            lang_icon = lang_icons.get(language, "📄")
            st.markdown(f"### {lang_icon} Code Editor — `{language.upper()}`")

            # Template selector
            with st.expander("📋 Templates & Help", expanded=False):
                if language in ["python", "py"]:
                    templates = PYTHON_TEMPLATES
                else:
                    templates = JAVASCRIPT_TEMPLATES

                selected_template = st.selectbox("Choose a Template", list(templates.keys()), key="template_select")

                if st.button("📥 Load Template"):
                    st.session_state.code = templates[selected_template]
                    try:
                        worksheet = api_client.get_worksheet(
                            st.session_state.room_id,
                            st.session_state.student_id,
                            question_id
                        )
                        api_client.save_code(worksheet["worksheet_id"], st.session_state.code)
                    except:
                        pass
                    st.rerun()

            # Initialize code
            if "code" not in st.session_state:
                st.session_state.code = ""

            # Initialize worksheet
            if "current_worksheet_id" not in st.session_state or st.session_state.get(
                    "current_question_id") != question_id:
                try:
                    worksheet = api_client.get_worksheet(
                        st.session_state.room_id,
                        st.session_state.student_id,
                        question_id
                    )
                    st.session_state.current_worksheet_id = worksheet["worksheet_id"]
                    st.session_state.current_question_id = question_id
                    if worksheet.get("code"):
                        st.session_state.code = worksheet["code"]
                except Exception as e:
                    st.error(f"Error loading worksheet: {e}")

            # Code editor
            code_input = st.text_area(
                "Write your code here:",
                value=st.session_state.code,
                height=350,
                key="code_input",
                label_visibility="collapsed"
            )

            # Auto-save
            if code_input != st.session_state.code:
                st.session_state.code = code_input
                if "current_worksheet_id" in st.session_state:
                    try:
                        api_client.save_code(st.session_state.current_worksheet_id, code_input)
                    except:
                        pass

            # Code quality indicators
            if code_input.strip():
                q_col1, q_col2, q_col3 = st.columns(3)

                has_output = False
                if language in ["python", "py"]:
                    has_output = "print(" in code_input
                else:
                    has_output = "console.log(" in code_input

                with q_col1:
                    if has_output:
                        st.success("✅ Output")
                    else:
                        st.warning("⚠️ No Output")
                with q_col2:
                    st.info(f"📝 {len(code_input)} chars")
                with q_col3:
                    st.info(f"📄 {len(code_input.splitlines())} lines")

            # ================================================================
            # ACTION BUTTONS: Run | Submit | Save
            # ================================================================
            btn_col1, btn_col2, btn_col3 = st.columns(3)

            with btn_col1:
                if st.button("▶️ Run Code", use_container_width=True):
                    if code_input.strip():
                        with st.spinner("Executing..."):
                            result = api_client.execute_code(code_input, language)
                        if "output" in result and result.get("success", True):
                            st.success("✅ Execution successful!")
                            st.code(result["output"], language="text")
                        elif "error" in result:
                            st.error("❌ Execution failed!")
                            st.code(result["error"], language="text")
                    else:
                        st.warning("Write some code first!")

            with btn_col2:
                if st.button("🚀 Submit", use_container_width=True, type="primary"):
                    if code_input.strip():
                        with st.spinner("Judging against all test cases..."):
                            result = api_client.submit_solution(
                                code=code_input,
                                language=language,
                                room_id=st.session_state.room_id,
                                question_id=question_id,
                                student_id=st.session_state.student_id
                            )
                        st.session_state.last_submission = result
                        st.rerun()
                    else:
                        st.warning("Write some code first!")

            with btn_col3:
                if st.button("💾 Save", use_container_width=True):
                    if "current_worksheet_id" in st.session_state:
                        try:
                            api_client.save_code(st.session_state.current_worksheet_id, code_input)
                            st.success("✅ Saved!")
                        except Exception as e:
                            st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Online Exam IDE",
        page_icon="💻",
        layout="wide"
    )

    # Apply Modern CSS Styling
    st.markdown("""
        <style>
        /* Global Background and Text */
        .stApp {
            background-color: #181d27;
            background-image: radial-gradient(circle at 15% 50%, rgba(80, 50, 120, 0.35) 0%, transparent 55%), 
                              radial-gradient(circle at 85% 30%, rgba(40, 90, 140, 0.35) 0%, transparent 55%);
            color: #ffffff;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: rgba(30, 36, 46, 0.75) !important;
            backdrop-filter: blur(14px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #238636;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            transition: all 0.2s ease-in-out;
            font-weight: 600;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
        }
        .stButton>button:hover {
            background-color: #2ea043;
            color: white;
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.5);
            transform: translateY(-1px);
        }
        .stButton>button[kind="secondary"] {
            background-color: #2a313c;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        .stButton>button[kind="secondary"]:hover {
            background-color: #3b4554;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        /* Metrics / Cards */
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #ffffff !important;
        }
        div[data-testid="metric-container"] {
            background-color: rgba(30, 36, 46, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(10px);
        }
        
        /* Inputs & Editors */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {
            background-color: #11151c !important;
            color: #ffffff !important;
            border: 1px solid #3b4554 !important;
            border-radius: 6px !important;
        }
        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
            border-color: #58a6ff !important;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.3) !important;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #212833;
            border-radius: 8px;
            border: 1px solid #3b4554;
            color: #ffffff !important;
        }
        
        /* Headers & Typography */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }
        
        p, span, div {
            color: #e2e8f0;
        }
        
        /* Main structural cleanups */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background-color: transparent !important;}
        
        /* Alerts */
        .stAlert {
            border-radius: 8px;
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if "role" not in st.session_state:
        st.session_state.role = None

    if "monitoring" not in st.session_state:
        st.session_state.monitoring = False

    # Create API client
    api_client = APIClient(BACKEND_URL)
    api_client.session_id = "session_123"

    # Role selection
    if not st.session_state.role:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.title("💻 Online Exam IDE")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Continue as Teacher", use_container_width=True, key="teacher_btn"):
                st.session_state.role = "teacher"
                st.rerun()

        with col2:
            if st.button("💻 Continue as Student", use_container_width=True, key="student_btn"):
                st.session_state.role = "student"
                st.rerun()

    else:
        if st.session_state.role == "teacher":
            teacher_page(api_client)
        else:
            student_page(api_client)

        if st.sidebar.button("🔓 Logout"):
            st.session_state.role = None
            st.session_state.pop("room_id", None)
            st.session_state.pop("room_code", None)
            st.session_state.pop("last_submission", None)
            st.session_state.pop("test_cases_draft", None)
            st.rerun()


if __name__ == "__main__":
    main()