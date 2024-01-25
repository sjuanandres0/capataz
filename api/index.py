import os
import json
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('layout.html', title='Home')

@app.route('/hello_world')
def hello_world():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

if __name__ == '__main__':
    app.run(debug=True)
