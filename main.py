from flask import Flask, request, url_for, redirect, render_template, flash
from flask_cors import CORS
from flask_sock import Sock
from flask_limiter import Limiter
from dotenv import load_dotenv
load_dotenv()

from database import *
from decorators import enforceSchema, jsonOnly, checkAPIKey, checkAdmin

app = Flask(__name__)
CORS(app)
sock = Sock(app)
limiter = Limiter(
    Universal.getIP,
    app=app,
    default_limits=["100 per minute"],
    storage_uri="memory://",
)

app.secret_key = os.environ.get("AppSecretKey", "DefaultKey2025")

@app.before_request
def beforeReq():
    if not (request.path.startswith("/admin") or request.path.startswith("/unauthorised") or request.path.startswith("/login")) and Universal.systemLock:
        return "ERROR: Service unavailable.", 503

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/unauthorised")
def unauthorised():
    return render_template("unauthorised.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/admin", methods=["GET"])
@checkAdmin
def admin():
    data = copy.deepcopy(DataStore.system)
    for id in data:
        del data[id]["secret"]
        data[id]["knownIPs"] = ", ".join(data[id]["knownIPs"])
        data[id]["created"] = Universal.fromUTC(data[id]["created"], localisedTo=Universal.localeOffset).strftime(Universal.readableDatetimeFormat)
        data[id]["lastUpdate"] = Universal.fromUTC(data[id]["lastUpdate"], localisedTo=Universal.localeOffset).strftime(Universal.readableDatetimeFormat) if data[id]["lastUpdate"] != None else None
    
    scData = {}
    for fragID in StreamCentre.connections:
        scData[fragID] = {}
        for cID in StreamCentre.connections[fragID]:
            scData[fragID][cID] = {
                "ip": StreamCentre.connections[fragID][cID]["ip"],
                "datetime": Universal.fromUTC(StreamCentre.connections[fragID][cID]["datetime"], localisedTo=Universal.localeOffset).strftime(Universal.readableDatetimeFormat)   
            }
    sc = {
        "data": scData,
        "streams": len(StreamCentre.connections),
        "conns": StreamCentre.getConnectionsCount(),
    }
    
    approved = {id: data[id] for id in data if data[id]["approved"]}
    pending = {id: data[id] for id in data if not data[id]["approved"]}
    
    return render_template("admin.html", approved=approved, pending=pending, adminKey=request.args.get("key", None), sc=sc)

@app.route("/admin/approveRequest", methods=["GET"])
@checkAdmin
def approveRequest():
    fragmentID = request.args.get("fragmentID", None)
    if fragmentID == None:
        return "ERROR: Invalid request.", 400
    
    if fragmentID not in DataStore.system:
        return "ERROR: Invalid request.", 400
    if DataStore.system[fragmentID]["approved"]:
        return redirect(url_for("admin", key=request.args.get("key", None)))
    
    DataStore.system[fragmentID]["approved"] = True
    DataStore.writeSystemMetadata()
    DataStore.writeFragment(fragmentID, {})
    
    Logger.log("APPROVEREQUEST: Fragment ID '{}' approved.".format(fragmentID))
    
    flash("Fragment '{}' approved.".format(fragmentID))
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/admin/deleteFragment", methods=["GET"])
@checkAdmin
def deleteFragment():
    fragmentID = request.args.get("fragmentID", None)
    if fragmentID == None:
        return "ERROR: Invalid request.", 400
    
    if fragmentID not in DataStore.system:
        return "ERROR: Invalid request.", 400
    
    DataStore.destroyFragment(fragmentID)
    del DataStore.system[fragmentID]
    DataStore.writeSystemMetadata()
    
    Logger.log("DELETEFRAGMENT: Fragment ID '{}' deleted.".format(fragmentID))
    
    flash("Fragment '{}' deleted.".format(fragmentID))
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/admin/getDataStore", methods=["GET"])
@checkAdmin
def getDataStore():
    data = copy.deepcopy(DataStore.rawLoad())
    return data, 200

@app.route("/admin/reloadMetadata", methods=["GET"])
@checkAdmin
def reloadMetadata():
    DataStore.loadSystemMetadata()
    
    flash("Metadata reloaded!")
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/admin/toggleLock", methods=["GET"])
@checkAdmin
def toggleLock():
    Universal.systemLock = not Universal.systemLock
    
    flash("System lock toggled! New status: {}".format("LOCKED" if Universal.systemLock else "UNLOCKED"))
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/admin/logs", methods=["GET"])
@checkAdmin
def viewLogs():
    try:
        logs = Logger.readAll()
        if isinstance(logs, str):
            return logs, 500
        
        if len(logs) == 0:
            return "No logs found.", 200
        
        return "<br>".join(logs), 200
    except Exception as e:
        return "ERROR: Failed to read logs. Error: {}".format(e), 500

@app.route("/admin/streamCentre/shutdown", methods=["GET"])
@checkAdmin
def shutdownStreamCentre():
    StreamCentre.shutdown()
    
    flash("Stream Centre shutdown.")
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/admin/streamCentre/closeFragment", methods=["GET"])
def closeFragmentStream():
    fragmentID = request.args.get("fragmentID", None)
    if fragmentID == None:
        return "ERROR: Invalid request.", 400
    
    if fragmentID not in DataStore.system or fragmentID not in StreamCentre.connections:
        return "ERROR: Invalid request.", 400
    
    StreamCentre.close(fragmentID)
    
    flash("Fragment '{}' stream closed.".format(fragmentID))
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/admin/streamCentre/closeConnection", methods=["GET"])
def closeConnection():
    fragmentID = request.args.get("fragmentID", None)
    connectionID = request.args.get("connectionID", None)
    if fragmentID == None or connectionID == None:
        return "ERROR: Invalid request.", 400

    if fragmentID not in DataStore.system or fragmentID not in StreamCentre.connections:
        return "ERROR: Invalid request.", 400
    if connectionID not in StreamCentre.connections[fragmentID]:
        return "ERROR: Invalid request.", 400
    
    StreamCentre.close(fragmentID, connectionID)
    
    flash("Connection '{}' closed.".format(connectionID))
    return redirect(url_for("admin", key=request.args.get("key", None)))

@app.route("/api/requestFragment", methods=["POST"])
@checkAPIKey
@jsonOnly
@enforceSchema(
    ("reason", str),
    ("secret", str)
)
def requestFragment():
    # Retrive data
    reason: str = request.json["reason"]
    secret: str = request.json["secret"]
    
    # Data validation
    if len(reason) > 150:
        return "ERROR: Reason too long.", 400
    if len(secret) < 6 or len(secret) > 20:
        return "ERROR: Secret too short/long.", 400
    
    hasNumbers = any(char.isdigit() for char in secret)
    hasLetters = any(char.isalpha() for char in secret)
    if not hasNumbers or not hasLetters:
        return "ERROR: Secret must contain both letters and numbers.", 400
    
    # Each fragment is uniquely identified by fragment ID.
    # An IP may request multiple fragments, but a request has to be approved before another can be requested.
    
    # Ensure that there are no current fragment requests from this IP that are not approved.
    for fragmentID, fragmentData in DataStore.system.items():
        if fragmentData["originalIP"] == Universal.getIP() and fragmentData["approved"] == False:
            return "ERROR: You have a pending fragment request ({}).".format(fragmentID), 403
    
    # Generate a new fragment ID and store the request.
    fragmentID = Universal.generateUniqueID()
    DataStore.system[fragmentID] = {
        "reason": request.json["reason"],
        "originalIP": Universal.getIP(),
        "knownIPs": [
            Universal.getIP()
        ],
        "secret": Encryption.encodeToSHA256(secret),
        "created": Universal.utcNowString(),
        "approved": False,
        "lastUpdate": None
    }
    DataStore.writeSystemMetadata()
    
    Logger.log("REQUESTFRAGMENT: New request from IP '{}' with fragment ID '{}'.".format(Universal.getIP(), fragmentID))
    
    return "SUCCESS: Fragment request successful; await approval. ID: {}".format(fragmentID), 200

@app.route("/api/writeFragment", methods=["POST"])
@checkAPIKey
@jsonOnly
@enforceSchema(
    ("fragmentID", str),
    ("secret", str),
    ("data", dict)
)
def writeFragment():
    # Retrieve data
    fragmentID: str = request.json["fragmentID"]
    secret: str = request.json["secret"]
    data: dict = request.json["data"]
    
    # Data validation
    if fragmentID not in DataStore.system:
        return "ERROR: Invalid request.", 400
    if not Encryption.verifySHA256(secret, DataStore.system[fragmentID]["secret"]):
        return "ERROR: Access unauthorised.", 401
    if DataStore.system[fragmentID]["approved"] == False:
        return "ERROR: Fragment request not approved.", 403
    
    # Write data
    DataStore.writeFragment(fragmentID, data)
    
    DataStore.system[fragmentID]["lastUpdate"] = Universal.utcNowString()
    sourceIP = Universal.getIP()
    if sourceIP not in DataStore.system[fragmentID]["knownIPs"]:
        DataStore.system[fragmentID]["knownIPs"].append(sourceIP)
    
    DataStore.writeSystemMetadata()
    
    # Logger.log("WRITEFRAGMENT: Data written to fragment ID '{}'.".format(fragmentID))
    return "SUCCESS: Write successful.", 200

@app.route("/api/readFragment", methods=["POST"])
@checkAPIKey
@jsonOnly
@enforceSchema(
    ("fragmentID", str),
    ("secret", str)
)
def readFragment():
    # Retrieve data
    fragmentID: str = request.json["fragmentID"]
    secret: str = request.json["secret"]
    
    # Data validation
    if fragmentID not in DataStore.system:
        return "ERROR: Invalid request.", 400
    if DataStore.system[fragmentID]["approved"] == False:
        return "ERROR: Fragment request not approved.", 403
    if not Encryption.verifySHA256(secret, DataStore.system[fragmentID]["secret"]):
        return "ERROR: Access unauthorised.", 401
    
    # Read data
    data = DataStore.readFragment(fragmentID)
    if data == None:
        return {}
    
    # Logger.log("READFRAGMENT: Data read from fragment ID '{}'.".format(fragmentID))
    return data, 200

@sock.route("/api/streamFragment")
def streamFragment(ws: Server):
    if not StreamCentre.checkPermission():
        ws.close(message="Fragment Stream API unavailable.")
        return
    if StreamCentre.getConnectionsCount() >= StreamCentre.maxConnections():
        ws.close(message="Max connections reached.")
        return
    
    # Authorisation with API key, fragment ID and secret
    ws.send(MessageWriter.normal("Authorisation required. Please submit credentials. All payloads as JSON."))
    auth = ws.receive(timeout=3)
    if auth == None:
        ws.send(MessageWriter.error("Authorisation timeout."))
        ws.close(message="Authorisation timeout.")
        return
    
    # Parse and verify the authorisation data
    fragID = None
    ip = Universal.getIP()
    try:
        auth = json.loads(auth)
        reqParams = ["apiKey", "fragmentID", "secret"]
        for param in reqParams:
            if (param not in auth) or (not isinstance(auth[param], str)):
                ws.send(MessageWriter.error("Invalid payload. Connection terminated."))
                return
        
        if "APIKey" in os.environ and auth["apiKey"] != os.environ.get("APIKey", None):
            ws.send(MessageWriter.error("Authorisation failed."))
            return
        
        fragID = auth["fragmentID"]
        secret = auth["secret"]
        
        if fragID not in DataStore.system:
            ws.send(MessageWriter.error("Fragment not found. Connection terminated."))
            return
        if not Encryption.verifySHA256(secret, DataStore.system[fragID]["secret"]):
            ws.send(MessageWriter.error("Authorisation failed."))
            return
    except Exception as e:
        Logger.log("STREAMFRAGMENT ERROR: Failed to verify auth payload. Error: {}".format(e))
        ws.send(MessageWriter.error("Invalid payload. Connection terminated."))
        return
    if len(StreamCentre.getConnections(fragID)) >= StreamCentre.maxStreamConnections():
        ws.send(MessageWriter.error("Max connections for this fragment stream has been reached."))
        ws.close(message="Max connections for fragment stream reached.")
        return
    
    ws.send(MessageWriter.successEvent("Connected to fragment ID '{}' stream successfully.".format(fragID)))
    connID = StreamCentre.addConnection(fragID, ip, ws)
    
    lastUpdateReceived = Universal.utcNow()
    
    while True:
        update = ws.receive()
        if (Universal.utcNow() - lastUpdateReceived).total_seconds() < 0.5:
            # Reject spam updates
            continue
        else:
            lastUpdateReceived = Universal.utcNow()
        
        try:
            update = json.loads(update)
        except Exception as e:
            ws.send(MessageWriter.error("Payload unparsable. Please try again."))
            continue
        
        # Process update
        if "action" in update:
            # Execute actions
            action = update["action"]
            if action == "write" and "data" in update and isinstance(update["data"], dict):
                # Write action
                
                # Write to DataStore
                DataStore.writeFragment(fragID, update["data"])
                
                DataStore.system[fragID]["lastUpdate"] = Universal.utcNowString()
                if ip not in DataStore.system[fragID]["knownIPs"]:
                    DataStore.system[fragID]["knownIPs"].append(ip)
                
                DataStore.writeSystemMetadata()
                
                # Blast update to all connections
                StreamCentre.push(fragID, MessageWriter.writeEvent(update["data"]))
            elif action == "read":
                # Read action
                ws.send(MessageWriter.readEvent(DataStore.readFragment(fragID)))
            elif action == "close":
                # Close action
                StreamCentre.close(fragID, connID)
                return
            else:
                ws.send(MessageWriter.error("Invalid action."))
                continue
        else:
            ws.send(MessageWriter.error("Unexpected payload. Please try again."))
            continue

@app.route("/api/deleteFragment", methods=["POST"])
@checkAPIKey
@jsonOnly
@enforceSchema(
    ("fragmentID", str),
    ("secret", str)
)
def destroyFragment():
    # Retrieve data
    fragmentID: str = request.json["fragmentID"]
    secret: str = request.json["secret"]
    
    # Data validation
    if fragmentID not in DataStore.system:
        return "ERROR: Invalid request.", 400
    if not Encryption.verifySHA256(secret, DataStore.system[fragmentID]["secret"]):
        return "ERROR: Access unauthorised.", 401
    
    # Delete data
    DataStore.destroyFragment(fragmentID)
    del DataStore.system[fragmentID]
    DataStore.writeSystemMetadata()
    
    Logger.log("DELETEFRAGMENT: Fragment ID '{}' deleted.".format(fragmentID))
    
    return "SUCCESS: Fragment deleted.", 200

if __name__ == "__main__":
    res = DataStore.setup(withSystemMetadata=True)
    if not res:
        print("MAIN ERROR: Failed to setup DataStore. Exiting...")
        sys.exit(1)
    
    print("MAIN: Booting now...")
    app.run(host='0.0.0.0', port=os.environ.get("RuntimePort", 8000))