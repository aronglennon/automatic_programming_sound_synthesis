import numpy as np

import rpy2.robjects.numpy2ri
from rpy2.robjects.packages import importr

rpy2.robjects.numpy2ri.activate()

# Set up our R namespaces
R = rpy2.robjects.r
DTW = importr('dtw')

# Generate our data
idx = np.linspace(0, 2*np.pi, 100)
template = np.cos(idx)
query = np.sin(idx) + np.array(R.runif(100))/10

# Calculate the alignment vector and corresponding distance
alignment = R.dtw(query, template, keep=True)
dist = alignment.rx('distance')[0][0]

print(dist)