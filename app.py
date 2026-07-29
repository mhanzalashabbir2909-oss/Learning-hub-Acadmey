from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "learnhub_secret_key")

USER_FILE = os.path.join(app.root_path, "users.json")
FEEDBACK_FILES = {
    "olevel": os.path.join(app.root_path, "feedback_olevel.json"),
    "alevel": os.path.join(app.root_path, "feedback_alevel.json")
}


# -------------------------
# Load Users
# -------------------------
def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as file:
            json.dump([], file)

    with open(USER_FILE, "r") as file:
        data = json.load(file)

    if not isinstance(data, list):
        data = []

    normalized_users = []
    for entry in data:
        if isinstance(entry, dict):
            normalized_users.append(entry)
        elif isinstance(entry, list) and len(entry) >= 2:
            normalized_users.append({
                "username": entry[0],
                "password": entry[1],
                "favorite_food": entry[2] if len(entry) > 2 else ""
            })

    if normalized_users != data:
        save_users(normalized_users)

    return normalized_users


# -------------------------
# Load Feedback
# -------------------------

def get_feedback_file(course="olevel"):
    if course in FEEDBACK_FILES:
        return FEEDBACK_FILES[course]
    return FEEDBACK_FILES["olevel"]


def load_feedback(course="olevel"):
    feedback_file = get_feedback_file(course)
    if not os.path.exists(feedback_file):
        with open(feedback_file, "w") as file:
            json.dump([], file)

    with open(feedback_file, "r") as file:
        data = json.load(file)

    if not isinstance(data, list):
        data = []

    normalized_feedback = []
    for entry in data:
        if isinstance(entry, dict) and "feedback" in entry:
            normalized_feedback.append(entry)
        elif isinstance(entry, str):
            normalized_feedback.append({"feedback": entry})

    if normalized_feedback != data:
        save_feedback(normalized_feedback, course)

    return normalized_feedback


# -------------------------
# Save Users
# -------------------------
def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)


# -------------------------
# Save Feedback
# -------------------------
def save_feedback(feedback_list, course="olevel"):
    feedback_file = get_feedback_file(course)
    with open(feedback_file, "w") as file:
        json.dump(feedback_list, file, indent=4)


# -------------------------
# Home Page
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# Sign In
# -------------------------
@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        next_url = request.form.get("next")

        users = load_users()

        for user in users:
            if user.get("username") == username:
                if user.get("password") == password:
                    session["username"] = username
                    if next_url and next_url.startswith("/"):
                        return redirect(next_url)
                    return redirect(url_for("dashboard"))
                flash("Incorrect password.")
                return redirect(url_for("signin", next=next_url))

        flash("Username not found.")
        return redirect(url_for("signin", next=next_url))

    next_url = request.args.get("next", "")
    return render_template("signin.html", next_url=next_url)


# -------------------------
# Sign Up
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        favorite_food = request.form.get("favorite_food")

        if not username or not password or not confirm_password or not favorite_food:
            flash("All fields are required.")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("signup"))

        users = load_users()
        for user in users:
            if user.get("username") == username:
                flash("Username already exists.")
                return redirect(url_for("signup"))

        users.append({
            "username": username,
            "password": password,
            "favorite_food": favorite_food
        })

        save_users(users)
        flash("Account created successfully! Please sign in.")
        return redirect(url_for("signin"))

    return render_template("signup.html")


# -------------------------
# Dashboard
# -------------------------
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("signin"))

    return render_template("index.html", username=session["username"])


# -------------------------
# Submit Feedback
# -------------------------
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if "username" not in session:
        return {"error": "Login required to submit feedback."}, 401

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return {"error": "Invalid request data."}, 400

    feedback_text = data.get("feedback", "")
    course = data.get("course", "olevel")
    if course not in FEEDBACK_FILES:
        course = "olevel"

    if not isinstance(feedback_text, str) or not feedback_text.strip():
        return {"error": "Feedback cannot be empty."}, 400

    feedback_list = load_feedback(course)
    feedback_list.append({
        "username": session["username"],
        "feedback": feedback_text.strip()
    })
    save_feedback(feedback_list, course)

    return {"success": True}, 200


# -------------------------
# Feedback API
# -------------------------
@app.route("/feedbacks")
def feedbacks():
    course = request.args.get("course", "olevel")
    if course not in FEEDBACK_FILES:
        course = "olevel"
    return {"feedbacks": load_feedback(course)}, 200


# -------------------------
# Render HTML Templates
# -------------------------
@app.route("/olevel-courses.html")
def olevel_courses():
    return render_template(
        "olevel-courses.html",
        feedbacks=load_feedback("olevel"),
        username=session.get("username")
    )





@app.route("/alevel-courses.html")
def alevel_courses():
    return render_template(
        "alevel-courses.html",
        feedbacks=load_feedback("alevel"),
        username=session.get("username")
    )


@app.route("/<path:template_name>.html")
def render_html_template(template_name):
    safe_name = os.path.normpath(template_name)
    if safe_name.startswith("..") or os.path.isabs(safe_name):
        return redirect(url_for("home"))

    template_name_normalized = safe_name.replace(os.path.sep, "/")
    template_file = f"{template_name_normalized}.html"
    template_path = os.path.join(
        app.root_path,
        app.template_folder or "templates",
        template_file
    )
    if os.path.exists(template_path):
        return render_template(template_file)

    return redirect(url_for("home"))


# -------------------------
# Logout
# -------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# -------------------------
# Forgot Password
# -------------------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username")
        favorite_food = request.form.get("favorite_food")

        if not username or not favorite_food:
            flash("Please enter both username and favourite food.")
            return redirect(url_for("forgot_password"))

        users = load_users()
        for user in users:
            if user.get("username") == username and user.get("favorite_food") == favorite_food:
                flash(f"Your password is: {user.get('password')}")
                return redirect(url_for("signin"))

        flash("No matching account found. Please check your username and favourite food.")
        return redirect(url_for("forgot_password"))

    return render_template("forgot-password.html")

# -------------------------
# Run Website
# -------------------------
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", debug=debug_mode)