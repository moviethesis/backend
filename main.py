import datetime
import uuid
import json
import pandas as pd
import os
from os import listdir
from os.path import isfile, join

from flask import Flask, render_template, request, make_response, redirect, jsonify
from flask_cors import CORS
from google.auth.transport import requests
from google.cloud import datastore


app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'
datastore_client = datastore.Client()


with open('data/top_list.json') as f:
    top_list_json = json.load(f)


def get_user_from_id(userID):
    key = datastore_client.key('user', int(userID))
    user = datastore_client.get(key)
    return user


def create_new_user():
    entity = datastore.Entity(key=datastore_client.key('user'))
    testGroup = get_and_create_group()
    entity.update({
        'createdAt': datetime.datetime.now(),
        'testGroup': testGroup,
        'selectedMovies': [],
        'country': 'NaN',
        'age': 0,
        'gender': 'NaN',
        'education': 'NaN',
        'work': 'NaN',
        'techknow': 'NaN',
        'useForRecommendations': True,
        'useForImprovementsForOthers': True,
        'useForSharing': True,
    })
    datastore_client.put(entity)
    return entity, entity.key.id


def add_profilic(user, PROLIFIC_PID, STUDY_ID, SESSION_ID):
    user.update({
        'PROLIFIC_PID': PROLIFIC_PID,
        'STUDY_ID': STUDY_ID,
        'SESSION_ID': SESSION_ID
    })
    datastore_client.put(user)
    return user


def update_user(user, body):
    user.update({
        'country': body.get("country"),
        'age': body.get("age"),
        'gender': body.get("gender"),
        'education': body.get("education"),
        'work': body.get("work"),
        'techknow': body.get("techknow"),
        'completedAt': datetime.datetime.now()
    })
    datastore_client.put(user)
    return user


def update_data_control(user, body):
    user.update({
        'useForRecommendations': body.get("useForRecommendations"),
        'useForImprovementsForOthers': body.get("useForImprovementsForOthers"),
        'useForSharing': body.get("useForSharing"),
    })
    datastore_client.put(user)
    return user


def weighted_rating(r, v, c, m):
    return ((r * v) + (c * m)) / (v + m)


def get_score(x):
    return x.get("wr")


# Scenario 1 [a] (Nontransparent and No user control)
# Scenario 2 [b] (Nontransparent and User control)
# Scenario 3 [c] (Transparent and No user control)
# Scenario 4 [d] (Transparent and User control)
def get_and_create_group():
    keyA = datastore_client.key('testGroup', 'a')
    a = datastore_client.get(keyA)
    keyB = datastore_client.key('testGroup', 'b')
    b = datastore_client.get(keyB)
    keyC = datastore_client.key('testGroup', 'c')
    c = datastore_client.get(keyC)
    keyD = datastore_client.key('testGroup', 'd')
    d = datastore_client.get(keyD)

    dict = {
        'a': a.get("count"),
        'b': b.get("count"),
        'c': c.get("count"),
        'd': d.get("count")
    }
    sorted_dict = sorted(dict.items(), key=lambda x: x[1], reverse=False)
    testGroup = sorted_dict[0][0] # get the group with least count and update
    testGroupCount = sorted_dict[0][1]
    testGroupCount += 1
    entity = datastore_client.get(datastore_client.key('testGroup', testGroup))
    entity.update({'count': testGroupCount})
    datastore_client.put(entity)
    return testGroup


def increment_start_count():
    key = datastore_client.key('testGroup', 'totalStart')
    count = datastore_client.get(key)
    newCount = count.get("count")
    newCount += 1
    count.update({'count': newCount})
    datastore_client.put(count)


def increment_finish_count():
    key = datastore_client.key('testGroup', 'totalFinish')
    count = datastore_client.get(key)
    newCount = count.get("count")
    newCount += 1
    count.update({'count': newCount})
    datastore_client.put(count)


def store_selection(entity, selection):
    entity.update({
        'selectedMovies': selection
    })
    datastore_client.put(entity)


def store_survey(user, survey):
    user.update({
        'q0': survey.get("q0"),
        'q1': survey.get("q1"),
        'q2': survey.get("q2"),
        'q3': survey.get("q3"),
        'q4': survey.get("q4"),
        'q5': survey.get("q5"),
        'q6': survey.get("q6"),
        'q7': survey.get("q7"),
        'q8': survey.get("q8"),
        'q9': survey.get("q9"),
        'q10': survey.get("q10"),
        'q11': survey.get("q11"),
        'q12': survey.get("q12"),
        'q13': survey.get("q13"),
        'q14': survey.get("q14"),
        'q15': survey.get("q15"),
        'q16': survey.get("q16")
    })
    datastore_client.put(user)


@app.route('/')
def root():
    userID = request.headers.get('userID')
    user = 0
    if userID and int(userID):
        user = get_user_from_id(userID)
    if user == 0:
        user, userID = create_new_user()
        increment_start_count()
    if user is None:
        user, userID = create_new_user()
        increment_start_count()

    user.update({'userID': userID})
    res = jsonify(user)
    return res


@app.route('/toplist')
def top_list():
    return jsonify(top_list_json)


@app.route('/generate-data')
def gendata():
    if not app.debug:
        return jsonify("NO!")

    query = datastore_client.query(kind='user')
    kinds = [entity for entity in query.fetch()]
    data  = jsonify(kinds)
    return data

@app.route('/update-from-explainer', methods=["POST"])
def profilic():
    userID = request.headers.get('userID')
    if userID and int(userID):
        user = get_user_from_id(userID)
    else:
        # do errror handling
        return jsonify("ERROR COULD NOT FIND USER")

    body = request.get_json()
    print(body)
    PROLIFIC_PID = body.get("PROLIFIC_PID")
    STUDY_ID = body.get("STUDY_ID")
    SESSION_ID = body.get("SESSION_ID")
    if PROLIFIC_PID and STUDY_ID and SESSION_ID:
        user = add_profilic(user, PROLIFIC_PID, STUDY_ID, SESSION_ID)

    dataControl = body.get("dataControl")
    user = update_data_control(user, dataControl)

    user.update({'userID': userID})
    res = jsonify(user)
    return res


@app.route('/recommend', methods=["POST"])
def recommend():
    userID = request.headers.get('userID')
    if userID and int(userID):
        user = get_user_from_id(userID)
    else:
        # do errror handling
        return jsonify("ERROR COULD NOT FIND USER")
    if user is None:
        return jsonify("ERROR COULD NOT FIND USER")

    selected_movies = request.get_json().get('selectedMovies')
    if selected_movies:
        # if we have some selected movies in the body, we update the user and
        # get recommendations
        store_selection(user, selected_movies)
    elif not user.get('selectedMovies'):
        # if we do not have any in body, we load it from the user, and if not
        # throw error
        return jsonify("ERROR COULD NOT FIND ANY USER SELECTED MOVIES")

    selected_movies = user.get('selectedMovies')
    # we limit the calculation to max 25 => save compute time
    selected_movies = selected_movies[0:25]

    json_res = {}
    json_res['selected_movies_count'] = len(selected_movies)
    json_res['rec_list'] = {}

    selected_movies_ids = [x.get("movieId") for x in selected_movies]
    all_ratings = []

    for m in selected_movies:
        # load recommendations for a given movie
        movie_id = m.get("movieId")
        with open('data/recs/{}_recs.json'.format(movie_id)) as f:
            recs = json.load(f)

        # loop trough the top 5 movie recs (not 10 to save resources)
        for r in recs:
            r_movie_id = r.get("movieId")
            # if the movie is already in the rec list, add it and increment count
            if json_res['rec_list'].get(r_movie_id):
                json_res['rec_list'][r_movie_id]["based_on_count"] += 1
                json_res['rec_list'][r_movie_id]["based_on"].append({
                    "movie_id": movie_id,
                    "title": m.get("title"),
                    "sim_score": r.get("average_similarity_score"),
                    "poster_path": m.get("poster_path")
                })
                all_ratings.append(r.get("average_similarity_score"))

            elif r_movie_id in selected_movies_ids:
                # if the movie is already a selected movie, we should not recommend
                continue

            else:
                # create the rec in the rec list if not already present
                json_res['rec_list'][r_movie_id] = {}
                json_res['rec_list'][r_movie_id]["movie"] = {
                    "movie_id": r_movie_id,
                    "title": r.get("title"),
                    "poster_path": r.get("poster_path")
                }
                json_res['rec_list'][r_movie_id]["based_on_count"] = 1
                json_res['rec_list'][r_movie_id]["based_on"] = []
                json_res['rec_list'][r_movie_id]["based_on"].append({
                    "movie_id": movie_id,
                    "title": m.get("title"),
                    "sim_score": r.get("average_similarity_score"),
                    "poster_path": m.get("poster_path")
                })
                all_ratings.append(r.get("average_similarity_score"))

    avg_ratings = sum(all_ratings) / len(all_ratings)
    for key, r in json_res['rec_list'].items():
        count = r.get("based_on_count")
        based_on = r.get("based_on")
        scores = [x.get("sim_score") for x in based_on]
        scores_avg = sum(scores) / count
        wr = weighted_rating(scores_avg, count, avg_ratings, 1)
        json_res['rec_list'][key]["wr"] = wr

    json_res['rec_list'] = [json_res['rec_list'][x] for x in json_res['rec_list']]
    json_res['rec_list'].sort(key=get_score, reverse=True)
    json_res['rec_list'] = json_res['rec_list'][0:12]

    json_res['user'] = user
    json_res["rec_list_count"] = len(json_res["rec_list"])

    res = jsonify(json_res)
    return res


@app.route('/update', methods=["POST"])
def updateSurveyPost():
    userID = request.headers.get('userID')
    if userID and int(userID):
        user = get_user_from_id(userID)
    else:
        # do errror handling
        return jsonify("ERROR COULD NOT FIND USER")
    if user is None:
        return jsonify("ERROR COULD NOT FIND USER")

    body = request.get_json()
    survey = body.get('survey')
    if survey is None:
        return jsonify("ERROR COULD NOT FIND SURVEY DATA")

    store_survey(user, survey)
    user = update_user(user, body)
    user.update({'userID': userID})
    res = jsonify(user)

    increment_finish_count()
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
