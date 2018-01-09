import json
import numpy as np
import random

# given a point1 x,y and a point2 x,y returns distance in miles
# points are given in long,lat geospatial cordinates
def distance(point1,point2):
	point1 = np.array(point1)
	point2 = np.array(point2)
	return np.linalg.norm(point1-point2)

# interpolates frmo distances
def interpolate(pt1,pt2,dist1,dist2,dist):
	percent = (dist - dist1) / (dist2 - dist1)
	x = percent * (pt2[0] - pt1[0]) + pt1[0]
	y = percent * (pt2[1] - pt1[1]) + pt1[1]
	return [x,y]

def unique(list):
	new_uniques = []
	newdict = {}
	for i in list:
		if newdict.get(str(i),False) == False:
			new_uniques.append(i)
			newdict[str(i)] = ""
	return new_uniques

# fuzzing a pt
def fuzz(pt):
	return [pt[0] + random.uniform(-.000001,.000001),pt[1] + random.uniform(-.000001,.000001)]

# fuzzing line
def fuzz_line(line):
	return [fuzz(i) for i in line]

# doing some shit
def distance_along(line,distances,fuzzbool=True):
	# fixing if a float is given
	if isinstance(distances,float):
		distances = [distances]
	if isinstance(distances,np.ndarray):
		distances = distances.tolist()

	# creating iterator
	distances = iter(distances)

	# pushing the unique values out of the array if needed
	line = unique(line)

	# setting up the interator if needed	
	try:
		dist = next(distances)
	except:
		dist = -10000
	
	oldpt = line[0]
	newlist = []
	totaldistance,old_distance = 0.0,0.0
	for i,pt in enumerate(line[1:]):
		boolval = False
		totaldistance += distance(oldpt,pt)
		newlist.append(oldpt)
		#
		while old_distance <= dist <= totaldistance:
			newpt = interpolate(oldpt,pt,old_distance,totaldistance,dist)
			newlist.append(newpt)
			newlist.append(newpt)
			try:
				dist = next(distances)
			except StopIteration:
				dist = -100000
		# setting actual values in the lien to constants
		oldpt = pt
		old_distance = totaldistance
	
	# appending final point to list
	newlist.append(oldpt)
	
	# the final sweep 
	# this prob isn't needed but it makes stuff a lot easier
	oldi = newlist[0]
	newline = [oldi]
	lines = []
	for i in newlist[1:]:
		newline.append(oldi)

		# if this collide then we start a new line
		if i == oldi:
			if newline[0] == newline[1]:
				newline = newline[1:]
			if fuzzbool == True:
				newline = fuzz_line(newline)
			lines.append(newline)
			newline = [i]
		oldi = i
	# adding the final line
	lines.append(newline)	
	return lines

