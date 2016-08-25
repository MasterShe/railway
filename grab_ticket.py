#!/usr/bin/python
# coding=utf-8

import os
import re
import sys
import time
import thread
import random
import urllib, urllib2
from svmutil import *
from datetime import datetime
from aubio import source, pitch
from cookielib import CookieJar
from threading import Thread

HOP_SIZE = 512
FRAME_SIZE = 2048
SIMPLE_RATE = 8000
FEATURE_SIZE = 8
PITCH_METHOD = 'yinfft'

INIT_URL = 'http://railway.hinet.net/check_ctno1.jsp'
CTNO_JS_URL = 'http://railway.hinet.net/ctno1.js'
CTNO_HTM_URL = 'http://railway.hinet.net/ctno1.htm'
IMAGE_URL = 'http://railway.hinet.net/ImageOut.jsp?pageRandom=%.16f'
AUDIO_URL = 'http://railway.hinet.net/PronounceRandonNumber.do?pageRandom=%.16f'
ORDER_URL = 'http://railway.hinet.net/order_no1.jsp'

def read_arguments():
	if len(sys.argv) == 2:
		return int(sys.argv[1])
	return 1

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
	
def char_pitches_to_string(char_pitches):
	string = ''
	for i in range(len(char_pitches)):
		labels = [0.0]
		data = [{}]
		for j in range(len(char_pitches[i]), FEATURE_SIZE):
			char_pitches[i].append(0)
		for j in range(len(char_pitches[i])):
			data[0][j+1] = char_pitches[i][j]
		p_labels, p_acc, p_vals = svm_predict(labels, data, model, '-q')
		string += str(int(p_labels[0]))
	return string

def input_params():
	params = {
		'person_id': '', 'from_station': '', 'to_station': '',
		'getin_date': '', 'train_no': '', 'order_qty_str': '0',
		't_order_qty_str': '0', 'n_order_qty_str': '0', 'd_order_qty_str': '0',
		'b_order_qty_str': '0', 'z_order_qty_str': '0', 'returnTicket': '0'
	}
	cj = CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	htm_resp = opener.open(urllib2.Request(CTNO_HTM_URL)).read()
	htm_resp = htm_resp.decode('big5').encode('utf-8')
	js_resp = opener.open(urllib2.Request(CTNO_JS_URL)).read()
	js_resp = js_resp
	# person_id
	params['person_id'] = raw_input('請輸入身分證字號: ').capitalize()
	if not re.match('^[A-Z][12][0-9]{8}$', params['person_id']):
		print '身分證字號格式錯誤.'
		return None
	table = "10987654932210898765431320"
	check_sum = int(table[ord(params['person_id'][0])-65]) + int(params['person_id'][9])
	for i in range(1, 9): check_sum += int(params['person_id'][i]) * (9 - i)
	if check_sum % 10 != 0: 
		print '身分證字號驗證失敗.' 
		return None
	# from_station
	params['from_station'] = raw_input('請輸入起站代碼(台北:100): ')
	if not re.match('[0-9]{3}$', params['from_station']):
		print '起站代碼格式錯誤.'
		return None
	from_station_obj = re.search('%s-([^<]+)' % params['from_station'], htm_resp)
	if from_station_obj == None:
		print '起站代碼驗證失敗.'
		return None
	# to_station
	params['to_station'] = raw_input('請輸入到站代碼(花蓮:051): ')
	if not re.match('[0-9]{3}$', params['to_station']):
		print '到站代碼格式錯誤.'
		return None
	to_station_obj = re.search('%s-([^<]+)' % params['to_station'], htm_resp)
	if to_station_obj == None:
		print '到站代碼驗證失敗.'
		return None
	# getin_date
	params['getin_date'] = raw_input('請輸入乘車日期(xxxx/xx/xx): ')
	if not re.match('^(19|20)[0-9]{2}\/(0[0-9]|1[0-2])\/([0-2][0-9]|3[0-1])$', params['getin_date']):
		print '乘車日期格式錯誤.'
		return None
	diff_days = abs(datetime.now() - datetime.strptime(params['getin_date'][:10], '%Y/%m/%d')).days
	params['getin_date'] = '%s-%d' % (params['getin_date'][:10], diff_days)
	
	# train_no
	params['train_no'] = raw_input('請輸入車次代碼: ')
	if not re.match('[0-9]+', params['train_no']):
		print '車次代碼格式錯誤.'
		return None
	# train_box_data
	has_box = {'n': False, 'd': False, 't': False, 'b': False, 'z': False}
	map_box = {' ': 'n', 'D': 'd', '5': 't', 'B': 'b', 'Z': 'z'}
	train_box_data = re.search('[0-9]{6}%s *([^"]+)' % params['train_no'], js_resp)
	if train_box_data == None:
		train_box_data = []
	else:
		train_box_data = train_box_data.group(1)
	for i in range(len(train_box_data)):
		if train_box_data[i] in map_box:
			has_box[map_box[train_box_data[i]]] = True

	if has_box['d'] or has_box['b'] or has_box['z']:
		has_box['t'] = False
		has_box_message = {'n': '一般車廂', 'd': '商務車廂', 'b': '兩鐵車廂', 'z': '桌型座位'}
		for key, value in has_box.iteritems():
			if value:
				params['%s_order_qty_str' % key] = raw_input('請輸入%s張數: ' % has_box_message[key])
	elif has_box['t']:
		params['t_order_qty_str'] = raw_input('請輸入訂票張數: ')
	else:
		params['order_qty_str'] = raw_input('請輸入訂票張數: ')
	total = 0
	has_box = ['', 'n_', 'd_', 't_', 'b_', 'z_']
	for i in range(len(has_box)):
		if not re.match('[0-9]+', params['%sorder_qty_str' % has_box[i]]):
			print '訂票張數格式錯誤.'
			return None
		else:
			total += int(params['%sorder_qty_str' % has_box[i]])
	if total < 1 or total > 6:
		print '訂票張數有誤(總張數至少一張且至多六張).'
		return None
	params['order_qty_str'] = str(total)
	return params

def save_data(opener, url, output):
	headers = {'referer': INIT_URL};
	data = opener.open(urllib2.Request(url, None, headers)).read()
	if len(output) > 0:
		f = open(output, 'wb')
		f.write(data)

def init_session(opener, params):
	headers = {'referer': CTNO_HTM_URL};
	resp = opener.open(urllib2.Request(INIT_URL, urllib.urlencode(params), headers)).read()
	resp = resp.decode('big5').encode('utf-8')
	params = {}
	new_params = re.findall('input name="([^"]+)[^v]+value="([^"]+)', resp)
	for i in range(len(new_params)):
		params[new_params[i][0]] = new_params[i][1]
	diff_days = abs(datetime.now() - datetime.strptime(params['getin_date'][:10], '%Y/%m/%d')).days
	params['getin_date'] = '%s-%d' % (params['getin_date'][:10], diff_days)
	return params

def buy_ticket(opener, params, lock, thread_id):
	rand = random.random()
	stamp = int(time.time() * 1000)
	save_data(opener, IMAGE_URL % rand, '')
	save_data(opener, AUDIO_URL % rand, 'Temp/%d_%d.wav' % (thread_id, stamp))
	params['randInput'] = char_pitches_to_string(split_pitches(get_pitches('Temp/%d_%d.wav' % (thread_id, stamp))))
	os.remove('Temp/%d_%d.wav' % (thread_id, stamp))
	# print params['randInput']
	headers = {'referer': INIT_URL};
	resp = opener.open(urllib2.Request('%s?%s' % (ORDER_URL, urllib.urlencode(params)), None, headers)).read()
	resp = resp.decode('big5').encode('utf-8')
	message = re.search('spanOrderCode[^>]+>([0-9]+)', resp)
	if message != None:
		lock.acquire()
		print '%d: 您的車票已訂到. 電腦代碼: %s, 身分證字號: %s' % (thread_id, message.group(1), params['person_id'])
		lock.release()
		return True
	message = re.search('<strong>([^<]+)<\/strong>', resp)
	if message == None:
		lock.acquire()
		if resp.find('對不起，車票已訂完') != -1:
			print '%d: 對不起，車票已訂完, 重試中 ...' % thread_id
		else:	
			print '%d: 發生其餘未知的錯誤(EX:購票超過6張) ...' % thread_id
		lock.release()
		return False
	lock.acquire()
	print '%d: %s, 重試中 ...' % (thread_id, message.group(1))
	lock.release()
	return False

def grab_ticket(params, lock, thread_id):
	global stop
	cj = CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	buy_params = init_session(opener, params)
	# from datetime import date
	while buy_ticket(opener, buy_params, lock, thread_id) == False and stop == False:
		diff_days = abs(datetime.now() - datetime.strptime(params['getin_date'][:10], '%Y/%m/%d')).days
		params['getin_date'] = '%s-%d' % (params['getin_date'][:10], diff_days)

	stop = True
	thread.exit()

def main():
	global model, stop
	thread_count = read_arguments()
	model = svm_load_model('Data/svm.model')
	df_params = input_params()
	print
	stop = False
	threads = []
	lock = thread.allocate_lock()
	for i in range(thread_count):
		threads.append(Thread(target = grab_ticket, args = (df_params, lock, i + 1,)))
		threads[i].start()
	try:
		while True:
			for t in threads:
				t.join(1)
	except KeyboardInterrupt:
		stop = True
		exit()

if __name__ == '__main__':
	main()
