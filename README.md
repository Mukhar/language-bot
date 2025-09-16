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

3. Database Setup:
   - The database tables are automatically created when the application starts
   - For manual setup or custom installations, use the provided schema.sql file:
   ```bash
   # For SQLite (default)
   sqlite3 healthcare_bot.db < schema.sql
   
   # For PostgreSQL
   psql -d your_database < schema.sql
   ```

4. Run the application:
```bash
uvicorn app.main:app --reload
source healthcare_bot_env/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000```
streamlit run streamlit_app.py
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
