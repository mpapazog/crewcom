# This is a Python 3 script that creates a simple browser-based communication system for video crews.
#  The person sitting at the streamer/mixing console views the main communications console for requests
#  by crew memebers. The crew members can request to be on the stream by pressing one button on their
#  web browsers.
#
# The script creates two web pages:
#  * http://server_ip/index     : This is the main communications console panel
#  * http://server_ip/remote    : This is the web page that should be opened by the remote crew member
#
# How to run the script:
#  python crewcom.py [-p <port>] [-d <dbfile path>]
#
# Command line parameters:
#  -p <port>            : Optional. Define which TCP port to run the server on. Default is 80.
#  -d <dbfile path>     : Optional. Specify a database file path. Default is 'crewcom.sqlite3'.
#
# Notes:
#  * This script was built for Python 3.7.1.
#  * Depending on your operating system, the command to start python can be either "python" or "python3". 
# 
# Required Python modules:
#  Flask        : http://flask.pocoo.org/  
#
# After installing Python, you can install these additional modules using pip with the following commands:
#  pip install flask
#
# Depending on your operating system, the command can be "pip3" instead of "pip".
#
# Last modified on 2018-12-12 by Mihail Papazoglou

import sys, getopt, os, sqlite3
from flask import Flask, jsonify, render_template, request, url_for

#SECTION: GLOBAL VARIABLES: MODIFY TO CHANGE SCRIPT BEHAVIOUR

#Default database file path
ARG_DBFILE  = 'crewcom.sqlite3'

#SECTION: GLOBAL VARIABLES: DO NOT MODIFY
CREW_STATUS = []

#SECTION: Flask web server definitions and functions  
    
class c_NodeData():
    def __init__(self):
        self.name       = ''
        self.id         = ''    
   
def loadnodes():
    try:
        db = sqlite3.connect(ARG_DBFILE)
        cursor = db.cursor()
        cursor.execute('''SELECT id, name from nodes''')
        fetched = cursor.fetchall()
        db.close()
    except getopt.GetoptError:
        print('Error connecting to database (5)')
        sys.exit(2)

    nodes = []
    for node in fetched:
        nodes.append( c_NodeData())
        nodes[len(nodes)-1].id   = node[0]
        nodes[len(nodes)-1].name = node[1]
        
    return(nodes)
   
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'awesome-crew-comms-script' 

@app.route("/", methods=['GET']) 

@app.route("/index/", methods=['GET'])
def index():
    return render_template('index.html', nodes=loadnodes())
    
@app.route("/remote/", methods=['GET'])
def remote():
    return render_template('remote.html', nodes=loadnodes())
    
@app.route("/crewstatus/", methods=['GET'])
def crewstatus():
    return jsonify(CREW_STATUS)
    
@app.route("/crewadd/", methods=['GET'])
def crewadd():
    global CREW_STATUS
    name = request.args.get('name')
    
    try:
        db = sqlite3.connect(ARG_DBFILE)
        cursor = db.cursor()
        cursor.execute('''INSERT INTO nodes(name) VALUES (?)''', (name,))
        db.commit()
        cursor.execute('''SELECT id FROM nodes''')
        fetched = cursor.fetchall()
        CREW_STATUS = []
        for item in fetched:
            CREW_STATUS.append({'id':item[0], 'status':'offline', 'requestingToggle':'false'})
        db.close()
    except getopt.GetoptError:
        print('Error connecting to database (4)')
        sys.exit(2)
        
    return jsonify({'status':'ok'})
    
@app.route("/crewdelete/", methods=['GET'])
def crewdelete():
    global CREW_STATUS
    id = request.args.get('id')
    
    try:
        db = sqlite3.connect(ARG_DBFILE)
        cursor = db.cursor()
        cursor.execute('''DELETE FROM nodes WHERE id=(?)''', (id,))
        db.commit()
        cursor.execute('''SELECT id FROM nodes''')
        fetched = cursor.fetchall()
        CREW_STATUS = []
        for item in fetched:
            CREW_STATUS.append({'id':item[0], 'status':'offline', 'requestingToggle':'false'})
        db.close()
    except getopt.GetoptError:
        print('Error connecting to database (3)')
        sys.exit(2)
    
    return jsonify({'status':'ok'})
    
    
@app.route("/mystatus/", methods=['GET'])
def mystatus():
    retvalue = []
    id = request.args.get('id')
    for line in CREW_STATUS:
        if str(line['id']) == id:
            retvalue = line
            break
    return jsonify(retvalue)
    
@app.route("/resetstatus/", methods=['GET'])
def resetstatus():
    global CREW_STATUS
    
    id = request.args.get('id')
    retvalue = 'none'
    for line in CREW_STATUS:
        if str(line['id']) == id:
            if line['status'] == 'online':
                line['status'] = 'offline'
                line['requestingToggle'] = 'false'
                retvalue = 'offline'
            else:
                line['status'] = 'online'
                line['requestingToggle'] = 'false'
                retvalue = 'online'
            break
    return jsonify({'result':retvalue})
    
@app.route("/requesttoggle/", methods=['GET'])
def requesttoggle():
    global CREW_STATUS
    
    id = request.args.get('id')
    for line in CREW_STATUS:
        if str(line['id']) == id:
            line['requestingToggle'] = 'true'
            break
    return jsonify({'result':'success'})
    
@app.route("/edit_team/", methods=['GET'])
def edit_team():    
    return render_template('edit_team.html', nodes=loadnodes())

@app.route("/debug_log/", methods=['GET'])
def log():
    data = request.args.get('data')
    print(data)
    return jsonify({'result':'success'}) 
    
    
#SECTION: main
    
def main(argv):
    global ARG_DBFILE
    global CREW_STATUS
    
    #initialize local command line arguments
    arg_port    = '80'
    
    #get command line arguments
    try:
        opts, args = getopt.getopt(argv, 'p:d:')
    except getopt.GetoptError:
        print('Error parsing options (2)')
        sys.exit(2)
        
    for opt, arg in opts:
        if   opt == '-p':
            arg_port   = arg
        elif opt == '-d':
            ARG_DBFILE = arg
            
    try:
        db = sqlite3.connect(ARG_DBFILE)
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS 
                nodes(id INTEGER PRIMARY KEY, name TEXT)''')
        db.commit()
        cursor.execute('''SELECT id FROM nodes''')
        fetched = cursor.fetchall()
        for item in fetched:
            CREW_STATUS.append({'id':item[0], 'status':'offline', 'requestingToggle':'false'})
        db.close()
    except getopt.GetoptError:
        print('Error initializing database (1)')
        sys.exit(2)
             
    app.run(host='0.0.0.0', port=arg_port)    
    
if __name__ == '__main__':
    main(sys.argv[1:])