class MaxConnection():
    def __init__ (self, inlet,outlet,connectionType):
        self.inlet = inlet
        self.outlet = outlet
        self.type = connectionType
        
        
'''
// Representation of a Max Connection in C++
struct MaxConnection {
    int inlet;            // inlet number
    int outlet;            // outlet number
    std::string type;    // type of the connection
};
'''