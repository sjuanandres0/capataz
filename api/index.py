import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify
from bcrypt import hashpw, checkpw, gensalt
from functools import wraps
import requests
from pprint import pprint

# print(sys.path)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db import client


app = Flask(__name__)
app.secret_key = "TukiTukiSecretKey"


def save_t_message(message):
    m = {
        'message': message,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        client.capataz.telegram.insert_one(m)
    except:
        print('Error saving to telegram.message')


def send_t_message(message):
    bot_id = os.environ.get("bot_id")
    chat_id = os.environ.get("chat_id")
    if bot_id is None or chat_id is None:
        from credentials import bot_id, chat_id
    api_url = f'https://api.telegram.org/bot{bot_id}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=HTML'
    response = requests.get(api_url)
    if response.status_code == 200:
        save_t_message(message)
    return response


def login_is_required(view_func):
    @wraps(view_func)
    def decorated_func(*args, **kwargs):
        if not session.get('username'):
            return abort(401)  # Authorization required
        else:
            return view_func(*args, **kwargs)
    return decorated_func


@app.route('/t_message', methods=['GET', 'POST'])
@login_is_required
def t_message():
    message = request.args.get('m')
    if message is None:
        message = 'No message was passed to argument m'
    response = send_t_message(message)
    return jsonify({'message': message, 'response.status_code': response.status_code})


@app.route('/', methods=['GET'])
def home():
    if not session.get('username'):
        return redirect('/login_register')
    return render_template('home.html')


@app.route('/login_register', methods=['GET'])
def login_register():
    if session.get('username'):
        return redirect('/')
    return render_template('login_register.html')


@app.route('/login', methods=["POST"])
def login():
    if session.get('username'):
        return redirect('/')
    if request.method == 'POST':
        input_username = request.form.get('username').lower()
        input_password = request.form.get('password')
        user = client.capataz.user.find_one({'username': input_username})
        if user is None:
            flash(['Username not existing! Register first.', 'danger'])
            return redirect('/login_register')
        else:
            if user and checkpw(input_password.encode('utf-8'), user['password']):
                flash(['Successfully logged in!', 'success'])
                session['username'] = input_username
                session['name'] = user['name']
                return redirect('/')
            else:
                flash(['Incorrect password!', 'danger'])
    return redirect('/login_register')


@app.route('/register', methods=["POST"])
def register():
    if session.get('name'):
        return redirect('/')
    if request.method == 'POST':
        input_username = request.form.get('username').lower()
        input_name = request.form.get('name')
        input_email = request.form.get('email').lower()
        input_password = request.form.get('password')
        hashed_password = hashpw(input_password.encode('utf-8'), gensalt())
        u = {
            'username': input_username,
            'name': input_name,
            'email': input_email,
            'password': hashed_password,
            'creationDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if client.capataz.user.find_one({'username': input_username}) is not None:
            flash(
                ['Username already registered. Try with a different username or Login!', 'warning'])
            return redirect('/login_register')
        if client.capataz.user.find_one({'email': input_email}) is not None:
            flash(
                ['Email already registered. Try with a different email or Login!', 'warning'])
            return redirect('/login_register')
        send_t_message(f'New user: {input_username}')
        client.capataz.user.insert_one(u)
        flash(['Successfully registered!', 'success'])
        return redirect('/login_register')
    return redirect('/login_register')


@app.route('/logout')
def logout():
    session.clear()
    flash(['Successfully logged out!', 'success'])
    return redirect('/')


@app.route('/about')
def about():
    return 'About'


@login_is_required
@app.route('/agricultura/cp/other', methods=['POST'])
def cp_other():
    if request.method == 'POST':
        action = request.form['action']
        query = {'id': request.form['id'], 'ctg': request.form['ctg']}
        print(f'Action:{action} - query:{query}')
        if action == 'cancel':
            newvalue = {'$set': {'status': 'cancelled'}}
            client.capataz.cp.update_one(query, newvalue)
        elif action == 'delete':
            client.capataz.cp.delete_one(query)
        elif action == 'close':
            kg_confirmed = request.form['kg_confirmed']
            date_confirmed = request.form['date_confirmed']
            newvalue = {'$set': {
                'status': 'closed',
                'kg_confirmed': kg_confirmed,
                'date_confirmed': date_confirmed,
            }}
            client.capataz.cp.update_one(query, newvalue)
    return redirect('/agricultura/cp')


@login_is_required
@app.route('/agricultura/cp', methods=['GET', 'POST'])
def cp():
    if request.method == 'POST':
        action = request.form['action']
        print(f'Action:{action}')
        cp = {
            "id": request.form['id'],
            "ctg": request.form['ctg'],
            "transport": json.loads(request.form['transport']),
            "origin": json.loads(request.form['origin']),
            "destination": request.form['destination'],
            "km": request.form['km'],
            "kg": request.form['kg'],
            "type": json.loads(request.form['type']),
            "status": request.form['status'],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print(f'CP: {cp}')
        # TODO: validate input and unique id/ctg
        if action == 'new':
            client.capataz.cp.insert_one(cp)
        elif action == 'update':
            query = {'id': cp['id'], 'ctg': cp['ctg']}
            client.capataz.cp.replace_one(query, cp)

    cp = list(client.capataz.cp.find({}, {'_id': 0}))
    transportista = list(client.capataz.transportista.find({}, {'_id': 0}))
    especie = list(client.capataz.especie.find({}, {'_id': 0}))
    establecimiento = list(client.capataz.establishment.find({}, {'_id': 0}))
    chofer = None
    destino = None
    destinatario = None

    # Group data by status
    grouped_cp = {}
    if cp:
        for item in cp:
            status = item["status"]
            if status not in grouped_cp:
                grouped_cp[status] = []
            grouped_cp[status].append(item)

    params = {
        'cp': cp,
        'grouped_cp': grouped_cp,
        'transportista': transportista,
        'chofer': chofer,
        'destino': destino,
        'destinatario': destinatario,
        'especie': especie,
        'establecimiento': establecimiento,
    }
    # pprint('PARAMS:')
    # pprint(params)
    return render_template('cp.html', title='Cartas de Porte', params=params)


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


@app.route('/agricultura')
@login_is_required
def agricultura():
    return render_template('agricultura.html', title='Agricultura')


@app.route('/configuracion')
@login_is_required
def configuracion():
    return render_template('configuracion.html', title='Configuracion')


def acumHas(data):
    for e in data:
        eAcum = 0
        if e['campos']:
            for c in e['campos']:
                cAcum = 0
                try:
                    for l in c['lotes']:
                        if l['area']:
                            cAcum += float(l['area'])
                        else:
                            cAcum = 0
                    c['hasAcum'] = round(cAcum, 2)
                    eAcum += cAcum
                except:
                    pass
            e['hasAcum'] = round(eAcum, 2)
    return data


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
    result = acumHas(result)
    print(f'result:')
    # pprint(result)
    params = {
        'establishment': result
    }
    return render_template('establecimiento.html', title='Lotes', params=params)


@app.route('/configuracion/<dimension>', methods=['GET', 'POST'])
@login_is_required
def configuracion_dimension(dimension):
    allowed_dimensions = ['transportista', 'chofer',
                          'destino', 'destinatario', 'especie', 'campana']
    if dimension in allowed_dimensions:
        collection = client.capataz[dimension]
        if request.method == 'POST':
            d = {
                'id': request.form['id'],
                'name': request.form['name']
            }
            collection.insert_one(d)
        result = list(collection.find({}, {'_id': 0}))
        params = {
            'dimension': dimension,
            'result': result
        }
        title = dimension.capitalize()
        return render_template('generic_settings_form.html', title=title, params=params)
    else:
        return 'Dimension not existing'


@app.route('/configuracion/campo', methods=['POST'])
@login_is_required
def campo():
    if request.method == 'POST':
        action = request.form['action']
        print(f'action:{action}')
        establecimientoId = request.form['campoEstablecimientoId']
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
        if action == 'newCampo':
            creationDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c['creationDate'] = creationDate
            myquery = {"id": f'{establecimientoId}'}
            newvalue = {"$push": {"campos": c}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'updateCampo':
            myquery = {"id": f'{establecimientoId}', "campos.id": f'{id}'}
            newvalue = {"$set": {"campos.$.name": f'{name}',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'deactivateCampo':
            myquery = {"id": f'{establecimientoId}', "campos.id": f'{id}'}
            newvalue = {"$set": {"campos.$.status": 'inactive',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'activateCampo':
            myquery = {"id": f'{establecimientoId}', "campos.id": f'{id}'}
            newvalue = {"$set": {"campos.$.status": 'active',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            client.capataz.establishment.update_one(myquery, newvalue)

    return redirect('/configuracion/establecimiento')


@app.route('/configuracion/lote', methods=['POST'])
@login_is_required
def lote():
    if request.method == 'POST':
        action = request.form['action']
        print(f'action:{action}')
        establecimientoId = request.form['loteEstablecimientoId']
        campoId = request.form['loteCampoId']
        id = request.form['idLote']
        name = request.form['nameLote']
        status = request.form['statusLote']
        try:
            area = request.form['area']
            geojson = json.loads(request.form['geojson'])
        except:
            area = ''
            geojson = ''
        lastUpdateDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        l = {
            'id': id,
            'name': name,
            'status': status,
            'lastUpdateDate': lastUpdateDate,
            'area': area,
            'geojson': geojson
        }
        if action == 'newLote':
            creationDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            l['creationDate'] = creationDate
            myquery = {"id": establecimientoId, "campos.id": campoId}
            newvalue = {"$push": {"campos.$.lotes": l}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'update':
            myquery = {"id": establecimientoId,
                       "campos.id": campoId, "campos.lotes.id": id}
            newvalue = {"$set": {
                        "campos.$[campo].lotes.$[lote].name": name,
                        "campos.$[campo].lotes.$[lote].geojson": geojson,
                        "campos.$[campo].lotes.$[lote].area": area,
                        "lastUpdateDate": lastUpdateDate
                        }}
            array_filters = [{"campo.id": campoId}, {"lote.id": id}]
            client.capataz.establishment.update_one(
                myquery, newvalue, array_filters=array_filters)
        elif action == 'deactivate':
            myquery = {"id": establecimientoId,
                       "campos.id": campoId, "campos.lotes.id": id}
            newvalue = {"$set": {"campos.$[campo].lotes.$[lote].status": 'inactive',
                                 "lastUpdateDate": lastUpdateDate}}
            array_filters = [{"campo.id": campoId}, {"lote.id": id}]
            client.capataz.establishment.update_one(
                myquery, newvalue, array_filters=array_filters)
        elif action == 'activate':
            myquery = {"id": establecimientoId,
                       "campos.id": campoId, "campos.lotes.id": id}
            newvalue = {"$set": {"campos.$[campo].lotes.$[lote].status": 'active',
                                 "lastUpdateDate": lastUpdateDate}}
            array_filters = [{"campo.id": campoId}, {"lote.id": id}]
            client.capataz.establishment.update_one(
                myquery, newvalue, array_filters=array_filters)
        elif action == 'delete':
            myquery = {"id": establecimientoId, "campos.id": campoId}
            update_operation = {
                "$pull": {
                    "campos.$.lotes": {"id": id}
                }
            }
            client.capataz.establishment.update_one(myquery, update_operation)

    return redirect('/configuracion/establecimiento')


@app.route('/map', methods=['GET', 'POST'])
@login_is_required
def map():
    return render_template('map.html', title='Map')


@app.route('/reportes_d3')
@login_is_required
def reportes_d3():
    return render_template('report_d3.html', title='Reportes')


@app.route('/reportes')
@login_is_required
def reportes():
    cp = list(client.capataz.cp.find({}, {'_id': 0}))
    params = {'cp': cp}
    return render_template('report_apex.html', title='Reportes', params=params)


if __name__ == '__main__':
    app.run(debug=True)
