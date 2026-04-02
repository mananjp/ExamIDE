# 🎓 Online Exam IDE

A modern, Dockerized platform for conducting secure online coding exams. Built with **FastAPI**, **Streamlit**, and **MongoDB**, this application allows instructors to create customizable coding assignments, monitor students in real-time, and automatically evaluate submissions using hidden and visible test cases.

## ✨ Features

### 👨‍🏫 Teacher Dashboard
- **Exam Creation**: Create exam rooms with custom language restrictions (Python, JavaScript, Java, C++) and durations.
- **Question Management**: Add questions with multiple test cases (visible to students for examples, hidden for strict auto-grading).
- **Live Code Monitor**: Watch students writing code in real-time, viewing their active lines directly from your dashboard.
- **Anti-Cheat System**: Automatically tracks window/tab-switching out of the exam environment. Students receive red flags and are blocked from submitting after reaching an automated violation threshold.
- **Exam Controls**: Start exams immediately, schedule for later, or manually end them. Includes a strict 5-minute late-entry lockout policy.
- **Automated Grading & Reports**: Download comprehensive PDF reports containing student scores, rankings, and violation counts.

### 👨‍🎓 Student Portal
- **Secure Access**: Join exams using a unique room code.
- **Waiting Lobby**: Students wait in a lobby until the instructor manually initiates the exam.
- **Split-Pane IDE**: Features a LeetCode/HackerRank style interface with the question description, code editor, and execution results intuitively accessible.
- **Live Execution**: Run code against example test cases before submitting.
- **Auto-Judge**: Submit solutions to be evaluated against all test cases, with immediate feedback and scoring.

## 🏛️ System Architecture

The application is designed using a decoupled client-server architecture, tailored specifically for easy containerized deployments locally or in the cloud.

### 1. Unified Proxy Routing (Nginx)
In production and single-container deployments (like Railway or Hugging Face Spaces), an **Nginx** reverse proxy dynamically routes incoming traffic on a unified port:
- `/api/*` requests are forwarded securely to the FastAPI backend.
- `/_stcore/stream` (WebSockets) and static assets are intelligently routed to the Streamlit frontend.

### 2. Frontend Layer (Streamlit)
The user interface is built entirely using **Streamlit**, serving as the client application.
- **State Management**: Maintains distinct session states for each connected user (Student/Teacher).
- **Live Collaboration Feel**: Leverages automated polling loops and streamlined UI components to visually simulate real-time live monitoring and active tab-switching detections without over-architecting WebSockets at the logic level.
- **API Driven**: Every action (from fetching the waiting lobby status to submitting code) triggers an external REST HTTP request to the backend.

### 3. Backend REST API (FastAPI)
The core engine governing exam rules, state synchronization, and validations. Built with **FastAPI**.
- **Stateless Endpoints**: Fully RESTful, allowing horizontal scalability.
- **Asynchronous I/O**: Communicates with MongoDB using the `motor` async driver, ensuring high throughput for continuous code-saving pings from dozens of students concurrently.
- **Report Generator**: Integrates with `ReportLab` to stitch together structured analytical data from MongoDB into binary PDF payloads streamed out securely upon request.

### 4. Database Layer (MongoDB Atlas)
A NoSQL format flawlessly maps the shifting hierarchical structures of classroom data:
- **Rooms**: The master document holding timers, states, test cases, global configurations, and violation maps (tab-switch tracking integers mapped by `student_id`).
- **Worksheets**: The atom of student progress. A composite key of `(room_id, student_id, question_id)` determines a worksheet. It serves as an auto-saving buffer storing the active code string, its chosen language, and arrays of scored `submission_results`.

### 5. Multi-Language Code Execution Engine
An isolated, native evaluation playground contained directly inside the backend docker image securely evaluates untrusted code.
- **Local Sandboxing**: Converts incoming request blocks into localized `/tmp` directory source files.
- **Compiler/Interpreter Chains**: Routes files to natively installed tools (`python`, `node`, `javac/java`, `g++`).
- **Defensive Guardrails**: Enforces strict `subprocess` timeout thresholds (usually 10s) to kill runaway logic and `while(true)` blocks cleanly, capturing `stdout` and `stderr` exclusively for precise grading against hidden assertions.

## 🛠️ Technology Stack
- **Frontend**: [Streamlit](https://streamlit.io/) + Custom HTML/CSS/JS components
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas) (Motor for async operations)
- **Reporting**: ReportLab for PDF generation
- **Deployment**: Docker & Docker Compose (Ready for Railway/Platform-as-a-Service)

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker and Docker Compose installed.
- A MongoDB Atlas cluster (with your IP whitelisted or set to `0.0.0.0/0` for development).

### 1. Environment Setup
Create a `.env` file in the `backend/` directory based on the example:
```env
# backend/.env
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

### 2. Build and Run
Use Docker Compose to spin up both the frontend and backend services:
```bash
# Build and start the containers
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

### 3. Access the Application
- **Frontend (Student & Teacher UI)**: [http://localhost:8501](http://localhost:8501)
- **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🐳 Useful Docker Commands

```bash
# Check container status
docker-compose ps

# Tail backend logs
docker-compose logs -f backend

# Stop and remove all services
docker-compose down
```

## 🔐 Deployment & Security Notes
- For production, ensure MongoDB Atlas IP restrictions are correctly configured to your host/deployment platform.
- Environment variables (like `MONGO_URI`) are passed securely into the container via `.env` files and should never be committed to source control (ensure `.env` is in `.gitignore`).
- When deploying to platforms like Railway, bind backend services to `::` (`0.0.0.0`) to handle internal IPv6 routing properly.
