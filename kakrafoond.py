#!/usr/bin/python3

from flask import Flask, request
app = Flask(__name__)

@app.route('/queue', methods=['POST'])
def queue_add():
    to_play = []
    print(request.form['json'])
    for id in request.files:
        file = request.files[id]
        if id.startswith('f') and id[1:].isdigit():
            file.save('/tmp/' + id)
            to_play.append(id)

    print(to_play)
    return 'apa'

@app.route('/queue/<qid>', methods=['DELETE'])
def queue_delete(qid):
    print('Deleting item ' + qid + ' from queue.')

if __name__ == '__main__':
    app.run()
