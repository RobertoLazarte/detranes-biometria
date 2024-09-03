import cv2
import dlpy
from dlpy import Model
import numpy as np
import os
import pandas as pd
from PIL import Image, ImageOps, ExifTags
import re
from scipy.spatial.distance import cosine
import swat
import pickle
from skimage.feature import local_binary_pattern
from math import isnan
from fabric import Connection
swat.options.cas.print_messages = False

#conn = swat.CAS('a-dtes-pvx05.sas.detran.es.gov.br',
#                5570,
#                'rodrigo.ferrari',
#                '{SAS002}23B6882C31A5DBF51C3F913F51CEA44B3C126085')

os.environ['TKESSL_OPENSSL_LIB'] = os.getenv('TKESSL_OPENSSL_LIB', '/usr/lib/x86_64-linux-gnu/libssl.so.1.1')
os.environ['CAS_CLIENT_SSL_CA_LIST'] = os.getenv('CAS_CLIENT_SSL_CA_LIST', '/dados/cacerts/trustedcerts.pem')
VIYA_HOST = os.getenv("VIYA_HOST", '10.0.12.50')
VIYA_PASSWORD = os.getenv("VIYA_PASSWORD", '{SAS002}23B6882C31A5DBF51C3F913F51CEA44B3C126085')
VIYA_USER = os.getenv("VIYA_USER", 'rodrigo.ferrari')
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", 0.5))
VIYA_OS_USER = os.getenv("VIYA_OS_USER")
VIYA_OS_PASSWORD = os.getenv("VIYA_OS_PASSWORD")

def copy_image_local_to_cas(local_file: str, cas_server_directory: str):
    with Connection(
            host=VIYA_HOST,
            user=VIYA_OS_USER,
            connect_kwargs={
                "password":VIYA_OS_PASSWORD 
            },
        ) as connection:
        connection.put(local_file, cas_server_directory)  
        
def delete_image_from_cas_server(cas_server_file: str):
    with Connection(
            host=VIYA_HOST,
            user=VIYA_OS_USER,
            connect_kwargs={
                "password":VIYA_OS_PASSWORD 
            },
        ) as connection:
        connection.run(f"rm {cas_server_file}")  

def orienta(image_full_path):
    image = Image.open(image_full_path)
    if image.mode == 'RGBA':
        image.load()
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        # 3 is the alpha channel
        image = background
        image = ImageOps.exif_transpose(image)
    return image


# Avaliação do arquivo
def allowed_file(filename, ALLOWED_EXTENSIONS=set(
        ['png', 'jpg', 'jpeg']), length=True):
    format_allow = '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS
    if length:
        name = filename.rsplit('.', 1)[0]
        name_allow = len(name) == 11 and name.isdigit()
    else:
        name_allow = True
    return format_allow and name_allow


# Carregamento dos modelos utilizados
def load_mods(conn, mod_files):
    # Tiny Yolo V2
    yolo_face = Model.from_sashdat(
        conn=conn, path=mod_files+'/Tiny-Yolov2_face.sashdat')
    # ResNet 50
    rn50 = Model.from_sashdat(conn=conn, path=mod_files+'/rn50.sashdat')
    return yolo_face, rn50

#yolo_face, rn50 = load_mods(conn, mod_files=os.environ.get("JUPYTER_HOME")
#                            + '/Teste_Integra/cnn_mods')

# Reset do CAS
def conn_reset(conn,mod_files):
    # Fechando a conexão
    conn.close()
    # Reabrindo a conexão
    conn = swat.CAS(VIYA_HOST,
                    5570,
                    VIYA_USER,
                    VIYA_PASSWORD)
    # Recarregando os modelos
    yolo_face, rn50 = load_mods(conn, mod_files=mod_files)
    return conn, yolo_face, rn50
    

#Modelo anti-spoofing temporariamente desabilitado
#escala, rf_spoof = pickle.load(open(os.environ.get("JUPYTER_HOME")
#                            + '/Teste_Integra/cnn_mods/rf_spoof.pkl', 'rb'))


# Procedimentos para obtenção das features
def run_proc(file, conn, yolo_face, rn50, PIL_img=None):
    # Carregando imagem
    foto = dlpy.ImageTable.load_files(conn, path=file)
    nfoto = foto.resize(416, 416, inplace=False)
    # Identificando bounding box
    yolo_face.predict(nfoto)
    # Recortando rosto da foto original
    allcols = yolo_face.valid_res_tbl.to_frame()
    pattern = re.compile(r'^\_P\_Object\d{1,}\_')
    my_cols = [i for i, my_str in enumerate(allcols.columns) if (pattern.match(my_str) is not None) and not isnan(allcols[allcols.columns[i]])]
    probs = allcols[allcols.columns[my_cols]]
    W = foto.image_summary[1]
    H = foto.image_summary[3]
    try:
        num = re.search(r'\d{1,}',
                        str(probs.columns[[i for i,mycol in enumerate(np.array(probs)[0, :]) if mycol == np.max(np.array(probs))]])).group(0)
        getcols = ['_Object'+num+'_x', '_Object'+num+'_y',
                   '_Object'+num+'_width', '_Object'+num+'_height']
        my_coords = np.array(allcols[getcols])[0]
        my_coords[0] = (my_coords[0]-my_coords[2]/2)*W
        my_coords[1] = (my_coords[1]-my_coords[3]/2)*H
        my_coords[2] = my_coords[2]*W
        my_coords[3] = my_coords[3]*H
        foto.crop(x=my_coords[0], y=my_coords[1], width=my_coords[2], height=my_coords[3], inplace=True)
    except:
        my_coords = np.array([0,0,W,H])

    #Procedimento anti-spoofing temporariamente desabilitado
    #if PIL_img is not None:
        #cv_img = cv2.cvtColor(np.array(PIL_img), cv2.COLOR_RGB2BGR)
        #coords=np.maximum(my_coords,0).astype(int)
        #cv_img = cv_img[coords[1]:coords[1]+coords[3], coords[0]:coords[0]+coords[2]]
        #cv_img = cv2.resize(cv_img,(224,224))
        #cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        #L = pd.Series(local_binary_pattern(cv_img, 24, 8,method="uniform").ravel()).value_counts().sort_index()
        #L=np.array(L.append(pd.Series(local_binary_pattern(cv_img, 8, 1,method="uniform").ravel()).value_counts().sort_index())).reshape(1, -1)
        #L=escala.transform(L)
        #if(rf_spoof.predict(L)==1): #Se a imagem nao for suspeita
        #    foto.resize(224, 224, inplace=True)
            # Recuperando os embeddings
        #    rn_embed = rn50.get_features(foto, "avg_pool")[0]
            # Quero apenas os embeddings, não preciso das outras informações
        #    return rn_embed
        #else:
        #    return('Imagem suspeita')
        
    foto.resize(224, 224, inplace=True)
    # Recuperando os embeddings
    rn_embed = rn50.get_features(foto, "avg_pool")[0]
    # Quero apenas os embeddings, não preciso das outras informações
    return rn_embed


# Comparação das features via medida de similaridade
def classifica(conn, filepath, orig_embed, yolo_face, rn50, PIL_image, threshold=SIM_THRESHOLD):
    cand_embed = run_proc(filepath, conn, yolo_face, rn50, PIL_image)
    if type(cand_embed)==str:
        return cand_embed, False
    else:
        score = int((1-cosine(orig_embed, cand_embed))*100)
        julga = score >= (threshold*100)
        if julga:
            return f"Identidade validada ({score}%)", julga
        else:
            return f"Identidade nao validada({score}%)", julga
