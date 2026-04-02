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

The application uses a decoupled client-server architecture, tailored for easy containerized deployments locally or in the cloud.

### 🏗️ Architecture Diagram
```mermaid
graph TD
    %% Define User Roles
    Teacher([👩‍🏫 Teacher])
    Student([👨‍🎓 Student])

    %% Defines Proxies & UIs
    subgraph Container/Host
        Nginx{Nginx Reverse Proxy\nPort: 7860}
        Streamlit[💻 Streamlit Frontend\nPort: 8501]
        FastAPI[⚙️ FastAPI Backend\nPort: 8000]
        Exec[🛑 Code Execution Engine\nLocal Subprocesses]
        PDF[📄 ReportLab Component]
    end

    %% External Services
    Mongo[(🍃 MongoDB Atlas)]

    %% Routing Flow
    Teacher --> |HTTP/WS| Nginx
    Student --> |HTTP/WS| Nginx
    
    Nginx -->|/api/*| FastAPI
    Nginx -->|/*, /_stcore| Streamlit
    
    %% API Calls from Frontend to Backend
    Streamlit -- REST API Calls --> FastAPI

    %% Backend internal connections
    FastAPI <-->|motor async| Mongo
    FastAPI -->|/api/execute\n/api/submit| Exec
    FastAPI -->|/api/rooms/{id}/report| PDF
```

### 📡 Detailed Component & API Flow

#### 1. Unified Proxy Routing (Nginx)
In single-container deployments (like Railway or Hugging Face Spaces), an **Nginx** reverse proxy dynamically routes incoming traffic on a unified port:
- `/api/*` requests bypass the UI and map directly to the FastAPI backend.
- `/_stcore/stream` (WebSockets) and static assets are routed to the Streamlit frontend.

#### 2. Frontend Layer (Streamlit)
The user interface is built using **Streamlit**. Every user action triggers a synchronous `requests` call to the Backend API.
- **Teacher Workflow**:
  - `POST /api/rooms/create`: Submits form data to initialize a new exam room.
  - `POST /api/rooms/{room_id}/questions`: Adds new questions along with visible/hidden test cases.
  - `GET /api/rooms/{room_id}/student-codes`: Continuously polled by the Live Monitor to fetch real-time student code progress.
  - `GET /api/rooms/{room_id}/report`: Triggers PDF report generation when the exam is concluded.
- **Student Workflow**:
  - `POST /api/rooms/{room_code}/join`: Validates room code and grants access to the Waiting Lobby or IDE.
  - `POST /api/worksheets/{worksheet_id}/save`: Auto-saves the student's code to the backend repeatedly as they type.
  - `POST /api/rooms/{room_id}/report_violation`: Automatically triggered via JS events if a student switches tabs, incrementing their "red flags".

#### 3. Backend REST API (FastAPI)
The core engine governing exam rules, built with **FastAPI**.
- **Stateless & Async**: Exposes RESTful endpoints and uses the `motor` async driver to handle high throughput, such as dozens of students simultaneously auto-saving code.
- **API Endpoints (`main.py`)**: Includes routes for room management (`/api/rooms/*`), question handling, worksheet syncing (`/api/worksheets/*`), and execution payloads.

#### 4. Database Layer (MongoDB Atlas)
A NoSQL format flawlessly maps the shifting hierarchical structures of classroom data:
- **`rooms`**: The master document holding timers, states, test cases, and violation maps (tab-switch tracking integers mapped by `student_id`).
- **`worksheets`**: The atom of student progress. A composite key of `(room_id, student_id, question_id)` determines a worksheet. It stores the active code string, language chosen, and the array of scored `submission_results`.

#### 5. Multi-Language Code Execution Engine
An isolated evaluation playground natively contained inside the backend docker image.
- **Live Run (`POST /api/execute`)**: Converts student code to localized `/tmp` files, invoking native tools (`python`, `node`, `javac`, `g++`) to run freeform tests.
- **Auto-Judge (`POST /api/submit`)**: Pipes the exact `stdin` from hidden and visible test cases into the subprocess. It enforces strict `subprocess` timeout thresholds (e.g., 10s) to kill runaway logic natively, matching `stdout`/`stderr` against expected outputs to assign automated grades.

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
