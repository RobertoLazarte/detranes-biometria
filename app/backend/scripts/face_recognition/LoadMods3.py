# Preparation
import os
# Pacote para obter localização de pastas e arquivos
import sys
import swat
# Pacote que permite realizar a integração Viya-Python
import pandas as pd
import swat
import numpy as np
import dlpy
from dlpy import Model
swat.options.cas.print_messages = False
# Permitir que sejam mostradas as mensagens do CAS
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter(action='ignore', category=FutureWarning)


def load_mods(conn, mod_files):
    # Tiny Yolo V2
    yolo_face = Model.from_sashdat(
        conn=conn, path=mod_files+'/Tiny-Yolov2_face.sashdat')

    # ResNet 50
    rn50 = Model.from_sashdat(
        conn=conn, path=mod_files+'/rn50.sashdat')

    # Fecha conexão
    return yolo_face, rn50
