from time import sleep

from flask import Flask
app = Flask(__name__)


@app.route('/')
def hello_world():
    sleep(1)
    return 'Hello, world.'
