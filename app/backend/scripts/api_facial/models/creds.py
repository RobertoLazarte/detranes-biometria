from scripts.api_facial import db
import numpy as np
from sqlalchemy.dialects.postgresql import ARRAY


# Banco de dados constando credenciais e as features do individuo
class Cred(db.Model):
    __tablename__ = 'features'
    # Numero maximo ajuda a garantir integridade
    id = db.Column(db.String(11), primary_key=True)
    features = db.Column(db.PickleType)
    #features = db.Column(ARRAY(db.Numeric))

    def __init__(self, id, features):
        self.id = id
        self.features = features

    def json(self):
        return {'cred': self.id, 'values': np.ndarray.tolist(self.features)}
        #return {'cred': self.id, 'values': self.features}

    def __str__(self):
        return f"{self.id}"
