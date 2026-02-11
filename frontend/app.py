import streamlit as st
import requests
import json
from datetime import datetime
import time

# ============================================================================
# STEP 4: CODE TEMPLATES CONFIGURATION
# ============================================================================

# Python Templates (8 templates)
PYTHON_TEMPLATES = {
    "📌 Simple Function": '''def greet(name):
    """A simple greeting function"""
    print(f"Hello, {name}!")

greet("World")''',

    "🔢 Function with Math": '''def add_numbers(a, b):
    """Add two numbers and return result"""
    result = a + b
    print(f"{a} + {b} = {result}")
    return result

add_numbers(5, 10)''',

    "🔁 For Loop": '''fruits = ["apple", "banana", "orange"]

for fruit in fruits:
    print(f"I like {fruit}")''',

    "❓ If-Else": '''age = 20

if age >= 18:
    print("You are an adult")
else:
    print("You are a minor")''',

    "📚 List Operations": '''numbers = [1, 2, 3, 4, 5]

# Add element
numbers.append(6)

# Remove element
numbers.remove(3)

# Print all
for num in numbers:
    print(num)''',

    "🔄 While Loop": '''count = 0

while count < 5:
    print(f"Count: {count}")
    count += 1''',

    "📝 List Comprehension": '''# Create a list of squares
squares = [x**2 for x in range(5)]
print(squares)

# Filter even numbers
numbers = [x for x in range(10) if x % 2 == 0]
print(numbers)''',

    "🎯 Dictionary": '''student = {
    "name": "John",
    "age": 20,
    "grade": "A"
}

print(student["name"])
print(student["grade"])'''
}

# JavaScript Templates (5 templates)
JAVASCRIPT_TEMPLATES = {
    "📌 Simple Function": '''function greet(name) {
  console.log(`Hello, ${name}!`);
}

greet("World");''',

    "🔢 Function with Math": '''function addNumbers(a, b) {
  let result = a + b;
  console.log(`${a} + ${b} = ${result}`);
  return result;
}

addNumbers(5, 10);''',

    "🔁 For Loop": '''let fruits = ["apple", "banana", "orange"];

for (let i = 0; i < fruits.length; i++) {
  console.log(`I like ${fruits[i]}`);
}''',

    "❓ If-Else": '''let age = 20;

if (age >= 18) {
  console.log("You are an adult");
} else {
  console.log("You are a minor");
}''',

    "📚 Array Operations": '''let numbers = [1, 2, 3, 4, 5];

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

BACKEND_URL = "http://localhost:8000"


# ============================================================================
# API CLIENT
# ============================================================================

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session_id = None
        self.role = None

    def create_room(self, room_name: str, teacher_name: str, language: str = "Python"):
        """Create a new exam room"""
        response = requests.post(
            f"{self.base_url}/api/rooms/create",
            json={
                "room_name": room_name,
                "teacher_name": teacher_name,
                "language": language,
                "session_id": self.session_id
            }
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

    def create_question(self, room_id: str, question_text: str, language: str):
        """Create a question in the room"""
        response = requests.post(
            f"{self.base_url}/api/rooms/{room_id}/questions",
            json={
                "question_text": question_text,
                "language": language
            }
        )
        return response.json()

    def get_questions(self, room_id: str):
        """Get all questions in a room"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/questions")
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

    def get_student_codes(self, room_id: str):
        """Get all student codes with NAMES in the room (STEP 3 - Live Monitor)"""
        response = requests.get(f"{self.base_url}/api/rooms/{room_id}/student-codes")
        return response.json()


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def teacher_page(api_client):
    """Teacher dashboard"""
    st.title("👨‍🏫 Teacher Dashboard")

    # Sidebar for room creation
    with st.sidebar:
        st.header("Create Exam Room")
        room_name = st.text_input("Exam/Assignment Name")
        teacher_name = st.text_input("Your Name")
        language = st.selectbox("Programming Language", ["Python", "JavaScript", "Java", "C++"])

        if st.button("Create Exam Room", key="create_room"):
            if room_name and teacher_name:
                result = api_client.create_room(room_name, teacher_name, language)
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
            st.info(f"📌 Room Code: `{st.session_state.room_code}`")
        with col2:
            st.info(f"📊 Room ID: `{st.session_state.room_id}`")

        # Create Question Section
        with st.expander("➕ Create New Question", expanded=True):
            question_text = st.text_area("Question Text")
            question_lang = st.selectbox("Language", ["Python", "JavaScript", "Java", "C++"], key="q_lang")

            if st.button("Add Question"):
                if question_text:
                    result = api_client.create_question(
                        st.session_state.room_id,
                        question_text,
                        question_lang
                    )
                    st.success("Question created!")

        # Get Room Details
        try:
            room = api_client.get_room(st.session_state.room_id)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Connected Students", len(room.get("students", [])))
            with col2:
                st.metric("Questions", len(room.get("questions", [])))
            with col3:
                st.metric("Status", "🟢 Active")

            # Questions list
            if room.get("questions"):
                st.subheader("Questions")
                for q in room["questions"]:
                    st.write(f"• {q.get('question_text', 'N/A')}")
        except Exception as e:
            st.error(f"Error loading room: {e}")

        # ====================================================================
        # STEP 3: LIVE CODE MONITOR (UPDATED - FIXED CODE DISPLAY)
        # ====================================================================

        st.divider()
        st.subheader("👁️ Live Code Monitor")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            # Get student names from room
            room = api_client.get_room(st.session_state.room_id)
            student_names_map = room.get("student_names", {})
            student_ids = room.get("students", [])

            # Create a list of student display names
            student_display = []
            for sid in student_ids:
                name = student_names_map.get(sid, f"Student ({sid[:8]}...)")
                student_display.append({"id": sid, "name": name})

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
            auto_refresh = st.checkbox("🔄 Auto Refresh", value=True, key="auto_refresh")
        with col3:
            refresh_interval = st.slider("Interval (sec)", 1, 10, 2, key="refresh_interval")

        # Live code display area
        if selected_student_id:
            st.write(f"**Monitoring:** 👤 {selected_student_name}")

            # Create placeholders for dynamic updates
            code_placeholder = st.empty()
            status_placeholder = st.empty()

            # Fixed: Properly fetch and display code
            while auto_refresh:
                try:
                    # Get all student codes
                    student_codes_response = api_client.get_student_codes(st.session_state.room_id)

                    if student_codes_response and "student_codes" in student_codes_response:
                        # Get the specific student's data
                        student_data = student_codes_response["student_codes"].get(selected_student_id, {})

                        # Extract code and metadata
                        code = student_data.get("code", "")
                        student_name = student_data.get("student_name", "Unknown")
                        language = student_data.get("language", "python").lower()
                        status = student_data.get("status", "idle")
                        last_updated = student_data.get("last_updated", "")

                        # Display code with syntax highlighting
                        with code_placeholder.container():
                            if code.strip():
                                st.code(code, language=language)
                            else:
                                st.info("⏳ Waiting for student to start coding...")

                        # Display status and metadata
                        with status_placeholder.container():
                            col1, col2, col3 = st.columns(3)

                            # Status
                            if status == "idle":
                                status_icon = "⚪"
                            elif status == "working":
                                status_icon = "🟢"
                            else:
                                status_icon = "🔵"

                            with col1:
                                st.write(f"**Status:** {status_icon} {status.upper()}")

                            # Language
                            with col2:
                                st.write(f"**Language:** {language.upper()}")

                            # Last Updated
                            if last_updated:
                                time_str = last_updated.split('T')[1][:8] if 'T' in last_updated else last_updated
                                with col3:
                                    st.write(f"**Updated:** {time_str}")

                    # Sleep before refresh
                    time.sleep(refresh_interval)
                    st.rerun()

                except Exception as e:
                    st.error(f"Error fetching code: {e}")
                    break
    else:
        st.info("👈 Create a room using the sidebar to get started!")


def student_page(api_client):
    """Student workspace"""
    st.title("👨‍💻 Student Workspace")

    # Sidebar for room joining
    with st.sidebar:
        st.header("Join Exam Room")
        room_code = st.text_input("Room Code")
        student_name = st.text_input("Your Name")

        if st.button("Join Room", key="join_room"):
            if room_code and student_name:
                result = api_client.join_room(room_code, student_name)
                if "room_id" in result:
                    st.session_state.room_id = result["room_id"]
                    st.session_state.student_id = result["student_id"]
                    st.session_state.student_name = student_name
                    st.success("Room joined!")
                else:
                    st.error(f"Error: {result.get('detail', 'Unknown error')}")

    if "room_id" in st.session_state:
        st.info(f"✅ Connected as **{st.session_state.student_name}**")

        # Get questions
        try:
            questions = api_client.get_questions(st.session_state.room_id)
            question_list = questions.get("questions", [])

            if question_list:
                # Question selection
                question_names = [q.get("question_text", f"Question {i + 1}") for i, q in enumerate(question_list)]
                selected_q_idx = st.selectbox("Select Question", range(len(question_names)),
                                              format_func=lambda i: question_names[i])
                selected_question = question_list[selected_q_idx]
                question_id = selected_question.get("question_id")

                st.write(f"**{selected_question['question_text']}**")
                language = selected_question.get("language", "Python").lower()

                # ================================================================
                # STEP 4: CODE TEMPLATES
                # ================================================================

                st.divider()
                st.subheader("📚 Code Templates")

                # Get appropriate templates based on language
                if language == "python":
                    templates = PYTHON_TEMPLATES
                else:
                    templates = JAVASCRIPT_TEMPLATES

                selected_template = st.selectbox("Choose a Template", list(templates.keys()), key="template_select")

                if st.button("📌 Load Template"):
                    st.session_state.code = templates[selected_template]
                    # Auto-save template to backend
                    try:
                        worksheet = api_client.get_worksheet(
                            st.session_state.room_id,
                            st.session_state.student_id,
                            question_id
                        )
                        api_client.save_code(worksheet["worksheet_id"], st.session_state.code)
                        st.success("Template loaded and saved!")
                    except:
                        st.success("Template loaded!")
                    st.rerun()

                # ================================================================
                # STEP 4: INDENTATION HELP
                # ================================================================

                with st.expander("📖 Indentation Help"):
                    if language == "python":
                        st.write("""
                        **Python Indentation Rules:**
                        - Use **4 spaces** per indentation level
                        - Consistent indentation is required
                        - Common places for indentation:
                          - Inside functions: 4 spaces
                          - Inside loops (for, while): 4 spaces
                          - Inside if/else blocks: 4 spaces
                          - Class methods: 8 spaces from class definition

                        **Keyboard Shortcuts:**
                        - TAB: Add 4 spaces
                        - Shift+TAB: Remove 4 spaces

                        **Example:**
                        ```python
                        def greet(name):      # No indentation
                            print(name)       # 4 spaces
                            if name:          # 4 spaces
                                print("Hi")   # 8 spaces
                        ```
                        """)
                    else:
                        st.write("""
                        **JavaScript Indentation Rules:**
                        - Use **2 spaces** per indentation level
                        - Common places for indentation:
                          - Inside functions: 2 spaces
                          - Inside loops (for, while): 2 spaces
                          - Inside if/else blocks: 2 spaces
                          - Inside objects: 2 spaces

                        **Keyboard Shortcuts:**
                        - TAB: Add 2 spaces
                        - Shift+TAB: Remove 2 spaces

                        **Example:**
                        ```javascript
                        function greet(name) {    // No indentation
                          console.log(name);      // 2 spaces
                          if (name) {             // 2 spaces
                            console.log("Hi");    // 4 spaces
                          }
                        }
                        ```
                        """)

                # Code editor
                st.divider()
                st.subheader("💻 Code Editor")

                if "code" not in st.session_state:
                    st.session_state.code = ""

                # Initialize worksheet for this question if not exists
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

                # Code input
                code_input = st.text_area(
                    "Write your code here:",
                    value=st.session_state.code,
                    height=250,
                    key="code_input"
                )

                # FIXED: Auto-save code as student types
                if code_input != st.session_state.code:
                    st.session_state.code = code_input
                    # Save to backend automatically
                    if "current_worksheet_id" in st.session_state:
                        try:
                            api_client.save_code(st.session_state.current_worksheet_id, code_input)
                        except:
                            pass  # Silently fail, don't interrupt user

                # ================================================================
                # STEP 4: CODE QUALITY CHECKER
                # ================================================================

                st.divider()
                st.subheader("✨ Code Quality Check")

                if code_input.strip():
                    col1, col2, col3 = st.columns(3)

                    # Check for output statement
                    has_output = False
                    if language == "python":
                        has_output = "print(" in code_input
                    else:
                        has_output = "console.log(" in code_input

                    with col1:
                        if has_output:
                            st.success(f"✅ Has Output Statement")
                        else:
                            st.warning(f"⚠️ No Output Statement")

                    # Character count
                    char_count = len(code_input)
                    with col2:
                        st.info(f"📝 Characters: {char_count}")

                    # Line count
                    lines = code_input.split('\n')
                    with col3:
                        st.info(f"📄 Lines: {len(lines)}")

                # Code execution
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("▶️ Run Code"):
                        if code_input.strip():
                            result = api_client.execute_code(code_input, language)
                            if "output" in result:
                                st.success("✅ Execution successful!")
                                st.code(result["output"], language="text")
                            elif "error" in result:
                                st.error("❌ Execution failed!")
                                st.code(result["error"], language="text")
                        else:
                            st.warning("Write some code first!")

                with col2:
                    if st.button("💾 Save Code"):
                        if "current_worksheet_id" in st.session_state:
                            try:
                                api_client.save_code(st.session_state.current_worksheet_id, code_input)
                                st.success("✅ Code saved!")
                            except Exception as e:
                                st.error(f"Error saving: {e}")

            else:
                st.info("No questions available yet. Ask your teacher to create some!")

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.info("👈 Join a room using the sidebar to get started!")


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Online Exam IDE",
        page_icon="💻",
        layout="wide"
    )

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
            if st.button("👨‍🏫 Continue as Teacher", use_container_width=True, key="teacher_btn"):
                st.session_state.role = "teacher"
                st.rerun()

        with col2:
            if st.button("👨‍💻 Continue as Student", use_container_width=True, key="student_btn"):
                st.session_state.role = "student"
                st.rerun()

    else:
        # Show appropriate page based on role
        if st.session_state.role == "teacher":
            teacher_page(api_client)
        else:
            student_page(api_client)

        # Logout button
        if st.sidebar.button("🚪 Logout"):
            st.session_state.role = None
            st.session_state.pop("room_id", None)
            st.session_state.pop("room_code", None)
            st.rerun()


if __name__ == "__main__":
    main()