# lineslice
A line segment segmentation libray. For more precise visualization of linestring.

A hackishly implemented line segment segmentation library. Basically it works roughly like so, you have distances in a string field in a dataframe in which you want to split the cordinates about. You also have a string list of hexidecimal colorkeys that is a 1 less the size of the distance ranges.

So it would work like this for just ONE line in a dataframe: 
dataframe['DISTANCES'] = ',d1,d2,d3,d4,d5'
dataframe['COLORKEYS'] = '#00ff00,#ff00ff,#aa00aa,#ff00bb'

So this would result in 4 lines and at the linear distances those points reach on the route. 

So you give a function a dataframe with regular alignment sand these fields it returns a split dataframe with the colorkeys and proper alignments in each coordinates field. 



