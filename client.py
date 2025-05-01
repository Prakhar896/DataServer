## Author: Prakhar Trivedi
## Version: 1.1
## Copyright: © 2025 Prakhar Trivedi. All rights reserved.

import os, requests, copy, json, datetime
from websockets.sync.client import ClientConnection, connect
from websockets import Data
from dotenv import load_dotenv
load_dotenv()

class CloudFragment:
    """
    ## Introduction
    `CloudFragment` is a class that allows interaction with the DataServer API developed by Prakhar Trivedi.
    
    Features include persistence of JSON data, with the ability to read, write, and delete data to what is known as a "fragment".
    
    A fragment is a unit of JSON data anchored to a unique fragment ID, which is generated upon a successful request.
    Fragments have to be requested, and approved by the maintainer of the target DataServer.
    
    ## Features
    - `__init__(apiKey: str=os.environ.get("APIKey", None), fragmentID: str=None, secret: str=None, reason: str=None, url: str="https://data.prakhar.app")`: Initialises the CloudFragment object.
    - `request()`: Requests a new fragment from the DataServer. Returns the fragment ID if successful.
    - `read(updateData: bool=True, returnOutputCopy: bool=True)`: Reads the data from the fragment. Returns the data as a dictionary if successful.
    - `write(data: dict=None, updateData: bool=True)`: Writes data to the fragment. Returns a success message if successful.
    - `delete(resetParams: bool=True)`: Deletes the fragment. Returns a success message if successful.
    - `data`: The data stored in the fragment. The `read()` and `write()` functions will update this attribute if `updateData=True`.
    
    ## Usage
    ```python
    # Initialising a fragment
    
    ## Initialising a fragment is very modular, based on the circumstance you are in.
    ## For API authorisation purposes, you need to set the API key accepted by the server; this can be done by setting the `APIKey` parameter or by simply setting a `APIKey` environment variable in a .env file.
    ## For other parameters, defaults are set, which can be changed as per your requirements.
    
    ### Example 1: Setting all parameters explicitly
    fragment = CloudFragment(apiKey="YourAPIKey", fragmentID="123456", secret="ABCD1234", reason="Testing", url="https://data.prakhar.app")
    
    #### In the above example, you are ready to call functions like `read()`, `write()`, `delete()`, etc.
    
    ### Example 2: Setting only the API key
    fragment = CloudFragment(apiKey="YourAPIKey")
    
    ### Example 3: API key in environment variable, and default values for other parameters
    fragment = CloudFragment()
    
    #### In the above examples, do note that you need to set the fragment ID and secret before calling any functions.
    
    # Typical workflow
    fragment = CloudFragment()
    fragment.reason = "I want to store some data."
    fragment.secret = "ABCD1234"
    print(fragment.request()) ## Expected output: Fragment ID or error message. If successful, the fragment ID will be auto-set in the object.
    
    ## Before proceeding with CRUD operations, the DataServer maintainer will have to approve your new fragment request.
    
    print(fragment.read()) ## Expected output: JSON Dictionary Data or error message.
    
    print(fragment.write({"hello": "world"})) ## Expected output: Success message or error message.
    
    print(fragment.data) ## Expected output: {"hello": "world"}
    
    print(fragment.delete()) ## Expected output: Success message or error message. Resets the fragment ID and secret.
    ```
    
    ## Advanced
    - The `data` attribute can be accessed directly to read the data stored in the fragment.
    - The `delete()` function can be called with `resetParams=False` to retain the fragment ID and secret.
    - Calling `read()`, `write()`, or `delete()` without setting the fragment ID and secret will raise an exception or return an error.
    - `write()` function accepts a specific payload as a parameter, which will be written to the fragment. If no payload is provided, the `data` attribute will be written.
    - The `url` parameter can be changed to point to a different DataServer instance.
    - See `CloudFragment.Stream` for more details on WebSocket-based data fragment streaming.
    
    ## Errors
    - The functions will try their best to return errors as strings.
    - The string will start with "ERROR: " followed by a message describing the error.
    - The error message will be detailed enough to understand the issue.
    - The error message will be returned if the request fails, or if the parameters are not set correctly.
    
    ## Dependencies
    - `os`, `requests`, `copy`, `dotenv`
    - `dotenv` is used to load environment variables from a `.env` file.
    - `requests` is used to make HTTP requests to the DataServer.
    - `copy` is used to create a deep copy of the data attribute.
    
    ## About this service
    This service has been written by Prakhar Trivedi, and is a part of the DataServer project.
    Thank you for using this service!
    
    Learn more at https://prakhartrivedi.works
    
    © 2025 Prakhar Trivedi. All rights reserved.
    """
    
    class StreamMessage:
        """
        `StreamMessage` is a class that represents JSON messages from the WebSocket server. Messages from the server can be of different types, and may/may not include messages or data.
        The server is expected to always send JSON parsable messages. This class parses the JSON data initialises it into a `StreamMessage` object.
        The aim is to make it easier to understand the message type and data.
        
        Attributes:
            type (str): The type of the message. Possible values are "error", 
                "event", "message", or "unknown".
            data (Any): The data payload of the message, if present. Defaults to None.
            message (str): The message content, if present. Defaults to None.
            buffer (str): The original JSON buffer string used to initialize the object.
        Methods:
            __str__(): Returns a string representation of the StreamMessage object.
        """
        def __init__(self, buffer: str):
            data = json.loads(buffer)
            msgType = None
            msg = None
            
            # Understand the message type
            if "error" in data:
                msgType = "error"
                msg = data["error"]
            elif "event" in data:
                msgType = data["event"]
            else:
                msgType = "unknown"
            
            # See if a message is present
            if "message" in data:
                if msgType == "unknown":
                    msgType = "message"
                msg = data["message"]
            
            self.type: str = msgType
            self.data = data["data"] if "data" in data else None
            self.message = msg
            self.buffer = buffer

        def __str__(self):
            return "StreamMessage(type='{}', data='{}', message='{}')".format(self.type, self.data, self.message)
    
    class Stream:
        """
        `Stream` is a sub-component of `CloudFragment` that enables WebSocket and stateful streaming of data to and from a data fragment at the server.
        The class, when initialised, connects to a WebSocket API endpoint at the given URL. `CloudFragment.initStream()` can be used to quickly create a WebSocket connection and `Stream` object at `CloudFragment.stream`.
        All implementations are synchronous and are non-blocking, though blocking could be achieved.
        
        Attributes:
            fragmentID (str): The unique identifier for the data fragment being streamed.
            secret (str): A secret key used for authentication with the server.
            apiKey (str): An optional API key for authentication. Defaults to the value of the
                          "APIKey" environment variable if not provided.
            url (str): The WebSocket server URL. Defaults to "wss://data.prakhar.app".
            conn (ClientConnection): The WebSocket connection object. Initialized as None.
        Methods:
            serverPath(path: str) -> str:
                Constructs the full server path by appending the given path to the base URL.
            status() -> bool:
                Checks the health of the WebSocket connection.
            addHistory(item):
                Adds a new item to the stream's history. Useful for debugging and investigation purposes.
                Requires self.historyEnabled=True.
            showHistory():
                Prints out all history items.
            send(data) -> bool | str:
                Sends data to the server over the WebSocket connection. Returns True if successful,
                or an error message if the operation fails.
            receive(timeout: float = None) -> Data | str:
                Receives data from the server over the WebSocket connection. Returns the received
                data or an error message if the operation fails.
            disconnect() -> bool:
                Closes the WebSocket connection if it is open. Always returns True.
            connect() -> bool | str:
                Establishes a WebSocket connection to the server, performs authentication, and
                validates the connection. Returns True if successful, or an error message if
                the connection or authentication fails.
            ping() -> bool | str:
                Sends a ping action to the server and expects to receive a pong acknowledgement within 3 seconds.
                Returns `True` is the procedure is successful. Error string if otherwise.
            write(data: dict) -> 'CloudFragment.StreamMessage | str':
                Sends a write action to the server with the provided data. Returns an acknowledgment
                message from the server or an error message if the operation fails.
            read() -> 'CloudFragment.StreamMessage | str':
                Sends a read action to the server to retrieve data. Returns the retrieved data or
                an error message if the operation fails.
    
        Example:
        ```
        # initialisation
        frag = CloudFragment(secret="a123456", reason="Testing")
        frag.request()
        input() # server admin approves request
        
        # setup a stream and send a write
        frag.initStream()
        frag.data = {"Hello": "World"}
        res: CloudFragment.StreamMessage = frag.writeWS() # the write action is pushed out as an update, delivering the write instantanously to all connections streaming the fragment.
        print(res)
        
        # stream the fragment yourself
        def doSomething(givenData):
            print("Implement your own function here which may or may not use 'data'.")
        frag.liveStream(runner=a) # providing runner is optional. this function is blocking on a given thread.
        
        # frag.liveStream will continuously receive updates (with a default 5 minute timeout for a period of no updates) and update the frag.data attribute.
        # if provided, the runner will be called with the data received from the server (CloudFragment.StreamMessage.data).
        ```
        """
        
        def __init__(self, fragmentID: str, secret: str, apiKey: str=os.environ.get("APIKey", None), url: str="wss://data.prakhar.app"):
            self.fragmentID: str = fragmentID
            self.secret: str = secret
            self.apiKey: str = apiKey
            self.url: str = url
            self.conn: ClientConnection = None
            self.historyEnabled: bool = True
            self.history = []
        
        def serverPath(self, path: str):
            return self.url + path
        
        def status(self):
            # Check connection status
            return self.conn != None and self.conn.close_code == None
        
        def addHistory(self, item):
            if self.historyEnabled:
                item = "{} {}".format(datetime.datetime.now(datetime.timezone.utc).isoformat(), item)
                self.history.append(item)
        
        def showHistory(self):
            print("{} Items".format(len(self.history)))
            for item in self.history:
                print(item)
            print("End of History")

        def send(self, data) -> bool | str:
            if not self.status():
                return "ERROR: Stream status unhealthy."
            
            try:
                self.conn.send(data, text=True)
            except Exception as e:
                self.addHistory("SNDERR: {}".format(e))
                return "ERROR: Send failed. Error: {}".format(e)
            
            self.addHistory("SND: {}".format(data))
            
            return True
        
        def receive(self, timeout: float=None) -> Data | str:
            if not self.status():
                return "ERROR: Stream status unhealthy."
            
            try:
                rc = self.conn.recv(timeout=timeout)
            except Exception as e:
                self.addHistory("RECERR: {}".format(e))
                return "ERROR: Receive failed. Error: {}".format(e)
            
            self.addHistory("REC: {}".format(rc))
            
            return rc

        def disconnect(self):
            if self.conn != None:
                if self.conn.close_code == None:
                    self.send(json.dumps({"action": "close"}))
                    self.conn.close(reason="Client disconnected.")
                self.conn = None
                self.addHistory("DC: {}".format(self.fragmentID))
            
            return True
        
        def connect(self):
            self.disconnect()
            
            try:
                self.conn = connect(self.serverPath("/api/streamFragment"))
            except Exception as e:
                self.disconnect()
                return "ERROR: Failed to connect. Error: {}".format(e)
            
            initialInstructions = self.receive(5)
            if initialInstructions.startswith("ERROR"):
                self.disconnect()
                return "ERROR: Failed to receive initial instructions. Error: {}".format(initialInstructions)
            
            authPayload = {
                "apiKey": self.apiKey,
                "fragmentID": self.fragmentID,
                "secret": self.secret
            }
            sendResult = self.send(json.dumps(authPayload))
            if sendResult != True:
                self.disconnect()
                return "ERROR: Failed to submit auth payload. Error: {}".format(sendResult)
            
            authSuccess = self.receive(5)
            if authSuccess.startswith("ERROR"):
                self.disconnect()
                return "ERROR: Failed to obtain authorisation attempt result. Error: {}".format(authSuccess)
            authSuccess = CloudFragment.StreamMessage(authSuccess)
            
            if authSuccess.type == "error":
                self.disconnect()
                return "ERROR: Authorisation attempt failed. Message: {}".format(authSuccess.message)
            if authSuccess.type != "success":
                self.disconnect()
                return "ERROR: Unknown auth result. Received: {}".format(authSuccess)
            
            self.addHistory("CONN: {}".format(self.fragmentID))
            
            print("{} STREAM: Connected successfully.".format(self.fragmentID))
            return True
        
        def ping(self) -> bool | str:
            if not self.status():
                return "ERROR: Stream status unhealthy."
            
            res = self.send(json.dumps({"action": "ping"}))
            if res != True:
                return "ERROR: Failed to submit ping action. Error: {}".format(res)
            
            ack = self.receive(3)
            if ack.startswith("ERROR"):
                return "ERROR: Ping submitted, but error in pong reception: {}".format(ack)
            
            ack = CloudFragment.StreamMessage(ack)
            if ack.type != "success":
                return "ERROR: Received unexpected message. Expected: 'success', received: '{}'".format(ack)
            
            return True

        def write(self, data: dict, ignoreAck=False) -> 'CloudFragment.StreamMessage | str':
            if not self.status():
                return "ERROR: Stream status unhealthy."
            
            res = self.send(json.dumps({
                "action": "write",
                "data": data
            }))
            if res != True:
                return "ERROR: Failed to submit write action. Error: {}".format(res)
            
            if ignoreAck:
                return CloudFragment.StreamMessage(json.dumps({"event": "write", "data": data}))
            
            ack = self.receive(3)
            if ack.startswith("ERROR"):
                return "ERROR: Write action submitted, but error in acknowledgement reception: {}".format(ack)
            ack = CloudFragment.StreamMessage(ack)
            
            return ack

        def read(self) -> 'CloudFragment.StreamMessage | str':
            if not self.status():
                return "ERROR: Stream status unhealthy."
            
            res = self.send(json.dumps({"action": "read"}))
            if res != True:
                return "ERROR: Failed to submit read action. Error: {}".format(res)
            
            read = self.receive(3)
            if read.startswith("ERROR"):
                return "ERROR: Read action submitted, error in receiving result: {}".format(read)
            read = CloudFragment.StreamMessage(read)
            
            return read
    
    def __init__(self, apiKey: str=os.environ.get("APIKey", None), fragmentID: str=None, secret: str=None, reason: str=None, url: str="https://data.prakhar.app", wsURL: str="wss://data.prakhar.app"):
        self.apiKey: str | None = apiKey
        self.fragmentID: str | None = fragmentID
        self.secret: str | None = secret
        self.reason: str | None = reason
        self.url: str = url
        self.wsURL: str = wsURL
        self.stream: CloudFragment.Stream | None = None
        self.data: dict | None = None
    
    def serverPath(self, path: str):
        return self.url + path
    
    def apiHeaders(self):
        if self.apiKey == None:
            raise Exception("API Key not set.")
        return {
            "APIKey": self.apiKey
        }

    def request(self) -> str:
        if self.fragmentID != None:
            return "ERROR: Fragment ID already set."
        
        if not isinstance(self.secret, str) or not isinstance(self.reason, str):
            return "ERROR: Secret and reason must be strings."
        
        if len(self.secret) < 6 or len(self.secret) > 20:
            return "ERROR: Secret must be between 6 and 20 characters."
        if len(self.reason) > 150:
            return "ERROR: Reason must be less than 150 characters."
        
        hasNumbers = any(char.isdigit() for char in self.secret)
        hasLetters = any(char.isalpha() for char in self.secret)
        if not hasNumbers or not hasLetters:
            return "ERROR: Secret must contain both letters and numbers."
        
        data = {
            "reason": self.reason,
            "secret": self.secret
        }
        
        requestResponse = None
        try:
            requestResponse = requests.post(
                url=self.serverPath("/api/requestFragment"),
                headers=self.apiHeaders(),
                json=data
            )
            
            requestResponse.raise_for_status()
            self.fragmentID = requestResponse.text[len("SUCCESS: Fragment request successful; await approval. ID: ")::]
            return self.fragmentID
        except Exception as e:
            readableMessage: str = "<No readable message>"
            try:
                readableMessage = requestResponse.text
            except:
                pass
            
            return "ERROR: Exception: {} Message: {}".format(e, readableMessage)

    def read(self, updateData: bool=True, returnOutputCopy: bool=True) -> dict | str:
        if self.fragmentID == None or self.secret == None:
            return "ERROR: Fragment ID or secret not set."
        
        data = {
            "fragmentID": self.fragmentID,
            "secret": self.secret
        }
        
        readResponse = None
        try:
            readResponse = requests.post(
                url=self.serverPath("/api/readFragment"),
                headers=self.apiHeaders(),
                json=data
            )
            
            readResponse.raise_for_status()
            
            if updateData:
                self.data = readResponse.json()
                
                if returnOutputCopy:
                    return copy.deepcopy(self.data)
                else:
                    return self.data
            else:
                return readResponse.json()
        except Exception as e:
            readableMessage: str = "<No readable message>"
            try:
                readableMessage = readResponse.text
            except:
                pass
            
            return "ERROR: Exception: {} Message: {}".format(e, readableMessage)
    
    def write(self, data: dict=None, updateData: bool=True) -> str:
        if self.fragmentID == None or self.secret == None:
            return "ERROR: Fragment ID or secret not set."
        
        payload = self.data if data == None else data
        
        writeResponse = None
        try:
            writeResponse = requests.post(
                url=self.serverPath("/api/writeFragment"),
                headers=self.apiHeaders(),
                json={
                    "fragmentID": self.fragmentID,
                    "secret": self.secret,
                    "data": payload
                }
            )
            
            writeResponse.raise_for_status()
            
            if updateData:
                self.data = payload
            
            return writeResponse.text
        except Exception as e:
            readableMessage: str = "<No readable message>"
            try:
                readableMessage = writeResponse.text
            except:
                pass
            
            return "ERROR: Exception: {} Message: {}".format(e, readableMessage)
    
    def delete(self, resetParams: bool=True) -> str:
        if self.fragmentID == None or self.secret == None:
            return "ERROR: Fragment ID or secret not set."
        
        data = {
            "fragmentID": self.fragmentID,
            "secret": self.secret
        }
        
        deleteResponse = None
        try:
            deleteResponse = requests.post(
                url=self.serverPath("/api/deleteFragment"),
                headers=self.apiHeaders(),
                json=data
            )
            
            deleteResponse.raise_for_status()
            
            if resetParams:
                self.fragmentID = None
                self.secret = None
                self.data = None
            
            return deleteResponse.text
        except Exception as e:
            readableMessage: str = "<No readable message>"
            try:
                readableMessage = deleteResponse.text
            except:
                pass
            
            return "ERROR: Exception: {} Message: {}".format(e, readableMessage)
    
    def initStream(self, autoConnect: bool=True) -> bool | str:
        if self.fragmentID == None or self.secret == None:
            return "ERROR: Fragment ID or secret not set."

        self.stream = CloudFragment.Stream(self.fragmentID, self.secret, self.apiKey, self.wsURL)
        
        if autoConnect:
            res = self.stream.connect()
            if res != True:
                return "ERROR: Failed to auto-connect new stream. Error: {}".format(res)
        
        return True
    
    def readWS(self, updateData: bool=True, returnOutputCopy: bool=True) -> dict | str:
        if self.stream == None:
            return "ERROR: Stream not initialised."
        if not self.stream.status():
            return "ERROR: Stream status unhealthy."
        
        readResponse = self.stream.read()
        if isinstance(readResponse, str):
            return readResponse
        if readResponse.type != "read":
            return "ERROR: Received unexpected event type. Expected: 'read', received: '{}'".format(readResponse.event)
        if readResponse.data == None:
            return "ERROR: No data received."
        
        if updateData:
            self.data = readResponse.data
            
            if returnOutputCopy:
                return copy.deepcopy(self.data)
            else:
                return self.data
        else:
            return readResponse.data
    
    def writeWS(self, data: dict=None, updateData: bool=True, ignoreAck: bool=False) -> bool | str:
        data = self.data if data == None else data
        if self.stream == None:
            return "ERROR: Stream not initialised."
        if not self.stream.status():
            return "ERROR: Stream status unhealthy."
        
        writeResponse = self.stream.write(data, ignoreAck=ignoreAck)
        if isinstance(writeResponse, str):
            return writeResponse
        if writeResponse.type != "write":
            return "ERROR: Received unexpected event type. Expected: 'write', received: '{}'".format(writeResponse.type)
        if writeResponse.data == None:
            return "ERROR: No data received."
        if updateData:
            self.data = writeResponse.data
        
        return True
    
    def liveStream(self, handler=None, timeout: float=300.0):
        if self.stream == None:
            return "ERROR: Stream not initialised."
        if not self.stream.status():
            return "ERROR: Stream status unhealthy."
        
        while True:
            update = self.stream.receive(timeout=timeout)
            if update.startswith("ERROR"):
                print("CF LIVESTREAM {} ERROR: {}".format(self.fragmentID, update))
                break
            update = CloudFragment.StreamMessage(update)
            if update.type == "ping":
                self.stream.send(json.dumps({"action": "pong"}))
            elif update.type == "write" and update.data != None:
                self.data = update.data
                if handler != None:
                    handler(self.data)
            else:
                print("CF LIVESTREAM {}: Unusual update received: {}".format(self.fragmentID, update))
    
    def __str__(self):
        return "CloudFragment: fragmentID={}, secret={}, reason={}".format(self.fragmentID, self.secret, self.reason)