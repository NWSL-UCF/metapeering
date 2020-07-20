import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})

def get_distance_between_two_pop_location(pop_location_a, pop_location_b):
    '''
    @note: Using formula from https://www.movable-type.co.uk/scripts/latlong.html
    @var R: Radius of earth (in Mile) 
    '''
    R = 3959  # in Mile
    dlat = np.deg2rad(pop_location_a.latitude - pop_location_b.latitude)
    dlong = np.deg2rad(pop_location_a.longitude - pop_location_b.longitude)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.deg2rad(pop_location_a.latitude)) * np.cos(np.deg2rad(pop_location_b.latitude)) * np.sin(dlong / 2) ** 2 
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    d = R * c
    return d
