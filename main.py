import datetime
import uuid
import json
import pandas as pd

from flask import Flask, render_template, request, make_response, redirect, jsonify
from flask_cors import CORS
from google.auth.transport import requests
from google.cloud import datastore


app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'
datastore_client = datastore.Client()


with open('data/top_100.json') as f:
    top_100 = json.load(f)


def get_user_from_id(userID):
    key = datastore_client.key('user', int(userID))
    user = datastore_client.get(key)
    return user


def create_new_user():
    entity = datastore.Entity(key=datastore_client.key('user'))
    # FIXME: We need to sort users into groups here.
    entity.update({
        'createdAt': datetime.datetime.now(),
        'testGroup': 'A',
        'selectedMovies': []
    })
    datastore_client.put(entity)
    return entity, entity.key.id


def store_visit(userID, urlSlug):
    entity = datastore.Entity(key=datastore_client.key('visit'))
    entity.update({
        'timestamp': datetime.datetime.now(),
        'userID': userID,
        'urlSlug': urlSlug
    })
    datastore_client.put(entity)


@app.route('/')
def root():
    userID = request.cookies.get("userID")
    if userID:
        user = get_user_from_id(userID)
        id_to_set = False
    else:
        user = create_new_user()
        id_to_set = str(user.id)
    if user is None:
        print("WTF!")

    store_visit(user.id, request.path)

    res = make_response(render_template('index.html', user=user))
    if id_to_set:
        res.set_cookie('userID', id_to_set)
    return res


@app.route('/api/start')
def api_root():
    userID = request.headers.get('userID')
    if userID and int(userID):
        user = get_user_from_id(userID)
    else:
        user, userID = create_new_user()

    store_visit(user.id, request.path)

    user.update({'userID': userID})
    res = jsonify(user)
    return res


@app.route('/api/toplist')
def api_get_top_list():
    return jsonify(top_100)


@app.route('/explainer')
def explainer():
    userID = request.cookies.get("userID")
    if userID:
        user = get_user_from_id(userID)
    else:
        return redirect("/", code=307)
    if user is None:
        return redirect("/", code=307)

    store_visit(user.id, request.path)

    res = make_response(render_template('explainer.html'))
    return res


@app.route('/select', methods=["GET", "POST"])
def select():
    userID = request.cookies.get("userID")
    if userID:
        user = get_user_from_id(userID)
    else:
        return redirect("/", code=307)
    if user is None:
        return redirect("/", code=307)

    store_visit(user.id, request.path)

    res = make_response(
        render_template(
            'select.html',
            top_100=top_100,
            selectedMovies=user.selectedMovies
        )
    )
    return res


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [START gae_python38_render_template]
