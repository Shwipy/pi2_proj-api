from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.user import requires_token
import jwt
import datetime
from functools import wraps

item_blueprint = Blueprint("item_blueprint", __name__)

@item_blueprint.route("/kits/<int:kit_id>/items", methods=["POST", "GET"])
@requires_token
def kit_items(kit_id):
    try:

        if request.method == "POST":
            
            return create_item(kit_id)
        
        if request.method == "GET":

            return get_kit_items(kit_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    
@item_blueprint.route("/items/<int:item_id>", methods=["PUT", "GET", "DELETE"])
@requires_token
def item(item_id):
    try:
        if request.method == "GET":
            
            return get_item(item_id)
        
        if request.method == "PUT":
            
            return update_item(item_id)
        
        if request.method == "DELETE":
            
            return delete_item(item_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    


def create_item(kit_id):

    connection, cursor = get_connection()

    token = get_auth_token()
    kituser_id = token["id"]
    
    cursor.execute("""SELECT * FROM kit WHERE id = %s and kituser_id = %s""",[kit_id, kituser_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Kit is not yours"}), codes.NOT_FOUND


    body = get_body()

    if not in_json(body, ["name"]):
        return jsonify({"error": "Missing required fields: (name)"}), codes.BAD_REQUEST
    
    if not in_json(body, ["category_id"]):
        category_id = None
    else:
        category_id = body["category_id"]

    cursor.execute("""INSERT INTO item (item_name, paid, kituser_id, kit_id, category_id)
                        VALUES (%s, false, %s, %s, %s)""",
                    [body["name"], kituser_id, kit_id, category_id])

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def get_kit_items(kit_id):

    connection, cursor = get_connection()

    token = get_auth_token()
    user_id = token["id"]

    cursor.execute("""SELECT kituser_id FROM kit WHERE id = %s""",[kit_id])
    results = cursor.fetchone()
    if user_id != results[0]:
        return jsonify({"error": "Cant view other users kits"}),codes.UNAUTHORIZED

    cursor.execute("""SELECT * FROM item WHERE kit_id = %s""",[kit_id])
    results = cursor.fetchall()

    kits = []
    for result_row in results:
        kits.append({
            "id": result_row[0],
            "item_name": result_row[1],
            "kit_id": result_row[2],
            "category_id": 0,
            "kituser_id": result_row[4],
            "paid": result_row[5]
        })
    
    connection.close()
    cursor.close()

    return jsonify(kits)

def get_item(item_id):
    connection, cursor = get_connection()
        
    cursor.execute("""SELECT item.id, item.item_name, item.category_id, item.kit_id, item.kituser_id, item.paid,
               category.category_name FROM item LEFT JOIN category ON item.category_id = category.id WHERE item.id = %s""",[item_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Item Index not Found"}),codes.NOT_FOUND

    item = {
        "id": results[0],
        "item_name": results[1],
        "category_id": results[2],
        "kit_id": results[3],
        "kituser_id": results[4],
        "paid": results[5],
        "category_name": results[6]
        }
    
    token = get_auth_token()
    id = token["id"]

    if (item["kituser_id"] != id):
        return jsonify({"error": "Can't see another Users Item"}), codes.UNAUTHORIZED
    
    
    connection.close()
    cursor.close()

    return jsonify(item)

def update_item(item_id):

    body = get_body()

    connection, cursor = get_connection()

    cursor.execute("""SELECT * FROM item WHERE id = %s""",[item_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Item not found"}), codes.NOT_FOUND
    
    item = {
        "id": results[0],
        "item_name": results[1],
        "category_id": results[2],
        "kit_id": results[3],
        "kituser_id": results[4],
        "paid": results[5]
    }

    token = get_auth_token()
    if token["id"] != results[4]:
        return jsonify({"error": "Can't update another users item"}), codes.UNAUTHORIZED

    if in_json(body, ["item_name"]):
        item["item_name"] = body["item_name"]

    if in_json(body, ["paid"]):
        item["paid"] = body["paid"]

    cursor.execute("""UPDATE item
                    SET item_name = %s, paid = %s
                    WHERE id = %s""",[item["item_name"], item["paid"], item_id])
    
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})



def delete_item(item_id):
    connection, cursor = get_connection()

    cursor.execute("""SELECT kituser_id FROM item WHERE id = %s""", [item_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Item Index not Found"}),codes.NOT_FOUND

    token = get_auth_token()
    if token["id"] != result[0]:
        return jsonify({"error": "Can't delete another users item"}), codes.UNAUTHORIZED
    

    cursor.execute("""DELETE FROM item WHERE id = %s""", [item_id])
    connection.commit()
    
    connection.close()
    cursor.close()

    return jsonify({"message": "OK"})
