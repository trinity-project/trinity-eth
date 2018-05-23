from functools import wraps

from flask import jsonify



def response_wrap(func):
    @wraps(func)
    def wrapper():
        response=func()
        return jsonify(response)
    return wrapper