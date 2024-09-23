from flask import Flask
from src.webhook_handler import webhook_blueprint
import logging

app = Flask(__name__)
app.register_blueprint(webhook_blueprint)
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

if __name__ == '__main__':
    app.run(port=4000)