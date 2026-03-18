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

#legend {
    display: flex; gap: 24px; margin: 12px 0;
    font-size: 14px; font-weight: bold;
}
.leg { display: flex; align-items: center; gap: 8px; }
.dot { width: 18px; height: 6px; border-radius: 3px; }
.dot-correct { background: #00cc55; }
.dot-wrong   { background: #ff3333; }

#groupList {
    margin-top: 12px; background: #1a1a1a; border: 1px solid #333;
    border-radius: 8px; padding: 14px 20px;
    width: 100%; max-width: 900px; font-size: 14px;
}
#groupList h3 { margin-bottom: 8px; color: #aaa; }
.group-row { padding: 5px 0; border-bottom: 1px solid #2a2a2a; }
.group-row:last-child { border-bottom: none; }
.tag-correct { color: #00ee66; font-weight: bold; }
.tag-wrong   { color: #ff4444; font-weight: bold; }
</style>
</head>
<body>

<h2>⚡ Live Student Wiring Monitor</h2>
<div id="statusBar">⏳ Waiting for student submission...</div>

<div class="btn-row">
  <button id="approveBtn" onclick="doApprove()">✅ Approve</button>
  <button id="rejectBtn"  onclick="doReject()">❌ Reject</button>
</div>

<div id="legend">
  <div class="leg"><div class="dot dot-correct"></div> Correct Connection</div>
  <div class="leg"><div class="dot dot-wrong"></div> Wrong Connection</div>
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
let SRC_W = 1200, SRC_H = 800;

// ── Correct groups (exact match) — ported from Python ────────────────────
const CORRECT_GROUPS = [
    new Set(["12","13","17","20","6"]),
    new Set(["12","13","17","19","6"]),
    new Set(["18","21","4","8","9"]),
    new Set(["18","22","4","8","9"]),
    new Set(["14","2","23","3","7"]),
    new Set(["14","2","25","3","7"]),
    new Set(["1","10","11","24","5"]),
    new Set(["1","10","11","26","5"]),
    new Set(["15","30"]),
    new Set(["15","31"]),
    new Set(["15","30","31"]),
    new Set(["16","32"]),
    new Set(["16","33"]),
    new Set(["16","32","33"]),
    new Set(["16","30"]),
    new Set(["16","31"]),
    new Set(["15","32"]),
    new Set(["15","33"]),
];

function setsEqual(a, b) {
    if (a.size !== b.size) return false;
    for (let x of a) if (!b.has(x)) return false;
    return true;
}

function isGroupCorrect(group) {
    let gs = new Set(group.map(String));
    return CORRECT_GROUPS.some(cg => setsEqual(cg, gs));
}

// ── Hub logic — exact port from Python ───────────────────────────────────
const HUB_NODES = new Set(["3","4","5","6","15","16"]);
const BASE_CHAINS = [
    ["23","2","3"], ["25","2","3"],
    ["24","1","5"], ["26","1","5"],
    ["6","17","19"], ["4","18","22"],
    ["15","30"], ["15","31"], ["15","30","31"],
    ["16","32"], ["16","33"], ["16","32","33"],
];

function isSubset(small, big) {
    for (let x of small) if (!big.has(x)) return false;
    return true;
}

function groupToEdges(group) {
    let nodes = group.map(String);
    if (nodes.length < 2) return [];
    let edges = [];
    let nodeSet = new Set(nodes);

    // Exact chain match
    for (let chain of BASE_CHAINS) {
        if (setsEqual(new Set(chain), nodeSet)) {
            for (let i = 0; i < chain.length - 1; i++)
                edges.push([chain[i], chain[i+1]]);
            return edges;
        }
    }
    // Subset chain match
    for (let chain of BASE_CHAINS) {
        if (isSubset(new Set(chain), nodeSet)) {
            for (let i = 0; i < chain.length - 1; i++)
                edges.push([chain[i], chain[i+1]]);
            let hub = null;
            for (let n of chain) if (HUB_NODES.has(n)) hub = n;
            for (let n of nodes) if (!chain.includes(n)) edges.push([hub, n]);
            return edges;
        }
    }
    // Fallback: hub star or chain
    let hubIndex = nodes.findIndex(n => HUB_NODES.has(n));
    if (hubIndex === -1) {
        for (let i = 0; i < nodes.length - 1; i++)
            edges.push([nodes[i], nodes[i+1]]);
        return edges;
    }
    for (let i = 0; i < hubIndex; i++)
        edges.push([nodes[i], nodes[i+1]]);
    let hub = nodes[hubIndex];
    for (let i = hubIndex + 1; i < nodes.length; i++)
        edges.push([hub, nodes[i]]);
    return edges;
}

// ── Board image ───────────────────────────────────────────────────────────
const img = new Image();
img.crossOrigin = "anonymous";
img.src = "/board.jpg";
img.onload  = () => { SRC_W = img.naturalWidth; SRC_H = img.naturalHeight;
                       canvas.width = SRC_W; canvas.height = SRC_H; init(); };
img.onerror = () => { canvas.width = 900; canvas.height = 900; init(); };

function scaleX(x) { return x * canvas.width  / SRC_W; }
function scaleY(y) { return y * canvas.height / SRC_H; }

function drawBoard() {
    if (img.complete && img.naturalWidth > 0)
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    else {
        ctx.fillStyle = "#1a1a1a";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
}

function drawNodes() {
    ctx.font = "bold 11px Arial";
    for (let n in nodePositions) {
        let [x, y] = nodePositions[n];
        let cx = scaleX(x), cy = scaleY(y);
        ctx.beginPath();
        ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
        ctx.strokeStyle = "red"; ctx.lineWidth = 2.5; ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
        ctx.fillStyle = "black"; ctx.fill();
        ctx.fillStyle = "lime";
        ctx.fillText(n, cx + 13, cy - 4);
    }
}

function drawWire(a, b, color) {
    let ka = String(a), kb = String(b);
    if (!nodePositions[ka] || !nodePositions[kb]) return;
    let [x1, y1] = nodePositions[ka];
    let [x2, y2] = nodePositions[kb];
    let sx1 = scaleX(x1), sy1 = scaleY(y1);
    let sx2 = scaleX(x2), sy2 = scaleY(y2);
    let dx = (sx2 - sx1) * 0.5;
    ctx.beginPath();
    ctx.moveTo(sx1, sy1);
    ctx.bezierCurveTo(sx1+dx, sy1, sx1+dx, sy2, sx2, sy2);
    ctx.strokeStyle = color;
    ctx.lineWidth = 5; ctx.lineCap = "round"; ctx.stroke();
}

function renderCanvas(groups) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBoard();
    // Draw each group with correct color
    let seen = new Set();
    groups.forEach(g => {
        let correct = isGroupCorrect(g);
        let color   = correct ? "#00cc55" : "#ff3333";
        let edges   = groupToEdges(g);
        edges.forEach(([a, b]) => {
            let key = a < b ? a+"-"+b : b+"-"+a;
            if (!seen.has(key)) { seen.add(key); drawWire(a, b, color); }
        });
    });
    drawNodes();
}

function showGroups(groups) {
    if (!groups || groups.length === 0) {
        groupRows.innerHTML = "<span style='color:#555'>None yet</span>";
        return;
    }
    groupRows.innerHTML = groups.map((g, i) => {
        let correct = isGroupCorrect(g);
        let tag = correct
            ? "<span class='tag-correct'>✅ CORRECT</span>"
            : "<span class='tag-wrong'>❌ WRONG</span>";
        return `<div class="group-row">Group ${i+1}: [ ${g.join(" → ")} ] &nbsp; ${tag}</div>`;
    }).join("");
}

function update() {
    fetch("/data").then(r => r.json()).then(d => {
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
        .finally(() => { renderCanvas([]); update(); setInterval(update, 1500); });
}
</script>
</body>
</html>
""")

# ================= SERVE board.jpg =================
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
