################################################################################################################################
################################################################################################################################
############################                                                                        ############################
############################     QUANDO INTERROMPER O PROCESSO, FECHAR A CONEXÃO (BLOCO ABAIXO)     ############################
############################                                                                        ############################
################################################################################################################################
################################################################################################################################

from scripts.api_facial import app
#from scripts.api_facial.functions.recfacial import conn

APP_IP = '0.0.0.0'
#APP_PORT = 7055

if __name__ == '__main__':
    app.run(debug=False,host=APP_IP)#, port=APP_PORT)