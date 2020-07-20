from .do_work import do_work
from .save_pop_locations import save_pop_locations
import sys

def debug(check=False):
    if check:
        debug_list = [(('cableone',11492), ('cablevision',6128)),
        (('cablevision',6128), ('cableone',11492)),
        (('cablevision',6128), ('centurylink',209)),
        (('cablevision',6128), ('cogent',174)),
        (('cablevision',6128), ('comcast',7922)),
        (('cablevision',6128), ('cox',22773)),
        (('cablevision',6128), ('sprint',1239)),
        (('centurylink',209), ('cablevision',6128)),
        (('cogent',174), ('cablevision',6128)),
        (('comcast',7922), ('cablevision',6128)),
        (('cox',22773), ('cablevision',6128)),
        (('sprint',1239), ('cablevision',6128))]
        for pair in debug_list:
            print(do_work(pair)),'\n\n'
        # do_work((('cogent', 174), ('cablevision',6128))), '\n\n'

    

        save_pop_locations()

        sys.exit()