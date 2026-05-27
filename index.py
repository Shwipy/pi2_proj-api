from flask import Flask
from routes.player import player_blueprint
from routes.quizz import quizz_blueprint
from routes.question import question_blueprint
from routes.activity import activity_blueprint
from dotenv import load_dotenv
import bcrypt

app = Flask(__name__)
app.register_blueprint(player_blueprint)
app.register_blueprint(quizz_blueprint)
app.register_blueprint(question_blueprint)
app.register_blueprint(activity_blueprint)


app.debug = True

if __name__ == "__main__":
    load_dotenv()

    app.run()
