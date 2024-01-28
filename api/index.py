import sys
print(sys.path)

import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify
from functools import wraps
from datetime import datetime
# from .db import db
import db


app = Flask(__name__)
app.secret_key = "TukiTukiSecretKey"

password_accepted = ['TukiTuki']


def login_is_required(view_func):
    @wraps(view_func)
    def decorated_func(*args, **kwargs):
        if 'password' not in session:
            return abort(401)  # Authorization required
        else:
            return view_func(*args, **kwargs)
    return decorated_func


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'password' in session:
        if session['password'] in password_accepted:
            return render_template('home.html')
    else:
        return redirect('/login')


@app.route('/login', methods=["GET", "POST"])
def login():
    if 'password' in session:
        if session['password'] in password_accepted:
            return redirect('/')

    if request.method == 'POST':
        input_password = request.form.get('input_password')
        print(f'input_password: {input_password}')
        if input_password in password_accepted:
            session.permanent = False
            session['password'] = input_password
            flash(['Successfully logged in!', 'success'])
            return redirect('/')
        else:
            flash(['Contrasena incorrecta. Intente nuevamente.', 'danger'])
            return render_template('login.html', title='Login')
    else:
        return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    if 'password' in session:
        session.clear()
    flash(['Successfully logged out!', 'success'])
    return redirect('/')


@app.route('/hello_world')
def hello_world():
    return 'Hello, World!'


@app.route('/about')
def about():
    return 'About'


@login_is_required
@app.route('/agricultura/cp', methods=['GET', 'POST'])
def cp():
    if request.method == 'POST':
        newCp = {
            "id": request.form['id'],
            "ctg": request.form['ctg'],
            "transport": request.form['tranport'],
            "origin": request.form['origin'],
            "destination": request.form['destination'],
            "km": request.form['km'],
            "kg": request.form['kg'],
            "type": request.form['type'],
            "status": "active",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print(f'NEW CP: {newCp}')
        # db.addNewCpToLocal(newCp)
        db.create('cp',newCp)

    cp = db.read('cp')

    # Group data by status
    grouped_cp = {}
    for item in cp:
        status = item["status"]
        if status not in grouped_cp:
            grouped_cp[status] = []
        grouped_cp[status].append(item)

    params = {
        'cp': cp,
        'grouped_cp': grouped_cp,
    }
    return render_template('cp.html', title='Cartas de Porte', params=params)


@login_is_required
@app.route('/contracts')
def contracts():
    return render_template('wip.html', title='Contratos')


@login_is_required
@app.route('/lpg')
def lpg():
    return render_template('wip.html', title='Liquidaciones')


@login_is_required
@app.route('/dash')
def dash():
    return render_template('wip.html', title='Dashboard')


@login_is_required
@app.route('/settings')
def settings():
    return render_template('wip.html', title='Configuracion')


@login_is_required
@app.route('/agricultura')
def agricultura():
    return render_template('agricultura.html', title='Agricultura')


@login_is_required
@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html', title='Configuracion')


@login_is_required
@app.route('/configuracion/establecimiento')
def establecimiento():
    return render_template('establecimiento.html', title='Establecimiento')


if __name__ == '__main__':
    app.run(debug=True)
