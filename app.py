#!/usr/bin/env python3
import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from threading import Thread
from client import PeerClient  

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.secret_key = (
    "IsThisTheRealSecret?"  # Please change the Secret if you want to public it.
)
db = SQLAlchemy(app)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin


@app.route("/", methods=["GET"])
def index():
    if session.get("logged_in"):
        return render_template("home.html", app=app)
    else:
        return render_template("index.html", app=app)


@app.route("/discover")
def discover():
    if session.get("logged_in") and session.get("is_admin"):
        return render_template("discover.html", app=app)
    elif session.get("logged_in"):
        return render_template("home.html", message="Permission Denied")
    else:
        return render_template("index.html", message="Please sign in first")


@app.route("/ping")
def ping():
    if session.get("logged_in") and session.get("is_admin"):
        return render_template("ping.html", app=app)
    elif session.get("logged_in"):
        return render_template("home.html", message="Permission Denied")
    else:
        return render_template("index.html", message="Please sign in first")


@app.route("/publish", methods=["GET", "POST"])
def publish():
    if request.method == "POST":
        file = request.files["file"]
        if "file" not in request.files or file.filename == "":
            return render_template("publish.html", message="No file provided")

        allowed_extensions = {".txt", ".pdf", ".docx", ".xlsx"}
        if not allowed_file(file.filename, allowed_extensions):
            return render_template("publish.html", message="Invalid file type")

        if request.form["filename"] == "":
            filename = secure_filename(file.filename)
        else:
            filename = request.form["filename"]
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        if os.path.exists(file_path):
            return render_template("publish.html", message="File already uploaded")

        file.save(file_path)

        upload_thread = Thread(target=PeerClient.upload, args=(file_path,))
        upload_thread.start()

        peer_repo = []
        peer_repo.append({"filename": filename, "reponame": file_path})

        return render_template(
            "publish.html", message="File uploaded and published successfully"
        )

    return render_template("publish.html")


def allowed_file(filename, allowed_extensions):
    print("Filename:", filename)
    _, file_extension = os.path.splitext(filename)
    print("File Extension:", file_extension)
    return "." in filename and file_extension.lower() in allowed_extensions

    if session.get("logged_in"):
        return render_template("publish.html", app=app)
    else:
        return render_template("index.html", alert="Please sign in first")


@app.route("/fetch", methods=["GET", "POST"])
def fetch():
    if request.method == "POST":
        filename = request.form["filename"]
        if filename == "":
            return render_template("fetch.html", message="No file provided")
        return redirect(url_for("fetch_file", filename=filename))

    if session.get("logged_in"):
        return render_template("fetch.html", app=app)
    else:
        return render_template("index.html", alert="Please sign in first")


@app.route("/fetch/<filename>")
def fetch_file(filename):
    if session.get("logged_in"):
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return render_template("fetch.html", message="File not found")

    return render_template("index.html", alert="Please sign in first")


@app.route("/register", methods=["GET", "POST"])
def register():
    message = None
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]

            if password != confirm_password:
                message = "Passwords do not match"
            else:
                with app.app_context():
                    existing_user = User.query.filter_by(username=username).first()
                    if existing_user:
                        message = "Username already exists."
                    else:
                        db.session.add(
                            User(username=username, password=password, is_admin=False)
                        )
                        db.session.commit()
                        return redirect(url_for("login"))
        except Exception as e:
            print(e)
            message = "An error occurred during registration. Please try again."

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        with app.app_context():
            user = User.query.filter_by(username=u, password=p).first()
            if user is not None:
                session["logged_in"] = True
                session["is_admin"] = user.is_admin
                return redirect(url_for("index"))
            return render_template("login.html", message="Incorrect Details")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session["logged_in"] = False
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if User.query.filter_by(is_admin=True).first() is None:
            db.session.add(
                User(username="admin", password="F3kePassword", is_admin=True)
            )  # Please change the password if you want to public it.
            db.session.commit()
    app.run(debug=True, host="0.0.0.0", port=5000)
