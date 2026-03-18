from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os

app = Flask(__name__)

latest_data = {"groups": []}
approval_status = {"approved": False}

ADMIN_PASSWORD = "college123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= HOME =================
@app.route("/")
def home():
    return "Admin Server Running"

# ================= ADMIN LOGIN =================
@app.route("/admin")
def admin():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Admin Login</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #111; color: white; font-family: Arial;
       display: flex; justify-content: center; align-items: center; height: 100vh; }
.box { background: #222; padding: 40px; border-radius: 12px; text-align: center; }
input[type=password] { padding: 10px; font-size: 16px; border-radius: 6px;
                        border: none; margin: 10px 0; width: 220px; }
input[type=submit] { background: #0077ff; color: white; border: none;
                     padding: 10px 30px; font-size: 16px; border-radius: 6px; cursor: pointer; }
</style>
</head>
<body>
<div class="box">
  <h2>🔐 Admin Login</h2>
  <form method="POST" action="/login">
    <input type="password" name="password" placeholder="Enter password"/><br><br>
    <input type="submit" value="Login">
  </form>
</div>
</body>
</html>
"""

# ================= ADMIN PANEL =================
@app.route("/login", methods=["POST"])
def login():
    if request.form["password"] != ADMIN_PASSWORD:
        return """
        <html><body style='background:#111;color:red;font-family:Arial;text-align:center;padding:60px'>
        <h2>❌ Wrong Password</h2>
        <a href='/admin' style='color:#0af'>Try again</a>
        </body></html>
        """
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Admin Wiring Monitor</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d0d0d; color: white;
    font-family: Arial, sans-serif;
    display: flex; flex-direction: column;
    align-items: center; padding: 20px;
}
h2 { margin-bottom: 12px; font-size: 24px; }
#statusBar {
    font-size: 18px; font-weight: bold;
    padding: 10px 30px; border-radius: 8px;
    margin-bottom: 14px; background: #333; color: #aaa;
}
.approved { background: #006622 !important; color: #00ff66 !important; }
.rejected { background: #660000 !important; color: #ff4444 !important; }
.received { background: #004466 !important; color: #44ddff !important; }
.btn-row { display: flex; gap: 16px; margin-bottom: 20px; }
button { font-size: 18px; padding: 12px 36px; border-radius: 8px;
         cursor: pointer; border: none; font-weight: bold; }
#approveBtn { background: #00cc55; color: white; }
#rejectBtn  { background: #cc2200; color: white; }
#canvasWrapper { border: 2px solid #444; border-radius: 8px; overflow: hidden; max-width: 95vw; }
canvas { display: block; max-width: 100%; height: auto; }
#groupList {
    margin-top: 16px; background: #1a1a1a; border: 1px solid #333;
    border-radius: 8px; padding: 14px 20px;
    width: 100%; max-width: 900px; font-size: 14px;
}
#groupList h3 { margin-bottom: 8px; color: #aaa; }
.group-row { padding: 4px 0; border-bottom: 1px solid #2a2a2a; color: #ddd; }
</style>
</head>
<body>

<h2>⚡ Live Student Wiring Monitor</h2>
<div id="statusBar">⏳ Waiting for student submission...</div>

<div class="btn-row">
  <button id="approveBtn" onclick="doApprove()">✅ Approve</button>
  <button id="rejectBtn"  onclick="doReject()">❌ Reject</button>
</div>

<div id="canvasWrapper">
  <canvas id="canvas"></canvas>
</div>

<div id="groupList">
  <h3>📡 Received Wire Groups</h3>
  <div id="groupRows"><span style='color:#555'>None yet</span></div>
</div>

<script>
const canvas    = document.getElementById("canvas");
const ctx       = canvas.getContext("2d");
const statusBar = document.getElementById("statusBar");
const groupRows = document.getElementById("groupRows");

let nodePositions = {};
let hasData = false;
let SRC_W = 1200, SRC_H = 800;  // will be updated once image loads

// ── Board image — served directly from /board.jpg ─────────────────────────
const img = new Image();
img.crossOrigin = "anonymous";
img.src = "/board.jpg";

img.onload = function() {
    console.log("✅ board.jpg loaded:", img.naturalWidth, img.naturalHeight);
    // Set canvas to exact image size — NO stretching
    SRC_W = img.naturalWidth;
    SRC_H = img.naturalHeight;
    canvas.width  = SRC_W;
    canvas.height = SRC_H;
    init();
};
img.onerror = function() {
    console.warn("⚠️ board.jpg failed to load");
    canvas.width  = 900;
    canvas.height = 900;
    init();
};

function scaleX(x) { return x * canvas.width  / SRC_W; }
function scaleY(y) { return y * canvas.height / SRC_H; }

function drawBoard() {
    if (img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    } else {
        ctx.fillStyle = "#1a1a1a";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#555";
        ctx.font = "20px Arial";
        ctx.fillText("board.jpg not found", 300, 400);
    }
}

function drawNodes() {
    ctx.font = "bold 11px Arial";
    for (let n in nodePositions) {
        let [x, y] = nodePositions[n];
        let cx = scaleX(x), cy = scaleY(y);
        ctx.beginPath();
        ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
        ctx.strokeStyle = "red";
        ctx.lineWidth = 2.5;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
        ctx.fillStyle = "black";
        ctx.fill();
        ctx.fillStyle = "lime";
        ctx.fillText(n, cx + 13, cy - 4);
    }
}

function drawWire(a, b) {
    let ka = String(a), kb = String(b);
    if (!nodePositions[ka] || !nodePositions[kb]) return;
    let [x1, y1] = nodePositions[ka];
    let [x2, y2] = nodePositions[kb];
    let sx1 = scaleX(x1), sy1 = scaleY(y1);
    let sx2 = scaleX(x2), sy2 = scaleY(y2);
    let dx = (sx2 - sx1) * 0.5;
    ctx.beginPath();
    ctx.moveTo(sx1, sy1);
    ctx.bezierCurveTo(sx1 + dx, sy1, sx1 + dx, sy2, sx2, sy2);
    ctx.strokeStyle = "#ffcc00";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.stroke();
}

function drawGroups(groups) {
    groups.forEach(g => {
        for (let i = 0; i < g.length - 1; i++) {
            drawWire(g[i], g[i + 1]);
        }
    });
}

function renderCanvas(groups) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBoard();
    drawGroups(groups);
    drawNodes();
}

function showGroups(groups) {
    if (!groups || groups.length === 0) {
        groupRows.innerHTML = "<span style='color:#555'>None yet</span>";
        return;
    }
    groupRows.innerHTML = groups.map((g, i) =>
        `<div class="group-row">Group ${i + 1}: [ ${g.join(" → ")} ]</div>`
    ).join("");
}

function update() {
    fetch("/data")
        .then(r => r.json())
        .then(d => {
            let groups = d.groups || [];
            renderCanvas(groups);
            showGroups(groups);
            if (groups.length > 0 && !hasData) {
                hasData = true;
                statusBar.textContent = "🔌 Student wiring received! Review and Approve / Reject.";
                statusBar.className = "received";
            } else if (groups.length === 0) {
                hasData = false;
                statusBar.textContent = "⏳ Waiting for student submission...";
                statusBar.className = "";
            }
        });
}

function doApprove() {
    fetch("/approve").then(() => {
        statusBar.textContent = "✅ APPROVED — Result sent to student!";
        statusBar.className = "approved";
    });
}

function doReject() {
    fetch("/reject").then(() => {
        statusBar.textContent = "❌ REJECTED — Student notified.";
        statusBar.className = "rejected";
    });
}

function init() {
    fetch("/socket_positions")
        .then(r => r.json())
        .then(data => { nodePositions = data; })
        .catch(e => console.warn("socket_positions failed:", e))
        .finally(() => {
            renderCanvas([]);
            update();
            setInterval(update, 1500);
        });
}
</script>
</body>
</html>
""")

# ================= SERVE board.jpg DIRECTLY =================
@app.route("/board.jpg")
def board_image():
    return send_from_directory(BASE_DIR, "board.jpg")

# ================= SOCKET JSON =================
@app.route("/socket_positions")
def socket_positions():
    return send_from_directory(BASE_DIR, "socket_positions_1.json")

# ================= STATIC =================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)

# ================= RECEIVE DATA =================
@app.route("/update", methods=["POST"])
def update_data():
    global latest_data
    latest_data = request.json
    approval_status["approved"] = False
    return "OK"

# ================= SEND DATA =================
@app.route("/data")
def data():
    return jsonify(latest_data)

# ================= APPROVAL =================
@app.route("/approve")
def approve():
    approval_status["approved"] = True
    return "Approved"

@app.route("/reject")
def reject():
    approval_status["approved"] = False
    return "Rejected"

@app.route("/check")
def check():
    if approval_status["approved"]:
        approval_status["approved"] = False
        return jsonify({"approved": True})
    return jsonify({"approved": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
