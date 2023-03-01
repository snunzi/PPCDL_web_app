
import sys
import os
import re
"""
Borrowed base code from
"""

def define_fastq_label(x):
	lanes = ['L001','L002','L003','L004']
	for i in lanes:
		x = x.replace("%s_"%(i),"")
	return x


def is_lane(x,y):
	lanes = ['L001','L002','L003','L004']
	items1 = re.split("_|-|\.",x)
	items2 = re.split("_|-|\.",y)
	num_diff = 0
	lane_diff = False
	if len(items2) != len(items1):
		return False
	for i in range(len(items1)):
		if items1[i] != items2[i]:
			num_diff+=1
			if items1[i] in lanes and items2[i] in lanes:
				lane_diff = True
	if lane_diff and num_diff==1:
		return True
	return False

def output_bash(groups):
	for i in groups:
		command = "cat "+" ".join(groups[i]) + " > "+define_fastq_label(i)
		os.system(command)
		for f in groups[i]:
			if os.path.isfile(f):
				os.remove(f)

def merge_fastq(file):
	groups = {}
	used = []
	#print (file)
	for i in file:
		if i in used:
			continue
		groups[i] = [i]
		for j in file:
			if is_lane(i,j):
				groups[i].append(j)
				used.append(j)
	keysList = list(groups.keys())
	keysList = [i.split('/')[-1] for i in keysList]
	output_bash(groups)
	return keysList
