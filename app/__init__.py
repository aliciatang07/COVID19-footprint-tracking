

from flask import Flask
from datetime import timedelta

webapp = Flask(__name__)
webapp.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)

from app import main
from app import dynamo
from app import footprint
from app import map_rendering
from app import login
from app import register
from app import footprint
from app import assessment_form
from app import S3
