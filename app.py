import phonenumbers
from flask import Flask, jsonify, render_template, request

from database import add_contact, init_db, lookup_phone

app = Flask(__name__)


def _normalize_phone(raw: str):
    """
    Parse and return the phone number in E.164 format.
    Raises ValueError with a descriptive message on invalid input.
    """
    if not raw or not raw.strip():
        raise ValueError("Phone number is required.")
    try:
        parsed = phonenumbers.parse(raw, "US")
    except phonenumbers.NumberParseException:
        raise ValueError(
            "Unable to parse the phone number. "
            "Include a country code (e.g. +1) if outside the US."
        )
    if not phonenumbers.is_valid_number(parsed):
        raise ValueError("The phone number entered is not valid.")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    """
    Query parameter: phone
    Returns JSON:
      - on success:   { "found": true,  "result": { ... } }
      - on not found: { "found": false }
      - on error:     { "error": "..." }  HTTP 400
    """
    raw = request.args.get("phone", "")
    try:
        normalized = _normalize_phone(raw)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    result = lookup_phone(normalized)
    if result:
        # Split comma-separated list fields into arrays for the frontend
        for field in ("other_numbers", "relatives"):
            if result.get(field):
                result[field] = [v.strip() for v in result[field].split(",")]
            else:
                result[field] = []
        return jsonify({"found": True, "result": result})
    return jsonify({"found": False})


_SUBMIT_FIELDS = {"age", "line_type", "carrier", "address", "city", "state", "zip", "email", "job_title", "employer"}


@app.route("/submit", methods=["POST"])
def submit():
    """
    Submit a phone number to be added to the database.
    Accepts JSON: { phone, name, age?, line_type?, carrier?, address?,
                    city?, state?, zip?, email?, job_title?, employer? }
    Returns JSON:
      - on success:  { "added": true }
      - on duplicate: { "error": "..." }  HTTP 409
      - on bad input: { "error": "..." }  HTTP 400
    """
    data = request.get_json(silent=True) or {}

    raw_phone = data.get("phone", "")
    name = (data.get("name") or "").strip()

    try:
        normalized = _normalize_phone(raw_phone)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not name:
        return jsonify({"error": "Name is required."}), 400

    optional = {}
    for field in _SUBMIT_FIELDS:
        val = data.get(field)
        if val not in (None, ""):
            if field == "age":
                try:
                    optional[field] = int(val)
                except (ValueError, TypeError):
                    return jsonify({"error": "Age must be a whole number."}), 400
            else:
                optional[field] = str(val).strip()

    added = add_contact(normalized, name, **optional)
    if added:
        return jsonify({"added": True})
    return jsonify({"error": "This number is already in our database."}), 409


if __name__ == "__main__":
    init_db()
    app.run(debug=False)
