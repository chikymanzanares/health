"""Flask front-end: login + claim submission over gRPC."""

from __future__ import annotations

import os
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from db import init_db, verify_user
from grpc_client import run_full_mri_flow

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-health-secret-change-me")
DB_PATH = os.environ.get("DATABASE_PATH", "/tmp/health.db")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def _ensure_db():
    init_db(DB_PATH)


@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        if verify_user(DB_PATH, username, password):
            session["user"] = username
            return redirect(url_for("home"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
@login_required
def home():
    return render_template("home.html", user=session["user"])


@app.route("/claims/new", methods=["GET"])
@login_required
def claims_new():
    return render_template("claim_form.html", user=session["user"])


@app.route("/claims", methods=["POST"])
@login_required
def claims_create():
    """
    HTML form or JSON API.

    JSON body example:
    {
      "policy_id": 1001,
      "type": "medical_expense",
      "amount": 450,
      "description": "MRI scan",
      "member_id": "M-1001",
      "provider_id": "PROV-MRI-01",
      "in_network": true
    }
    """
    if request.is_json:
        data = request.get_json(silent=True) or {}
        policy_id = int(data.get("policy_id") or 0)
        claim_type = (data.get("type") or "medical_expense").strip()
        amount = float(data.get("amount") or 0)
        description = (data.get("description") or "").strip()
        member_id = (data.get("member_id") or "M-1001").strip()
        provider_id = (data.get("provider_id") or "PROV-MRI-01").strip()
        in_network = bool(data.get("in_network", True))
        want_json = True
    else:
        policy_id = int(request.form.get("policy_id") or 0)
        claim_type = (request.form.get("type") or "medical_expense").strip()
        amount = float(request.form.get("amount") or 0)
        description = (request.form.get("description") or "").strip()
        member_id = (request.form.get("member_id") or "M-1001").strip()
        provider_id = (request.form.get("provider_id") or "PROV-MRI-01").strip()
        in_network = request.form.get("in_network") == "on"
        want_json = False

    result = run_full_mri_flow(
        policy_id=policy_id,
        member_id=member_id,
        amount=amount,
        description=description,
        claim_type=claim_type,
        provider_id=provider_id,
        in_network=in_network,
    )

    if want_json:
        status = 200 if result["ok"] else 400
        return jsonify(result), status

    return render_template("claim_result.html", user=session["user"], result=result)


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    init_db(DB_PATH)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
