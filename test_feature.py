#!/usr/bin/python

from svmutil import *

labels, data = svm_read_problem('Data/Test_features.txt')
model = svm_load_model('Data/svm.model')
p_labels, p_acc, p_vals = svm_predict(labels, data, model)
