# Local Development Setup

Follow these instructions to run Asterion directly on your host machine for development or debugging.

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+
- **Git**

## 1. Clone the Repository

```bash
git clone https://github.com/sriram21-09/Asterion.git
cd Asterion
```

## 2. Backend Setup

The backend encompasses the FastAPI server and the decoupled scientific engine.

```bash
cd backend
python -m venv .venv

# Activate Virtual Environment
# Windows:
.\.venv\Scripts\activate
# Unix:
source .venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env

# Initialize Database Schema
alembic upgrade head

# Run the Server
uvicorn main:app --reload --port 8222
```

## 3. Frontend Setup

In a new terminal window:

```bash
cd frontend

# Install Dependencies
npm install

# Configure Environment
cp .env.example .env

# Run the Development Server
npm run dev
```

The application will be accessible at `http://localhost:3000`.

## 4. Running the Test Suite

Asterion's unified test suite (933 tests) validates both the backend API and the scientific engine. It must be run from the repository root.

```bash
# Ensure backend virtual environment is active
# Windows:
.\backend\.venv\Scripts\activate
# Unix:
source backend/.venv/bin/activate

# Run tests
pytest
```
