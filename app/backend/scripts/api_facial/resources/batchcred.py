import base64
import io
import json
import os
import shutil
from datetime import datetime

import requests
import werkzeug
from flask import request
from flask_restplus import Resource, reqparse
from pyunpack import Archive
from rarfile import RarFile
from scripts.api_facial import (
    BATCH_FOLDER,
    ENDPOINT,
    LOGIN,
    PASSWORD,
    UPLOAD_FOLDER,
    db,
    name_space,
)
from scripts.api_facial.functions.recfacial import *
from scripts.api_facial.models.batchcred import Batch
from scripts.api_facial.models.creds import Cred
from werkzeug.utils import secure_filename

parser = reqparse.RequestParser()
parser.add_argument(
    "file",
    type=werkzeug.datastructures.FileStorage,
    required=True,
    location="files",
    help="Arquivo em formato zip ou rar contendo pastas cujo nome segue o padrão 'cpf-documento-tipoProcesso'",
)

VIYA_HOST = os.getenv("VIYA_HOST", "10.0.12.50")
VIYA_PASSWORD = os.getenv(
    "VIYA_PASSWORD", "{SAS002}23B6882C31A5DBF51C3F913F51CEA44B3C126085"
)
VIYA_USER = os.getenv("VIYA_USER", "rodrigo.ferrari")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", 0.5))

# Manipulação do banco de batches
@name_space.route("/batch")
class Batchange(Resource):
    @name_space.expect(parser)
    @name_space.doc(
        responses={
            200: "Avaliação dos lotes finalizada",
            400: "Problema no recebimento do arquivo (formato incorreto, arquivo ausente ou chave mal especificada)",
        }
    )
    def post(self):
        os.environ["TKESSL_OPENSSL_LIB"] = "/usr/lib/x86_64-linux-gnu/libssl.so.1.1"
        os.environ["CAS_CLIENT_SSL_CA_LIST"] = "/dados/cacerts/trustedcerts.pem"
        momento = datetime.now()
        # Arquivo sem caminho especificado
        if "file" not in request.files:
            return {"message": "Nenhuma parte de nome file no pedido"}, 400

        # Arquivo não seleciondo
        file = request.files["file"]
        if file.filename == "":
            return {"message": "Nenhum arquivo selecionado para upload"}, 400

        # Receber arquivo (.rar ou .zip, exige instalação de patool e pyunpack)
        filename = secure_filename(file.filename)
        if not allowed_file(filename, ALLOWED_EXTENSIONS=set(["zip"]), length=False):
            return {"message": "Formato de arquivo incorreto (aceita zip)"}

        # Salvar na pasta do batch
        file.save(os.path.join(BATCH_FOLDER, filename))
        # Descompactar arquivos (exige instalar patool e pyunpack)
        Archive(os.path.join(BATCH_FOLDER, filename)).extractall(BATCH_FOLDER)
        creds = [
            f.name
            for f in os.scandir(BATCH_FOLDER)
            if f.is_dir() and not f.name.startswith(".")
        ]

        # Iterar por pasta
        for name in creds:
            try:
                cpf, renach, processo = name.split("-")
            except:
                continue
            if not (cpf.isdigit()):
                continue

            cred = Cred.query.filter_by(id=cpf).first()
            conn = swat.CAS(VIYA_HOST, 5570, VIYA_USER, VIYA_PASSWORD)  ##
            yolo_face, rn50 = load_mods(
                conn, mod_files="/dados/infra/api-rec-facial-dados"
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
                    ref = Image.open(io.BytesIO(ref_thomas))
                    ref.save(os.path.join(UPLOAD_FOLDER, "temp2.jpg"))

                    ref = run_proc(
                        os.path.join(UPLOAD_FOLDER, "temp2.jpg"), conn, yolo_face, rn50
                    )

                    os.remove(os.path.join(UPLOAD_FOLDER, "temp2.jpg"))
                    cred = Cred(id=cpf, features=ref)
                    db.session.add(cred)
                    db.session.commit()
                except:
                    conn.close()  ##
                    continue

            files = [
                f
                for f in os.listdir(os.path.join(BATCH_FOLDER, name))
                if f.startswith(".") is False
            ]
            recusa = ""
            total = 0
            aceita = 0
            # Iterar por arquivo
            for file in files:
                if not allowed_file(file, length=False):
                    continue
                caminho = os.path.join(BATCH_FOLDER, name, file)
                nova = orienta(caminho)
                nova.save(caminho)

                resp, julga = classifica(
                    conn, caminho, ref, yolo_face, rn50, nova, threshold=SIM_THRESHOLD
                )

                os.remove(caminho)

                total += 1
                if julga:
                    aceita += 1
                else:
                    recusa += file + " "

            lote = Batch(
                cred=cpf,
                acesso=momento,
                total=total,
                aprovadas=aceita,
                recusadas=recusa[0 : (len(recusa) - 1)],
            )
            db.session.add(lote)
            db.session.commit()
            conn.close()  ##

        # Removendo arquivos usados para a análise
        os.remove(BATCH_FOLDER + "/" + filename)
        [shutil.rmtree(BATCH_FOLDER + "/" + i) for i in creds]
        return {"message": "Avaliação dos lotes finalizada"}


@name_space.route("/batch/<string:numcred>")
class BatchGetDel(Resource):
    @name_space.doc(
        params={
            "numcred": "Especificar o número da credencial (CPF) para obter todos os registros de avaliação do indivíduo"
        },
        responses={200: "OK", 400: "Credencial não consta no banco de dados"},
    )
    def get(self, numcred):
        batches = Batch.query.filter_by(cred=numcred)
        if batches.first():
            return [batch.json() for batch in batches]
        else:
            return {"message": "Credencial não consta no banco de dados"}, 400

    @name_space.doc(
        params={
            "numcred": "Especificar o número da credencial (CPF) para remover todos os registros de avaliação do indivíduo"
        },
        responses={
            200: "Registro dos acessos da credencial removidos",
            400: "Credencial não consta no banco de dados",
        },
    )
    def delete(self, numcred):
        registro = Batch.query.filter_by(cred=numcred).first()
        # Consta ao menos um registro da credencial?
        if registro:
            db.session.query(Batch).filter(Batch.cred == numcred).delete()
            db.session.commit()
            return {"message": f"Registros de {numcred} removidos"}, 200
        else:
            return {"message": "Credencial não consta no banco de dados"}, 400
