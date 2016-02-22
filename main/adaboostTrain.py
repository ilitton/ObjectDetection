__authors__ = "Isabel Litton, Vincent Pham, Henry Tom"
__team__ = "CaptainDataCrunch"

import numpy as np
from sklearn import tree
import time
import sys

from adaboostFeatures import *
from adaboostImages import *

sys.setrecursionlimit(10000)

def calculate_error(prediction, label):
	"""Calculates error of classification
	:param prediction: label given from classifier
	:param label: actual label
	:return: 0 if correct, 1 if incorrect
	"""
	if prediction == label:
		return 0
	else:
		return 1

def calculate_alpha(error):
	"""Calculates weight used to update the distribution
	:param error_counter: sum of incorrect classifications
	:return: weight
	"""
	alpha = 0
	if error != 0:
		alpha = (.5) * np.log((1-error)/error)
	return alpha

def normalization_constant(dists):
	"""Calculates constant to normalize distribution so that the integral sums to 1
	:param dists: List of distribution values
	:return: constant value
	"""
	normalization = sum(dists)
	return normalization

def get_feature_values(gray_imgs, features):
	integral_images_dict = dict()
	start1 = time.time()
	for gray_img in gray_imgs:
		blocks = partition_image(gray_img)
		for i, feature in enumerate(features):
			for j, block in enumerate(blocks):
				key_img = (i,j)
				diff = feature(gray_img, block)
				if key_img in integral_images_dict:
					integral_images_dict[key_img].append(diff)
				else:
					integral_images_dict[key_img] = [diff]
	end1= time.time()
	print "time of triple loop is:", ((end1 - start1)/60), "min"
	return integral_images_dict

def weak_learner(gray_imgs, integral_images_dict, features, labels, distribution):
	"""Creates decision trees for each feature and each block and calculates training error. Selects the best model for a specific feature and block based on lowest training error.
	:param gray_imgs: list where each element is an array of pixels
	:param integral_images_dict:
	:param features: list of function names to caculate features
	:param labels: list of 1's or -1's
	:param distribution: list of weights for each image
	:return: tuple of (best_model, best_block, best_feature, lowest_error_rate, correctly_classified)
	"""
	best_feature = []
	correctly_classified = []
	lowest_error_rate = 1.0
	best_model = []
	best_block = []

	start2 = time.time()
	for k, v in integral_images_dict.items():
		X = v
		X_list = [[item] for item in X]
		clf1 = tree.DecisionTreeClassifier(max_depth = 1)
		clf = clf1.fit(X_list, labels)
		predictions = clf.predict(X_list)
		#print predictions.tolist()
		#print predictions.tolist()[0]
		#print type(predictions), type(predictions.tolist()), type(predictions.tolist()[0])
		incorrectly_classified = [x[0] != x[1] for x in zip(predictions.tolist(), labels)]
		error_rate = sum([x[0]*x[1] for x in zip(distribution, incorrectly_classified)])
		#print v
		print "error rate of key", k, "is", error_rate

		if error_rate < lowest_error_rate:
			best_feature = features[k[0]]
			best_block = k[1]
			lowest_error_rate = error_rate
			best_model = clf
			correctly_classified = [x[0] == x[1] for x in zip(predictions, labels)]
	end2 = time.time()
	print "time of classification loop is:", ((end2 - start2)/60), "min"
	return (best_model, best_block, best_feature, lowest_error_rate, correctly_classified)
  

def adaboost_train(pos_filepath, neg_filepath, T=3):
	"""Performs adaboost on training set
	:param pos_filepath: directory of positive files
	:param neg_filepath: directory of negative files
	:return: tuple of (alphas, best_models, best_blocks, best_features) where alphas are the weights of the models
	"""
	images = get_gray_imgs(pos_filepath, neg_filepath)

	gray_imgs = [x[0] for x in images]
	labels = [x[1] for x in images]

	n = len(gray_imgs)
	error = 0

	dists = [1.0/n for i in range(n)]

	alphas = list()
	correctly_classified = list()
	error_counter = 0

	features = [feat_two_rectangles, feat_three_rectangles, feat_four_rectangles]
	integral_images_dict = get_feature_values(gray_imgs, features)

	best_models = list()
	best_features = list()
	best_blocks = list()	
	error_rate_list = list()
	for t in range(T):
		best_model, best_block, best_feature, lowest_error_rate, correctly_classified = weak_learner(gray_imgs, integral_images_dict, features, labels, dists)
		error_rate_list.append(lowest_error_rate)
		#print best_model, best_block, best_feature, lowest_error_rate, correctly_classified
		print lowest_error_rate
		best_models.append(best_model)
		best_features.append(best_feature)
		best_blocks.append(best_block)
		alpha = calculate_alpha(lowest_error_rate)
		alphas.append(alpha)
		for i in range(n):
			if correctly_classified[i] == True:
				dists[i] = dists[i]*np.exp(-alpha)  # update distributions for each image based on if they are correctly classified
			else:
				dists[i] = dists[i]*np.exp(alpha)
		normalization = normalization_constant(dists)
		dists = [x/normalization for x in dists]
		#print "distributution", dists
	return alphas, best_models, best_blocks, best_features, error_rate_list