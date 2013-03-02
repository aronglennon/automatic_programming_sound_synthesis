'''
#include "PredicateFunctors.h"

using namespace std;

// constructor sets what type you are going to look for...and this is what is passed
// in to a function that is looking for a predicate function...so the function that
// is passed in is a HasNoInlet with a specified type 
HasNoInlet::HasNoInlet(const string& t)
: type(t) {}

// Does the given object not have any inlets of the specified type?
bool HasNoInlet::operator()(const MaxObject& obj)
{    
    if (type == "none")    // for terminals
    {
        // if there is ANY input connection, then this object is NOT a terminal
        // so check to see if there aren't any input connections.  If not, then
        // we have a terminal and we return false
        if (obj.typeOfInputConnections.size() == 0) 
        {
            return false;
        }
        // ...otherwise, it is not a terminal and therefore we return true
        return true;
    }
    
    // look through all of the object's input connections
    for (int i = 0; i < obj.typeOfInputConnections.size(); i++)
    {
        // for every input connection, look through all of its inlet types
        for(int j = 0; j < obj.typeOfInputConnections[i].inletTypes.size(); j++)
        {
            // if ANY inlet type from ANY input connection is the correct type, return false
            if (obj.typeOfInputConnections[i].inletTypes[j] == type)
            {
                return false;
            }
        }
    }
    // ...otherwise, it is true that it has no inlet of the specified type
    return true;
}

// constructor sets what type you are going to look for...and this is what is passed
// in to a function that is looking for a predicate function...so the function that
// is passed in is a HasNoOutlet with a specified type
HasNoOutlet::HasNoOutlet(const string& t)
: type(t) {}

// Does the given object not have any outlets of the specified type?
bool HasNoOutlet::operator()(const MaxObject& obj)
{
    // for every output connection
    for (int i = 0; i < obj.typeOfOutputConnections.size(); i++)
    {
        // if ANY output connection outputs the specified type, return false
        if (obj.typeOfOutputConnections[i] == type)
        {
            return false;
        }
    }
    // ...otherwise, the object doesn't have the specified output connection, so
    // return true
    return true;
}
'''
