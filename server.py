from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

approval_status = {"approved": False}
latest_data = {"groups": []}

ADMIN_PASSWORD = "college123"

# ─────────────────────────────────────────────
@app.route("/")
def home():
    return "Power Electronics Admin Server Running"

# ─────────────────────────────────────────────
# RECEIVE LIVE DATA FROM PYQT
@app.route("/update", methods=["POST"])
def update():
    global latest_data
    latest_data = request.json
    return "OK"

# ─────────────────────────────────────────────
@app.route("/admin")
def admin_panel():
    return """
    <h2>Admin Login</h2>
    <form method="POST" action="/login">
        Password: <input type="password" name="password"/>
        <input type="submit" value="Login"/>
    </form>
    """

# ─────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    if request.form["password"] != ADMIN_PASSWORD:
        return "Wrong Password"

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Admin Wiring Monitor</title>

<style>
body {
    background:#111;
    color:white;
    text-align:center;
    font-family:Arial;
}

canvas {
    background:#000;
    border:2px solid white;
}

button {
    margin:10px;
    padding:10px 20px;
    font-size:16px;
    cursor:pointer;
}
</style>

</head>

<body>

<h2>⚡ Live Wiring Monitor</h2>

<button onclick="approve()">Approve</button>
<button onclick="reject()">Reject</button>

<br><br>

<canvas id="canvas" width="1000" height="700"></canvas>

<script>

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

// 🔥 Node positions (adjust to match your board)
const nodePositions = {
    "1":[100,100], "2":[200,100], "3":[300,100],
    "4":[400,100], "5":[500,100], "6":[600,100],

    "7":[100,200], "8":[200,200], "9":[300,200],
    "10":[400,200], "11":[500,200], "12":[600,200],

    "13":[100,300], "14":[200,300], "15":[300,300],
    "16":[400,300], "17":[500,300], "18":[600,300],

    "19":[100,400], "20":[200,400], "21":[300,400],
    "22":[400,400], "23":[500,400], "24":[600,400],

    "25":[200,500], "26":[400,500],
    "30":[300,550], "31":[500,550],
    "32":[200,600], "33":[400,600]
};

// Draw nodes
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

// Draw wire
function drawWire(a,b){
    let [x1,y1] = nodePositions[a];
    let [x2,y2] = nodePositions[b];

    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.lineTo(x2,y2);

    ctx.strokeStyle="yellow";
    ctx.lineWidth=4;
    ctx.stroke();
}

// Draw groups
function drawGroups(groups){
    groups.forEach(group=>{
        for(let i=0;i<group.length-1;i++){
            drawWire(group[i], group[i+1]);
        }
    });
}

// Load live data
function loadData(){
    fetch('/data')
    .then(r=>r.json())
    .then(d=>{
        ctx.clearRect(0,0,canvas.width,canvas.height);
        drawNodes();
        drawGroups(d.groups || []);
    });
}

setInterval(loadData, 1000);

function approve(){ fetch('/approve'); }
function reject(){ fetch('/reject'); }

</script>

</body>
</html>
    """)

# ─────────────────────────────────────────────
@app.route("/data")
def data():
    return jsonify(latest_data)

# ─────────────────────────────────────────────
@app.route("/approve")
def approve():
    approval_status["approved"] = True
    return "Approved"

@app.route("/reject")
def reject():
    approval_status["approved"] = False
    return "Rejected"

# ─────────────────────────────────────────────
@app.route("/check")
def check():
    if approval_status["approved"]:
        approval_status["approved"] = False
        return jsonify({"approved": True})
    return jsonify({"approved": False})

# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)