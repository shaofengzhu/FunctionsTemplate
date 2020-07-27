import logging
import json
import sys

import azure.functions as func
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from metadata import generate_metadata


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Defer the import until triggered so that failure is attached to the response
    try:
        import Functions
    except ModuleNotFoundError:
        # Try the Azure Functions name if the "natural" name was missing
        import __app__.Functions as Functions

    if req.method == "POST":
        try:
            payload = req.get_json()
        except Exception as ex:
            return func.HttpResponse("Invalid request: {}".format(ex), status_code=400)
        return execute_function(Functions, payload)

    return get_metadata(Functions)


def json_default(o):
    return vars(o)


def get_metadata(functions):
    fns = ((n, getattr(functions, n, None)) for n in dir(functions))
    md = {
        "functions": [generate_metadata(n, f) for n, f in fns
                      if f and callable(f) and n[:1] != "_"]
    }
    return func.HttpResponse(
        json.dumps(md),
        mimetype="application/json",
    )


def execute_function(functions, payload):
    try:
        n = payload["id"]
    except LookupError:
        return func.HttpResponse("Invalid request: no 'id' field", status_code=422)

    try:
        f = getattr(functions, n)
    except AttributeError:
        return func.HttpResponse("Unknown function: '{}'".format(n), status_code=422)

    args = payload.get("parameters", [])

    ret = f(*args)
    return func.HttpResponse(
        json.dumps(ret, default=json_default),
        mimetype="application/json",
    )
