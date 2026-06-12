from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from functools import wraps
import datetime
import bcrypt
import jwt
import os

user_blueprint = Blueprint("user_blueprint", __name__)


def requires_token(f):
    """
    This function is a wrapper for the Authorization.
    It gets the `Authorization` header and reads the token. If the token is not sent, valid or has expired
    it returns a error
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        if not get_auth_header():
            return jsonify({"error": "Missing authorization token"}), codes.BAD_REQUEST

        token = get_auth_token()

        if not token:
            return jsonify({"error": "Wrong token type. Must send 'Bearer {token}'"})

        expire_date = datetime.datetime.fromtimestamp(
            token["expire_date"]).timestamp()
        current_date = datetime.datetime.now().timestamp()

        if expire_date < current_date:
            return jsonify({"error": "Token has expired"}), codes.BAD_REQUEST

        connection, cursor = get_connection()
       
        cursor.execute("""SELECT user_name FROM kituser WHERE id = %s""",
                       [get_auth_token()["id"]])
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "User doesn't exist"})

        connection.close()
        cursor.close()

        return f(*args, **kwargs)

    return decorator


@user_blueprint.route("/login", methods=["POST"])
def login():
    try:
        if request.method == "POST":

            body = get_body()

            if not in_json(body, ["name", "password"]):
                return jsonify({"error": "Missing required fields: (name, password)"}), codes.BAD_REQUEST
            
            username = body["name"].strip().lower()

            connection, cursor = get_connection()

            cursor.execute("""SELECT id, password FROM kituser WHERE user_name = %s""",[username])
            result = cursor.fetchone()

            if result is None:
                return jsonify({"error": "User not Found"}), codes.NOT_FOUND 
            
            id, db_password_hash = result  

            user_password_bytes = body["password"].encode("utf-8")
            db_bytes = db_password_hash.encode("utf-8")

            password_correct = bcrypt.checkpw(user_password_bytes, db_bytes )

            if not password_correct:
                return jsonify({"message": "Password Incorrect"}), codes.UNAUTHORIZED

            token = jwt.encode({
                "id": id,
                "expire_date": (datetime.datetime.now() + datetime.timedelta(minutes = 999)).timestamp()
            }, os.getenv("TOKEN_KEY")).decode()

            connection.close()
            cursor.close()

            return jsonify({"token": token})
    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR


@user_blueprint.route("/token", methods=["PUT"])
@requires_token
def token():
    """
    Tries to login with the required token. 
    If it's still not expired it will return a renewed token with another expire date
    """

    try:
        token = get_auth_token()

        renewed_token = jwt.encode({
            "id": token["id"],
            #Comentario para não me esquecer de mudar o tempo de vida do token para um valor ok, pq estou farto de receber token expired... :C
            "expire_date": (datetime.datetime.now() + datetime.timedelta(minutes = 999)).timestamp()
        }, os.getenv("TOKEN_KEY")).decode()

        return jsonify({"token": renewed_token})

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR

@user_blueprint.route("/register", methods=["POST"])
def register():
    try:
        body = get_body()

        if not in_json(body, ["name", "password"]):
            return jsonify({"error": "Missing required fields: (name, password)"}), codes.BAD_REQUEST

        connection, cursor = get_connection()

        user_name = body["name"].strip().lower()
        
        pass_bytes = body["password"].encode('utf-8')
        hash_bytes = bcrypt.hashpw(pass_bytes,  bcrypt.gensalt())
        hash_string = hash_bytes.decode("utf-8")

        cursor.execute("""INSERT INTO kituser (user_name, password)
                            VALUES (%s, %s)""",
                       [user_name, hash_string])

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    
@user_blueprint.route("/user", methods=["GET"])
@requires_token
def user():
    try:
        token = get_auth_token()
        my_id = str(token["id"])

        connection, cursor = get_connection()

        cursor.execute("""SELECT id, user_name FROM kituser WHERE id = %s""", [my_id])
        result = cursor.fetchone()

        user_name = {
            "id": result[0],
            "name": result[1]
        }

        connection.close()
        cursor.close()

        return jsonify(user_name)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR