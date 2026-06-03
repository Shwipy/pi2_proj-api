from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.user import requires_token
import jwt
import datetime
from functools import wraps

kit_blueprint = Blueprint("kit_blueprint", __name__)

@kit_blueprint.route("/kits", methods=["POST", "GET"])
@kit_blueprint.route("/kits/<kit_id>", methods=["PUT", "GET", "DELETE"])
@requires_token
def kits(kit_id = None):
    try:

        if request.method == "POST":
            token = get_auth_token()
            id = token["id"]
            
            return create_kit(id)
        
        if request.method == "PUT":
            
            return update_kit(kit_id)
        
        if request.method == "GET":
            id = request.args.get("id")
            
            if kit_id is not None:
                return get_single(kit_id)
                
            if id:
               return get_from_user(id)

            return get_all()

        if request.method == "DELETE":
            return delete_kit_blueprint(kit_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR

def create_kit(kituser_id):

    body = get_body()

    if not in_json(body, ["name"]):
        return jsonify({"error": "Missing required fields: (name)"}), codes.BAD_REQUEST

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""INSERT INTO kit (kit_name, payed, kituser_id)
                        VALUES (%s, false, %s)""",
                    [body["name"], kituser_id])

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def update_kit(kit_id):

    body = get_body()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM kit WHERE id = %s""",[kit_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "kit not found"}), codes.NOT_FOUND
    
    kit = {
        "title": results[1],
        "description": results[2],
        "duration": results[3]
    }

    token = get_auth_token()
    if token["id"] != results[4]:
        return jsonify({"error": "Can't update another user kit"}), codes.UNAUTHORIZED

    if in_json(body, ["title"]):
        kit["title"] = body["title"]

    if in_json(body, ["description"]):
        kit["description"] = body["description"]    
    
    if in_json(body, ["duration"]):
        kit["duration"] = body["duration"] 

    cursor.execute("""UPDATE kit
                    SET title = %s, description = %s, duration = %s
                    WHERE id = %s""",[kit["title"], kit["description"], kit["duration"], kit_id])
    
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def get_all():
    token = get_auth_token()
    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM kit_blueprint ORDER BY id""")
    results = cursor.fetchall()
    
    quizes = []
    for result_row in results:
        quizes.append({
            "id": result_row[0],
            "title": result_row[1],
            "description": result_row[2],
            "duration": result_row[3],
            "kituser_id": result_row[4],
            "owned": result_row[4] == token["id"]
        })
    
    return jsonify(quizes)

def get_from_user(id):

    token = get_auth_token()
    
    if str(token["id"]) != id:
        return jsonify({"error": "Can't see another Users Kits"}), codes.UNAUTHORIZED

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM kit WHERE kituser_id = %s ORDER BY id""",id)
    results = cursor.fetchall()

    if not results:
        return jsonify({"error": "Kit Index not Found"}),codes.BAD_REQUEST
    
    kits = []
    for result_row in results:
        kits.append({
            "id": result_row[0],
            "kit_name": result_row[1],
            "kituser_id": result_row[2]
        })
    
    return jsonify(kits)

def get_single(kit_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM kit WHERE id = %s""",[kit_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "kit Index not Found"}),codes.NOT_FOUND

    kit = {
        "id": results[0],
        "name": results[1],
        "payed": results[2],
        "kituser_id": results[3]
        }
    
    return jsonify(kit)

def delete_kit_blueprint(kit_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT kituser_id FROM kit WHERE id = %s""", [kit_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "kit Index not Found"}),codes.NOT_FOUND

    token = get_auth_token()
    if token["id"] != result[0]:
        return jsonify({"error": "Can't delete another user kit"}), codes.UNAUTHORIZED
    

    cursor.execute("""DELETE FROM kit WHERE id = %s""", [kit_id])
    connection.commit()
    
    return jsonify({"message": "OK"})
