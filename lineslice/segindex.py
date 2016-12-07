import pipegeohash as pg
import pandas as pd
import numpy as np
import geohash
import itertools
import json
import mapkit as mk
import deepdish as dd

# returns a set of points that traverse the linear line between two points
def generate_points(number_of_points,point1,point2,pos):
	# getting x points
	x1,x2 = point1[0],point2[0]
	xdelta = (float(x2) - float(x1)) / float(number_of_points)
	xcurrent = x1

	# getting y points
	y1,y2 = point1[1],point2[1]
	ydelta = (float(y2) - float(y1)) / float(number_of_points)
	ycurrent = y1

	newlist = [['LONG','LAT']]

	count = 0
	while count < number_of_points:
		count += 1
		xcurrent += xdelta
		ycurrent += ydelta
		newlist.append([xcurrent,ycurrent,pos])

	return newlist

# gets the extrema dictionary of the alignment df
def get_extrema(df):
	# getting lat and long columns
	for row in df.columns.values.tolist():
		if 'lat' in str(row).lower():
			latheader = str(row)
		if 'lon' in str(row).lower():
			longheader = str(row)
	
	# getting n,s,e,w extrema
	south,north = df[latheader].min(),df[latheader].max()
	west,east = df[longheader].min(),df[longheader].max()

	# making dictionary for extrema
	extrema = {'n':north,'s':south,'e':east,'w':west}

	return extrema

# hopefully a function can be made to properly make into lines
def fill_geohashs(data,size,**kwargs):
	flat = False
	for key,value in kwargs.iteritems():
		if key == 'flat':
			flat = value


	extrema = get_extrema(data)

	# getting upper lefft and lowerright point
	ul = [extrema['w'],extrema['n']]
	lr = [extrema['e'],extrema['s']]


	# getting geohash for ul and lr
	# assuming 8 for the time being as abs min
	ulhash = geohash.encode(ul[1],ul[0],size)
	lrhash = geohash.encode(lr[1],lr[0],size)

	lat,long,latdelta,longdelta = geohash.decode_exactly(ulhash)

	latdelta,longdelta = latdelta * 2.0,longdelta * 2.0

	hashsize = ((latdelta ** 2) + (longdelta ** 2)) ** .5

	count = 0
	for row in data.columns.values.tolist():
		if 'lat' in str(row).lower():
			latheader = row
		elif 'long' in str(row).lower():
			longheader = row
		count += 1


	count = 0
	newlist = []
	currents = []
	for row in data[[longheader,latheader,'POS']].values.tolist():
		if count == 0:
			count = 1
		else:
			dist = distance(oldrow[:2],row[:2])
			if dist > hashsize / 10.0:
				newlist.append(oldrow)
				number = (dist / hashsize) * 10.0
				number = int(number)
				pointlist = generate_points(number,oldrow[:2],row[:2],row[2])[1:]
				newlist += pointlist
				newlist.append(row)
			else:
				newlist.append(row)
			
			count +=1
		oldrow = row

	newlist = pd.DataFrame(newlist,columns=['LONG','LAT','POS'])
	newlist = pg.map_table(newlist,size,map_only=True)

	if flat == True:
		return newlist
	else:
		return flatten_nonsorted(newlist)


# making flat list non sorted
def flatten_nonsorted(data):
	ghashs = data['GEOHASH']
	indexes = np.unique(ghashs, return_index=True)[1]
	list = [ghashs[index] for index in sorted(indexes)]
	return list	


#gets lat and long for polygons and lines in postgis format
def get_coords_geom(geometry):	
	# parsing through the text geometry to yield what will be rows
	try:
		geometry=str.split(geometry,'(')
		geometry=geometry[-1]
		geometry=str.split(geometry,')')
	except TypeError:
		return [[0,0],[0,0]] 
	# adding logic for if only 2 points are given 
	if len(geometry) == 3:
		newgeometry = str.split(str(geometry[0]),',')
		
	else:
		if not len(geometry[:-2]) >= 1:
			return [[0,0],[0,0]]
		else:
			newgeometry=geometry[:-2][0]
			newgeometry=str.split(newgeometry,',')

	coords=[]
	for row in newgeometry:
		row=str.split(row,' ')
		long=float(row[0])
		lat=float(row[1])
		coords.append([long,lat])

	return coords

# given a point1 x,y and a point2 x,y returns distance in miles
# points are given in long,lat geospatial cordinates
def distance(point1,point2):
	point1 = np.array(point1)
	point2 = np.array(point2)
	return np.linalg.norm(point1-point2)

# gettin distances of each coordinate position
def get_distances(geometry):
	count = 0
	newlist = []
	for row in geometry:
		if count == 0:
			dist = 0
			count = 1
		else:
			tempdist = distance(oldrow,row)
			dist += tempdist
		oldrow = row
		newrow = row + [dist]
		newlist.append(newrow)
	return newlist

# creates a temporary dictionary of each geohash,pos in a dict
def create_temp(geometry):
	newdict = {}
	for row in geometry[['GEOHASH','POS']].values.tolist():
		newdict[row[0]] = row[1]
	return newdict

def gener(list):
	for row in list:
		yield row

# getting the dict alignment corresponding to filled geohashs
def get_alignment_dict(geohashs,tempdict):
	newdict = {}
	lastpos = 0
	initialgeohashs = tempdict.keys()
	for row in geohashs:
		try:
			pos = [tempdict[row]]
		except:
			pos = [pos[0],pos[0]+1]
		newdict[row] = pos
	return newdict


def get_cords_json(coords):
	data = '{"a":%s}' % coords.decode('utf-8') 
	data = json.loads(data)	
	return data['a']

def get_distance_frompos(pos):
	global distances
	return distances[pos]

def make_distances(data,distancelist,geohashs,lats,longs):
	global distances
	data['POS'] = data['POS'].astype(int)
	distances = distancelist
	data['DISTANCES'] = data['POS'].astype(int).map(get_distance_frompos)
	distances = geohashs
	data['GEOHASH_TEMP'] = data['POS'].astype(int).map(get_distance_frompos)
	distances = lats
	data['LAT'] = data['POS'].astype(int).map(get_distance_frompos)
	distances = longs
	data['LONG'] = data['POS'].astype(int).map(get_distance_frompos)
	return data

# makes an multiindex dictionary structure that 
# contains data structures needed to parse multi lines
def make_multiline_index(data,idfield,filename,index=False,filename=False):
	count = 0
	for row in data.columns.values.tolist():
		if row == 'coords':
			position = count
		if row == idfield:
			positionid = count
		count += 1

	totaldict = {}
	count = 0
	total = 0
	# iterating through each value in coords
	for row in data.values.tolist():
		# getting id value
		idval = str(row[positionid])
		
		# getting geometry
		geometry = row[position] 
		geometry = get_cords_json(geometry)

		# getting the distance of each coord point
		# as well as setting the position in which they appear in coords
		geometry = get_distances(geometry)
		geometry = pd.DataFrame(geometry,columns=['LONG','LAT','DISTANCE'])
		geometry['POS'] = range(len(geometry))
		geometry = pg.map_table(geometry,8,map_only=True)

		# creating temporary alignment dictionary to be used when creating the real one
		tempdict = create_temp(geometry)

		# getting the geohashsfills
		totalgeohashs = fill_geohashs(geometry,8)

		# getting real alignment dictionary
		alignmentdict = get_alignment_dict(totalgeohashs,tempdict)

		# getting distance list
		distancelist = geometry['DISTANCE'].values.tolist()

		# getting coord list
		coords = geometry[['LONG','LAT']].values.tolist()	

		dictperid = {'coords':coords,'distance':distancelist,'alignmentdict':alignmentdict,'geohashs':totalgeohashs}
		totaldict[idval] = dictperid

		count += 1
		if count == 10:
			total += 10
			print 'Total [%s / %s]' % (total,len(data))
			count = 0
	if not index == False and not filename == False:
		index['multi'] = totaldict
		dd.io.save(filename,index)
	with open(filename,'wb') as f:
		json.dump(totaldict,f)


# makes an multiindex dictionary structure that 
# contains data structures needed to parse multi lines
def make_multiline_index_sql(dbname,idfield):
	data = mk.get_database(dbname)
	newtable = dbname + '_segindex'
	sqlquerry,engine = mk.make_query(dbname)

	#data = mk.get_database(dbname)
	#data = dbname  # delete this
	count = 0
	for row in data.columns.values.tolist():
		if row == 'coords':
			position = count
		if row == idfield:
			positionid = count
		count += 1

	totaldict = {}
	count = 0
	total = 0
	# iterating through each value in coords
	for row in data.values.tolist():
		# getting id value
		idval = str(row[positionid])
		
		# getting geometry
		geometry = row[position] 
		geometry = get_cords_json(geometry)

		# getting the distance of each coord point
		# as well as setting the position in which they appear in coords
		geometry = get_distances(geometry)
		geometry = pd.DataFrame(geometry,columns=['LONG','LAT','DISTANCE'])
		geometry['POS'] = range(len(geometry))
		geometry = pg.map_table(geometry,8,map_only=True)

		# getting geohash list
		geohashlist = geometry['GEOHASH'].values.tolist()

		# creating temporary alignment dictionary to be used when creating the real one
		tempdict = create_temp(geometry)

		# getting the geohashsfills
		df = fill_geohashs(geometry,8,flat=True)
		
		# getting real alignment dictionary
		#alignmentdict = get_alignment_dict(totalgeohashs,tempdict)

		# getting distance list
		distancelist = geometry['DISTANCE'].values.tolist()

		# getting lat and longs
		lats = geometry['LAT'].values.tolist()
		longs = geometry['LONG'].values.tolist()

		df = make_distances(df,distancelist,geohashlist,lats,longs)
		df[idfield] = int(idval)

		df = df[[idfield,'LAT','LONG','DISTANCES','POS','GEOHASH','GEOHASH_TEMP']]
		df.to_sql(newtable, engine,if_exists='append')

		# getting coord list
		#coords = geometry[['LONG','LAT']].values.tolist()	

		#dictperid = {'coords':coords,'distance':distancelist,'alignmentdict':alignmentdict,'geohashs':totalgeohashs}
		#totaldict[idval] = dictperid


		count += 1
		if count == 10:
			total += 10
			print 'Total [%s / %s]' % (total,len(data))
			count = 0
	with open(filename,'wb') as f:
		json.dump(totaldict,f)


# reads json that could be from a multindex dict
def read_json(filename):
	with open(filename,'rb') as f:
		data = json.load(f)
	return data

# read test data 
def read_test_data():
	args = bl.make_query('la_routes')
	data = pd.read_sql_query(*args)
	return data
	
