from client import CloudFragment
import os, json

creds = {"fragmentID": None, "secret": None}
if os.path.isfile(os.path.join(os.getcwd(), "creds.json")):
    with open("creds.json", "r") as f:
        creds = json.load(f)
else:
    with open("creds.json", "w") as f:
        json.dump(creds, f)

fragment = CloudFragment(fragmentID=creds["fragmentID"], secret=creds["secret"], url="http://localhost:8250")

def saveCreds():
    with open("creds.json", "w") as f:
        json.dump(creds, f)

# Request fragment if not exists
if fragment.fragmentID == None:
    print("Requesting fragment...")
    fragment.reason = input("Enter reason: ")
    fragment.secret = input("Enter secret: ")
    print(fragment.request())
    print()
    input("Request made. Please approve.")
    
    creds["fragmentID"] = fragment.fragmentID
    creds["secret"] = fragment.secret
    saveCreds()

# Get fragment data
print("Data:")
print(fragment.read())

# Loop
while True:
    try:
        exec(input(">>> "))
    except Exception as e:
        print("ERROR: {}".format(e))