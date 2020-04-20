#!venv/bin/python
from app import webapp
import os

webapp.run( host = '0.0.0.0', port = 5000, debug = True)