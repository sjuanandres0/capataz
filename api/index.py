import os
import json
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "TukiTukiSecretKey"

password_accepted = ['TukiTuki']

data_folder_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data')
print(f'data_folder_path: {data_folder_path}')
# with open(f'{data_folder_path}/products.json', 'r') as json_file:
#     products = json.load(json_file)


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
            # return redirect('/cp')
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
            print(f'Session: {session}')
            session.permanent = False
            session['password'] = input_password
            flash(['Successfully logged in!', 'success'])
            return redirect('/')
        else:
            flash(['Incorrect password! Please try again.', 'danger'])
            return render_template('login.html', title='Login')
    else:
        return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    if 'password' in session:
        session.clear()
    flash(['Successfully logged out!', 'primary'])
    return redirect('/')


@app.route('/hello_world')
def hello_world():
    return 'Hello, World!'


@app.route('/about')
def about():
    return 'About'


def addNewCpToLocal(new_element):
    try:
        with open(f'{data_folder_path}/cp.json', 'r') as json_file:
            data = json.load(json_file)
        data.append(new_element)
        with open(f'{data_folder_path}/cp.json', 'w') as json_file:
            json.dump(data, json_file, indent=2)
        flash(['Nueva CP cargada exitosamente!', 'success'])
        return print("New element appended successfully.")
    except:
        flash(['Error al guardar Nueva CP!', 'danger'])
        print('Error to save new CP')


@login_is_required
@app.route('/cp', methods=['GET', 'POST'])
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
            # "date": "2023-07-24 15:59:33"
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print(f'NEW CP: {newCp}')
        addNewCpToLocal(newCp)

    with open(f'{data_folder_path}/cp.json', 'r') as json_file:
        cp = json.load(json_file)

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


if __name__ == '__main__':
    app.run(debug=True)
