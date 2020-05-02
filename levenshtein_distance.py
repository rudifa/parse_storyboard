# https://github.com/imalic3/levenshtein-distance-python/blob/master/levenshtein_distance.py

import numpy
import sys

def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def find_nearest(item, candidates):
    sc = sorted(candidates, key=lambda candidate: levenshteinDistance(item, candidate))
    return sc[0]

def doit():
    if len(sys.argv) >= 3:
    	print('------ Calculating ------')
    	msg = ''
    	lab = ''
    	with open(sys.argv[1], encoding='utf-8') as f:
    	    lab = f.read().replace('\n', '').replace(' ','')

    	with open(sys.argv[2], encoding='utf-8') as f:
    	    msg = f.read().replace('\n', '').replace(' ','')

    	#result = wer(list(lab), list(msg), False)
    	result = levenshteinDistance(lab, msg)
    	bigger = max(len(lab), len(msg))
    	result = ((bigger - result) / bigger) * 100
    	print('Accuracy : %.2f%%'%(result))
    else:
    	print('Error: Invalid parameters')
    	print('Usage: levenshtein_distance.py [label_file] [result_file]')

if __name__ == "__main__":

    vcs = [
        'StickerGridViewController',
        'StickerShopViewController',
        'FeedbackViewController',
        'SelectCalendarViewController',
        'LegalViewController',
        'SubscriptionViewController',
        'ShowQRCodeViewController',
    ]

    uws = [
        'unwindToStickerGridVC',
        'unwindToShowQRCodeVC',
        'unwindToSubscriptionVC',
        'unwindToLegalVC'
    ]
    for uw in uws:
        uw = uw.replace('VC', 'ViewController')
        for vc in vcs:
            d = levenshteinDistance(uw, vc)
            print(d, uw, vc)
        print()

    for uw in uws:
        uw = uw.replace('VC', 'ViewController')
        nearest = find_nearest(uw, vcs)
        print(uw, nearest)
