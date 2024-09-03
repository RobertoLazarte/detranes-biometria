from scripts.api_facial import db
from scripts.api_facial.models.logscred import Acesso
from flask_restplus import Resource
from scripts.api_facial import name_space

@name_space.route('/logs/<string:numcred>')
# Registro dos acessos (acesso por credencial)
class Logs(Resource):
    @name_space.doc(params = {'numcred': 'Especificar o número da credencial (CPF) para obter todos os registros de avaliação do indivíduo'},
                              responses = {200: 'OK',
                                          400: 'Credencial não consta no banco de dados'})
    def get(self, numcred):
        creds = Acesso.query.filter_by(cred=numcred)
        if creds.first():
            return [cred.json() for cred in creds]
        else:
            return {'message': 'Credencial não consta no banco de dados'}, 400

    @name_space.doc(params = {'numcred': 'Especificar o número da credencial (CPF) para remover todos os registros de avaliação do indivíduo'},
                              responses = {200: 'Registro dos acessos da credencial removidos',
                                          400: 'Credencial não consta no banco de dados'})
    def delete(self, numcred):
        registro = Acesso.query.filter_by(cred=numcred).first()
        # Consta ao menos um registro da credencial?
        if registro:
            db.session.query(Acesso).filter(Acesso.cred == numcred).delete()
            db.session.commit()
            return {
                'message': f'Registro dos acessos de {numcred} removidos'}, 200
        else:
            return {'message': 'Credencial não consta no banco de dados'}, 400
