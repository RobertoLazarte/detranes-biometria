from scripts.api_facial import db


# Banco das análises por lote
class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    cred = db.Column(db.String(11))
    acesso = db.Column(db.DateTime)
    total = db.Column(db.Integer)
    aprovadas = db.Column(db.Integer)
    recusadas = db.Column(db.String)

    def __init__(self, cred, acesso, total, aprovadas, recusadas):
        self.cred = cred
        self.acesso = acesso
        self.total = total
        self. aprovadas = aprovadas
        self.recusadas = recusadas

    def json(self):
        if len(self.recusadas) == 0:
            return {'cred': self.cred,
                    'acesso': self.acesso.strftime("%d/%m/%Y %H:%M:%S"),
                    'total': self.total, 'aprovadas': self.aprovadas}
        else:
            return {'cred': self.cred, 'acesso': self.acesso.strftime(
                "%d/%m/%Y %H:%M:%S"), 'total': self.total, 'aprovadas':
                self.aprovadas, 'recusadas': self.recusadas.split(' ')}
