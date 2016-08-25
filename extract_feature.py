#!/usr/bin/python

import sys
from aubio import source, pitch

HOP_SIZE = 512
FRAME_SIZE = 2048
SIMPLE_RATE = 8000
PITCH_METHOD = 'yinfft'

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

def read_arguments():
	if len(sys.argv) < 2 or (sys.argv[1] != 'test' and sys.argv[1] != 'train'):
		print 'usage: ./extract_feature.py test'
		print '   or: ./extract_feature.py train'
		return False
	sys.argv[1] = 'T%s' % sys.argv[1][1:]
	return True

def main():
	if read_arguments() == False:
		exit(1)
	max = 0
	audio_char_pitches = []
	answers = [line.rstrip('\n') for line in open('Data/%s/answer.txt' % sys.argv[1])]

	for i in range(len(answers)):
		filename = 'Data/%s/%d.wav' % (sys.argv[1] ,i)
		audio_char_pitches.append(split_pitches(get_pitches(filename)))
		print '%s' % filename
		for j in range(len(audio_char_pitches[i - 1])):
			if (len(audio_char_pitches[i - 1][j])> max):
				max = len(audio_char_pitches[i - 1][j])
			print  len(audio_char_pitches[i - 1][j]) ,audio_char_pitches[i - 1][j]

	output_file = open('Data/%s_features.txt' % sys.argv[1], 'a');
	for i in range(len(answers)):
		if len(answers[i]) != len(audio_char_pitches[i]):
			print 'Index %d: length not match' % i
			break
		for j in range(len(audio_char_pitches[i])):
			for k in range(len(audio_char_pitches[i][j]), max):
				audio_char_pitches[i][j].append(0)
			output_file.write(answers[i][j] + ' ' + ' '.join([(str(index + 1) + ':' + str(value)) for index, value in enumerate(audio_char_pitches[i][j])]) + '\n')
	output_file.close()

if __name__ == '__main__':
	main()

