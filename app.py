from flask import Flask, render_template, request
from flask_login import LoginManager

app = Flask(__name__)

import config


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'danger'

import models 

import routes

if __name__ == '__main__':
    app.run(debug=True)

