import pandas as pd
import numpy as np
import itertools
import random
import json

# function that returns a list of 51 gradient blue to red heatmap 
def get_heatmap51():
	list = ['#0030E5', '#0042E4', '#0053E4', '#0064E4', '#0075E4', '#0186E4', '#0198E3', '#01A8E3', '#01B9E3', '#01CAE3', '#02DBE3', '#02E2D9', '#02E2C8', '#02E2B7', '#02E2A6', '#03E295', '#03E184', '#03E174', '#03E163', '#03E152', '#04E142', '#04E031', '#04E021', '#04E010', '#09E004', '#19E005', '#2ADF05', '#3BDF05', '#4BDF05', '#5BDF05', '#6CDF06', '#7CDE06', '#8CDE06', '#9DDE06', '#ADDE06', '#BDDE07', '#CDDD07', '#DDDD07', '#DDCD07', '#DDBD07', '#DCAD08', '#DC9D08', '#DC8D08', '#DC7D08', '#DC6D08', '#DB5D09', '#DB4D09', '#DB3D09', '#DB2E09', '#DB1E09', '#DB0F0A']
	return list

# function for taking a geojson alignment string to a coordinate list
def get_cords_json(coords):
	data = '{"a":%s}' % coords.decode('utf-8') 
	data = json.loads(data)	
	return data['a']

# given a point1 x,y and a point2 x,y returns distance in miles
# points are given in long,lat geospatial cordinates
def distance(point1,point2):
	point1 = np.array(point1)
	point2 = np.array(point2)
	return np.linalg.norm(point1-point2)

# makes the split index that will be used to split the lines
# filename is an h5 filename
def make_lineslice_index(data,filename=False):
	newdict = {}
	size = len(data)
	count2 = 0
	for LINEID,coords in data[['LINEID','coords']].values.tolist():
		coords = get_cords_json(coords)
		count = 0
		totaldistance = 0
		newlist = []
		for point in coords:
			if count == 0:
				count = 1
			else:
				totaldistance += distance(oldpoint,point)
			newlist.append(point + [totaldistance])
			oldpoint = point
		newlist = pd.DataFrame(newlist,columns = ['LONG','LAT','DISTANCE'])
		print 'Making Split Index: [%s / %s]' % (count2,size)
		count2 += 1
		newdict[LINEID] = newlist.set_index('DISTANCE')
	
	# logic for writing to h5 file
	if not filename == False:
		with pd.HDFStore(filename) as f:
			for i in newdict.keys():
				f['a' + str(i)] = newdict[i]
		print 'Wrote split_index h5 file to %s.' % filename
		return ''
	return newdict

# wrapper function for reading a split index into memory
def read_lineslice_index(filename):
	with pd.HDFStore(filename) as f:
		# getting unique LINEIDs
		LINEIDs = f.keys()

		# now creating dictionary
		newdict = {}
		for i in LINEIDs:
			newdict[int(i[2:])] = f[str(i)]
	return newdict

# creates random colors for a set of input data
def uniform_split_colors(data,size):
	colorlist = get_heatmap51()
	colorlistsize = len(colorlist)-1
	totalsplits = []
	totalcolors = []
	for LINEID,maxdistance in data[['LINEID','maxdistance']].values.tolist():	
		# creating splits
		split_count = int((maxdistance / size))
		splits = np.linspace(0.,split_count*size,split_count+1).tolist()[1:]
	
		# creating colors		
		start,end = colorlist[26],colorlist[-1]
		colors = [start,end] * (((len(splits) + 1) / 2) + 1)
		colors = colors[:len(splits)+1]

		# logic for if splits is 0
		if split_count == 0:
			splits = ['']

		# str joining of colors and splits list
		splits,colors = ','.join([str(i) for i in sorted(splits)]),','.join(colors)
		
		# appending colors and splits to total list
		totalsplits.append(splits)
		totalcolors.append(colors)

	# adding fields to dataframe
	data['DISTANCES'] = totalsplits
	data['COLORKEYS'] = totalcolors

	# selecting only applicable linstrings
	data = data[(data['DISTANCES'] != '')&(data['DISTANCES'] != '0.0')]
	
	return data

# creates random colors for a set of input data
def randomize_splits_colors(data):
	colorlist = get_heatmap51()
	colorlistsize = len(colorlist)-1
	totalsplits = []
	totalcolors = []
	for LINEID,maxdistance in data[['LINEID','maxdistance']].values.tolist():	
		split_count = random.randint(2,10)
		splits = []
		colors = []
		while not len(splits) == split_count:
			splits.append(random.uniform(0.,maxdistance))
		while not len(colors) == split_count + 1:
			colors.append(colorlist[random.randint(0,colorlistsize)])
		splits,colors = ','.join([str(i) for i in sorted(splits)]),','.join(colors)
		totalsplits.append(splits)
		totalcolors.append(colors)
	data['DISTANCES'] = totalsplits
	data['COLORKEYS'] = totalcolors
	return data

# turns a dataframe containing a 'DISTANCES' & 'COLORKEYS' field 
# comma seperated i.e. '.00009999' & '#ff00ff,#ff00ff'
# and turns them into a dataframe that can be sent into nlgeojson.make_lines correctly
def make_splits(data,index,points=False):
	totalalignments = []
	splits = [0] * len(data)

	# this block of code generates the points that will hinge each split
	totalsize = len(data)
	for LINEID,splits in itertools.izip(data['LINEID'].values.tolist(),data['DISTANCES'].values.tolist()):
		# creating splits as a list and getting the correct LINEIDdf
		splits = str.split(splits,',')
		LINEIDdf = index[LINEID]

		# setting up LINEIDdf
		LINEIDdf = LINEIDdf.reindex(sorted(LINEIDdf.index.values.tolist() + [float(i) for i in splits]))
		LINEIDdf['BOOL'] = pd.isnull(LINEIDdf['LAT'])
		LINEIDdf['range'] = range(len(LINEIDdf))
		LINEIDdf['DISTANCE'] = LINEIDdf.index
		
		# getting pivot inds
		pivotinds =  LINEIDdf[LINEIDdf['BOOL'] == True]['range'].values.tolist() + [len(LINEIDdf) - 1]
		oldrow = 0
		indlist = []
		for row in pivotinds:
			newrange2 = [oldrow,row+1]
			indlist.append(newrange2)
			oldrow = row

		# iterpolating points
		LINEIDdf[['LONG','LAT']] =  LINEIDdf[['DISTANCE','LONG','LAT']].interpolate()[['LONG','LAT']]
		
		# creating the coord field
		# that will be indexed as a regular list
		LINEIDdf['COORD'] = '[' + LINEIDdf['LONG'].astype(str) + ',' + LINEIDdf['LAT'].astype(str) + ']'

		# creating a vanilla list of string coord points
		coords = LINEIDdf['COORD'].values.tolist()

		# iterating through each set of inds slicing the 
		# correct coords, stringigy them appending and finally
		# joining into a merged alignment string
		alignments = ['[%s]' % ','.join(coords[a:b]) for a,b in indlist]
		alignments = '|'.join(alignments)

		# appending the alignment string for each line to a list
		totalalignments.append(alignments)
		
		# logic for adding points to toal points
		if points == True:
			totalpoints += LINEIDdf[LINEIDdf['BOOL'] == True][['LONG','LAT']].values.tolist() 
	
	# logic for only returning the points
	if points == True:
		return pd.DataFrame(totalpoints,columns=['LONG','LAT'])	

	# this block of code abstracts the alignments field and drills down each alignment
	# with the appropriate colorkey field positons as well
	# i.e. the block of code that splits the alignments into indivdual lines
	data['ALIGNMENTS'] = totalalignments	
	data['a'] = 'a'
	colorkeys = data.groupby('a')['COLORKEYS'].apply(lambda x:"%s" % ','.join(x))['a']
	dummydf = pd.DataFrame(data.ALIGNMENTS.str.split('|').tolist(), index=data.LINEID).stack()
	dummydf = dummydf.reset_index()
	dummydf = dummydf[['LINEID',0]]
	dummydf.columns = ['LINEID','ALIGNMENTS']
	data = data.set_index('LINEID')
	data = data.drop('ALIGNMENTS',axis=1).loc[dummydf.LINEID.values]
	dummydf[data.columns] = data.reset_index().drop('LINEID',axis=1)
	dummydf['coords'] = dummydf['ALIGNMENTS']
	colorkeys = str.split(colorkeys,',')
	dummydf['COLORKEY'] = colorkeys
	
	return dummydf
