import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, session, redirect, request, abort, flash, jsonify
from bcrypt import hashpw, checkpw, gensalt
from functools import wraps
import requests

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
    # message = 'Hello, this is a test'
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
        # db.create('cp', newCp)

    # cp = db.read('cp')
    cp = None

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


@app.route('/configuracion/<dimension>', methods=['GET', 'POST'])
@login_is_required
def configuracion_dimension(dimension):
    allowed_dimensions = ['transportista', 'chofer', 'destino', 'destinatario']
    if dimension in allowed_dimensions:
        collection = client.capataz[dimension]
        if request.method == 'POST':
            d = {
                'name': request.form['name'],
                'number': request.form['number']
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
        area = request.form['area']
        geojson = json.loads(request.form['geojson'])
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
            myquery = {"id": f'{establecimientoId}', "campos.id": f'{campoId}'}
            newvalue = {"$push": {"campos.$.lotes": l}}
            client.capataz.establishment.update_one(myquery, newvalue)
        elif action == 'update':
            myquery = {"id": f'{establecimientoId}',
                       "campos.id": f'{campoId}', "campos.lotes.id": f'{id}'}
            newvalue = {"$set": {"campos.$[campo].lotes.$[lote].name": f'{name}',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            array_filters = [{"campo.id": f'{campoId}'}, {"lote.id": f'{id}'}]
            client.capataz.establishment.update_one(
                myquery, newvalue, array_filters=array_filters)
        elif action == 'deactivate':
            myquery = {"id": f'{establecimientoId}',
                       "campos.id": f'{campoId}', "campos.lotes.id": f'{id}'}
            newvalue = {"$set": {"campos.$[campo].lotes.$[lote].status": 'inactive',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            array_filters = [{"campo.id": f'{campoId}'}, {"lote.id": f'{id}'}]
            client.capataz.establishment.update_one(
                myquery, newvalue, array_filters=array_filters)
        elif action == 'activate':
            myquery = {"id": f'{establecimientoId}',
                       "campos.id": f'{campoId}', "campos.lotes.id": f'{id}'}
            newvalue = {"$set": {"campos.$[campo].lotes.$[lote].status": 'active',
                                 "lastUpdateDate": f'{lastUpdateDate}'}}
            array_filters = [{"campo.id": f'{campoId}'}, {"lote.id": f'{id}'}]
            client.capataz.establishment.update_one(
                myquery, newvalue, array_filters=array_filters)

    return redirect('/configuracion/establecimiento')


@app.route('/map_modal', methods=['GET', 'POST'])
@login_is_required
def map_modal():
    return render_template('map_modal.html', title='Map Modal')

@app.route('/map', methods=['GET', 'POST'])
@login_is_required
def map():
    return render_template('map.html', title='Map')


@app.route('/map_marker', methods=['POST'])
@login_is_required
def map_marker():
    coordinates = request.form.get('coordinates')
    print(f'map_marker:{coordinates}')
    return jsonify({'message': 'Marker coordinates received successfully', 'coordinates': coordinates})


@app.route('/map_polygon', methods=['POST'])
@login_is_required
def map_polygon():
    coordinates = request.form.get('coordinates')
    areaInHectares = request.form.get('ha')
    print(f'map_polygon:{coordinates}')
    print(f'areaInHectares:{areaInHectares}')
    return jsonify({'message': 'Polygon coordinates received successfully', 'coordinates': coordinates})


@app.route('/map_w_polygon', methods=['GET', 'POST'])
@login_is_required
def map_w_polygon():
    pol1 = [[-32.810122066446176, -61.138937337045434], [-32.80500243570437, -61.131406233545796], [-32.807309911415985, -61.12634258560871], [-32.80657080462293, -61.125956375172855],
            [-32.804641887213315, -61.13089128629797], [-32.801973782927625, -61.126600059232636], [-32.814286055649845, -61.11662295630575], [-32.81042851386125, -61.139023161586756]]
    pol2 = [[-32.79145436071166, -61.15548323887184], [-32.783232239060126, -61.14123893189331],
            [-32.78683852633699, -61.138235614156876], [-32.79488002041138, -61.15265153929178]]

    return render_template('map_w_polygon.html', title='Map', pol1=pol1, pol2=pol2)


if __name__ == '__main__':
    app.run(debug=True)
