from flask import Flask
from src.webhook_handler import webhook_blueprint

app = Flask(__name__)
app.register_blueprint(webhook_blueprint)

if __name__ == '__main__':
    app.run(port=4000)