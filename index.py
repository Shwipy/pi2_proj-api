from flask import Flask
from routes.user import user_blueprint
from routes.kit import kit_blueprint
from routes.question import question_blueprint
from routes.activity import activity_blueprint
from dotenv import load_dotenv
import bcrypt

app = Flask(__name__)
app.register_blueprint(user_blueprint)
app.register_blueprint(kit_blueprint)
app.register_blueprint(question_blueprint)
app.register_blueprint(activity_blueprint)


app.debug = True

if __name__ == "__main__":
    load_dotenv()

    app.run()
