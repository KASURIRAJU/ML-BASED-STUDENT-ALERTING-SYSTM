# Setup Instructions

*PENDING FIX: The project currently lacks standard dependency management.*

Once `pyproject.toml` is created, setup will be:
1. `uv sync` or `pip install -e .`
2. Configure `.env` with `DATABASE_URL` and `SECRET_KEY`.
3. `fastapi dev app/main.py`
