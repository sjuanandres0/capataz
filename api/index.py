import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify
from bcrypt import hashpw, checkpw, gensalt
from functools import wraps

# print(sys.path)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db import client


app = Flask(__name__)
app.secret_key = "TukiTukiSecretKey"

# def getPasswordAccepted():
#     password_accepted = os.environ.get("password_accepted")
#     if password_accepted is None:
#         from credentials import password_accepted
#     password_accepted = [password_accepted]
#     return password_accepted


def login_is_required(view_func):
    @wraps(view_func)
    def decorated_func(*args, **kwargs):
        if not session.get('username'):
            return abort(401)  # Authorization required
        else:
            return view_func(*args, **kwargs)
    return decorated_func


@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('username'):
        return redirect('/login')
    return render_template('home.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if session.get('username'):
        return redirect('/')
    if request.method == 'POST':
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        user = client.capataz.user.find_one({'username': input_username})
        if user is None:
            flash(['Username not existing! Register first.', 'danger'])
            return redirect('/register')
        else:
            if user and checkpw(input_password.encode('utf-8'), user['password']):
                flash(['Successfully logged in!', 'success'])
                session['username'] = input_username
                session['name'] = user['name']
                return redirect('/')
            else:
                flash(['Incorrect password!', 'danger'])
    return render_template('login.html', title='Login')


@app.route('/register', methods=["GET", "POST"])
def register():
    if session.get('name'):
        return redirect('/')
    if request.method == 'POST':
        input_username = request.form.get('username')
        input_name = request.form.get('name')
        input_email = request.form.get('email')
        input_password = request.form.get('password')
        hashed_password = hashpw(input_password.encode('utf-8'), gensalt())
        u = {
            'username': input_username,
            'name': input_name,
            'email': input_email,
            'password': hashed_password
        }
        if client.capataz.user.find_one({'username': input_username}) is not None:
            flash(
                ['Username already registered. Try with a different or Login!', 'warning'])
            return redirect('/register')
        if client.capataz.user.find_one({'email': input_email}) is not None:
            flash(
                ['Email already registered. Try with a different or Login!', 'warning'])
            return redirect('/register')
        client.capataz.user.insert_one(u)
        flash(['Successfully registered!', 'success'])
        return redirect('/login')
    return render_template('register.html', title='Register')


@app.route('/logout')
def logout():
    session.clear()
    flash(['Successfully logged out!', 'success'])
    return redirect('/')


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

@app.route('/maquinaria')
@login_is_required
def maquinaria():
    return render_template('wip.html', title='Maquinaria')

@app.route('/ganaderia')
@login_is_required
def ganaderia():
    return render_template('wip.html', title='Ganaderia')


@app.route('/contracts')
@login_is_required
def contracts():
    return render_template('wip.html', title='Contratos')


@app.route('/lpg')
@login_is_required
def lpg():
    return render_template('wip.html', title='Liquidaciones')


@app.route('/reportes')
@login_is_required
def reportes():
    return render_template('wip.html', title='Reportes')


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
        if action == 'newEstablecimiento':
            creationDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            e['creationDate'] = creationDate
            client.capataz.establishment.insert_one(e)
        elif action == 'updateEstablecimiento':
            newvalue = {"$set": {"name": f'{name}',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'deactivateEstablecimiento':
            newvalue = {"$set": {"status": 'inactive',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'activateEstablecimiento':
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


@app.route('/configuracion/campo', methods=['POST'])
@login_is_required
def campo():
    if request.method == 'POST':
        action = request.form['action']
        print(f'action:{action}')
        if action == 'newCampo':
            establecimientoId = request.form['newCampoEstablecimientoId']
            id = request.form['idCampo']
            name = request.form['nameCampo']
            status = request.form['statusCampo']
            lastUpdateDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c = {
                'id': id,
                'name': name,
                'status': status,
                'lastUpdateDate': lastUpdateDate
            }
            creationDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c['creationDate'] = creationDate
            # client.capataz.establishment.insert_one(c)
            myquery = {"id": f'{establecimientoId}'}
            newvalue = {"$push": {"campos": c }}
            client.capataz.establishment.update_one(myquery, newvalue)
    return redirect('/configuracion/establecimiento')


@app.route('/configuracion/lote', methods=['POST'])
@login_is_required
def lote():
    if request.method == 'POST':
        action = request.form['action']
        print(f'action:{action}')
        if action == 'newLote':
            establecimientoId = request.form['newLoteEstablecimientoId']
            campoId = request.form['newLoteCampoId']
            id = request.form['idLote']
            name = request.form['nameLote']
            status = request.form['statusLote']
            lastUpdateDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            l = {
                'id': id,
                'name': name,
                'status': status,
                'lastUpdateDate': lastUpdateDate
            }
            creationDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            l['creationDate'] = creationDate
            # client.capataz.establishment.insert_one(c)
            myquery = {"id": f'{establecimientoId}', "campos.id": f'{campoId}'}
            newvalue = {"$push": {"campos.$.lotes": l }}
            client.capataz.establishment.update_one(myquery, newvalue)
    return redirect('/configuracion/establecimiento')


if __name__ == '__main__':
    app.run(debug=True)
