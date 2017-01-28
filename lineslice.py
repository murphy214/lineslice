import pandas as pd
import numpy as np
import itertools
import random
import simplejson as json

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

# a function to properly return the index location of the 
# the two points along the line that the point falls inbetween
def get_after(data,dist):
	if not data.index.name == 'DISTANCE':
		data = data.set_index('DISTANCE')
	data['range'] = range(len(data))
	temp = data['range'].loc[dist:dist+1.]
	temp = temp.iloc[:2].values.tolist()
	if temp == [1]:
		temp = [0,1]
	if len(temp) == 1:
		temp = [temp[0]-1,temp[0]]

	return temp

# makes the split index that will be used to split the lines
# filename is an h5 filename
def make_lineslice_index(data,filename=False):
	newdict = {}
	size = len(data)
	count2 = 0
	for gid,coords in data[['gid','coords']].values.tolist():
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
		newdict[gid] = newlist.set_index('DISTANCE')
	
	# logic for writing to h5 file
	if not filename == False:
		with pd.HDFStore(filename) as f:
			for i in newdict.keys():
				f[str(i)] = newdict[i]
		print 'Wrote split_index h5 file to %s.' % filename
		return ''
	return newdict

# wrapper function for reading a split index into memory
def read_lineslice_index(filename):
	with pd.HDFStore(filename) as f:
		# getting unique gids
		gids = f.keys()

		# now creating dictionary
		newdict = {}
		for i in gids:
			newdict[int(i[1:])] = f[str(i)]
	return newdict

# creates random colors for a set of input data
def uniform_split_colors(data,size):
	from math import floor
	colorlist = get_heatmap51()
	colorlistsize = len(colorlist)-1
	totalsplits = []
	totalcolors = []
	for gid,maxdistance in data[['gid','maxdistance']].values.tolist():	
		split_count = int((maxdistance / size))
		splits = np.linspace(0.,split_count*size,split_count+1).tolist()[1:]
		colors = []
		boolthing = False
		start,end = colorlist[26],colorlist[-1]
		while not len(colors) == len(splits) + 1 and not split_count == 0:
			if boolthing == False:
				boolthing = True
				colors.append(start)
			elif boolthing == True:
				boolthing = False
				colors.append(end)
		if split_count == 0:
			splits = ['']
		splits,colors = ','.join([str(i) for i in sorted(splits)]),','.join(colors)
		totalsplits.append(splits)
		totalcolors.append(colors)
	data['DISTANCES'] = totalsplits
	data['COLORKEYS'] = totalcolors
	data = data[(data['DISTANCES'] != '')&(data['DISTANCES'] != '0.0')]
	return data

# creates random colors for a set of input data
def randomize_splits_colors(data):
	colorlist = get_heatmap51()
	colorlistsize = len(colorlist)-1
	totalsplits = []
	totalcolors = []
	for gid,maxdistance in data[['gid','maxdistance']].values.tolist():	
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
	newlist = []
	totalalignments = []
	splits = [0] * len(data)
	totallist = []

	# this block of code generates the points that will hinge each split
	for gid,splits in itertools.izip(data['gid'].values.tolist(),data['DISTANCES'].values.tolist()):
		splits = str.split(splits,',')
		giddict = index[gid]

		newlist = []
		for split in splits:
			split = float(split)

			# slicing the iter df
			inds = get_after(giddict,split)

			# slicing the dist df
			distslice = giddict.iloc[inds[0]:inds[1]+1]

			# iteropolating to find long and lat
			long = np.interp(split,distslice.index.values,distslice['LONG'].values)
			longs = distslice['LONG'].values
			lats = distslice['LAT'].values

			if not sorted(longs) == longs:
				longs = sorted(longs)
				lats = [lats[1],lats[0]]
			
			lat = np.interp(long,longs,lats)

			# making and appending point
			point = [long,lat]	
			percent = [(split / data.set_index('gid')['maxdistance'].loc[gid]) * 100.]
			newlist.append(point)
		
		# creating the line list from the subset of points
		temp = giddict[['LONG','LAT']]
		temp['DIST'] = giddict.index.values.tolist()
		dists = iter([float(i) for i in splits])
		pts = iter(newlist)
		currentdist = next(dists)
		combined = []
		count = 0
		for dist,long,lat in temp[['DIST','LONG','LAT']].values.tolist():
			if count == 0:
				count = 1
				olddist = 0.
			else:
				combined.append([olddist,long,lat,False])
				if dist > currentdist and olddist < currentdist:
					point = next(pts)
					combined.append([currentdist] + point + [True])
					try:
						currentdist = next(dists)
					except StopIteration:
						currentdist = 1000000.
					while dist > currentdist and olddist < currentdist:
						point = next(pts)						
						combined.append([currentdist] + point + [True])
						try:
							currentdist = next(dists)
						except StopIteration:
							currentdist = 1000000.
					#print float(splits[count])

			olddist = dist
		
		# creating the combined list
		combined = pd.DataFrame(combined,columns=['DIST','LONG','LAT','BOOL'])
		totallist.append(combined)
		
		# creating the indexlist
		fixs = []
		indexlist = [0] + combined[combined.BOOL == True].index.values.tolist() + [len(combined) - 1]

		# creating the index list with proper positon locations
		count = 0
		indexlist2 = []
		for i in indexlist:
			if count == 0:
				count = 1
			else:
				current = oldi
				currentlist = [oldi]
				while not len(currentlist) == (i - oldi) + 1:
					current += 1
					currentlist.append(current)
				indexlist2.append(currentlist)
			oldi = i
		
		# finally generating string alignments
		alignments = []
		for i in indexlist2:
			alignment = combined[['LONG','LAT']].loc[i].values.tolist()
			alignment = '[%s]' % ','.join(['[%s,%s]' % (x,y) for x,y in alignment])
			alignments.append(alignment)

		# creating one string field and appending to list
		alignments = '|'.join(alignments)
		totalalignments.append(alignments)


		if points == True:
			totallist += newlist
		
	# logic for returning the points dataframe
	if points == True:
		return pd.DataFrame(totallist,columns=['LONG','LAT'])

	# this block of code abstracts the alignments field and drills down each alignment
	# with the appropriate colorkey field positons as well
	# i.e. the block of code that splits the alignments into indivdual lines
	data['ALIGNMENTS'] = totalalignments	
	data['a'] = 'a'
	colorkeys = data.groupby('a')['COLORKEYS'].apply(lambda x:"%s" % ','.join(x))['a']
	dummydf = pd.DataFrame(data.ALIGNMENTS.str.split('|').tolist(), index=data.gid).stack()
	dummydf = dummydf.reset_index()
	dummydf = dummydf[['gid',0]]
	dummydf.columns = ['gid','ALIGNMENTS']
	data = data.set_index('gid')
	data = data.drop('ALIGNMENTS',axis=1).loc[dummydf.gid.values]
	dummydf[data.columns] = data.reset_index().drop('gid',axis=1)
	dummydf['coords'] = dummydf['ALIGNMENTS']
	colorkeys = str.split(colorkeys,',')
	dummydf['COLORKEY'] = colorkeys
	
	return dummydf
'''
import mapkit as mk

data= pd.read_csv('a.csv')
#index = make_split_index(data,filename='split_index.h5')

index = read_splitindex('split_index.h5')
data = uniform_split_colors(data,.001)
#print data.columns.values.tolist()
#index = make_split_index(data,filename='split_index.h5')
data = make_splits(data,index)
#points = make_splits(data,index,points=True)
mk.cln()
mk.make_lines(data,'',mask=True)
#mk.make_lines(data,'',mask=True)
#mk.make_map([data,'lines'])
mk.b()
'''
