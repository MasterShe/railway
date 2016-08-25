#!/usr/bin/python
# coding=utf-8
from svmutil import *
from aubio import source, pitch
import time
import random
import getpass
import urllib, urllib2
from cookielib import CookieJar

HOP_SIZE = 512
FRAME_SIZE = 2048
SIMPLE_RATE = 8000
FEATURE_SIZE = 8
PITCH_METHOD = 'yinfft'

INIT_URL = 'http://railway.hinet.net/check_ctno1.jsp'
IMAGE_URL = 'http://railway.hinet.net/ImageOut.jsp?pageRandom=%.16f'
AUDIO_URL = 'http://railway.hinet.net/PronounceRandonNumber.do?pageRandom=%.16f'
ORDER_URL = 'http://railway.hinet.net/order_no1.jsp'

# http://railway.hinet.net/ctno1.js
def init_session():
	person_id = getpass.getpass('請輸入身分證字號: ')
	from_station = raw_input('請輸入起站代碼(台北:100): ')
	to_station = raw_input('請輸入到站代碼(花蓮:051): ')
	getin_date = raw_input('請輸入乘車日期(xxxx/xx/xx): ')
	train_no = raw_input('請輸入車次代碼: ')
	order_qty_str = raw_input('請輸入訂票張數: ')
	n_order_qty_str = raw_input('一般車廂(若非普悠瑪輸入0): ')
	z_order_qty_str = raw_input('桌型座位(若非普悠瑪輸入0): ')
	params = {
		'person_id': person_id, 'from_station': from_station, 'to_station': to_station,
		'getin_date': getin_date + '-08', 'train_no:': train_no, 'order_qty_str': order_qty_str,
		't_order_qty_str': '0', 'n_order_qty_str': n_order_qty_str, 'd_order_qty_str': '0',
		'b_order_qty_str': '0', 'z_order_qty_str': z_order_qty_str, 'returnTicket': '0'
	}
	opener.open(urllib2.Request(INIT_URL, urllib.urlencode(params))).read()
	return params

def save_data(url, output):
	headers = {'referer': INIT_URL};
	data = opener.open(urllib2.Request(url, None, headers)).read()
	if len(output) > 0:
		f = open(output, 'wb')
		f.write(data)

def buy_ticket(params):
	rand = random.random()
	stamp = int(time.time())
	save_data(IMAGE_URL % rand, 'Temp/%d.jpg' % stamp)
	save_data(AUDIO_URL % rand, 'Temp/%d.wav' % stamp)
	params['randInput'] = char_pitches_to_string(split_pitches(get_pitches('Temp/%d.wav' % stamp)))
	print params['randInput']
	headers = {'referer': INIT_URL};
	resp = opener.open(urllib2.Request(ORDER_URL, urllib.urlencode(params), headers)).read()
	resp = resp.decode('big5').encode('utf-8')
	return resp.find('亂數號碼錯誤') == -1

def split_pitches(pitches):
	zero_count = -1
	char_pitches = []
	for i in range(len(pitches)):
		if pitches[i] != 0 and zero_count >= 0 and zero_count <= 3:
			zero_count = 0
			char_pitches[len(char_pitches) - 1] += [pitches[i]]
		elif pitches[i] != 0:
			zero_count = 0
			char_pitches.append([pitches[i]])
		elif zero_count >= 0:
			zero_count += 1
	return char_pitches

def get_pitches(filename):
	pitches = []
	s = source(filename, 8000, HOP_SIZE)
	p = pitch(PITCH_METHOD, FRAME_SIZE, HOP_SIZE, SIMPLE_RATE)
	while True:
	    samples, read = s()
	    pit = p(samples)[0]
	    pitches += [pit]
	    if read < HOP_SIZE: break
	return pitches

def char_pitches_to_string(char_pitches):
	string = ''
	for i in range(len(char_pitches)):
		labels = [0.0]
		data = [{}]
		for j in range(len(char_pitches[i]), feature_s):
			char_pitches[i].append(0)
		for j in range(len(char_pitches[i])):
			data[0][j+1] = char_pitches[i][j]
		p_labels, p_acc, p_vals = svm_predict(labels, data, model, '-q')
		string += str(int(p_labels[0]))
	return string

def main():
	global opener, model
	cj = CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	model = svm_load_model('Data/svm.model')
	buy_session = init_session()
	while buy_ticket(buy_session) == False:
		print "buy_ticket failed."

if __name__ == '__main__':
	main()
