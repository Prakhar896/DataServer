from flask import request, redirect, url_for
import functools, os, sys, datetime, random, json

def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        if not os.environ.get("DECORATOR_DEBUG_MODE", "False") == "True":
            return func(*args, **kwargs)
        
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__}() returned {repr(value)}")
        return value
    return wrapper_debug

def jsonOnly(func):
    """Enforce the request to be in JSON format. 400 error if otherwise."""
    @functools.wraps(func)
    @debug
    def wrapper_jsonOnly(*args, **kwargs):
        if not request.is_json:
            return "ERROR: Invalid request format.", 400
        else:
            return func(*args, **kwargs)
    
    return wrapper_jsonOnly

def checkAPIKey(func):
    """Check if the request has the correct API key. 401 error if otherwise."""
    @functools.wraps(func)
    @debug
    def wrapper_checkAPIKey(*args, **kwargs):
        if ("APIKey" in os.environ) and (("APIKey" not in request.headers) or (request.headers["APIKey"] != os.environ.get("APIKey", None))):
            return "ERROR: Request unauthorised.", 401
        else:
            return func(*args, **kwargs)
    
    return wrapper_checkAPIKey

def checkAdmin(func):
    """Check if the request has the correct admin key. 401 error if otherwise."""
    @functools.wraps(func)
    @debug
    def wrapper_checkAdmin(*args, **kwargs):
        if ("AdminKey" in os.environ) and (("key" not in request.args) or (request.args["key"] != os.environ.get("AdminKey", None))):
            return redirect(url_for('unauthorised'))
        else:
            return func(*args, **kwargs)
    
    return wrapper_checkAdmin

def enforceSchema(*expectedArgs):
    """Enforce a specific schema for the JSON payload.
    
    Requires request to be in JSON format, or 415 werkzeug.exceptions.BadRequest error will be raised.
    
    Sample implementation:
    ```python
    @app.route("/")
    @enforceSchema(("hello", int), "world", ("john"))
    def home():
        return "Success!"
    ```
    
    The above implementation mandates that 'hello', 'world' and 'john' attributes must be present. Additionally, 'hello' must be an integer.
    
    Parameter definition can be one of the following:
    - String: Just ensures that the parameter is present, regardless of its value's datatype.
    - Tuple, with two elements: First element is the parameter name, second element is the expected datatype.
        - If the datatype (second element) is not provided, it will be as if the parameter's name was provided directly, i.e. it will just ensure that the parameter is present.
        - Example: `("hello", int)` ensures that 'hello' is present and is an integer. But, `("hello")` ensures that 'hello' is present, but does not enforce any datatype.
        
    Raises `"ERROR: Invalid request format", 400` if the schema is not met.
    """
    def decorator_enforceSchema(func):
        @functools.wraps(func)
        @debug
        def wrapper_enforceSchema(*args, **kwargs):
            jsonData = request.get_json()
            for expectedTuple in expectedArgs:
                if isinstance(expectedTuple, tuple):
                    if expectedTuple[0] not in jsonData:
                        return "ERROR: Invalid request format.", 400
                    if len(expectedTuple) > 1:
                        if not isinstance(jsonData[expectedTuple[0]], expectedTuple[1]):
                            return "ERROR: Invalid request format.", 400
                elif expectedTuple not in jsonData:
                    return "ERROR: Invalid request format.", 400
            
            return func(*args, **kwargs)
        
        return wrapper_enforceSchema
    
    return decorator_enforceSchema