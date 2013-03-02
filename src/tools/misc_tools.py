'''
// how many elements of a vector have the value 'name'?
template <class T>
int countInVector(std::vector<T> objs, T name)
{
    int count(0);
    // search for all elements equal to name and increase count
    // every time one is found.
    for    (int i = 0; i < objs.size(); i++)
    {
        if (objs[i] == name)
        {
            count++;
        }
    }
    return count;
}
'''
