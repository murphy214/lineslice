# LineSlice 
**A line segment segmentation libray. For more precise visualization of linestring.**

# What is lineslice?
Lineslice is a module that allows you to operate on a set of lines (a road network) in a dataframe like normal but allows you to include two fields: 'DISTANCES' & 'COLORKEYS' respectively to style and slice lines finer at some distance along each line or row in dataframe.

Both distances and colorkeys are stored as comma separted string in a pandas dataframe field. As you might have guessed we will have one more colorkey than distances as distances represent the junction or breaking nodes along the line.
This is useful because you can operate using abstract data structures that take into account gradient as distance along a line then easily add that to an already existing data structure that can easily be sent out into a geojson. This makes it pretty useful for visualizations. (I think, possibly)

#### Example Input 
![](https://cloud.githubusercontent.com/assets/10904982/22403009/aa3e2d66-e5d8-11e6-9c94-873321093da2.png)

#### Example Output
![](https://cloud.githubusercontent.com/assets/10904982/22403006/67397e6c-e5d8-11e6-96e3-9a0c08be7411.png)
![](https://cloud.githubusercontent.com/assets/10904982/22403005/63c2d63e-e5d8-11e6-9b71-68dc0925dcf8.png)

# Requirements
Currently lineslice requires a dataframe to be formatted in a pretty specific way with a maxdistance field for each line and coords fields that is a string representation of what would go into a geojson alignment field.

**If you would like to know more about how these dfs are formatted I suggest you look at [nlgeojson](https://github.com/murphy214/nlgeojson).**

# Example Code
```python
import lineslice
import pandas as pd

# reading a nlgeojson df into memory
data = pd.read_csv('test.csv')

# creating lineslice index and saving to disk
lineslice.make_lineslice_index(data,filename='exmaple.h5')

# reading h5 file index into memory
index = lineslice.read_lineslice_index('exmaple.h5')

# creating a sample data set input
data = lineslice.uniform_split_colors(data,.001)
inputsize = len(data)

# print the input fields that matter
# i.e. the inputs that handle this alg.
print data[['DISTANCES','COLORKEYS']].head()

# creating the final output with the split lines
data = lineslice.make_splits(data,index)

print '%s lines before, %s lines after' % (inputsize,len(data))

'''
OUTPUT:
Wrote split_index h5 file to a.h5.
                                           DISTANCES  \
0  0.001,0.002,0.003,0.004,0.005,0.006,0.007,0.00...   
1          0.001,0.002,0.003,0.004,0.005,0.006,0.007   
2                                        0.001,0.002   
3          0.001,0.002,0.003,0.004,0.005,0.006,0.007   
4  0.001,0.002,0.003,0.004,0.005,0.006,0.007,0.00...   

                                           COLORKEYS  
0  #2ADF05,#DB0F0A,#2ADF05,#DB0F0A,#2ADF05,#DB0F0...  
1  #2ADF05,#DB0F0A,#2ADF05,#DB0F0A,#2ADF05,#DB0F0...  
2                            #2ADF05,#DB0F0A,#2ADF05  
3  #2ADF05,#DB0F0A,#2ADF05,#DB0F0A,#2ADF05,#DB0F0...  
4  #2ADF05,#DB0F0A,#2ADF05,#DB0F0A,#2ADF05,#DB0F0...  
192 lines before, 5789 lines after
'''
```
