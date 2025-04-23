# main.py
from flask import Flask

from blueprint.format_resume_api import format_resume_bp

app = Flask(__name__)

app.register_blueprint(format_resume_bp)

if __name__ == '__main__':
    app.run()