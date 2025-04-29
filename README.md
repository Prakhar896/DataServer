# DataServer

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

Sample implementation in [test.py](test.py)

© 2025 Prakhar Trivedi. All rights reserved.