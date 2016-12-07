import berrl as bl
import pandas as pd
import numpy as np
import geohash
import itertools
import json
import pipeleaflet as pl
import random

# given a point1 x,y and a point2 x,y returns distance in miles
# points are given in long,lat geospatial cordinates
def distance(point1,point2):
	point1 = np.array(point1)
	point2 = np.array(point2)
	return np.linalg.norm(point1-point2)


# reads json that could be from a multindex dict
def read_json(filename):
	with open(filename,'rb') as f:
		data = json.load(f)
	return data

# get geohashs
def get_geohashs(string):
	string = str.split(string,',')
	return string

# assembles points given two different positons
def assemble_points(pos1,pos2,coords):
	return coords[pos1:pos2+1]

# getting last point value
def get_last(coords,ghash,pos):
	pt1 = coords[pos[0]]
	pt2 = coords[pos[1]]

	lat,long = geohash.decode(ghash)

	slope = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0])
	if slope == 0:
		slope = 1000000

	pointy = slope * (long - pt1[0]) + pt1[1]
	point = [long,pointy]
	return point

def make_geohash_coords(multi,geohashs):
	totalgeohashs = multi['geohashs']
	aligndict = multi['alignmentdict']
	coords = multi['coords']
	geoms = []
	for row in geohashs:
		if row == geohashs[0]:
			pos1 = 0
			pos2 = aligndict[row]
			if not len(pos2) == 1:
				lastpoint = get_last(pos2)
				pos2 = pos2[0]
			else:
				pos2 = pos2[0]
				lastpoint = []
			points = assemble_points(pos1,pos2,coords)
			if not lastpoint == []:
				points = points + [lastpoint]
			geoms.append(points)
			lastpoint = points[-1]
		else:
			point = lastpoint
			pos1 = aligndict[oldrow]
			pos2 = aligndict[row]

			if not len(pos1) == 1:
				pos1 = pos1[1]
			else:
				pos1 = pos1[0]
			if not len(pos2) == 1:
				lastpoint = get_last(coords,row,pos2)
				nextpos = pos2[1]
				pos2 = pos2[0]
			else:
				pos2 = pos2[0]
				nextpos = pos2
				lastpoint = []
			points = assemble_points(pos1,pos2,coords)
			points = [point] + points 
			if not lastpoint == []:
				points = points + [lastpoint]

			geoms.append(points)
			lastpoint = points[-1]
		oldrow = row
	point = lastpoint
	print nextpos
	points = assemble_points(nextpos,len(coords)-1,coords)
	points = [point] + points
	geoms.append(points)
	print geoms
	return geoms

# cuts the df of lines up if not field == False
# if field is equal to false will return normal coords
def cut_df(data,multi_ind,idfield):
	count = 0
	for row in data.columns.values.tolist():
		if row == 'coords':
			position = count
		if row == idfield:
			positionid = count
		if row == 'MULTI':
			positionmulti = count
		if row == 'COLORKEYS':
			positioncolor = count
		count += 1

	newlist = []
	totalgeoms = []
	for row in data.values.tolist():
		valid,geom,multi = str(row[positionid]),row[position],row[positionmulti]
		colorkey = row[positioncolor]
		colorkey = str.split(colorkey,',')
		# logic that decides whether the field will get cut up at all
		if not multi == False:
			if not '.' in str(multi):
				geohashs = get_geohashs(multi)
				geoms = make_geohash_coords(multi_ind[valid],geohashs)
				# logic for geometry split
			else:
				pass
				# logic or function for distance
		else:
			coords = multi_ind[valid]['coords']
			geoms = [coords]
		
		count = 0
		addlist = []
		for row in [row] * len(geoms):
			color = colorkey[count]
			newrow = row + [color]
			addlist.append(newrow)
			count+= 1

		newlist += addlist
		totalgeoms += geoms
	data = pd.DataFrame(newlist,columns=data.columns.values.tolist()+['COLORKEY'])
	newheader = []
	for row in data.columns.values.tolist():
		if not row == 'geom' and not row == 'st_asewkt':
			newheader.append(row)
	return data[newheader],totalgeoms

def gener(list):
	for row in list:
		yield row

# function that propigates the dictionary positons of a 
# distance list given 
def get_positions_fromdistance(first,distances):	
	generdist = gener(distances)
	prime = 0
	testdistance = next(generdist)
	count = 0
	positions = [0]
	oldrow = distances[0]
	for row in first['distance']:
		if prime == 0:
			prime = 1
		else:
			for testdistance in distances:
				if testdistance < row and testdistance > oldrow:
					positions.append(count)

		count += 1
		oldrow = row
	return positions

def get_position(dist,distancelist):
	count = 0
	oldrow = 0
	for row in distancelist:
		if oldrow <= dist and row >= dist:
			return count
		count += 1

# given 2 points and a delta distance
# returns the point in which would make that delta
def make_point_dist(pt1,pt2,deltadistance):
	# getting totaldist 
	totalldist = distance(pt1,pt2)

	# getitng factor
	factor = deltadistance / totalldist


	# getting x and y deltas
	xdelta = pt2[0] - pt1[0]
	ydelta = pt2[1] - pt1[1]


	xvalue = (xdelta * factor) + pt1[0]
	yvalue = (ydelta * factor) + pt1[1]

	return [round(xvalue,6),round(yvalue,6)]

# converts a cordlist to a string
def convert_coords_tostring(data):
	newlist = []
	for long,lat in data:
		newlist.append('[%s, %s]' % (long,lat))

	string = ', '.join(newlist)
	return '[' + string + ']'
'''
# returns a list of cordstrings associtated 
# with the lines indicated in the split distances
def make_distance_splits(splitdistances,first):
	newlist = []
	for row in splitdistances:
		newlist.append(float(row))

	splitdistances = newlist
	positions = get_positions_fromdistance(first,splitdistances)
	lastpoint = first['coords'][0]
	firstpoint = lastpoint
	oldposition = 0
	alignlist = []
	ind = 1
	count = 0
	print first['distance']
	print positions,splitdistances
	for dist,position in itertools.izip(splitdistances,positions):
		# getting the final point
		pt1,pt2 = first['coords'][position:position+1]

		pointdist = first['distance'][position]
		deltadistance = dist - pointdist

		# sending the delta distance in points to create teh last point
		point = make_point_dist(pt1,pt2,deltadistance)

		deltacoords = first['coords'][oldposition:position+1]
		if count == 0:
			count = 1
		if count == 1 and deltacoords[0] == firstpoint:
			deltacoords = deltacoords[1:]

		# apply logic to delta coords
		deltacoords = [lastpoint] + deltacoords
		


		totalcoords = deltacoords + [point]


		# converting to str
		totalcoords = convert_coords_tostring(totalcoords)
		#print deltacoords
		oldposition = position
		lastpoint = point
		alignlist.append(totalcoords)
	alignlist.append(first['coords'][oldposition:])
	return alignlist
'''
'''
def make_distance_splits(splitdistances,first):
	count = 0
	oldposition = 0
	oldpoint = first['coords'][0]
	maxdistance = first['distance'][-1]

	print first['coords']
	print first['distance']
	print splitdistances
	newlist = []
	for row in splitdistances:
		count += 1
		maskrow = row 
		boolmask = False
		if float(row) > maxdistance:
			row = maxdistance
			boolmask = True

		position = get_position(float(row),first['distance'])
		if len(first['coords'][position:position+2]) == 1 or len(splitdistances) < 2:

			pt1,pt2 = oldpoint,first['coords'][position]


		elif row == splitdistances[-2] or splitdistances[-1] == row or True == boolmask:
			pt1,pt2 = first['coords'][-2:]
		else:
			pt1,pt2 = first['coords'][position:position+2]
		
		deltadistance = float(row) - first['distance'][position]

		point = make_point_dist(pt1,pt2,deltadistance)



		if position - oldposition >= 2:
			#deltadistance = first['coords']
			# do somethign
			if position  == 0:
				if float(row) < first['distance'][0]:
					corddelta = first['coords'][oldposition+1:position]
					totalalignment = corddelta[0] + [oldpoint] + corddelta[1:] + [point]			
			else:
				totalalignment = [oldpoint] + first['coords'][oldposition+1:position] + [point]
				
			print 'here'
			print totalalignment
		else:
			print 'less'
			if position == oldposition:
				if not oldpoint == point:
					totalalignment = [oldpoint] + [point]
			else:
				totalalignment = [oldpoint] + [first['coords'][position]] + [point]
			print totalalignment

		print position
		# stringify coords here
		newlist.append(convert_coords_tostring(totalalignment))
		print oldpoint,'before'
		oldpoint = totalalignment[-1]
		print oldpoint,'after'
		oldposition = position
	if not first['coords'][position+1:] == []:
		if [oldpoint] == first['coords'][position+1:]:
			string = convert_coords_tostring([oldpoint])
		else:
			string = convert_coords_tostring([oldpoint]+first['coords'][position+1:])
		newlist.append(string)

	print first['coords']
	print first['distance']
	print splitdistances

	for row in newlist:
		print row
	return newlist
'''


def make_distance_splits(splitdistances,first):
	count = 0
	oldposition = 0
	oldpoint = first['coords'][0]
	maxdistance = first['distance'][-1]
	maxpoint = first['coords'][-1]

	newlist = []
	newpositions = []
	olddist = first['distance'][0]
	dist = first['distance'][0]

	for i in range(len(first['coords'])):
		row = i
		if count == 0:
			count = 1
			newlist.append(first['coords'][row])
		else:
			pt1,pt2 = first['coords'][row],first['coords'][oldrow]
			long,lat = first['coords'][i]
			dist = first['distance'][i]

			# iterating through our given points
			for testdistance in splitdistances:
				testdistance = float(testdistance)
				if  testdistance < dist and testdistance > olddist:
					deltadistance = dist - olddist
					point = make_point_dist(pt1,pt2,deltadistance)
					newpositions.append(count)
					newlist.append(point)
					count += 1

			newlist.append([long,lat])
			count += 1
			olddist = dist
			
		oldrow = row
	'''
	print len(newlist)
	print len(first['distance'])
	print first['coords']
	print newlist,'newlist'
	for row in newpositions:
		print row
		print newlist[int(row)]
	'''
	oldlist = []
	total = []
	count = 0
	newpositions = [0] + newpositions + [(len(newlist) - 1)]
	for row in newpositions:
		if count == 0:
			count = 1
		else:
			x,y = oldrow,row
			x,y = x,y+1
			if x < 0:
				x = 0
			if row == newpositions[-1]:
				total.append(newlist[x:])
			else:
				total.append(newlist[x:y])




		oldrow = row
	newlist3 = []	
	for row in total:
		newlist3.append(convert_coords_tostring(row))

	return newlist3


# returns a list of random distances
# make lines
def random_inputs(gid):
	global segindex
	global colors 
	number = random.randint(2,7)

	maxdistance = segindex[str(gid)]['distance'][-1]
	colorlist = []
	newlist = []
	count = 0
	while count < number:
		count+= 1
		colorlist.append(colors[count])
		newlist.append(random.uniform(0.0,maxdistance))
	newlist = sorted(newlist[:-1])
	newlist2 = []
	for row in newlist:
		newlist2.append(str(row))
	newlist = newlist2
	stringdist = ','.join(newlist)
	stringcolor = ','.join(colorlist)

	return stringdist + '|' +stringcolor


# creating random inputs
def create_random_inputs(data,indexs):
	global colors
	global segindex
	colors = bl.get_heatmap51()
	segindex = indexs

	holder = data['gid'].map(random_inputs)
	holder = holder.str.split('|',expand=True)
	data[['MULTI','COLORKEYS']] = holder
	return data



# given a distance filled with column name multi
# and a colorkeys field contain the colors within a certain 
# range returns all the line segments in a format ready to go into
# make_lines
# if field is equal to false will return normal coords
def distance_cut(data,multi_index,idfield):
	count = 0
	for row in data.columns.values.tolist():
		if row == 'coords':
			position = count
		if row == idfield:
			positionid = count
		if row == 'MULTI':
			positionmulti = count
		if row == 'COLORKEYS':
			positioncolor = count
		count += 1

	newlist = []
	totalgeoms = []
	for row in data.values.tolist():
		valid,geom,multi = str(row[positionid]),row[position],row[positionmulti]
		colorkey = row[positioncolor]
		colorkey = str.split(colorkey,',')
		# logic that decides whether the field will get cut up at all
		if not multi == False:

			first = multi_index[str(row[0])]
			distances = row[positionmulti]
			distances = str.split(distances,',')
			geoms = make_distance_splits(distances,first)
			# logic for geometry split

				# logic or function for distance
		else:
			coords = multi_ind[valid]['coords']
			geoms = [coords]
		
		count = 0
		addlist = []
		for row in [row] * len(geoms):
			color = colorkey[count]
			newrow = row + [color]
			addlist.append(newrow)
			count+= 1

		newlist += addlist
		totalgeoms += geoms
	data = pd.DataFrame(newlist,columns=data.columns.values.tolist()+['COLORKEY'])
	newheader = []
	for row in data.columns.values.tolist():
		if not row == 'geom' and not row == 'st_asewkt' and not 'COLORKEYS' == row:
			newheader.append(row)
	return data[newheader],totalgeoms


'''
positions = get_positions_fromdistance(first,distances)
lastpoint = first['coords'][0]
oldposition = 0
alignlist = []
for dist,position in itertools.izip(distances,positions):
	# getting the final point
	pt1,pt2 = first['coords'][position:position+2]
	pointdist = first['distance'][position]
	deltadistance = dist - pointdist

	# sending the delta distance in points to create teh last point
	point = make_point_distances(pt1,pt2,deltadistance)

	deltacoords = first['coords'][oldposition:position+1]
	totalcoords = deltacoords + [point]

	# apply logic to delta coords
	if not lastpoint == deltacoords[0]:
		deltacoords = [lastpoint] + deltacoords
	
	# converting to str
	totalcoords = convert_coords_tostring(totalcoords)

	#print deltacoords
	oldposition = position
	lastpoint = point
	alignlist.append(totalcoords)
'''

'''
generdist = gener(distances)
prime = 0
testdistance = next(generdist)
count = 0
positions = []
for row in first['distance']:
	if prime == 0:
		prime = 1
	else:
		try:
			if testdistance < row and testdistance > oldrow:
				testdistance = next(generdist)
				positions.append(count)
				print count,'here'
		except StopIteration:
			if testdistance < row and testdistance > oldrow:
				positions.append(count)
		count += 1
	oldrow = row
print positions

#make_multiline_index(data,'gid','test.json')

'''

'''
data = data.set_index(data['gid'].astype(str))
data['MULTI'].loc[news] = geos
data['COLORKEYS'] = False
data['COLORKEYS'].loc[news] = colorkeys
print data
print data.loc[0]
print multi['93664']
'''
