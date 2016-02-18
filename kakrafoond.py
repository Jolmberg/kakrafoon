#!/usr/bin/python3

from flask import Flask, request
app = Flask(__name__)

@app.route('/queue', methods=['POST'])
def queue():
    to_play = []
    for id in request.files:
        file = request.files[id]
        if id.startswith('f') and id[1:].isdigit():
            file.save('/tmp/' + id)
            to_play.append(id)

    print(to_play)
    return 'apa'

if __name__ == '__main__':
    app.run()
