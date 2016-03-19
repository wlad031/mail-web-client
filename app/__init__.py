from flask import Flask

import config as cfg

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.secret_key = cfg.AppConfig['FORM_SECRET_KEY']

from app import views