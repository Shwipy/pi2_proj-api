from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.user import requires_token
import jwt
import datetime
from functools import wraps

activity_blueprint = Blueprint("activity_blueprint", __name__)

@activity_blueprint.route("/activity", methods=["PUT"])
@activity_blueprint.route("/activity/<quizz_id>", methods=["POST"])
@requires_token
def activity(quizz_id = None):
    try:
        if request.method == "POST":
            return play_quizz(quizz_id)
        
        if request.method == "PUT":
            return end_quizz()

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    
def play_quizz(quizz_id):
    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT duration FROM quizz WHERE id = %s""",[quizz_id])
    results = cursor.fetchone()
    
    if not results:
        return jsonify({"error": "Quizz Index not Found"}),codes.NOT_FOUND

    now = datetime.datetime.now().timestamp()

    time_limit = now + results[0]

    print(time_limit, now)

    token = get_auth_token()
    id = token["id"]

    cursor.execute("""INSERT INTO quizz_activity (time_limit, player_id, quizz_id)
                        VALUES (%s, %s, %s)""",
                    [time_limit, id, quizz_id])
    
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def end_quizz():

    connection = get_connection()
    cursor = connection.cursor()

    token = get_auth_token()
    id = token["id"]

    cursor.execute("""UPDATE quizz_activity
                    SET time_limit = null
                    WHERE player_id = %s""",[id])
    
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})