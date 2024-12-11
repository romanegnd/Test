from flask import Flask, jsonify, request
#from alumno import Alumno
#from profesor import Profesor
from flask_sqlalchemy import SQLAlchemy
import boto3
from botocore.exceptions import NoCredentialsError
import random
import string
import time
import uuid
import os
from classes import db, Alumno, Profesor
from werkzeug.utils import secure_filename


app = Flask(__name__)
# Remplace par tes paramètres RDS (endpoint, utilisateur, mot de passe, nom de la base)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:passwordBD-uady@uady-bd.cziypuodxgrb.us-east-1.rds.amazonaws.com:3306/uady_bd' ##############
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()


#-----Infos modifiables avec identifiants etc-----
#Infos sessions pour boto3
YOUR_AWS_ACCESS_KEY_ID = 'ASIA3AX7JATRO5YACBMC'
YOUR_AWS_SECRET_ACCESS_KEY = 'wUS4obtjjIglSYQ6pcbDanlU8tzFv1SDQMOjRrBm'
YOUR_AWS_SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEOX//////////wEaCXVzLXdlc3QtMiJGMEQCICW92G2TNrPtdgd5F0Cwb3jysQeZqsAx2UWJYqAQyAniAiA9mnUiyCRJ1gZjiF+Jb2B0ydMWpLt/7PhViEzCqW8eqiqzAgie//////////8BEAEaDDc1NzUyMzM1MDc1NCIMqoL8E4af/bUooKYXKocCWNJSZM8BMbO7EcNUtc6REfc57sR4aGrYAZzjY4QOYXg3CYTKmuO8vZtmin0CfJjmoDhtcQFhQdaQlX+ZaUVhlnZKG6e5TQKTeOR2sl42ISGWAmz/6uY1PP2XFnVUMJ/qUAYQPizLTzIfypHO7PqOIt7OD/cq8U8BOPLndBAT0uXuS228+S0a2BGoz2Pz+lwSLtUe8MD9WaJBB5hCxS7SLw8dLhBSmdQozN4/L8FTXAVXUlOzL1gnG1KAACAXkP8FsjU+ddoD6ZF2Iq6100kV462IB27ctGWhg8hSMWwbpdrEQ0Lyg+7Ax5n7hUnvbl9I0A5JJrkYLBMgw3WpJNFuMJ2NgKAgodAw0qnkugY6ngFfM3EH6lEPNbay3si7rInArS+3TLrkYKXzEwrIwYKE+c0ZvaKWSQWx7Z7PCHLQFvcTcT9ziNK6lasasVHyVfY3kzd/Oz1hdqLN1mh1gsupAB1eXVgWUYihrV6omdtzgyTutq3yHkNn959Ov66/gcuGnH8RiI6F/38Y7o1xJE4jmwscLOieX8q4ppnoRug6Um6W3qa9tJshBibvbhookQ=='
YOUR_AWS_REGION_NAME = 'us-east-1' 

#infos bucket
BUCKET_NAME = 'bk-alumnos'

#infos SNS
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:757523350754:notif-alumno'  

#infos table DynamoDB
dynamoname = 'sesiones-alumnos'

#-----Configuations-----
#Config client S3
s3 = boto3.client(
    's3',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,
    region_name=YOUR_AWS_REGION_NAME
)

#Config SNS 
sns_client = boto3.client(
    'sns',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,  
    region_name=YOUR_AWS_REGION_NAME 
)

#Config client DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=YOUR_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=YOUR_AWS_SECRET_ACCESS_KEY,
    aws_session_token=YOUR_AWS_SESSION_TOKEN,  
    region_name=YOUR_AWS_REGION_NAME   
)

# Table DynamoDB
table = dynamodb.Table(dynamoname)



#______________________________ALUMNOS
# GET /alumnos
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([alumno.to_dict() for alumno in alumnos]), 200

# GET /alumnos/{id}
@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno_by_id(id):
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'ID no encontrado'}), 404
    return jsonify(alumno.to_dict()), 200
    

# POST /alumnos
@app.route('/alumnos', methods=['POST'])
def add_alumno():
    data = request.get_json()
    try:
        nuevo_alumno = Alumno(
            nombres=data['nombres'],
            apellidos=data['apellidos'],
            matricula=data['matricula'],
            promedio=data['promedio'],
            password=data['password']
        )
        db.session.add(nuevo_alumno)
        db.session.commit()
        return jsonify(nuevo_alumno.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


# POST /alumnos/{id}/fotoPerfil
@app.route('/alumnos/<int:id>/fotoPerfil', methods=['POST'])
def upload_foto_perfil(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({'error': 'ID no encontrado'}), 404

    if 'foto' not in request.files:
        return jsonify({'error': 'Archivo no encontrado en la solicitud'}), 400
    
    file = request.files['foto']
    if file.filename == '':
        return jsonify({'error': 'El nombre del archivo está vacío'}), 400

    try:
        # Sécuriser le nom du fichier
        filename = secure_filename(file.filename)

        # Construire le chemin de l'objet dans S3
        s3_path = f"{id}/{filename}"

        # Téléverser l'image dans S3
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            s3_path,
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )

        # Construire l'URL publique de l'image
        photo_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_path}"

        # Mettre à jour l'URL dans la base de données
        alumno.fotoPerfilUrl = photo_url
        db.session.commit()

        return jsonify({'message': 'Foto de perfil subida con éxito', 'fotoPerfilUrl': photo_url}), 200

    except NoCredentialsError:
        return jsonify({'error': 'No se encontraron credenciales AWS'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#POST /alumnos/{id}/email
@app.route('/alumnos/<int:id>/email', methods=['POST'])
def send_email_notification(id):
    # Récupérer les données de l'élève
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    # Construire le contenu de l'email
    email_content = (
        f"Información del alumno:\n"
        f"Nombre: {alumno.nombres} {alumno.apellidos}\n"
        f"Promedio: {alumno.promedio}\n"
    )

    try:
        # Publier le message dans le topic SNS
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_content,
            Subject="Calificaciones y datos del alumno"
        )
        return jsonify({'message': 'Notificación enviada correctamente'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# POST/alumnos/{id}/session/login
@app.route('/alumnos/<int:id>/session/login', methods=['POST'])
def login_session(id):
    data = request.get_json()
    alumno = Alumno.query.get(id)

    # Vérification des données: 
    if alumno is None:
        return jsonify({'error': 'Alumno no encontrado'}), 404

    if not 'password' in data:
        return jsonify({'error': 'Contraseña requerida'}), 400
    
    if alumno.password != data['password']:
        return jsonify({'error': 'Contraseña incorrecta'}), 400

    # Générer un UUID et un sessionString aléatoire
    session_id = str(uuid.uuid4())
    session_string = ''.join(random.choices(string.ascii_letters + string.digits, k=128))
    timestamp = int(time.time())

    # Mettre infos session dans DynamoDB
    table.put_item(
        Item={
            'id': session_id,
            'fecha': timestamp,
            'alumnoId': id,
            'active': True,
            'sessionString': session_string
        }
    )
    return jsonify({'message': 'Sesión creada', 'sessionString': session_string, 'sessionId': session_id}), 200


# POST alumnos/{id}/session/verify
@app.route('/alumnos/<int:id>/session/verify', methods=['POST'])
def verify_session(id):
    data = request.get_json()

    if not 'sessionString' in data:
        return jsonify({'error': 'SessionString requerido'}), 400

    #trouver la session dans DynamoDB
    response = table.scan(
        FilterExpression='alumnoId = :alumnoId AND sessionString = :sessionString',
        ExpressionAttributeValues={
            ':alumnoId': id,
            ':sessionString': data['sessionString']
        }
    )

    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'Sesión no válida'}), 400

    #tests session active ?
    session = items[0]
    if not session['active']:
        return jsonify({'error': 'Sesión inactiva'}), 400

    return jsonify({'message': 'Sesión válida'}), 200


# POST  alumnos/{id}/session/logout
@app.route('/alumnos/<int:id>/session/logout', methods=['POST'])
def logout_session(id):
    data = request.get_json()

    if not 'sessionString' in data:
        return jsonify({'error': 'SessionString requerido'}), 400

    #trouver la session dans DynamoDB
    response = table.scan(
        FilterExpression='alumnoId = :alumnoId AND sessionString = :sessionString',
        ExpressionAttributeValues={
            ':alumnoId': id,
            ':sessionString': data['sessionString']
        }
    )

    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'Sesión no encontrada'}), 400

    session = items[0]

    #fermer la session
    table.update_item(
        Key={'id': session['id']},
        UpdateExpression='SET active = :active',
        ExpressionAttributeValues={':active': False}
    )

    return jsonify({'message': 'Sesión cerrada con éxito'}), 200


# PUT /alumnos/{id}
@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    data = request.get_json()
    alumno = Alumno.query.get(id)  # Recherche dans la base de données
    if alumno is None:
        return jsonify({'error': 'ID no encontrado'}), 404
    try:
        # Tests de validation des champs
        if 'nombres' in data and (not data['nombres'] or not isinstance(data['nombres'], str)):
            return jsonify({"error": "Nombres invalidos"}), 400
        if 'apellidos' in data and (not data['apellidos'] or not isinstance(data['apellidos'], str)):
            return jsonify({"error": "Apellidos invalidos"}), 400
        if 'promedio' in data and (not isinstance(data['promedio'], (int, float)) or data['promedio'] < 0 or data['promedio'] > 10):
            return jsonify({"error": "Promedio invalido"}), 400
        if 'matricula' in data and (not data['matricula'] or not isinstance(data['matricula'], str)):
            return jsonify({"error": "Matricula invalida"}), 400

        # Mise à jour des champs si les validations passent
        alumno.nombres = data.get('nombres', alumno.nombres)
        alumno.apellidos = data.get('apellidos', alumno.apellidos)
        alumno.matricula = data.get('matricula', alumno.matricula)
        alumno.promedio = data.get('promedio', alumno.promedio)

        # Enregistrement dans la base de données
        db.session.commit()
        return jsonify(alumno.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400



# DELETE /alumnos/{id}
@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = Alumno.query.get(id)
    if alumno is None:
        return jsonify({'error': 'ID no encontrado'}), 404
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({'message': 'Eliminacion exitosa'}), 200


#______________________________PROFESORES
#  GET /profesores
@app.route('/profesores', methods=['GET'])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([profesor.to_dict() for profesor in profesores]), 200

# GET /profesores/{id}
@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor_by_id(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({'error': 'ID no encontrado'}), 404
    return jsonify(profesor.to_dict()), 200
    
# POST /profesores
@app.route('/profesores', methods=['POST'])
def add_profesor():
    data = request.get_json()
    try:
        nuevo_profesor = Profesor(
            nombres=data['nombres'],
            apellidos=data['apellidos'],
            numeroEmpleado=data['numeroEmpleado'],
            horasClase=data['horasClase']
        )
        db.session.add(nuevo_profesor)
        db.session.commit()
        return jsonify(nuevo_profesor.to_dict()), 201
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

# PUT /profesores/{id}
@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    data = request.get_json()
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({'error': 'ID no encontrado'}), 404
    try:
        if 'nombres' in data and (not data['nombres'] or not isinstance(data['nombres'], str)):
            return jsonify({"error": "nombres invalidos"}), 400
        if 'apellidos' in data and (not data['apellidos'] or not isinstance(data['apellidos'], str)):
            return jsonify({"error": "apellidos invalidos"}), 400
        if 'horasClase' in data and (not isinstance(data['horasClase'], (int, float)) or data['horasClase'] < 0) : 
            return jsonify({"error": "horasClase invalidas"}), 400
        if 'numeroEmpleado' in data and not isinstance(data['numeroEmpleado'], int):
            return jsonify({'error': 'Numero empleado inválido'}), 400


        profesor.nombres = data.get('nombres', profesor.nombres)
        profesor.apellidos = data.get('apellidos', profesor.apellidos)
        profesor.horasClase = data.get('horasClase', profesor.horasClase)
        profesor.numeroEmpleado = data.get('numeroEmpleado', profesor.numeroEmpleado)
        db.session.commit()
        return jsonify(profesor.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# DELETE /profesores/{id}
@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({'error': 'ID no encontrado'}), 404
    db.session.delete(profesor)
    db.session.commit()
    return jsonify({'message': 'Eliminacion exitosa'}), 200


if __name__ == '__main__':
    app.run(debug=True)
