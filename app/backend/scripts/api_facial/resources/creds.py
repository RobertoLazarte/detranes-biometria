import base64
import io  # #
import json  # #
import os
from datetime import datetime

import numpy as np
import requests  # #
import werkzeug
from flask import request
from flask_restplus import Resource, fields, reqparse
from scripts.api_facial import ENDPOINT, LOGIN, PASSWORD, UPLOAD_FOLDER, db, name_space
from scripts.api_facial.functions.recfacial import *
from scripts.api_facial.models.creds import Cred
from scripts.api_facial.models.logscred import Acesso
from werkzeug.utils import secure_filename

parser = reqparse.RequestParser()
parser.add_argument(
    "file",
    type=werkzeug.datastructures.FileStorage,
    required=True,
    location="files",
    help="Imagem a ser comparada com a da base da Thomas & Greg (aceita jpg, jpeg e png)",
)

VIYA_HOST = os.getenv("VIYA_HOST", "10.0.12.50")
VIYA_PASSWORD = os.getenv(
    "VIYA_PASSWORD", "{SAS002}23B6882C31A5DBF51C3F913F51CEA44B3C126085"
)
VIYA_USER = os.getenv("VIYA_USER", "rodrigo.ferrari")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", 0.5))
mod_files = os.getenv("MOD_FILES", "/dados/infra/api-rec-facial-dados")

# Classe com permissão de visualização e remoção individual
@name_space.route("/cred/<string:numcred>")
class CredGetDel(Resource):
    @name_space.doc(
        params={
            "numcred": "Especificar o número da credencial (CPF) para obter seus atributos, se existirem"
        },
        responses={200: "Retorno dos atributos", 404: "Credencial não encontrada"},
    )
    def get(self, numcred):

        cred = Cred.query.filter_by(id=numcred).first()

        if cred:
            return cred.json()
        else:
            # If you request a credential not yet in the list
            return {"message": "Credencial não encontrada"}, 404

    @name_space.doc(
        params={
            "numcred": "Especificar o número da credencial (CPF) para remover o registro dos seus atributos"
        },
        responses={
            200: "Registro da credencial removido com sucesso",
            400: "Credencial não consta no banco de dados",
        },
    )
    def delete(self, numcred):

        cred = Cred.query.filter_by(id=numcred).first()

        if cred:
            db.session.delete(cred)
            db.session.commit()
            return {"note": f"Registro de {numcred} removido com successo"}, 200
        else:
            return {"message": "Credencial não consta no banco de dados"}, 400


# Classe com permissão de post (imagem deve ter credencial como nome)
@name_space.route("/cred")
class CredResource(Resource):
    @name_space.doc(
        params={
            "cpf": {
                "in": "formData",
                "type": "string",
                "required": "true",
                "description": "CPF do indivíduo",
            },
            "renach": {
                "in": "formData",
                "type": "string",
                "required": "true",
                "description": "Número do Renach (caso se trate de instrutor, inserir 0)",
            },
            "processo": {
                "in": "formData",
                "type": "string",
                "required": "true",
                "description": "Tipo do processo (1: Renach, 2: Reciclagem)",
            },
        },
        responses={
            201: "Retorno do resultado da avaliação",
            400: "Erro no envio (credencial incorreta, imagem não consta, chave não utilizada)",
            404: "Credencial não encontrada",
        },
    )
    @name_space.expect(parser)
    def post(self):

        os.environ["TKESSL_OPENSSL_LIB"] = os.getenv('TKESSL_OPENSSL_LIB', '/usr/lib/x86_64-linux-gnu/libssl.so.1.1')
        os.environ["CAS_CLIENT_SSL_CA_LIST"] = os.getenv('CAS_CLIENT_SSL_CA_LIST', '/dados/cacerts/trustedcerts.pem')

        # Arquivo sem caminho especificado
        if "file" not in request.files:
            return {
                "message": "Nenhuma parte de nome file no pedido",
                "status": False,
            }, 400

        # Arquivo não seleciondo
        myreq = request.form.to_dict()
        file = request.files["file"]
        cpf = myreq["cpf"]
        renach = myreq["renach"]
        processo = myreq["processo"]

        temp_file = cpf + ".png"

        caminho = os.path.join(UPLOAD_FOLDER, temp_file)

        if file.filename == "":
            return {
                "message": "Nenhum arquivo selecionado para upload",
                "status": False,
            }, 400

        # Arquivo dentro das especificações
        if len(cpf) == 11 and cpf.isdigit():  ##
            # filename = secure_filename(file.filename)
            # name = file.filename.rsplit('.', 1)[0]
            cred = Cred.query.filter_by(id=cpf).first()
            conn = swat.CAS(VIYA_HOST, 5570, VIYA_USER, VIYA_PASSWORD)  ##
            yolo_face, rn50 = load_mods(
                conn, mod_files=mod_files
            )  ##
            # Se existir a credencial na base
            if cred:
                ref = cred.features
            # Se não existir, busca no local especificado
            else:
                try:
                    payload = {
                        "login": LOGIN,
                        "senha": PASSWORD,
                        "cpf": cpf,
                        "documento": renach,
                        "tipoProcesso": 1,
                        "tipoImagem": 2001,
                    }
                    response = requests.post(ENDPOINT, json=payload).json()
                except:
                    conn.terminate()  ##
                    return {
                        "message": "Erro na busca pela foto de referência - contatar administrador.",
                        "status": False,
                    }, 404
                try:                    
                    ref_thomas = base64.b64decode(response["imagem"])
                    ref = Image.open(io.BytesIO(ref_thomas))
                    ref.save(os.path.join(UPLOAD_FOLDER, "temp2.jpg"))
                    ref_file = cpf + "_ref.png"
                    ref.save(os.path.join(UPLOAD_FOLDER, ref_file))
                    copy_image_local_to_cas(local_file=os.path.join(UPLOAD_FOLDER, ref_file), cas_server_directory=UPLOAD_FOLDER)
                    ref = run_proc(
                        os.path.join(UPLOAD_FOLDER, ref_file), conn, yolo_face, rn50
                    )

                    os.remove(os.path.join(UPLOAD_FOLDER, ref_file))
                    delete_image_from_cas_server(cas_server_file = os.path.join(UPLOAD_FOLDER, ref_file))
                    # cred = Cred(id=cpf, features=ref)
                    cred = Cred(id=cpf, features=ref)
                    db.session.add(cred)
                    db.session.commit()
                except:
                    conn.terminate()  ##
                    return {
                        "message": "Erro no processamento da foto de referência - contatar administrador.",
                        "status": False,
                    }, 404

            file.save(caminho)
            # Orientando a imagem e salvando por cima
            nova = orienta(caminho)
            nova.save(caminho)
            copy_image_local_to_cas(local_file=caminho, cas_server_directory=UPLOAD_FOLDER)

            resp, julga = classifica(
                conn, caminho, ref, yolo_face, rn50, nova, threshold=SIM_THRESHOLD
            )

            os.remove(caminho)
            delete_image_from_cas_server(cas_server_file = caminho)

            acesso = Acesso(cred=cpf, resultado=resp)
            db.session.add(acesso)
            db.session.commit()
            conn.terminate()  ##
            return {"message": resp, "status": julga}, 201

        # Credencial fora das especificações
        else:
            return {"message": "Credencial incorreta", "status": False}, 400


# Classe com permissão de visualizar base inteira
@name_space.route("/creds")
class AllCreds(Resource):
    @name_space.doc(responses={200: "Retorno de cada CPF e seus respectivos atributos"})
    def get(self):
        # return all credentials
        creds = Cred.query.all()

        return [cred.json() for cred in creds]


@name_space.route("/compara")
class Compara(Resource):
    rec_facial_model = name_space.model(
        "RecFacial",
        {
            "imagem": fields.List(fields.Integer(required=True)),
            "cpf": fields.String(required=True),
            "renach": fields.String(required=True),
            "processo": fields.String(required=True),
        },
    )

    @name_space.doc(
        responses={
            201: "Retorno do resultado da avaliação",
            400: "Erro no envio (credencial incorreta, imagem não consta)",
            404: "Credencial não encontrada",
        }
    )
    @name_space.expect(rec_facial_model)
    def post(self):
        dados = request.get_json()
        cpf = dados["cpf"]
        renach = dados["renach"]
        processo = dados["processo"]
        os.environ["TKESSL_OPENSSL_LIB"] = os.getenv('TKESSL_OPENSSL_LIB', '/usr/lib/x86_64-linux-gnu/libssl.so.1.1')
        os.environ["CAS_CLIENT_SSL_CA_LIST"] = os.getenv('CAS_CLIENT_SSL_CA_LIST', '/dados/cacerts/trustedcerts.pem')

        temp_file = cpf + ".png"

        caminho = os.path.join(UPLOAD_FOLDER, temp_file)

        # Arquivo dentro das especificações
        if (
            len(cpf) == 11 and cpf.isdigit() and renach.isdigit() and processo.isdigit()
        ):  ##
            cred = Cred.query.filter_by(id=cpf).first()
            conn = swat.CAS(VIYA_HOST, 5570, VIYA_USER, VIYA_PASSWORD)  ##
            yolo_face, rn50 = load_mods(
                conn, mod_files=mod_files
            )  ##
            # Se existir a credencial na base
            if cred:
                ref = cred.features
            # Se não existir, busca no local especificado
            else:
                try:
                    payload = {
                        "login": LOGIN,
                        "senha": PASSWORD,
                        "cpf": cpf,
                        "documento": renach,
                        "tipoProcesso": 1,
                        "tipoImagem": 2001,
                    }
                    response = requests.post(ENDPOINT, json=payload).json()
                    ref_thomas = base64.b64decode(response["imagem"])
                except:
                    conn.terminate()  ##
                    return {
                        "message": "Erro na busca pela foto de referência - contatar administrador.",
                        "status": False,
                    }, 404
                try:                    
                    ref = Image.open(io.BytesIO(ref_thomas))
                    ref_filename = cpf + "_ref.png"
                    ref.save(os.path.join(UPLOAD_FOLDER, ref_filename))
                    copy_image_local_to_cas(local_file=os.path.join(UPLOAD_FOLDER, ref_filename), cas_server_directory=UPLOAD_FOLDER)
                    ref = run_proc(
                        os.path.join(UPLOAD_FOLDER, ref_filename), conn, yolo_face, rn50
                    )

                    os.remove(os.path.join(UPLOAD_FOLDER, ref_filename))
                    delete_image_from_cas_server(cas_server_file = os.path.join(UPLOAD_FOLDER, ref_filename))
                    cred = Cred(id=cpf, features=ref)
                    db.session.add(cred)
                    db.session.commit()
                except:
                    conn.terminate()  ##
                    return {
                        "message": "Erro no processamento da foto de referência - contatar administrador.",
                        "status": False,
                    }, 404
            try:
                imagem = Image.open(io.BytesIO(bytearray(dados["imagem"])))
            except:
                return {
                    "message": "Erro no recebimento da imagem (precisa ser bytearray)",
                    "status": False,
                }, 404
            imagem.save(caminho)
            # Orientando a imagem e salvando por cima
            nova = orienta(caminho)
            nova.save(caminho)
            copy_image_local_to_cas(local_file=caminho, cas_server_directory=UPLOAD_FOLDER)

            resp, julga = classifica(
                conn, caminho, ref, yolo_face, rn50, nova, threshold=SIM_THRESHOLD
            )

            os.remove(caminho)
            delete_image_from_cas_server(cas_server_file = caminho)

            acesso = Acesso(cred=cpf, resultado=resp)
            db.session.add(acesso)
            db.session.commit()
            conn.terminate()  ##
            return {"message": resp, "status": julga}, 201

        # Credencial fora das especificações
        else:
            return {"message": "Credencial incorreta", "status": False}, 400
