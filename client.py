## Author: Prakhar Trivedi
## Version: 1.0
## Copyright: © 2025 Prakhar Trivedi. All rights reserved.

import os, requests, copy
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
    
    def __init__(self, apiKey: str=os.environ.get("APIKey", None), fragmentID: str=None, secret: str=None, reason: str=None, url: str="https://data.prakhar.app"):
        self.apiKey: str | None = apiKey
        self.fragmentID: str | None = fragmentID
        self.secret: str | None = secret
        self.reason: str | None = reason
        self.url: str = url
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
    
    def __str__(self):
        return "CloudFragment: fragmentID={}, secret={}, reason={}".format(self.fragmentID, self.secret, self.reason)