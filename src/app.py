"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planets, People, Favorites
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    usuarios = User.query.all()
    serialized_usuarios = list(map(lambda x: x.serialize(), usuarios))

    return jsonify(serialized_usuarios), 200


@app.route('/planets', methods=['GET'])
def get_planetas():
    planets = Planets.query.all()
    serialized_planets = list(map(lambda x: x.serialize(), planets))

    return jsonify(serialized_planets), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    if planet_id:

        planet = Planets.query.get(planet_id)
        if planet is None:
            return jsonify({"error": "Planet not found"}), 404

        return jsonify(planet.serialize()), 200

    return "planet not found", 404


@app.route('/people', methods=['GET'])
def get_personas():
    personas = People.query.all()
    serialized_people = list(map(lambda x: x.serialize(), personas))

    return jsonify(serialized_people), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    if people_id:
        person = People.query.get(people_id)
        if person is None:
            return jsonify({"error": "Person not found"}), 404
        return jsonify(person.serialize()), 200

    return "person not found", 404


@app.route('/person', methods=['POST'])
def handle_person():

    body = request.get_json()

    if body is None:
        raise APIException(
            "You need to specify the request body as a json object", status_code=400)
    if 'username' not in body:
        raise APIException('You need to specify the username', status_code=400)
    if 'email' not in body:
        raise APIException('You need to specify the email', status_code=400)

    # at this point, all data has been validated, we can proceed to insert into the database
    user1 = User(username=body['username'], email=body['email'])
    db.session.add(user1)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201


@app.route('/users/favorites', methods=['GET'])
def get_favorites():
    usuario_data = request.get_json('user_id')
    if not usuario_data:
        return jsonify({"error": "Missing user_id"}), 400

    usuario_id = usuario_data['user_id']

    favoritos = Favorites.query.filter_by(user_id=usuario_id).all()
    serialized_favorites = list(map(lambda x: x.serialize(), favoritos))

    return jsonify(serialized_favorites), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST', 'DELETE'])
def push_planetfav(planet_id):
    usuario_data = request.json.get()
    if not usuario_data or 'user_id' not in usuario_data:
        return jsonify({"error": "Missing user_id"}), 400

    usuario_id = usuario_data['user_id']

    if request.method == 'POST':
        planeta_fav = Favorites.query.filter_by(
            user_id=usuario_id, planet_id=planet_id).first()
        if not planeta_fav:
            new_fav = Favorites(user_id=usuario_id, planet_id=planet_id)
            db.session.add(new_fav)
            db.session.commit()
            return jsonify({"message": "Planet added to favorites"}), 201
        return jsonify({"error": "Planet already in favorites"}), 400

    if request.method == 'DELETE':
        planeta_fav = Favorites.query.filter_by(
            user_id=usuario_id, planet_id=planet_id).first()
        if planeta_fav:
            db.session.delete(planeta_fav)
            db.session.commit()
            return jsonify({"message": "Planet removed from favorites"}), 200
        return jsonify({"error": "Planet not found in favorites"}), 404


@app.route('/favorite/people/<int:people_id>', methods=['POST', 'DELETE'])
def post_peoplefav(people_id):

    usuario_data = request.json.get()
    if not usuario_data or 'user_id' not in usuario_data:
        return jsonify({"error": "Missing user_id"}), 400

    usuario_id = usuario_data['user_id']

    people_fav = Favorites.query.filter_by(
        user_id=usuario_id,  people_id=people_id)
    if request.method == 'POST':
        if not people_fav:
            new_fav = Favorites(user_id=usuario_id, people_id=people_id)
            db.session.add(new_fav)
            db.session.commit()
            return jsonify({"message": "Person added to favorites"}), 201
        return jsonify({"error": "Person already in favorites"}), 400

    if request.method == 'DELETE':
        if people_fav:
            db.session.delete(people_fav)
            db.session.commit()
            return "Person deleted from Favorites", 200
    return "Impossible delete this person from favorites", 404


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
