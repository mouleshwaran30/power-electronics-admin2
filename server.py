from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os

app = Flask(__name__)

latest_data = {"groups": []}
approval_status = {"approved": False}

ADMIN_PASSWORD = "college123"

# ================= HOME =================
@app.route("/")
def home():
    return "Admin Server Running"

# ================= ADMIN LOGIN =================
@app.route("/admin")
def admin():
    return """
    <h2>Admin Login</h2>
    <form method="POST" action="/login">
        Password: <input type="password" name="password"/>
        <input type="submit">
    </form>
    """

# ================= ADMIN PANEL =================
@app.route("/login", methods=["POST"])
def login():
    if request.form["password"] != ADMIN_PASSWORD:
        return "Wrong password"

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Admin Wiring Monitor</title>
<style>
body { background:black; color:white; text-align:center; }
canvas { border:2px solid white; }
</style>
</head>
<body>

<h2>⚡ Live Wiring Monitor</h2>

<button onclick="approve()">Approve</button>
<button onclick="reject()">Reject</button>

<br><br>
<canvas id="canvas" width="1200" height="800"></canvas>

<script>
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

let nodePositions = {};

const img = new Image();
img.src = "/static/board.jpg";

img.onload = () => {
    fetch("/socket_positions")
    .then(r => r.json())
    .then(data => {
        nodePositions = data;
        update();
    });
};

function drawNodes(){
    for(let n in nodePositions){
        let [x,y] = nodePositions[n];
        ctx.beginPath();
        ctx.arc(x,y,8,0,2*Math.PI);
        ctx.fillStyle="red";
        ctx.fill();
        ctx.fillStyle="white";
        ctx.fillText(n,x+10,y);
    }
}

function drawWire(a,b){
    let [x1,y1] = nodePositions[a];
    let [x2,y2] = nodePositions[b];

    let dx = (x2-x1)/2;

    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.bezierCurveTo(x1+dx,y1,x1+dx,y2,x2,y2);

    ctx.strokeStyle="yellow";
    ctx.lineWidth=5;
    ctx.stroke();
}

function drawGroups(groups){
    groups.forEach(g=>{
        for(let i=0;i<g.length-1;i++){
            drawWire(g[i],g[i+1]);
        }
    });
}

function render(groups){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    drawNodes();
    drawGroups(groups);
}

function update(){
    fetch("/data")
    .then(r=>r.json())
    .then(d=>{
        render(d.groups || []);
    });
}

setInterval(update,1000);

function approve(){ fetch("/approve"); }
function reject(){ fetch("/reject"); }

</script>
</body>
</html>
""")

# ================= SOCKET JSON =================
@app.route("/socket_positions")
def socket_positions():
    return send_from_directory(os.getcwd(), "socket_positions_1.json")

# ================= STATIC =================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.getcwd(), filename)

# ================= RECEIVE DATA =================
@app.route("/update", methods=["POST"])
def update_data():
    global latest_data
    latest_data = request.json
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
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
