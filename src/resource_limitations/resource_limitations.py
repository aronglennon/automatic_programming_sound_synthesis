# resource limitations methods
def get_max_tree_depth(init_depth, final_depth, num_generations, depth_type, current_generation):
    if depth_type == "static":
        return init_depth
    elif depth_type == "dynamic":
        # if we start with init and end with final, we want to stay on both as equally long as all depths in between
        # therefore, we could imagine breaking all generations up into (final_depth - init_depth + 1) sections
        return int((final_depth - init_depth + 1)*(current_generation / num_generations)) + init_depth
    
def get_max_resource_count(init_resource_count, final_resource_count, num_generations, resource_limitation_type, current_generation):
    if resource_limitation_type == "RLGP":
        return init_resource_count
    elif resource_limitation_type == "dRLGP":
        # if we start with init and end with final, we want to stay on both as equally long as all depths in between
        # therefore, we could imagine breaking all generations up into (final_depth - init_depth + 1) sections
        return int((final_resource_count - init_resource_count + 1)*(current_generation / num_generations)) + init_resource_count