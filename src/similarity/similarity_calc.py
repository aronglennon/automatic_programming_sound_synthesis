import numpy as np
from matplotlib import pylab as pl

def get_similarity(features1, features2, similarity_type):
    print 'calculating similarity'
    # option 1: calculate euclidean distance and send back multiplicative inverse so that a larger distance has lower fitness
    if similarity_type == 'euclidean':
        return 1.0/get_euclidean(features1, features2)
    # option 2: use DTW
    elif similarity_type == 'DTW':
        print 'WARNING: DTW not implemented yet'
        return 0
    # option 3: SI-CSW
    elif similarity_type == 'SIC-DPLA':
        return get_SIC_DPLA(features1, features2)

def get_euclidean(features1, features2):
    # make sure both matrices are the same size...if not truncate the larger one
    dist = 0
    if len(features1) > len(features2):
        features1 = features1[:len(features2)]
    elif len(features1) < len(features2):
        features2 = features2[:len(features1)]
    for i in range(0, features1.shape[0]):
        dist += np.linalg.norm(features1[i][:]-features2[i][:])
    return dist

def get_SIC_DPLA(features1, features2):
    similarity = 0.0
    ICDPLA_left = 0.0
    ICDPLA_right = 0.0
    max_sequence_length = max(len(features1), len(features2))
    # create similarity matrix as input to Smith Waterman
    similarity_matrix = np.zeros(shape=(len(features1),len(features2)))
    for i in range(0, len(features1)):
        for j in range(0, len(features2)):
            similarity_matrix[i][j] = np.linalg.norm(features1[i][:]-features2[j][:])
    # generate Smith-Waterman H matrix
    alignment_matrix = np.zeros(shape=(len(features1),len(features2)))
    # generate corresponding path matrix P (to track the alignment path to any index i,j)
    path_trace_matrix = np.zeros(shape=(len(features1),len(features2)))
    # generate corresponding warp extension matrix (to track how far a warping is being extended)
    warp_extension_matrix = np.zeros(shape=(len(features1),len(features2)))
    # each element is generated with info from elements to its left, diagonal-down-left, and below it AND
    # elements in the similarity matrix from its diagonal-down-left, left, and below
    # --- calculate first elements
    for i in range(0, len(features1)-1):
        # j is zero
        alignment_matrix[i][0] = max(similarity_matrix[i][0], 0)
        path_trace_matrix[i][0] = [-1,-1]
    for j in range(1, len(features2)-1):
        # i is zero
        alignment_matrix[0][j] = max(similarity_matrix[0][j], 0)
        path_trace_matrix[0][j] = [-1,-1]
    # --- calculate the rest of the matrices
    for i in range(1, len(features1)-1):
        for j in range(1, len(features2)-1):
            diagonal = alignment_matrix[i-1][j-1]+similarity_matrix[i][j]
            left = alignment_matrix[i][j-1]+similarity_matrix[i][j] - delta(warp_extension_matrix[i][j-1], max_sequence_length)
            right = alignment_matrix[i-1][j]+similarity_matrix[i][j] - delta(warp_extension_matrix[i-1][j], max_sequence_length)
            alignment_matrix[i][j] = max(diagonal, left, right, 0)
            max_index = [diagonal, left, right, 0].index(alignment_matrix[i][j])
            # diagonal was chosen
            if max_index == 0:
                warp_extension_matrix[i][j] = 0
                path_trace_matrix[i][j] = [i-1,j-1]
            # left was chosen
            elif max_index == 1:
                warp_extension_matrix[i][j] = warp_extension_matrix[i][j-1] + 1
                path_trace_matrix[i][j] = [i,j-1]
            # right was chosen
            elif max_index == 2:
                warp_extension_matrix[i][j] = warp_extension_matrix[i-1][j] + 1
                path_trace_matrix[i][j] = [i-1,j]
            # zero was chosen (meaning no alignment path is allowed)
            else:
                warp_extension_matrix[i][j] = 0
                # sentinel meaning (not traceable - i.e. if you reach this, it is the start of a local alignment)
                path_trace_matrix[i][j] = [-1,-1] 
    ICDPLA_left = ICDPLA(alignment_matrix, path_trace_matrix, features1, features2)
    ICDPLA_right = ICDPLA(alignment_matrix, path_trace_matrix, features2, features1)
    return 2.0 / (ICDPLA_left + ICDPLA_right)

def ICDPLA(alignment_matrix, path_trace_matrix, superior, inferior):
    # find max in Smith-Waterman matrix
    max_index = pl.unravel_index(alignment_matrix.argmax(), alignment_matrix.shape)
    # calculate distance over alignment path
    local_distance = 0.0
    # the start index will be where the alignment begins (necessary to remove submatrix)
    start_x = 0
    # these indices trace path backwards
    x_index = max_index[0]
    y_index = max_index[1]
    while (x_index != -1):
        start_x = x_index
        local_distance += np.linalg.norm(superior[x_index][:]-inferior[y_index][:]) 
        [x_index, y_index] = path_trace_matrix[x_index][y_index]
    # remove appropriate rows from sequence1 and split into two matrices to be involved in the same process
    alignment_top_submatrix = alignment_matrix[:start_x,:]
    alignment_bottom_submatrix = alignment_matrix[max_index[0]:, :]
    return local_distance + ICDPLA(alignment_top_submatrix, path_trace_matrix, superior, inferior) + ICDPLA(alignment_bottom_submatrix, path_trace_matrix, superior, inferior)
    
# warping penalty - note that this is before the length is increased at i,j, which is appropriate, because
# this formula assumes a warping opening has a length of 0
def delta(warp_length, max_sequence_length):
    return 0.5*(1.0 + warp_length/max_sequence_length)

'''
    // perform DTW and place best path in 'path' and warped distance in 'similarity'
    // !!!!!!!!!!! fastDTW(path, similarity, targetFeatures, testFeatures, radius);
    // since the warped distance will always refer to a path that is at least as long as the longer vector
    // sequence of the two, to find the similarity we normalize this distance over the length of the
    // path - giving us a mean euclidean distance error over the path. 
    // !!!!!!!!!!! similarity /= path.size();
    return similarity;
}

// perform Fast DTW and save the best path in the 'path' vector (with each index containing time indices from
// the two sequences) - recursive
void fastDTW(vector< vector<int> >& path,        // the best path from this iteration
             double& distance,                    // the warping distance using best path
             vector< vector<double> > normal,    // the first series
             vector< vector<double> > toWarp,    // the second series
             const int radius)                    // search window size around the low resolution best path
{
    // This is the length of the largest time series for which we will perform a FULL DTW...used in base case of recursion
    int minSize(radius + 2);
    // base case: if either length is less than the max size for which we will perform a full DTW, perform the full DTW
    if (normal.size() <= minSize || toWarp.size() <= minSize) 
    {
        DTW(path, distance, normal, toWarp);
    }
    // otherwise, go deeper into recursion
    else 
    {
        // create coarse versions of vector series
        vector< vector<double> > coarseNormal(getCoarseSeries(normal));
        vector< vector<double> > coarseToWarp(getCoarseSeries(toWarp));
        // best path from one level deeper in recursion (using coarser time series). The path is simply
        // a vector of ints where index is first number in pair, and value is second. Therefore, we will
        // always have a length of the longer of the two series
        vector< vector<int> > lowResolutionPath;
        fastDTW(lowResolutionPath, distance, coarseNormal, coarseToWarp, radius);
        // take low resolution path and expand the path to a window for use with the DTW function
        vector< vector<int> > window(expandPathToWindow(lowResolutionPath, normal, toWarp, radius));
        DTW(path, distance, normal, toWarp, window);
    }
}

// window-constrained DTW
void DTW(vector< vector<int> >& path, double& distance, vector< vector<double> > normal, 
         vector< vector<double> > toWarp, vector< vector<int> > window)
{
    // the diagonal penalty evens the playing field for up-right and right-up moves
    double diagPenalty(1.5);
    // cost matrix will be normal.size (# rows) by toWarp.size (# cols)
    vector< vector<double> > costMatrix (normal.size(), vector<double> (toWarp.size(), -1));
    
    // Create the costMatrix one column at a time
    
    // first column (special case)
    costMatrix[0][0] = euclideanDistance(normal[0], toWarp[0]);
    // only fill the first column up to the window restriction
    int i(1);
    while (i < normal.size() && window[i][0] == 0)
    {
        // to get first column, there is no entry to the left or diagonal down-left, so we always choose down
        costMatrix[i][0] = costMatrix[i-1][0] + euclideanDistance(normal[i], toWarp[0]);
        i++;
    }
    
    // bottom row (special case)
    i = 1;
    // keep filling up row until we hit the max column for this row in the search area
    while (i <= window[0][1])
    {
        // to fill first row, there is no entry down or down-left, so always use left
        costMatrix[0][i] = costMatrix[0][i-1] + euclideanDistance(normal[0], toWarp[i]);
        i++;
    }
    
    // all other columns - now that we've filled the first column and first row, we can fill out one
    // one column at a time starting with the 2nd (index 1).
    for (i = 1; i < normal.size(); i++)
    {
        // set j to min of window
        int j(window[i][0]);
        // min of window: special case - if you are the min you can't look left.
        // The if statement is necessary, since we have already filled in i,j if j = 0 (first column)
        if (j != 0) 
        {
            if (window[i][0] != window[i-1][0]) 
            {
                costMatrix[i][j] = min(costMatrix[i-1][j], diagPenalty*costMatrix[i-1][j-1]) + euclideanDistance(normal[i], toWarp[j]);
            }
            // if the min is the same as in the row below, we can't look diagonal down-left either
            else
            {
                costMatrix[i][j] = costMatrix[i-1][j] + euclideanDistance(normal[i], toWarp[j]);
            }
        }
        j++;
        // while j is less than max of window, fill out cost matrix
        while (j < window[i][1]) 
        {
            // to find the min distance point to i,j we use the min of the left, down-left, and down values
            // which are the only places we could have come from and which contain the min distance up to 
            // their locations, and then add the distance it takes to go through i,j.
            // NOTE: I can add an additional penalty to the diagonal step so that the path has 
            // an equally good chance of going up-right or left-up as it does of going diagonally up...
            // is this useful??? Seems to me it will allow for best possible alignment of curve shapes
            // and I don't care about anything else at the moment.
            double minDist(getMin(costMatrix[i-1][j], costMatrix[i][j-1], diagPenalty*costMatrix[i-1][j-1]));
            costMatrix[i][j] = minDist + euclideanDistance(normal[i], toWarp[j]);
            j++;
        }
        // max of window: special case (only in 'else' statement)
        if (window[i][1] == window[i-1][1]) 
        {
            double minDist(getMin(costMatrix[i-1][j], costMatrix[i][j-1], diagPenalty*costMatrix[i-1][j-1]));
            costMatrix[i][j] = minDist + euclideanDistance(normal[i], toWarp[j]);
        }
        // if the max is not the same as in the row below, we can't look down
        else 
        {
            costMatrix[i][j] = min(costMatrix[i][j-1], diagPenalty*costMatrix[i-1][j-1]) + euclideanDistance(normal[i], toWarp[j]);
        }
    }
    // this is our warp distance (distance using the best warp path)
    distance = costMatrix[normal.size() - 1][toWarp.size() - 1];
    
    // find path
    
    // first put the end position in the path
    vector<int> lastStop;
    lastStop.push_back(normal.size() - 1);
    lastStop.push_back(toWarp.size() - 1);
    path.push_back(lastStop);
    
    // fill in the rest until we bump against the first row or first column
    int row(normal.size() - 1);
    int col(toWarp.size() - 1);
    
    while (row !=0 && col != 0)
    {
        vector<int> previousStop;
        
        if (window[row][0] <= (col-1))
        {
            if (window[row-1][0] <= col-1) 
            {
                // if the left, bottom-left, and bottom can be tested find the smallest and push those indices
                // onto the path
                if (window[row-1][1] >= col) 
                {
                    if (costMatrix[row-1][col] <= costMatrix[row][col-1])
                    {
                        if (costMatrix[row-1][col] <= costMatrix[row-1][col-1]) 
                        {
                            previousStop.push_back(row-1);
                            previousStop.push_back(col);
                            row--;
                        }
                        else 
                        {
                            previousStop.push_back(row-1);
                            previousStop.push_back(col-1);
                            row--;
                            col--;
                        }
                    }
                    else 
                    {
                        if (costMatrix[row][col-1] <= costMatrix[row-1][col-1])
                        {
                            previousStop.push_back(row);
                            previousStop.push_back(col-1);
                            col--;
                        }
                        else 
                        {
                            previousStop.push_back(row-1);
                            previousStop.push_back(col-1);
                            row--;
                            col--;
                        }
                    }                    
                }
                // if only the left and bottom-left can be tested, find the min between them and place the
                // appropriate indices on the path
                else 
                {
                    if (costMatrix[row][col-1] <= costMatrix[row-1][col-1]) 
                    {
                        previousStop.push_back(row);
                        previousStop.push_back(col-1);
                        col--;
                    }
                    else 
                    {
                        previousStop.push_back(row-1);
                        previousStop.push_back(col-1);
                        row--;
                        col--;
                    }
                }
            }
            // if only the left can be tested, then it MUST be our previous stop
            else 
            {
                previousStop.push_back(row);
                previousStop.push_back(col-1);
                col--;
            }
        }
        else if (window[row-1][0] <= col-1)
        {
            // if the bottom left and the bottom can be tested, find the min between them and place the
            // appropriate indices on the path
            if (window[row-1][1] >= col)
            {
                if (costMatrix[row-1][col-1] <= costMatrix[row-1][col]) 
                {
                    previousStop.push_back(row-1);
                    previousStop.push_back(col-1);
                    row--;
                    col--;
                }
                else 
                {
                    previousStop.push_back(row-1);
                    previousStop.push_back(col);
                    row--;
                }
            }
            // if only the bottom left can be tested, then it must be our previous stop
            else
            {
                previousStop.push_back(row-1);
                previousStop.push_back(col-1);
                row--;
                col--;
            }
        }
        // if just the bottom can be tested, then it must be our previous stop
        else 
        {
            previousStop.push_back(row-1);
            previousStop.push_back(col);
            row--;
        }
        path.push_back(previousStop);
    }
    // fill in any first column or row entries
    if (row != 0) 
    {
        for (int k = (row-1); k >= 0; k--) 
        {
            vector<int> previousStop;
            previousStop.push_back(k);
            previousStop.push_back(0);
            path.push_back(previousStop);
        }
    }
    if (col != 0) 
    {
        for (int k = (col-1); k >= 0; k--) 
        {
            vector<int> previousStop;
            previousStop.push_back(0);
            previousStop.push_back(k);
            path.push_back(previousStop);
        }
    }
    // path is calculated backwards, so to put path in order, we must reverse it
    reverse(path.begin(), path.end());
}

// full DTW
void DTW(vector< vector<int> >& path, double& distance, vector< vector<double> > normal, 
         vector< vector<double> > toWarp)
{
    vector< vector<int> > window (normal.size(), vector<int> (2, 0));
    for (int i = 0; i < window.size(); i++) 
    {
        window[i][1] = toWarp.size() - 1;
    }
    // call windowed DTW
    DTW(path, distance, normal, toWarp, window);
}

double getMin(double d1, double d2, double d3)
{
    double min1(min(d1, d2));
    double min2(min(d2, d3));
    return min(min1, min2);
}

// look at pics in documentation to realize that as long as every cell to the diagonal top-left and diagonal bottom-right
// of every cell in the path is filled in, the window will be the appropriate size
vector< vector<int> > expandPathToWindow(vector<vector<int> > lowResolutionPath, vector< vector<double> > normal, 
                                         vector< vector<double> > toWarp, const int radius)
{
    vector<vector<int> > highResPath;
    highResPath = getHighResPath(lowResolutionPath, normal.size(), toWarp.size());
    // window will be the same length as the number of rows as the cost matrix, and will contain the min and max 
    // col vals for each row through which your path may travel.
    // I presized the matrix so that I didn't have to create vectors of ints and then push them on
    vector< vector<int> > window (normal.size(), vector<int> (2, 0));
    // init mins to largest possible value
    for (int i =0; i< window.size(); i++) 
    {
        window[i][0] = toWarp.size() - 1;
    }
    // go through every position in the path
    for (int i = 0; i < highResPath.size(); i++) 
    {
        for (int j = 1; j < (radius + 1); j++) 
        {
            // try to expand window diagonal up-left (always would change min, never max)
            if (highResPath[i][0] + j < normal.size() && highResPath[i][1] - j >= 0) 
            {
                // only do so if this cell is NOT included in the current window
                if (window[(highResPath[i][0] + j)][0] > highResPath[i][1] - j) 
                {
                    window[(highResPath[i][0] + j)][0] = (highResPath[i][1] - j);
                }
            }
            // try to expand window diagonal down-right (always would change max, never min)
            if (highResPath[i][0] - j >= 0 && highResPath[i][1] + j < toWarp.size()) 
            {
                // only do so if this cell is NOT included in the current window
                if (window[(highResPath[i][0] - j)][1] < highResPath[i][1] + j) 
                {
                    window[(highResPath[i][0] - j)][1] = (highResPath[i][1] + j);
                }
            }
            // try to expand window diagonal down-left (always would change min, never max)
            if (highResPath[i][0] - j >= 0 && highResPath[i][1] - j >= 0) 
            {
                // only do so if this cell is NOT included in the current window
                if (window[(highResPath[i][0] - j)][0] > highResPath[i][1] - j) 
                {
                    window[(highResPath[i][0] - j)][0] = (highResPath[i][1] - j);
                }
            }
            // try to expand window diagonal up-right (always would change max, never min)
            if (highResPath[i][0] + j < normal.size() && highResPath[i][1] + j < toWarp.size()) 
            {
                // only do so if this cell is NOT included in the current window
                if (window[(highResPath[i][0] + j)][1] < highResPath[i][1] + j) 
                {
                    window[(highResPath[i][0] + j)][1] = (highResPath[i][1] + j);
                }
            }
        }
    }
    return window;
}

vector<vector<int> > getHighResPath(vector<vector<int> > lowResolutionPath, int rowMax, int colMax)
{
    vector<vector<int> > highResPath;
    // create a vector to hold each new path point that is of size 2 (with init vals of 0)
    //
    // if we had an odd number of elements in either series, then when making low res version,
    // we simply just take the last element.  Thus, when going back to high res version the last
    // part of the low res path won't contain 4 elements for every 1 in the low res path.  That is
    // why you see the if statements in the loop.
    vector<int> element (2, 0);
    for (int i = 0; i < lowResolutionPath.size(); i++) 
    {
        // bottom left corner
        element[0] = 2*lowResolutionPath[i][0];
        element[1] = 2*lowResolutionPath[i][1];
        highResPath.push_back(element);
        if (rowMax > 2*lowResolutionPath[i][0]+1) 
        {
            // top left
            element[0] = 2*lowResolutionPath[i][0] + 1;
            element[1] = 2*lowResolutionPath[i][1];
            highResPath.push_back(element);
        }
        if (colMax > 2*lowResolutionPath[i][1]+1) 
        {
            // bottom right corner
            element[0] = 2*lowResolutionPath[i][0];
            element[1] = 2*lowResolutionPath[i][1] + 1;
            highResPath.push_back(element);
        }
        if (rowMax > 2*lowResolutionPath[i][0]+1 && colMax > 2*lowResolutionPath[i][1]+1)
        {
            // top right corner
            element[0] = 2*lowResolutionPath[i][0] + 1;
            element[1] = 2*lowResolutionPath[i][1] + 1;
            highResPath.push_back(element);
        }
        // must add 1, 2 and 2, 1 if next cell is diagonal (see pics for convincing)
        if (i+1 < lowResolutionPath.size() 
            && lowResolutionPath[i+1][0] > lowResolutionPath[i][0]
            && lowResolutionPath[i+1][1] > lowResolutionPath[i][1]
           ) 
        {
            if (rowMax > 2*lowResolutionPath[i][0]+2 && colMax > 2*lowResolutionPath[i][1]+1)
            {
                element[0] = 2*lowResolutionPath[i][0] + 2;
                element[1] = 2*lowResolutionPath[i][1] + 1;
                highResPath.push_back(element);
            }
            if (rowMax > 2*lowResolutionPath[i][0]+1 && colMax > 2*lowResolutionPath[i][1]+2)
            {
                element[0] = 2*lowResolutionPath[i][0] + 1;
                element[1] = 2*lowResolutionPath[i][1] + 2;
                highResPath.push_back(element);
            }
        }
    }
    return highResPath;
}

vector< vector<double> > getCoarseSeries(vector< vector<double> > original)
{
    vector< vector<double> > coarse;
    for (int i = 0; i < original.size()/2; i++) 
    {
        coarse.push_back(mean(original[2*i], original[2*i+1]));
    }
    // check if original.size() is odd...if so, we haven't done anything with the last man out,
    // so just save him in the last entry of the coarse vector
    if (original.size()%2 == 1) 
    {
        coarse.push_back(original[original.size()-1]);
    }
    return coarse;
}

vector<double> mean(vector<double> vec1, vector<double> vec2)
{
    if (vec1.size() != vec2.size()) 
    {
        cerr << "Trying to compute mean on two vectors of unequal size!" << endl;
        exit(1);
    }
    else
    {
        vector<double> average;
        for (int i = 0; i < vec1.size(); i++) 
        {
            average.push_back((vec1[i]+vec2[i])/2.0);
        }
        return average;
    }
}

void displayVector(vector<double> doubVec)
{
    for (int i = 0; i < doubVec.size(); i++) 
    {
        cout << doubVec[i] << " ";
    }
    cout << endl;
}

void displayVector(vector<int> intVec)
{
    for (int i = 0; i < intVec.size(); i++) 
    {
        cout << intVec[i] << " ";
    }
    cout << endl;
}

void displayMatrix(vector< vector<double> > doubMat)
{
    for (int i = 0; i < doubMat.size(); i++) 
    {
        for (int j = 0; j < doubMat[i].size(); j++)
        {
            cout << doubMat[i][j] << " ";
        }
        cout << endl;
    }
    cout << endl;
}

void displayMatrix(vector< vector<int> > intMat)
{
    for (int i = 0; i < intMat.size(); i++) 
    {
        for (int j = 0; j < intMat[i].size(); j++)
        {
            cout << intMat[i][j] << " ";
        }
        cout << endl;
    }
    cout << endl;
}

bool isZeroMatrix(vector< vector<double> > features)
{
    for (int i = 0; i < features.size(); i++) 
    {
        for (int j = 0; j < features[i].size(); j++)
        {
            if (features[i][j] > 0.00001 || features[i][j] < -0.00001) 
            {
                return false;
            }
        }
    }
    return true;
}
'''
