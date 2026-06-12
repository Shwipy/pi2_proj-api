from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.user import requires_token
import jwt
import datetime
from functools import wraps

kit_blueprint = Blueprint("kit_blueprint", __name__)

@kit_blueprint.route("/kits", methods=["POST", "GET"])
@kit_blueprint.route("/kits/<int:kit_id>", methods=["PUT", "GET", "DELETE"])
#@kit_blueprint.route("/kits/<int:kit_id>", methods=["PUT", "GET", "DELETE"])
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
            
            if kit_id is not None:
                return get_single(kit_id)

            return get_from_user()


        if request.method == "DELETE":
            return delete_kit(kit_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR

def create_kit(kituser_id):

    body = get_body()

    if not in_json(body, ["name"]):
        return jsonify({"error": "Missing required fields: (name)"}), codes.BAD_REQUEST

    connection, cursor = get_connection()

    cursor.execute("""INSERT INTO kit (kit_name, kituser_id)
                        VALUES (%s, %s)""",
                    [body["name"], kituser_id])

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def update_kit(kit_id):

    body = get_body()

    connection, cursor = get_connection()

    cursor.execute("""SELECT * FROM kit WHERE id = %s""",[kit_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "kit not found"}), codes.NOT_FOUND
    
    kit = {
        "id": results[0],
        "kit_name": results[1],
        "kituser_id": results[2]
    }

    token = get_auth_token()
    if token["id"] != results[2]:
        return jsonify({"error": "Can't update another user kit"}), codes.UNAUTHORIZED

    if in_json(body, ["kit_name"]):
        kit["kit_name"] = body["kit_name"]

    cursor.execute("""UPDATE kit
                    SET kit_name = %s
                    WHERE id = %s""",[kit["kit_name"], kit_id])
    
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def get_from_user():

    connection, cursor = get_connection()

    token = get_auth_token()
    id = token["id"]

    cursor.execute("""SELECT * FROM kit WHERE kituser_id = %s ORDER BY id""",[id])
    results = cursor.fetchall()
    
    kits = []
    for result_row in results:
        kits.append({
            "id": result_row[0],
            "kit_name": result_row[1],
            "kituser_id": result_row[2]
        })
    
    connection.close()
    cursor.close()

    return jsonify(kits)

def get_single(kit_id):
    connection, cursor = get_connection()
        
    cursor.execute("""SELECT * FROM kit WHERE id = %s""",[kit_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "kit Index not Found"}),codes.NOT_FOUND

    kit = {
        "id": results[0],
        "name": results[1],
        "kituser_id": results[2]
        }
    
    token = get_auth_token()
    id = token["id"]

    if (kit["kituser_id"] != id):
        return jsonify({"error": "Can't see another Users Kits"}), codes.UNAUTHORIZED
    
    
    connection.close()
    cursor.close()

    return jsonify(kit)

def delete_kit(kit_id):
    connection, cursor = get_connection()

    cursor.execute("""SELECT kituser_id FROM kit WHERE id = %s""", [kit_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "kit Index not Found"}),codes.NOT_FOUND

    token = get_auth_token()
    if token["id"] != result[0]:
        return jsonify({"error": "Can't delete another user kit"}), codes.UNAUTHORIZED
    

    cursor.execute("""DELETE FROM kit WHERE id = %s""", [kit_id])
    connection.commit()
    
    connection.close()
    cursor.close()

    return jsonify({"message": "OK"})
