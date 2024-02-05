import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify
from flask_session import Session
from functools import wraps

# print(sys.path)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import client

app = Flask(__name__)
app.secret_key = "TukiTukiSecretKey"
password_accepted = os.environ.get("password_accepted")
if password_accepted is None:
    from credentials import password_accepted
password_accepted = [password_accepted]

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def login_is_required(view_func):
    @wraps(view_func)
    def decorated_func(*args, **kwargs):
        if not session.get('name'):
            return abort(401)  # Authorization required
        else:
            return view_func(*args, **kwargs)
    return decorated_func


# @app.route('/test')
# def test():
#     collection = client.dummyDatabase.dummyCollection
#     result = collection.find_one()
#     print(result)
#     return json.dumps(result, default=str)


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('name'):
        return redirect('/login')
    return render_template('home.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if session.get('name'):
        return redirect('/')
    if request.method == 'POST':
        input_password = request.form.get('password')
        if input_password in password_accepted:
            flash(['Successfully logged in!', 'success'])
            session['name'] = request.form.get('name')
            return redirect('/')
        else:
            flash(['Incorrect password!', 'danger'])
    return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    session.clear()
    flash(['Successfully logged out!', 'success'])
    return redirect('/')


@app.route('/hello_world')
def hello_world():
    return 'Hello, World!'


@app.route('/about')
def about():
    return 'About'


# @login_is_required
# @app.route('/agricultura/cp', methods=['GET', 'POST'])
# def cp():
#     if request.method == 'POST':
#         newCp = {
#             "id": request.form['id'],
#             "ctg": request.form['ctg'],
#             "transport": request.form['tranport'],
#             "origin": request.form['origin'],
#             "destination": request.form['destination'],
#             "km": request.form['km'],
#             "kg": request.form['kg'],
#             "type": request.form['type'],
#             "status": "active",
#             "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         }
#         print(f'NEW CP: {newCp}')
#         # db.addNewCpToLocal(newCp)
#         db.create('cp', newCp)

#     cp = db.read('cp')

#     # Group data by status
#     grouped_cp = {}
#     for item in cp:
#         status = item["status"]
#         if status not in grouped_cp:
#             grouped_cp[status] = []
#         grouped_cp[status].append(item)

#     params = {
#         'cp': cp,
#         'grouped_cp': grouped_cp,
#     }
#     return render_template('cp.html', title='Cartas de Porte', params=params)


@app.route('/wip')
@login_is_required
def wip():
    return render_template('wip.html', title='WIP')


@app.route('/contracts')
@login_is_required
def contracts():
    return render_template('wip.html', title='Contratos')


@app.route('/lpg')
@login_is_required
def lpg():
    return render_template('wip.html', title='Liquidaciones')


@app.route('/dash')
@login_is_required
def dash():
    return render_template('wip.html', title='Dashboard')


@app.route('/settings')
@login_is_required
def settings():
    return render_template('wip.html', title='Configuracion')


@app.route('/agricultura')
@login_is_required
def agricultura():
    return render_template('agricultura.html', title='Agricultura')


@app.route('/configuracion')
@login_is_required
def configuracion():
    return render_template('configuracion.html', title='Configuracion')


@app.route('/configuracion/establecimiento', methods=['GET', 'POST'])
@login_is_required
def establecimiento():
    if request.method == 'POST':
        action = request.form['action']
        print(f'action = {action}')
        # TODO: Sanitize user input - particularly for query params / avoid taking id from frontend
        id = request.form['id']
        name = request.form['name']
        status = request.form['status']
        lastUpdateDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        e = {
            'id': id,
            'name': name,
            'status': status,
            'lastUpdateDate': lastUpdateDate
        }
        myquery = {"id": f'{id}'}
        if action == 'new':
            creationDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            e['creationDate'] = creationDate
            client.capataz.establishment.insert_one(e)
        elif action == 'update':
            newvalue = {"$set": {"name": f'{name}',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'deactivate':
            newvalue = {"$set": {"status": 'inactive',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'activate':
            newvalue = {"$set": {"status": 'active',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        else:
            flash(['Error - condition undefined.', 'danger'])

        flash(['Success!', 'success'])

    collection = client.capataz.establishment
    result = list(collection.find({}, {'_id': 0}))
    print(f'result: {result}')
    params = {
        'establishment': result
    }
    return render_template('establecimiento.html', title='Establecimiento', params=params)


if __name__ == '__main__':
    app.run(debug=True)
