from pathlib import Path

from flask import Blueprint, Flask, flash, redirect, render_template, request, url_for

from components.dashboard_component import build_dashboard_context
from components.deck_component import build_deck_detail_context, build_deck_list_context
from components.review_component import build_review_context, submit_review_result
from services.deck_service import create_deck_from_pdf, delete_deck, find_deck


def register_routes(app: Flask) -> None:
    web = Blueprint("web", __name__)

    @web.route("/")
    def home():
        return render_template("index.html", dashboard=build_dashboard_context(app.config))

    @web.route("/decks")
    def decks():
        query = request.args.get("q", "").strip()
        return render_template("decks.html", query=query, deck_view=build_deck_list_context(app.config, query))

    @web.route("/decks/<int:deck_id>")
    def deck_detail(deck_id: int):
        deck = find_deck(app.config, deck_id)
        if not deck:
            flash("Deck not found.", "error")
            return redirect(url_for("web.decks"))
        return render_template("deck_detail.html", deck_view=build_deck_detail_context(app.config, deck_id))

    @web.post("/decks/<int:deck_id>/delete")
    def remove_deck(deck_id: int):
        delete_deck(app.config, deck_id)
        flash("Deck deleted successfully.", "success")
        return redirect(url_for("web.decks"))

    @web.route("/upload", methods=["GET", "POST"])
    def upload():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            subject = request.form.get("subject", "").strip()
            provider = request.form.get("provider", "auto").strip()
            file = request.files.get("pdf")

            if not file or not file.filename:
                flash("Please choose a PDF file first.", "error")
                return redirect(url_for("web.upload"))

            if Path(file.filename).suffix.lower() != ".pdf":
                flash("Only PDF files are supported right now.", "error")
                return redirect(url_for("web.upload"))

            try:
                deck_id = create_deck_from_pdf(
                    app.config,
                    title=title,
                    subject=subject,
                    provider=provider,
                    uploaded_file=file,
                )
            except Exception as exc:
                flash(str(exc), "error")
                return redirect(url_for("web.upload"))

            flash("Deck created and ready for practice.", "success")
            return redirect(url_for("web.deck_detail", deck_id=deck_id))

        return render_template("upload.html")

    @web.route("/review")
    @web.route("/review/<int:deck_id>")
    def review(deck_id: int | None = None):
        return render_template("review.html", review_view=build_review_context(app.config, deck_id))

    @web.post("/review/<int:card_id>")
    def submit_review(card_id: int):
        rating = int(request.form.get("rating", "0"))
        deck_id = request.form.get("deck_id")
        submit_review_result(app.config, card_id, rating)
        if deck_id:
            return redirect(url_for("web.review", deck_id=int(deck_id)))
        return redirect(url_for("web.review"))

    app.register_blueprint(web)
