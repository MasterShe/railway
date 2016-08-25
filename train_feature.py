#!/usr/bin/python

from svmutil import *

labels, data = svm_read_problem('Data/Train_features.txt')
model = svm_train(labels, data, '')
svm_save_model('Data/svm.model', model)