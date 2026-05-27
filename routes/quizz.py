from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.player import requires_token
import jwt
import datetime
from functools import wraps

quizz_blueprint = Blueprint("quizz_blueprint", __name__)

@quizz_blueprint.route("/quizes", methods=["POST", "GET"])
@quizz_blueprint.route("/quizes/<quizz_id>", methods=["PUT", "GET", "DELETE"])
@requires_token
def quizes(quizz_id = None):
    try:

        if request.method == "POST":
            token = get_auth_token()
            id = token["id"]
            
            return create_quizz(id)
        
        if request.method == "PUT":
            
            return update_quizz(quizz_id)
        
        if request.method == "GET":
            #id = request.args.get("id")
            
            if quizz_id is not None:
                return get_single(quizz_id)
                
            #if id:
            #    return get_from_player(id)

            return get_all()

        if request.method == "DELETE":
            return delete_quizz(quizz_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR

def create_quizz(player_id):

    body = get_body()

    if not in_json(body, ["title", "description", "duration"]):
        return jsonify({"error": "Missing required fields: (title, description, duration)"}), codes.BAD_REQUEST

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""INSERT INTO quizz (title, description, duration, player_id)
                        VALUES (%s, %s, %s, %s)""",
                    [body["title"], body["description"], body["duration"], player_id])

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def update_quizz(quizz_id):

    body = get_body()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM quizz WHERE id = %s""",[quizz_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Quizz not found"}), codes.NOT_FOUND
    
    quizz = {
        "title": results[1],
        "description": results[2],
        "duration": results[3]
    }

    token = get_auth_token()
    if token["id"] != results[4]:
        return jsonify({"error": "Can't update another user quizz"}), codes.UNAUTHORIZED

    if in_json(body, ["title"]):
        quizz["title"] = body["title"]

    if in_json(body, ["description"]):
        quizz["description"] = body["description"]    
    
    if in_json(body, ["duration"]):
        quizz["duration"] = body["duration"] 

    cursor.execute("""UPDATE quizz
                    SET title = %s, description = %s, duration = %s
                    WHERE id = %s""",[quizz["title"], quizz["description"], quizz["duration"], quizz_id])
    
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def get_all():
    token = get_auth_token()
    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM quizz ORDER BY id""")
    results = cursor.fetchall()
    
    quizes = []
    for result_row in results:
        quizes.append({
            "id": result_row[0],
            "title": result_row[1],
            "description": result_row[2],
            "duration": result_row[3],
            "player_id": result_row[4],
            "owned": result_row[4] == token["id"]
        })
    
    return jsonify(quizes)

#def get_from_player(id):
#
#    token = get_auth_token()
#    
#    if str(token["id"]) != id:
#        return jsonify({"error": "Can't see another Users quizes"}), codes.UNAUTHORIZED
#
#    connection = get_connection()
#    cursor = connection.cursor()
#
#    cursor.execute("""SELECT * FROM quizz WHERE player_id = %s ORDER BY id""",id)
#    results = cursor.fetchall()
#
#    if not results:
#        return jsonify({"error": "Quizz Index not Found"}),codes.BAD_REQUEST
#    
#    quizes = []
#    for result_row in results:
#        quizes.append({
#            "id": result_row[0],
#            "title": result_row[1],
#            "description": result_row[2],
#            "duration": result_row[3],
#            "player_id": results[4]
#        })
#    
#    return jsonify(quizes)

def get_single(quizz_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM quizz WHERE id = %s""",[quizz_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Quizz Index not Found"}),codes.NOT_FOUND

    quiz = {
        "id": results[0],
        "title": results[1],
        "description": results[2],
        "duration": results[3],
        "player_id": results[4]
        }
    
    return jsonify(quiz)

def delete_quizz(quizz_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT player_id FROM quizz WHERE id = %s""", [quizz_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Quizz Index not Found"}),codes.NOT_FOUND

    token = get_auth_token()
    if token["id"] != result[0]:
        return jsonify({"error": "Can't delete another user quizz"}), codes.UNAUTHORIZED
    
    now = datetime.datetime.now().timestamp()
    print(now)
    cursor.execute("""SELECT time_limit FROM quizz_activity WHERE quizz_id = %s AND time_limit > %s""", [quizz_id, now])
    result = cursor.fetchall()

    if result:
        return jsonify({"error": "Quizz está a ser jogado"}),codes.CONFLICT

    cursor.execute("""DELETE FROM quizz WHERE id = %s""", [quizz_id])
    connection.commit()
    
    return jsonify({"message": "OK"})
