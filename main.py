from flask import Flask, request, render_template
from PIL import Image
import numpy as np 
import cv2
from io import BytesIO
import base64
from flask_socketio import SocketIO, emit
import os
from twilio.rest import Client
from recognition import getXY
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

account_sid = os.environ['ukey']
auth_token = os.environ['token']
client = Client(account_sid, auth_token)

sockets = []

app = Flask('app')
socketio = SocketIO(app)

app.static_folder = 'static'

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

# CLIENT ROUTES

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/monitor')
def monitor():
  return render_template('monitor.html')

# SOCKET ROUTES
@socketio.on('connect')
def connect(auth):
  sockets.append(request.sid)

@socketio.on('disconnect')
def disconnect(auth):
  sockets.remove(request.sid)


# RASPI ROUTES
@app.route('/rpi/image', methods=['POST'])
def get_image():
  file = request.files['image'].read()
  npimg = np.fromstring(file, np.uint8)
  img = cv2.imdecode(npimg,cv2.IMREAD_COLOR)
  img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
  y = getXY(img)
  
  img = Image.fromarray(img.astype("uint8"))
  bad = False
  if y > img.size[0]/2:
    bad = True
    message = client.messages.create(
        body="Imminent oopsie, your baby is climbing!",
        from_='+13194088215',
        to='4804764880'
    )

  print('XY', y, img.size[0]/2)
  buffer = BytesIO()
  img.save(buffer,format="JPEG")
  myimage = buffer.getvalue() 
  socketio.emit('img', {"image": "data:image/jpeg;base64,"+base64.b64encode(myimage).decode(), "climbing": bad})
  return "received"

@app.route('/', methods=['POST'])
def dum_post():
  return 'Never gonna give you up'

socketio.run(app, debug=True, host='0.0.0.0', port=3001)