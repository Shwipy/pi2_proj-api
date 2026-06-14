from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.user import requires_token
import jwt
import datetime
from functools import wraps

category_blueprint = Blueprint("category_blueprint", __name__)

@category_blueprint.route("/items/<int:item_id>/category<int:category_id>", methods=["POST", "GET"])
@requires_token
def category_items(kit_id,category_id):
    try:

        if request.method == "POST":
            
            return add_category_item(kit_id)
        
        if request.method == "GET":

            return get_category_items(kit_id, category_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    
@category_blueprint.route("/categories/", methods=["POST","GET"])
@category_blueprint.route("/categories/<int:category_id>", methods=["PUT", "GET", "DELETE"])
@requires_token
def category(category_id = None):
    try:
        if request.method == "POST":
            
            return create_category()
        
        if request.method == "GET":
            if get_category is not None:
                return get_category(category_id)
            
            return get_categories()
        
        if request.method == "PUT":
            
            return update_category(category_id)
        
        if request.method == "DELETE":
            return delete_category(category_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    


def create_category():

    token = get_auth_token()
    kituser_id = token["id"]

    body = get_body()

    if not in_json(body, ["category_name"]):
        return jsonify({"error": "Missing required fields: (category_name)"}), codes.BAD_REQUEST

    connection, cursor = get_connection()

    cursor.execute("""INSERT INTO category (category_name, kituser_id)
                        VALUES (%s, %s)""",
                    [body["category_name"], kituser_id])

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def get_categories():
    token = get_auth_token()
    id = token["id"]
    connection, cursor = get_connection()
        
    cursor.execute("""SELECT * FROM category WHERE kituser_id = %s""",[id])
    results = cursor.fetchall()

    categories = []
    for result_row in results:
        categories.append({
            "id": result_row[0],
            "category_name": result_row[1],
            "kituser_id": result_row[2]
        })
    
    connection.close()
    cursor.close()

    return jsonify(categories)

def get_category(category_id):

    connection, cursor = get_connection()
    cursor.execute("""SELECT * FROM category WHERE id = %s""",[category_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Category not found"}), codes.NOT_FOUND
    
    category = {
        "id": results[0],
        "category_name": results[1],
        "kituser_id": results[2]
    }

    cursor.close()
    connection.close()

    return jsonify(category)

def update_category(category_id):
    
    body = get_body()
    connection, cursor = get_connection()
    cursor.execute("""SELECT * FROM category WHERE id = %s""",[category_id])
    results = cursor.fetchone()

    if not results:
        return jsonify({"error": "Category not found"}), codes.NOT_FOUND
    
    category = {
        "id": results[0],
        "category_name": results[1],
        "kituser_id": results[2]
    }

    token = get_auth_token()
    if token["id"] != results[2]:
        return jsonify({"error": "Can't update another users category"}), codes.UNAUTHORIZED

    if in_json(body, ["category_name"]):
        category["category_name"] = body["category_name"]

    cursor.execute("""UPDATE category
                    SET category_name = %s
                    WHERE id = %s""",[category["category_name"], category_id])
    
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def delete_category(category_id):
    connection, cursor = get_connection()

    cursor.execute("""SELECT kituser_id FROM category WHERE id = %s""", [category_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Item Index not Found"}),codes.NOT_FOUND

    token = get_auth_token()
    if token["id"] != result[0]:
        return jsonify({"error": "Can't delete another users item"}), codes.UNAUTHORIZED
    

    cursor.execute("""DELETE FROM category WHERE id = %s""", [category_id])
    connection.commit()
    
    connection.close()
    cursor.close()

    return jsonify({"message": "OK"})
#------------------------------------------------------------------------------------------------

def get_category_items(kit_id):

    connection, cursor = get_connection()

    token = get_auth_token()
    id = token["id"]

    

    cursor.execute("""SELECT * FROM item WHERE kit_id = %s and kituser_id = %s ORDER BY id""",[kit_id, id])
    results = cursor.fetchall()

    if not results:
        return jsonify({"error": "kit Index not Found"}),codes.NOT_FOUND

    
    kits = []
    for result_row in results:
        kits.append({
            "id": result_row[0],
            "kit_name": result_row[1],
            "kit_id": result_row[2],
            "kituser_id": result_row[3],
            "paid": result_row[4]
        })
    
    connection.close()
    cursor.close()

    return jsonify(kits)


