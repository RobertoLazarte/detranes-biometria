from scripts.api_facial import db
from datetime import datetime


# Registro dos acessos
class Acesso(db.Model):
    __tablename__ = 'acessos'
    id = db.Column(db.Integer, primary_key=True)
    cred = db.Column(db.String(11))
    acesso = db.Column(db.DateTime)
    resultado = db.Column(db.String)

    def __init__(self, cred, resultado):
        self.cred = cred
        self.acesso = datetime.now()
        self.resultado = resultado

    def json(self):
        return {'cred': self.cred, 'acesso': self.acesso.strftime(
            "%d/%m/%Y %H:%M:%S"), 'message': self.resultado}
