import os
import io
import threading
import datetime
import json
from flask import Flask, render_template, request, jsonify, send_file, abort
from model import train_model_background, extract_embedding_for_image, MODEL_PATH

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_FILE = os.path.join(APP_DIR, "students.json")
ATTENDANCE_FILE = os.path.join(APP_DIR, "attendance.json")
DATASET_DIR = os.path.join(APP_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

TRAIN_STATUS_FILE = os.path.join(APP_DIR, "train_status.json")

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------- DB helpers ----------
def load_json_file(filepath, default=None):
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return default

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def init_db():
    # Initialize JSON files if they don't exist
    if not os.path.exists(STUDENTS_FILE):
        save_json_file(STUDENTS_FILE, [])
    if not os.path.exists(ATTENDANCE_FILE):
        save_json_file(ATTENDANCE_FILE, [])

init_db()

# ---------- Train status helpers ----------
def write_train_status(status_dict):
    with open(TRAIN_STATUS_FILE, "w") as f:
        json.dump(status_dict, f)

def read_train_status():
    if not os.path.exists(TRAIN_STATUS_FILE):
        return {"running": False, "progress": 0, "message": "Not trained"}
    with open(TRAIN_STATUS_FILE, "r") as f:
        return json.load(f)

# ensure initial train status file exists
write_train_status({"running": False, "progress": 0, "message": "No training yet."})

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

# Dashboard simple API for attendance stats (last 30 days)
@app.route("/attendance_stats")
def attendance_stats():
    attendance_data = load_json_file(ATTENDANCE_FILE, [])
    if not attendance_data:
        from datetime import date, timedelta
        days = [(date.today() - datetime.timedelta(days=i)).strftime("%d-%b") for i in range(29, -1, -1)]
        return jsonify({"dates": days, "counts": [0]*30})
    
    # Process attendance data
    last_30 = [ (datetime.date.today() - datetime.timedelta(days=i)) for i in range(29, -1, -1) ]
    counts = []
    for d in last_30:
        count = 0
        for record in attendance_data:
            record_date = datetime.datetime.fromisoformat(record['timestamp']).date()
            if record_date == d:
                count += 1
        counts.append(count)
    dates = [ d.strftime("%d-%b") for d in last_30 ]
    return jsonify({"dates": dates, "counts": counts})

# -------- Add student (form) --------
@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "GET":
        return render_template("add_student.html")
    # POST: save student metadata and return student_id
    data = request.form
    name = data.get("name","").strip()
    roll = data.get("roll","").strip()
    cls = data.get("class","").strip()
    sec = data.get("sec","").strip()
    reg_no = data.get("reg_no","").strip()
    if not name:
        return jsonify({"error":"name required"}), 400
    
    students = load_json_file(STUDENTS_FILE, [])
    # Generate new ID
    sid = max([s.get('id', 0) for s in students], default=0) + 1
    now = datetime.datetime.utcnow().isoformat()
    
    new_student = {
        'id': sid,
        'name': name,
        'roll': roll,
        'class': cls,
        'section': sec,
        'reg_no': reg_no,
        'created_at': now
    }
    students.append(new_student)
    save_json_file(STUDENTS_FILE, students)
    
    # create dataset folder for this student
    os.makedirs(os.path.join(DATASET_DIR, str(sid)), exist_ok=True)
    return jsonify({"student_id": sid})

# -------- Upload face images (after capture) --------
@app.route("/upload_face", methods=["POST"])
def upload_face():
    student_id = request.form.get("student_id")
    if not student_id:
        return jsonify({"error":"student_id required"}), 400
    files = request.files.getlist("images[]")
    saved = 0
    folder = os.path.join(DATASET_DIR, student_id)
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    for f in files:
        try:
            fname = f"{datetime.datetime.utcnow().timestamp():.6f}_{saved}.jpg"
            path = os.path.join(folder, fname)
            f.save(path)
            saved += 1
        except Exception as e:
            app.logger.error("save error: %s", e)
    return jsonify({"saved": saved})

# -------- Train model (start background thread) --------
@app.route("/train_model", methods=["GET"])
def train_model_route():
    # if already running, respond accordingly
    status = read_train_status()
    if status.get("running"):
        return jsonify({"status":"already_running"}), 202
    # reset status
    write_train_status({"running": True, "progress": 0, "message": "Starting training"})
    # start background thread
    t = threading.Thread(target=train_model_background, args=(DATASET_DIR, lambda p,m: write_train_status({"running": True, "progress": p, "message": m})))
    t.daemon = True
    t.start()
    return jsonify({"status":"started"}), 202

# -------- Train progress (polling) --------
@app.route("/train_status", methods=["GET"])
def train_status():
    return jsonify(read_train_status())

# -------- Mark attendance page --------
@app.route("/mark_attendance", methods=["GET"])
def mark_attendance_page():
    return render_template("mark_attendance.html")

# -------- Recognize face endpoint (POST image) --------
@app.route("/recognize_face", methods=["POST"])
def recognize_face():
    if "image" not in request.files:
        return jsonify({"recognized": False, "error":"no image"}), 400
    img_file = request.files["image"]
    try:
        emb = extract_embedding_for_image(img_file.stream)
        if emb is None:
            return jsonify({"recognized": False, "error":"no face detected"}), 200
        # attempt prediction
        from model import load_model_if_exists, predict_with_model
        clf = load_model_if_exists()
        if clf is None:
            return jsonify({"recognized": False, "error":"model not trained"}), 200
        pred_label, conf = predict_with_model(clf, emb)
        # threshold confidence
        if conf < 0.5:
            return jsonify({"recognized": False, "confidence": float(conf)}), 200
        # find student name
        students = load_json_file(STUDENTS_FILE, [])
        student = next((s for s in students if s['id'] == int(pred_label)), None)
        name = student['name'] if student else "Unknown"
        
        # save attendance record with timestamp
        attendance_data = load_json_file(ATTENDANCE_FILE, [])
        # Generate new ID
        att_id = max([a.get('id', 0) for a in attendance_data], default=0) + 1
        ts = datetime.datetime.utcnow().isoformat()
        
        new_attendance = {
            'id': att_id,
            'student_id': int(pred_label),
            'name': name,
            'timestamp': ts
        }
        attendance_data.append(new_attendance)
        save_json_file(ATTENDANCE_FILE, attendance_data)
        
        return jsonify({"recognized": True, "student_id": int(pred_label), "name": name, "confidence": float(conf)}), 200
    except Exception as e:
        app.logger.exception("recognize error")
        return jsonify({"recognized": False, "error": str(e)}), 500

# -------- Attendance records & filters --------
@app.route("/attendance_record", methods=["GET"])
def attendance_record():
    period = request.args.get("period", "all")  # all, daily, weekly, monthly
    attendance_data = load_json_file(ATTENDANCE_FILE, [])
    filtered_records = []
    
    if period == "daily":
        today = datetime.date.today().isoformat()
        for record in attendance_data:
            record_date = datetime.datetime.fromisoformat(record['timestamp']).date().isoformat()
            if record_date == today:
                filtered_records.append(record)
    elif period == "weekly":
        start = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        for record in attendance_data:
            record_date = datetime.datetime.fromisoformat(record['timestamp']).date().isoformat()
            if record_date >= start:
                filtered_records.append(record)
    elif period == "monthly":
        start = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        for record in attendance_data:
            record_date = datetime.datetime.fromisoformat(record['timestamp']).date().isoformat()
            if record_date >= start:
                filtered_records.append(record)
    else:
        filtered_records = attendance_data
    
    # Sort by timestamp descending and limit to 5000
    filtered_records.sort(key=lambda x: x['timestamp'], reverse=True)
    filtered_records = filtered_records[:5000]
    
    # Convert to tuple format for template compatibility
    rows = [(r['id'], r['student_id'], r['name'], r['timestamp']) for r in filtered_records]
    return render_template("attendance_record.html", records=rows, period=period)

# -------- CSV download --------
@app.route("/download_csv", methods=["GET"])
def download_csv():
    attendance_data = load_json_file(ATTENDANCE_FILE, [])
    # Sort by timestamp descending
    attendance_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    output = io.StringIO()
    output.write("id,student_id,name,timestamp\n")
    for r in attendance_data:
        output.write(f'{r["id"]},{r["student_id"]},{r["name"]},{r["timestamp"]}\n')
    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name="attendance.csv", mimetype="text/csv")

# -------- Students API for listing/editing --------
@app.route("/students", methods=["GET"])
def students_list():
    students = load_json_file(STUDENTS_FILE, [])
    # Sort by id descending
    students.sort(key=lambda x: x['id'], reverse=True)
    return jsonify({"students": students})

@app.route("/students/<int:sid>", methods=["DELETE"])
def delete_student(sid):
    # Remove student
    students = load_json_file(STUDENTS_FILE, [])
    students = [s for s in students if s['id'] != sid]
    save_json_file(STUDENTS_FILE, students)
    
    # Remove attendance records
    attendance_data = load_json_file(ATTENDANCE_FILE, [])
    attendance_data = [a for a in attendance_data if a['student_id'] != sid]
    save_json_file(ATTENDANCE_FILE, attendance_data)
    
    # also delete dataset folder
    folder = os.path.join(DATASET_DIR, str(sid))
    if os.path.isdir(folder):
        import shutil
        shutil.rmtree(folder, ignore_errors=True)
    return jsonify({"deleted": True})

# ---------------- run ------------------------
if __name__ == "__main__":
    app.run(debug=True)