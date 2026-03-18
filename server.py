from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os

app = Flask(__name__)

# ===============================
# DATA STORAGE
# ===============================
submissions = {}       # { student_name: { "groups": [...] } }
student_status = {}    # { student_name: "pending" | "approved" | "rejected" }

ADMIN_PASSWORD = "college123"


# ===============================
# HOME
# ===============================
@app.route("/")
def home():
    return "Power Electronics Admin Server Running"


# ===============================
# ADMIN LOGIN PAGE
# ===============================
@app.route("/admin")
def admin_panel():
    return """
    <h2>Admin Login</h2>
    <form method="POST" action="/login">
        Password: <input type="password" name="password"/>
        <input type="submit" value="Login"/>
    </form>
    """


# ===============================
# LOGIN → ADMIN UI
# ===============================
@app.route("/login", methods=["POST"])
def login():
    if request.form["password"] != ADMIN_PASSWORD:
        return "Wrong Password"

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>⚡ Real Wiring Monitor</title>
<style>
* { box-sizing: border-box; }
body {
    background: black;
    color: white;
    font-family: Arial;
    margin: 0;
    padding: 10px;
}
h2 { text-align: center; }

#layout {
    display: flex;
    gap: 16px;
    align-items: flex-start;
}

/* LEFT PANEL - Student List */
#student-panel {
    width: 260px;
    min-width: 260px;
    background: #111;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 12px;
}
#student-panel h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.student-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: border-color 0.2s;
}
.student-card:hover { border-color: #888; }
.student-card.active { border-color: yellow; }
.student-name {
    font-weight: bold;
    font-size: 14px;
    margin-bottom: 6px;
}
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
}
.status-pending  { background: #444; color: #ccc; }
.status-approved { background: #1a4a1a; color: #4caf50; border: 1px solid #4caf50; }
.status-rejected { background: #4a1a1a; color: #f44336; border: 1px solid #f44336; }

.btn-approve {
    background: #1a4a1a;
    color: #4caf50;
    border: 1px solid #4caf50;
    padding: 4px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    margin-top: 6px;
    margin-right: 4px;
}
.btn-reject {
    background: #4a1a1a;
    color: #f44336;
    border: 1px solid #f44336;
    padding: 4px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    margin-top: 6px;
}
.btn-approve:hover { background: #2a6a2a; }
.btn-reject:hover  { background: #6a2a2a; }

/* RIGHT PANEL - Canvas */
#canvas-panel {
    flex: 1;
}
#canvas-panel h3 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #aaa;
}
canvas { border: 2px solid white; display: block; }

#no-selection {
    color: #555;
    font-size: 14px;
    margin-top: 20px;
    text-align: center;
}
</style>
</head>
<body>

<h2>⚡ Live Wiring Monitor — Admin</h2>

<div id="layout">

  <!-- LEFT: Student list -->
  <div id="student-panel">
    <h3>Students</h3>
    <div id="student-list">
      <div style="color:#555;font-size:13px">No submissions yet...</div>
    </div>
  </div>

  <!-- RIGHT: Canvas -->
  <div id="canvas-panel">
    <h3 id="canvas-title">Select a student to view their wiring</h3>
    <canvas id="canvas" width="900" height="700"></canvas>
  </div>

</div>

<script>
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const img = new Image();
img.src = "/static/board.jpg";

const nodePositions = {
 "1":[120,100], "2":[240,100], "3":[360,100],
 "4":[480,100], "5":[600,100], "6":[720,100],
 "7":[120,200], "8":[240,200], "9":[360,200],
 "10":[480,200], "11":[600,200], "12":[720,200],
 "13":[120,300], "14":[240,300], "15":[360,300],
 "16":[480,300], "17":[600,300], "18":[720,300],
 "19":[120,400], "20":[240,400], "21":[360,400],
 "22":[480,400], "23":[600,400], "24":[720,400],
 "25":[240,500], "26":[480,500],
 "30":[360,600], "31":[600,600],
 "32":[240,700], "33":[480,700]
};

let selectedStudent = null;
let allSubmissions = {};

function drawNodes() {
    for (let n in nodePositions) {
        let [x, y] = nodePositions[n];
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, 2 * Math.PI);
        ctx.fillStyle = "red";
        ctx.fill();
        ctx.fillStyle = "white";
        ctx.fillText(n, x + 10, y);
    }
}

function drawWire(a, b) {
    let [x1, y1] = nodePositions[a];
    let [x2, y2] = nodePositions[b];
    let dx = (x2 - x1) * 0.5;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.bezierCurveTo(x1 + dx, y1, x1 + dx, y2, x2, y2);
    ctx.strokeStyle = "yellow";
    ctx.lineWidth = 5;
    ctx.stroke();
}

function drawGroups(groups) {
    (groups || []).forEach(group => {
        for (let i = 0; i < group.length - 1; i++) {
            drawWire(group[i], group[i + 1]);
        }
    });
}

function render(groups) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    drawNodes();
    drawGroups(groups);
}

function selectStudent(name) {
    selectedStudent = name;
    document.getElementById("canvas-title").textContent = "Wiring by: " + name;
    document.querySelectorAll(".student-card").forEach(c => c.classList.remove("active"));
    const card = document.getElementById("card-" + name);
    if (card) card.classList.add("active");
    const data = allSubmissions[name];
    render(data ? data.groups : []);
}

function approveStudent(name) {
    fetch("/approve?name=" + encodeURIComponent(name))
        .then(() => updateStudentStatus(name, "approved"));
}

function rejectStudent(name) {
    fetch("/reject?name=" + encodeURIComponent(name))
        .then(() => updateStudentStatus(name, "rejected"));
}

function updateStudentStatus(name, status) {
    const badge = document.getElementById("badge-" + name);
    if (badge) {
        badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        badge.className = "status-badge status-" + status;
    }
}

function buildStudentList(submissions) {
    allSubmissions = submissions;
    const container = document.getElementById("student-list");

    if (Object.keys(submissions).length === 0) {
        container.innerHTML = '<div style="color:#555;font-size:13px">No submissions yet...</div>';
        return;
    }

    container.innerHTML = "";
    for (let name in submissions) {
        const status = submissions[name].status || "pending";
        const card = document.createElement("div");
        card.className = "student-card" + (selectedStudent === name ? " active" : "");
        card.id = "card-" + name;
        card.innerHTML = `
            <div class="student-name">${name}</div>
            <span id="badge-${name}" class="status-badge status-${status}">
                ${status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
            <div>
                <button class="btn-approve" onclick="event.stopPropagation();approveStudent('${name}')">✓ Approve</button>
                <button class="btn-reject"  onclick="event.stopPropagation();rejectStudent('${name}')">✗ Reject</button>
            </div>
        `;
        card.addEventListener("click", () => selectStudent(name));
        container.appendChild(card);
    }

    // Re-render canvas for selected student if still present
    if (selectedStudent && submissions[selectedStudent]) {
        render(submissions[selectedStudent].groups);
    }
}

function loadData() {
    fetch("/submissions")
        .then(r => r.json())
        .then(data => {
            buildStudentList(data);
        });
}

img.onload = () => {
    render([]);
};

setInterval(loadData, 1000);
loadData();
</script>

</body>
</html>
""")


# ===============================
# STATIC FILES (IMAGE)
# ===============================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.getcwd(), filename)


# ===============================
# RECEIVE DATA FROM STUDENT APP
# ===============================
@app.route("/update", methods=["POST"])
def update():
    data = request.json
    name = data.get("student_name", "Unknown")
    submissions[name] = {
        "groups": data.get("groups", []),
        "status": student_status.get(name, "pending")
    }
    if name not in student_status:
        student_status[name] = "pending"
    return "OK"


# ===============================
# GET ALL SUBMISSIONS (for admin UI)
# ===============================
@app.route("/submissions")
def get_submissions():
    result = {}
    for name, data in submissions.items():
        result[name] = {
            "groups": data.get("groups", []),
            "status": student_status.get(name, "pending")
        }
    return jsonify(result)


# ===============================
# APPROVAL SYSTEM (per student)
# ===============================
@app.route("/approve")
def approve():
    name = request.args.get("name")
    if name:
        student_status[name] = "approved"
        return f"Approved: {name}"
    return "No name provided", 400


@app.route("/reject")
def reject():
    name = request.args.get("name")
    if name:
        student_status[name] = "rejected"
        return f"Rejected: {name}"
    return "No name provided", 400


@app.route("/check")
def check():
    name = request.args.get("name")
    if not name:
        return jsonify({"approved": False})
    status = student_status.get(name, "pending")
    if status == "approved":
        student_status[name] = "pending"  # reset after student sees it
        return jsonify({"approved": True})
    return jsonify({"approved": False, "status": status})


# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
