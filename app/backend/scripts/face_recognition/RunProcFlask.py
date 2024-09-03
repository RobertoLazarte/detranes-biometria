# Procedure
import os
# Pacote para obter localização de pastas e arquivos
import sys
import re
import swat
# Pacote que permite realizar a integração Viya-Python
import pandas as pd
import numpy as np
import dlpy
from dlpy import Model
swat.options.cas.print_messages = False
# Permitir que sejam mostradas as mensagens do CAS
from scipy.spatial.distance import cosine
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter(action='ignore', category=FutureWarning)


def listdir(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f


def run_proc(file, conn, yolo_face, rn50):
    # Carregando imagem
    foto = dlpy.ImageTable.load_files(conn, path=file)
    nfoto = foto.resize(416, 416, inplace=False)
    # Identificando bounding box
    yolo_face.predict(nfoto)

    # Recortando rosto da foto original
    allcols = yolo_face.valid_res_tbl.to_frame()
    pattern = re.compile(r'^\_P\_Object\d{1,}\_')
    my_cols = [
        i for i, my_str in enumerate(allcols.columns)
        if (pattern.match(my_str) is not None)]
    probs = allcols[allcols.columns[my_cols]]
    num = re.search(r'\d{1,}', str(probs.columns[[i for i,
                    mycol in enumerate(np.array(probs)[0, :])
                    if mycol == np.nanmax(np.array(probs))]])).group(0)
    getcols = [
        '_Object' + num + '_x', '_Object' + num + '_y',
        '_Object' + num + '_width', '_Object' + num + '_height']
    my_coords = np.array(allcols[getcols])
    W = foto.image_summary[1]
    H = foto.image_summary[3]

    if ~np.isnan(my_coords[:, 0]):
        my_coords[:, 0] = (my_coords[:, 0]-my_coords[:, 2]/2)*W
        my_coords[:, 1] = (my_coords[:, 1]-my_coords[:, 3]/2)*H
        my_coords[:, 2] = my_coords[:, 2]*W
        my_coords[:, 3] = my_coords[:, 3]*H

        foto.crop(
            x=my_coords[0, 0], y=my_coords[0, 1], width=my_coords[0, 2],
            height=my_coords[0, 3], inplace=True)

    foto.resize(224, 224, inplace=True)

    # Recuperando os embeddings
    rn_embed = rn50.get_features(foto, "avg_pool")[0]
    # Quero apenas os embeddings, não preciso das outras informações
    return rn_embed


def get_resul(conn, filepath, origem, yolo_face, rn50):
    registry = listdir(filepath)
    cand_embed = run_proc(filepath, conn, yolo_face, rn50)
    orig_embed = run_proc(origem, conn, yolo_face, rn50)
    resul = cosine(orig_embed, cand_embed)
    return resul


def classifica(conn, filepath, origem, yolo_face, rn50, threshold=0.5):
    score = get_resul(conn, filepath, origem, yolo_face, rn50)
    if score <= threshold:
        my_class = True
    else:
        my_class = False
    score = int((1-score)*100)
    return my_class, score
