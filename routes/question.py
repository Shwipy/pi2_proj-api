from flask import Blueprint, request, jsonify
from database import get_connection, get_connection
from utils import get_auth_header, get_auth_token, get_body, in_json, codes
from routes.player import requires_token
import jwt
import datetime
from functools import wraps

question_blueprint = Blueprint("question_blueprint", __name__)

@question_blueprint.route("/questions", methods=["POST", "GET"])
@question_blueprint.route("/questions/<question_id>", methods=["PUT", "GET", "DELETE"])
@requires_token
def questions(question_id = None):
    try:
        if request.method == "POST":
            return create_question()
        
        if request.method == "PUT":
            
            return update_question(question_id)

        if request.method == "GET":
            quiz_id = request.args.get("quiz_id")
            
            if question_id is not None:
                return get_question_data(question_id)

            if quiz_id:
                return get_quiz_questions(quiz_id)

            #return get_all()
        
        if request.method == "DELETE":
            return delete_question(question_id)

    except Exception as e:
        return jsonify({"error": str(e)}), codes.API_ERROR
    
def create_question():
    body = get_body()

    if not in_json(body, ["question", "correct_answer", "answer1", "answer2","quiz_id"]):
        return jsonify({"error": "Missing required fields: (question, correct_answer, answer1, answer2, quiz_id)"}), codes.BAD_REQUEST

    answer3 = body["answer3"] if "answer3" in body else None
    answer4 = body["answer4"] if "answer4" in body else None
    img = body["img"] if "img" in body else None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT player_id FROM quizz WHERE id = %s""", [body["quiz_id"]])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Quiz já não existe."}),codes.NOT_FOUND
    
    token = get_auth_token()
    if token["id"] != result[0]:
        return jsonify({"error": "Can't Add a Question to a Quiz you Dont Own"}), codes.UNAUTHORIZED



    cursor.execute("""INSERT INTO question (question, correct_answer, answer1, answer2, answer3, answer4, img, quizz_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    [body["question"], body["correct_answer"], body["answer1"], body["answer2"], answer3, answer4, img, body["quiz_id"]])
    
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})

def get_quiz_questions(quiz_id):
    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT id FROM quizz WHERE id = %s""", [quiz_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Quiz já não existe."}),codes.NOT_FOUND

    cursor.execute("""SELECT * FROM question WHERE quizz_id = %s ORDER BY id""", [quiz_id])
    results = cursor.fetchall()

    questions = []
    for result_row in results:
        questions.append({
            "id": result_row[0],
            "question": result_row[1],
            "correct_answer": result_row[2],
            "answer1": result_row[3],
            "answer2": result_row[4],
            "answer3": result_row[5],
            "answer4": result_row[6],
            "img": result_row[7],
            "quiz_id": result_row[8]
        })

    if not questions:
        return jsonify({"error": "Quiz não tem perguntas."}),codes.BAD_REQUEST


    return jsonify(questions)

def get_question_data(question_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM question WHERE id = %s""", [question_id])
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "Quiz já não existe"}),codes.NOT_FOUND

    question ={
            "id": result[0],
            "question": result[1],
            "correct_answer": result[2],
            "answer1": result[3],
            "answer2": result[4],
            "answer3": result[5],
            "answer4": result[6],
            "img": result[7],
            "quiz_id": result[8]
        }

    return jsonify(question)

def update_question(question_id):
    body = get_body()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM question WHERE id = %s""",[question_id])
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "Question not found"}), codes.NOT_FOUND
    
    question = {
        "question": result[1],
        "correct_answer": result[2],
        "answer1": result[3],
        "answer2": result[4],
        "answer3": result[5],
        "answer4": result[6],
        "img": result[7]
    }

    cursor.execute("""SELECT player_id FROM quizz WHERE id = %s""", [result[8]])
    player_id = cursor.fetchone()

    token = get_auth_token()
    if token["id"] != player_id[0]:
        return jsonify({"error": "Can't update another user question"}), codes.UNAUTHORIZED

    if in_json(body, ["question"]):
        question["question"] = body["question"]

    if in_json(body, ["correct_answer"]):
        question["correct_answer"] = body["correct_answer"]

    if in_json(body, ["answer1"]):
        question["answer1"] = body["answer1"]
    
    if in_json(body, ["answer2"]):
        question["answer2"] = body["answer2"]
    
    if in_json(body, ["answer3"]):
        if body["answer3"] == "__null__":
             question["answer3"] = None
        else:
            question["answer3"] = body["answer3"]
    
    if in_json(body, ["answer4"]):
        if body["answer4"] == "__null__":
            question["answer4"] = None
        else:
            question["answer4"] = body["answer4"]

    if in_json(body, ["img"]):
        if body["img"] == "__null__":
            question["img"] = None
        else:
            question["img"] =  body["img"]


    cursor.execute("""UPDATE question
                    SET question = %s, correct_answer = %s, answer1 = %s, answer2 = %s, answer3 = %s, answer4 = %s, img = %s
                    WHERE id = %s""",[question["question"], question["correct_answer"], question["answer1"], question["answer2"],question["answer3"],question["answer4"],question["img"], question_id])
    
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "ok"})


    
def delete_question(question_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT id, quizz_id FROM question WHERE id = %s""", [question_id])
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Question já não existe."}),codes.NOT_FOUND
    
    cursor.execute("""SELECT player_id FROM quizz WHERE id = %s""", [result[1]])
    results = cursor.fetchone()
    
    token = get_auth_token()
    if token["id"] != results[0]:
        return jsonify({"error": "Can't delete another user question"}), codes.UNAUTHORIZED

    cursor.execute("""DELETE FROM question WHERE id = %s""", [question_id])
    connection.commit()

    return jsonify({"message": "OK"})