import os
from flask import Flask, redirect, Blueprint, url_for
from flask_restplus import Api
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

#Alterados para teste
# Caminho de arquivos de interesse
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/dados/infra/api-facial/temp')
BATCH_FOLDER = os.getenv('BATCH_FOLDER', '/dados/infra/api-facial/batch_temp')
os.environ['TKESSL_OPENSSL_LIB'] = os.getenv('TKESSL_OPENSSL_LIB', '/usr/lib/x86_64-linux-gnu/libssl.so.1.1')
os.environ['CAS_CLIENT_SSL_CA_LIST'] = os.getenv('CAS_CLIENT_SSL_CA_LIST', '/dados/cacerts/trustedcerts.pem')

# Criação da aplicação
app = Flask(__name__)
app.secret_key = "R0g3r1O"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')#'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ENDPOINT = os.getenv("ENDPOINT_COLETA_RECFACIAL","http://externo.detran.es.gov.br:5000/api/Coletas")##
LOGIN = os.getenv("LOGIN_COLETA_RECFACIAL", "vert")
PASSWORD = os.getenv("PASSWORD_COLETA_RECFACIAL", "pAoC|4)*#{G-}@5{-M_QwM40-N=7#U+}")

# Criação do banco de dados
db = SQLAlchemy(app, engine_options={
    'pool_size': 10,
    'pool_recycle': 60,
    'pool_pre_ping': True
})
# Integração do banco de dados com o app
Migrate(app, db)

# Fix of returning swagger.json on HTTP
@property
def specs_url(self):
    """
    The Swagger specifications absolute url (ie. `swagger.json`)

    :rtype: str
    """
    return url_for(self.endpoint('specs'), _external=False)

Api.specs_url = specs_url

#blueprint = Blueprint('api', __name__)
api = Api(app,
          version = '1.0',
          title = 'SAS-Vert API',
          description  = 'API para validação automatizada de processos de Telemetria (Reconhecimento Facial)')
#app.register_blueprint(blueprint)

name_space = api.namespace('telemetria', description='Endpoints para realização de reconhecimento facial no processo de telemetria')

# Criação da base de dados, caso não exista
@app.before_first_request
def create_tables():
    db.create_all()

# Para os models, db precisa estar definido
from scripts.api_facial.resources.creds import *
from scripts.api_facial.resources.logscred import *
from scripts.api_facial.resources.batchcred import *
