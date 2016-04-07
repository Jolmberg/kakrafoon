#!/usr/bin/python3

import uuid
import os
import kakmsg
from flask import Flask, request
app = Flask(__name__)

@app.route('/queue', methods=['POST'])
def queue_add():
    request_id = str(uuid.uuid4())
    to_play = []
    if 'json' in request.form:
        schema = kakmsg.EnqueueRequestSchema()
        print(request.form['json'])
        json = schema.loads(request.form['json']).data
    else:
        json = None

    files = {}
    if request.files:
        path = os.path.join('/tmp/', request_id)
        os.mkdir(path)
        for id in request.files:
            file = request.files[id]
            filename = os.path.split(file.filename)[1]
            if id.startswith('f') and id[1:].isdigit():
                id_no = int(id[1:])
                fpath = os.path.join(path, filename)
                file.save(fpath)
                files[id_no] = fpath

    print(json)
    print(files)
    return 'apa'

@app.route('/queue/<qid>', methods=['DELETE'])
def queue_delete(qid):
    print('Deleting item ' + qid + ' from queue.')

if __name__ == '__main__':
    app.debug=True
    app.run()
