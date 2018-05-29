

from flask import Flask
from flask_jsonrpc import JSONRPC
from flask_sqlalchemy import SQLAlchemy
from ..config import setting


app = Flask(__name__)

jsonrpc = JSONRPC(app, "/")


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s/%s' %(setting.MYSQLDATABASE["user"],
                                                                setting.MYSQLDATABASE["passwd"],
                                                                setting.MYSQLDATABASE["host"],
                                                                setting.MYSQLDATABASE["db"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=True
db = SQLAlchemy(app)


from .controller import *

