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

