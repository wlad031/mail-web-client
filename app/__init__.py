from flask import Flask

import config as cfg

app = Flask(__name__)

from app import views