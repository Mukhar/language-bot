# Healthcare Communication Practice Bot

A FastAPI-based backend system for healthcare communication training with AI evaluation.

## Setup

1. Create virtual environment:
```bash
python3 -m venv healthcare_bot_env
source healthcare_bot_env/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Features

- Healthcare scenario generation
- Response collection and validation
- AI-powered evaluation system
- Progress tracking
- Scenario categorization

## Tech Stack

- FastAPI
- SQLAlchemy
- LM Studio integration
- SQLite/PostgreSQL
- JWT authentication
