
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to a strong key

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def load_data():
    try:
        with open("database.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"messages": [], "live_scores": [], "events": []}


def load_users():
    try:
        with open("database.json", "r") as f:
            return json.load(f)["users"]
    except (FileNotFoundError, KeyError):
        return []


def save_data(data):
    with open("database.json", "w") as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    data = load_data()
    return render_template('index.html', live_scores=data["live_scores"])

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/get_events')
def get_events():
    data = load_data()
    return jsonify(data["events"])


@app.route('/add_event', methods=["POST"])
def add_event():
    if not session.get("admin"):
        return redirect(url_for("login"))

    title = request.form["title"]
    date = request.form["date"]
    url = request.form.get("url", "")

    data = load_data()
    data["events"].append({"title": title, "date": date, "url": url})
    save_data(data)
    return redirect(url_for("calendar"))

@app.route('/delete_event', methods=['POST'])
def delete_event():
    if not session.get("admin"):
        return "Unauthorized", 403

    event_title = request.form.get('title')
    event_date = request.form.get('date')

    data = load_data()
    data["events"] = [e for e in data["events"] if not (e["title"] == event_title and e["date"] == event_date)]
    save_data(data)
    return "Event deleted", 200


@app.route('/gallery')
def gallery():
    images = os.listdir(UPLOAD_FOLDER)
    return render_template('gallery.html', images=images)

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if 'file' not in request.files:
        return redirect(url_for("gallery"))

    file = request.files['file']
    if file.filename == '' or file.filename.split('.')[-1].lower() not in ALLOWED_EXTENSIONS:
        return redirect(url_for("gallery"))

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return redirect(url_for("gallery"))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/merchandise')
def merchandise():
    return render_template('merchandise.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        for user in users:
            if user['username'] == username and check_password_hash(user['password'], password):
                session['admin'] = True
                return redirect(url_for('home'))

        error = "Invalid credentials. Please try again."

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))



@app.route('/delete_image', methods=['POST'])
def delete_image():
    if not session.get("admin"):
        return "Unauthorized", 403

    filename = request.form.get("filename")
    if not filename:
        return redirect(url_for("gallery"))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    return redirect(url_for("gallery"))


if __name__ == "__main__":
    app.run(debug=True, port="8080")
