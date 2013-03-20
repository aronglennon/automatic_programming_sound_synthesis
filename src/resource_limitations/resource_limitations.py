# resource limitations methods
def get_max_tree_depth(init_depth, num_generations, type):
    if type == "static":
        return init_depth
    elif type == "dynamic":
        return (int(num_generations / 10) + init_depth)