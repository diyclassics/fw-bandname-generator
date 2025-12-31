from flask import Flask
from flask_bootstrap import Bootstrap
import os

# Get the parent directory (project root)
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__,
            static_folder=os.path.join(basedir, 'static'),
            template_folder='templates')
bootstrap = Bootstrap(app)

from app import routes
