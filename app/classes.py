from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Alumno(db.Model):
    __tablename__ = 'alumnos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    promedio = db.Column(db.Float, nullable=False)
    fotoPerfilUrl = db.Column(db.String(200), nullable=True)  # URL de la photo de profil
    password = db.Column(db.String(100), nullable=False)  # Mot de passe

    def __init__(self, nombres, apellidos, matricula, promedio, password, fotoPerfilUrl=None):
        # Tests de validation
        if not nombres or not isinstance(nombres, str):
            raise ValueError("Nombres debe ser un str")
        if not apellidos or not isinstance(apellidos, str):
            raise ValueError("Apellidos debe ser un str")
        if not matricula or not isinstance(matricula, str):
            raise ValueError("Número de Empleado debe ser un str")
        if not isinstance(promedio, (int, float)) or promedio < 0 or promedio > 10:
            raise ValueError("Promedio debe ser un número entre 0 y 10")
        if not password or not isinstance(password, str):
            raise ValueError("Password debe ser un str")

        #self.id = id
        self.nombres = nombres
        self.apellidos = apellidos
        self.matricula = matricula
        self.promedio = promedio
        self.password = password
        self.fotoPerfilUrl = fotoPerfilUrl

    def to_dict(self):
        """Convert Alumno to a dictionary => JSON."""
        return {
            "id": self.id,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "matricula": self.matricula,
            "promedio": self.promedio,
            "fotoPerfilUrl": self.fotoPerfilUrl,
            "password": self.password
        }


class Profesor(db.Model): 
    __tablename__ = 'profesores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numeroEmpleado = db.Column(db.String(50), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    horasClase = db.Column(db.Integer, nullable=False)

    #vérifier l'ordre de création du profesor!!
    def __init__ (self, nombres, apellidos, numeroEmpleado, horasClase):
        #test on format
        if not nombres or not isinstance(nombres, str):
            raise ValueError("Nombres debe ser un str")
        if not apellidos or not isinstance(apellidos, str):
            raise ValueError("Apellidos debe ser un str")
        if not numeroEmpleado or not isinstance(numeroEmpleado, int):
            raise ValueError("Número de Empleado debe ser ser un int")
        if not isinstance(horasClase, (int, float)) or horasClase < 0:
            raise ValueError("Horas de Clase debe ser un número positivo")


        #self.id = id
        self.numeroEmpleado = numeroEmpleado
        self.nombres = nombres
        self.apellidos = apellidos
        self.horasClase = horasClase

    def to_dict(self):
        """Convert Profesor to a dictionary."""
        return {
            "id": self.id,
            "numeroEmpleado": self.numeroEmpleado,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "horasClase": self.horasClase
        }



    

