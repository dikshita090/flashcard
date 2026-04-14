from pathlib import Path

from flask import Flask

from routes import register_routes
from services.storage import init_db


def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
    app.config["BASE_DIR"] = base_dir
    app.config["DATABASE_PATH"] = base_dir / "data" / "flashcards.db"
    app.config["UPLOAD_FOLDER"] = base_dir / "data" / "uploads"
    app.config["SECRET_KEY"] = "flashcard-engine-dev"

    init_db(app.config["DATABASE_PATH"])
    register_routes(app)
    return app
