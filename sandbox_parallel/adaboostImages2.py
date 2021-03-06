__authors__ = "Isabel Litton, Vincent Pham, Henry Tom"
__team__ = "CaptainDataCrunch"

import cv2
from adaboostData import *
from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

def read_image(imagefile):
    """Change image to grayscale
    :param imagefile: image
    :return: image in grayscale
    """
    # read in image
    img = cv2.imread(imagefile)

    # change image to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return gray_img


def get_gray_imgs(pos_filepath, neg_filepath):
    """Labels and converts images to gray scale
    :param pos_filepath: path of directory containing all pos images
    :param neg_filepath: path of directory containing all neg images
    :return: list of tuples(gray image, label)
    """
    pos_images = load_data(pos_filepath, 1)
    neg_images = load_data(neg_filepath, -1)
    images = pos_images + neg_images
    gray_imgs = list()
    for image in images:
        gray_imgs.append((read_image(image[0]), image[1]))
    return gray_imgs


def s(gray_img, x, y):
    """Cumulative row sum to calculate integral image
    :param gray_img: image in gray scale
    :param x: x coordinate
    :param y: y coordinate
    :return: row sum of pixel intensities
    """
    sums = 0
    if y == -1:
        return sums
    else:
        sums += gray_img[y][x] + s(gray_img, x, y - 1)
    return sums


def ii(gray_img, x, y):
    """Cumulative column sum to calcualte integral image
    :param gray_img: image in gray scale
    :param x: x coordinate
    :param y: y coordinate
    :return: column sum of pixel intensities
    """
    sums = 0
    if x == -1:
        return sums
    else:
        sums += ii(gray_img, x - 1, y) + s(gray_img, x, y)
    return sums


def integralImage2(gray_img, locations):
    """Calculates integral image to compute rectangle features
    :param gray_img: image in gray scale
    :param x0, y0, x1, y1: coordinates describing the rectangle
    :return: sum of all the pixels above and to the left of (x1, y1)
    """
    x0, y0, x1, y1 = locations
    D = ii(gray_img, x1, y1)
    C = ii(gray_img, x0, y1)
    B = ii(gray_img, x1, y0)
    A = ii(gray_img, x0, y0)

    diff = D - C - B + A
    return diff

def integralImage(gray_img, locations):
    sum = 0
    if rank == 0:
        D = iiD(gray_img, locations)
        comm.send(D, dest=4, tag=11)
    if rank == 1:
        C = iiC(gray_img, locations)
        comm.send(C, dest=4, tag=12)
    if rank == 2:
        B = iiB(gray_img, locations)
        comm.send(B, dest=4, tag=13)
    if rank == 3:
        A = iiA(gray_img, locations)
        comm.send(A, dest=4, tag=14)
    if rank == 4:
        data1 = comm.recv(source=0, tag=11)
        data2 = comm.recv(source=1, tag=12)
        data3 = comm.recv(source=2, tag=13)
        data4 = comm.recv(source=3, tag=14)

        return data1 - data2 - data3 + data4
    else:
        return 0

def iiD(gray_img, locations):
    x0, y0, x1, y1 = locations
    D = ii(gray_img, x1, y1)
    return D

def iiC(gray_img, locations):
    x0, y0, x1, y1 = locations
    C = ii(gray_img, x0, y1)
    return C

def iiB(gray_img, locations):
    x0, y0, x1, y1 = locations
    B = ii(gray_img, x1, y0)
    return B

def iiA(gray_img, locations):
    x0, y0, x1, y1 = locations
    A = ii(gray_img, x0, y0)
    return A

def partition_image(gray_img):
    """Splits image into 3x3 windows
    :param gray_img: array of pixels
    :return: list of tuples where each tuple = (top left corner of window, bottom right corner of window)
    """
    width, height = gray_img.shape
    x = width / 3
    y = height / 3
    block1 = (0, 0, x - 1, y - 1)
    block2 = (x, 0, 2 * x - 1, y - 1)
    block3 = (2 * x, 0, 3 * x - 1, y - 1)
    block4 = (0, y, x - 1, 2 * y - 1)
    block5 = (x, y, 2 * x - 1, 2 * y - 1)
    block6 = (2 * x, y, 3 * x - 1, 2 * y - 1)
    block7 = (0, 2 * y, x - 1, 3 * y - 1)
    block8 = (x, 2 * y, 2 * x - 1, 3 * y - 1)
    block9 = (2 * x, 2 * y, 3 * x - 1, 3 * y - 1)

    return [block1, block2, block3,
            block4, block5, block6,
            block7, block8, block9]
