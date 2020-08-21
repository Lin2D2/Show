
from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)


class Placeholder(Resource):
    def get(self):
        return {"data": "test"}


if __name__ == "__main__":
    app.run(debug=True)
