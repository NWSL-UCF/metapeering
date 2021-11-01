import os, json
from .convert_city_state_to_pop_location import convert_city_state_to_pop_location

def get_isp_lat_long(isp_a_name, isp_a_asn, isp_b_name, isp_b_asn):

    isp_a_json_file_name = os.path.abspath(os.path.dirname(
        './compute/')) + "/data/cache/" + str(isp_a_asn) + "_peering_db_data_file.json"
    isp_b_json_file_name = os.path.abspath(os.path.dirname(
        './compute/')) + "/data/cache/" + str(isp_b_asn) + "_peering_db_data_file.json"

    temp_a_city_state_list, temp_b_city_state_list = [], []

    if os.path.exists(isp_a_json_file_name) and os.path.exists(isp_b_json_file_name):
        fin = open(isp_a_json_file_name)
        data = json.load(fin)['data']
        fin.close()

        temp_a_city_state_list = customizePoPs(data['pop_list'], customPoPList)
        fin = open(isp_b_json_file_name)
        data = json.load(fin)['data']
        fin.close()

        temp_b_city_state_list = customizePoPs(data['pop_list'], customPoPList)
    else:
        print("Input file missing for either {} or {}".format(
            isp_a_name, isp_b_name))
        return None, None

    isp_a_pop_location_id_list = convert_city_state_to_pop_location(
        temp_a_city_state_list)
    isp_b_pop_location_id_list = convert_city_state_to_pop_location(
        temp_b_city_state_list)

    print(isp_a_pop_location_id_list)
    print("SEPARATION")
    print(isp_b_pop_location_id_list)

    return isp_a_pop_location_id_list, isp_b_pop_location_id_list

#def get_isp_lat_long():

    #isp_a_pop_locations_list = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_a.my_pop_locations_list]
    #isp_b_pop_locations_list = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_b.my_pop_locations_list]
