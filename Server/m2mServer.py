"""
    M2M Server

    Sample M2M Server code for the university challenge.
    This code is based off of the Flask tutorial by Armin Ronacher, found here:
       http://flask.pocoo.org/docs/tutorial/

    :license: BSD, see LICENSE for more details.
"""

#################################
#            Imports     	#
#################################

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, make_response, Response
from flask.ext.googlemaps import GoogleMaps, Map
import json, os, sys, datetime
from functools import wraps
from math import *
try:
    import cPickle as pickle
except:
    import pickle

app = Flask(__name__)
GoogleMaps(app)

# Load default config or override config from an environment variable, if it exists
app.config.update(dict(
    DATABASE = sys.path[0]+'/M2M.db',
    DEBUG=True,
    SECRET_KEY='someRandomKey',
    USERNAME='m2m',
    PASSWORD='challenge'
))
app.config.from_envvar('M2M_SETTINGS', silent=True)

#################################
#       Database methods        #
#################################


def connect_db():
    """Connects to the database defined in config."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()



#######################################
#        Basic auth functions     	   #
#######################################

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == app.config['USERNAME'] and password == app.config['PASSWORD']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


#################################
#       String to float         #
#################################
def str_float (data):
    #print data
    data = str(data)
    N = ""
    extract = []
    print "Inside the fun call"
    for x in range(1,len(data)):
        if data[x] == "[":
            x = x + 1
            while data[x] != "]" and data[x] != '\0':
                while data[x] != "," and data[x] != "]":
                    N = N + data[x]
                    #print data[x]
                    x = x + 1
                N = float(N)
                N = round(N,4)
                extract.append(N)
                N = ""
                if data[x] == "]":
                    break
                x = x + 1
    xa=[]
    ya=[]
    yaw=[]
    i = 0
    while (i<=len(extract)-2):
        xa.append(extract[i])
        ya.append(extract[i+1])
        yaw.append(extract[i+2])
        i = i + 3
    d=dict(X=xa,Y=ya,Yaw=yaw)

    return d


#################################
#       Route definitions       #
#################################

@app.route('/records')
def show_records():
    """ Returns a page showing all the records currently in the DB, rendered as a
    nice human readable list.
    """
    db = get_db()
    cur = db.execute('select cpu_ID, display_string, lat, lon, arbitraryText, displacement from records order by id desc')
    records = cur.fetchall()
    return render_template('show_records.html', records=records)

@app.route('/indoor_track')
def show_track():
    """ Returns a page showing all the records currently in the DB, rendered as a
    nice human readable list.
    """
    db = get_db()
    cur = db.execute('select cpu_ID, display_string, lat, lon, arbitraryText, displacement from records order by id desc')
    records = cur.fetchall()
    return render_template('show_track.html', records=records)

@app.route('/')
def show_gsg():
    """ Returns a page showing all the records currently in the DB, rendered as a
    nice human readable list. 
    """
    db = get_db()
    cur = db.execute('select cpu_ID, display_string, lat, lon, arbitraryText, displacement from records order by id desc')
    records = cur.fetchall()
    return render_template('show_records.html', records=records)

@app.route('/map')
def show_map_unique_cpu():
    return render_template('map_unique.html')

# This method uses the python google-maps api to add basic markers to the google map
@app.route('/map_python')
def show_map():
    db = get_db()
    cur = db.execute('select cpu_ID, display_string, lat, lon, arbitraryText from records order by id desc')
    records = cur.fetchall()
    
    # create list of markers from the lat/lng values for each records in the DB
    markerList = []
    for item in records:
        markerList.append((float(item[2]), float(item[3])))
    
    # create the map object
    mymap = Map(
        identifier="mymap",
        lat=-28,
        lng=135,
        zoom=4,
        markers=markerList,
	style="height:600px;width:800px;"
    )

    return render_template('map_python.html', mymap=mymap)

# Handles the various methods for /api/position
# GET: returns JSON list of all the records already in the DB
# POST: accepts positions details sent from the client in JSON format, and inserts them into the SQLite db.
@app.route('/api/position', methods=['GET', 'POST', 'OPTIONS'])
def add_record():
    keys = ('cpu_ID','display_string','lat', 'lon', 'arbitraryText', 'displacement')
    db = get_db()
    if request.method == 'POST':
        jsonData = request.get_json(force=True)
        #print "###################################################Raw data #####################################################"
        #print "REQ DATA", jsonData
        print "###################################################Displacement##################################################"
        #print "Acc", jsonData['displacement']
        displace = str_float(jsonData["displacement"])
        print displace
        print jsonData["displacement"]
        print "Pickle the displacement"
        displace_string = pickle.dumps(displace)
        db.execute('insert into records (cpu_ID, display_string, lat, lon, arbitraryText, time_stamp, displacement) values (?, ?, ?, ?, ?, ?, ?)',
        [jsonData['cpuID'],jsonData['displayString'], jsonData['latitude'], jsonData['longitude'] ,jsonData['arbitraryText'], datetime.datetime.now(), displace_string])
        db.commit()
        #cur = db.execute('select cpu_ID, display_string, lat, lon, arbitraryText, displacement from records order by id desc')
        #records = cur.fetchall()
        #print "Acc in sql: ", dict(zip('displacement', records))
        return '200 OK'
    
    if request.method == 'GET':
        cur = db.execute('select cpu_ID, display_string, lat, lon, arbitraryText, displacement from records order by id desc')
        records = cur.fetchall()
        
        if len(records) > 0:
            outputList = []
            for record in records:
                outputList.append(dict(zip(keys, record)))
                
            # craft response    
            resp2 = Response(json.dumps(outputList),  mimetype='application/json')			
            resp2.headers.add('Access-Control-Allow-Origin', '*')
            return resp2
        else:
            return 'no records posted'

    if request.method == 'OPTIONS':
            resp = make_response()          
            resp.headers.add('Access-Control-Allow-Headers', 'origin, content-type, accept')
            resp.headers.add('Access-Control-Allow-Origin', '*')
            return resp




if __name__ == '__main__':
    #init_db() 
    # Uncommenting the above line will make the server reinitialise the db each time it's run,
    # removing any previous records, leave commented for a persistent DB
    
    app.run(host='0.0.0.0', port=80)  # Make server publicly available on port 80
    #app.run() # Make the server only available locally on port 5000 (127.0.0.1:5000)
