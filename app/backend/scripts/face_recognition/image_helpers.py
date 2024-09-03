# Module created to develop auxiliary functions to deal with images
import cv2
import face_recognition
from matplotlib import pyplot
from PIL import Image, ExifTags
import numpy as np
import datetime
import os
from imutils import paths


def open_image_canon_position(image_full_path):
    ''' Open an image file and returns it the image in it at canon position'''

    image = Image.open(image_full_path)

    for orientation in ExifTags.TAGS.keys():
        # First we verify if there's the metadata needed to make know if
        # the image is in canon position
        if ExifTags.TAGS[orientation] == 'Orientation':
            break

    if(image._getexif()):
        exif = dict(image._getexif().items())
        try:
            if exif[orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image = image.rotate(90, expand=True)
        except KeyError:
            print("Codificação da imagem inválida")

    return image


def rotate_image(image, degrees):
    # get image height, width
    (h, w) = image.shape[:2]
    # calculate the center of the image
    center = (w / 2, h / 2)
    scale = 1.0

    # Perform the counter clockwise rotation holding at the center
    M = cv2.getRotationMatrix2D(center, degrees, scale)
    rotated = cv2.warpAffine(image, M, (h, w))

    return rotated


def resize_image(image, minimum_size):
    scale_percent = 50
    width = int(image.shape[1] / 2)
    height = int(image.shape[0] / 2)
    while(width > minimum_size and height > minimum_size):
        width = int(width / 2)
        height = int(height / 2)

    dim = (width, height)

    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)


def find_face(image):
    ''' Receives an image in canon pose and returns
    the tuple boxes and the original image resized '''
    resized = resize_image(image, 400)

    # detect the (x, y)-coordinates of the bounding boxes
    # corresponding to each face in the input image
    boxes = []

    boxes = face_recognition.face_locations(resized, model="cnn")

    return boxes, resized


def crop_face(image):
    ''' Receives a cv2 vector image and returns an image of a single face in it
    if none was found returns the original image '''

    boxes, resized = find_face(image)

    if(boxes):
        bottom_y, bottom_x, floor_y, floor_x = boxes[0]
        face = resized[bottom_y:floor_y, floor_x:bottom_x]
        return face

    return image


def open_crop_and_resize_face(filePath):
    # load image from file
    original_image = open_image_canon_position(filePath)
    # Covert to RGB and also to an array that can be interpreted by openCV
    image_nparray = cv2.cvtColor(
        np.array(original_image), cv2.COLOR_BGR2RGB)
    #  cv2.imshow("Image", image)
    #  cv2.waitKey(0)
    face = crop_face(image_nparray)
    face = cv2.resize(face, (224, 224))

    return face, original_image


def save_image(
    imagem_comparada, nome_arquivo_comparado, nome_arquivo_conhecido,
        nome_database):
    '''Receive image known and unknown to save them in folder for future
    comparison and presentation'''
    now = datetime.datetime.now()
    # Primeiro nós encontramos o caminho para a primeira foto da pessoa
    # sendo comparada na base de dados conhecida
    imagePath = list(paths.list_images(
        "./database_conhecidos/" + nome_arquivo_conhecido[:-5]))[0]

    # Depois criamos a pasta, caso ela não exista.
    if os.makedirs("./database_" + nome_database):
        print(
            "[INFO]Diretório para a base de dados "
            + nome_database + " criada com sucesso.")

    # E então armazenamos a foto comparada seguida da original com suas
    # respectivas denotações
    try:
        imagem_comparada.save(
            "./database_" + nome_database + "/" + str(now.day) + "_"
            + str(now.hour) + "h" + str(now.minute) + 'm' + str(now.second)
            + "s_" + nome_arquivo_comparado[:-5] + "_comparado" + ".jpg")
    except:
        print(
            "[INFO]Foto " + nome_arquivo_comparado[-5:]
            + " teve problemas ao ser armazenado.")

    try:
        imagem_conhecida = Image.open(imagePath)
        imagem_conhecida.save(
            "./database_" + nome_database + "/" + str(now.day) + "_"
            + str(now.hour) + "h" + str(now.minute) + 'm' + str(now.second)
            + "s_" + nome_arquivo_comparado[:-5] + "_original" + ".jpg")
    except:
        print(
            "[INFO]Foto " + nome_arquivo_comparado[-5:]
            + "_original teve problemas ao ser armzenado")
