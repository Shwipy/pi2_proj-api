from flask import Flask
from routes.user import user_blueprint
from routes.kit import kit_blueprint
from routes.item import item_blueprint
from routes.category import category_blueprint
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(user_blueprint)
app.register_blueprint(kit_blueprint)
app.register_blueprint(item_blueprint)
app.register_blueprint(category_blueprint)


app.debug = True

if __name__ == "__main__":
    load_dotenv()

    app.run()
