from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
import json

app = Flask(__name__)

# ===============================
# DATA STORAGE
# ===============================
approval_status = {"approved": False}
latest_data = {"groups": []}

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
body {
    background:black;
    color:white;
    text-align:center;
    font-family:Arial;
}

canvas {
    border:2px solid white;
}
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

// BOARD IMAGE
const img = new Image();
img.src = "/static/board.jpg";

// NODE POSITIONS (adjust later if needed)
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


// DRAW NODES
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


// DRAW CURVED WIRE
function drawWire(a,b){
    let [x1,y1] = nodePositions[a];
    let [x2,y2] = nodePositions[b];

    let dx = (x2 - x1) * 0.5;

    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.bezierCurveTo(x1+dx,y1, x1+dx,y2, x2,y2);

    ctx.strokeStyle="yellow";
    ctx.lineWidth=5;
    ctx.stroke();
}


// DRAW GROUP CONNECTIONS
function drawGroups(groups){
    groups.forEach(group=>{
        for(let i=0;i<group.length-1;i++){
            drawWire(group[i], group[i+1]);
        }
    });
}


// RENDER EVERYTHING
function render(groups){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    drawNodes();
    drawGroups(groups);
}


// LOAD LIVE DATA
function loadData(){
    fetch('/data')
    .then(r=>r.json())
    .then(d=>{
        render(d.groups || []);
    });
}

setInterval(loadData, 1000);


// BUTTONS
function approve(){ fetch('/approve'); }
function reject(){ fetch('/reject'); }

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
    global latest_data
    latest_data = request.json
    return "OK"


# ===============================
# SEND DATA TO ADMIN UI
# ===============================
@app.route("/data")
def data():
    return jsonify(latest_data)


# ===============================
# APPROVAL SYSTEM
# ===============================
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


# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
