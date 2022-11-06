'''
@note: This is the main function.
'''
import os, json
from .gVars import List_Of_POP_Locations, Max_Common_Pop_Count, Output_Directory
from .convert_city_state_to_pop_location import convert_city_state_to_pop_location, convert_city_state_to_pop_location_custom_requester
from .peering_algorithm_implementation import peering_algorithm_implementation
from .ISP import ISP
from .compute_all_acceptable_peering_contracts import compute_all_acceptable_peering_contracts

# Note: customPoPList is a list of tuples in the format (city, state)
def customizePoPs(popList, customPoPList):

    if customPoPList:
        newPoPList = []
        for pop in popList:
            if (not isInCustomList(customPoPList, pop)):
                newPoPList.append(pop)
        print("---len of newpoplist---", len(newPoPList))
        return newPoPList
    else:
        # print("Outgoing poplist: ",popList)
        return popList

def isInCustomList(customPoPList, PoP):
    for loc in customPoPList:
        if (PoP['city'] == loc[0] and PoP['state'] == loc[1]):
            return True

    return False

def do_work(isp_pair, customPoPList=None):
    '''
    @return: If there is no PPC at all, there is no APC!
    Previously, we returned None, in such case. We return exact same object as like any pair with PPC, APC except,
    in such case, the value will be set to 0.
    And, in such cases, rather comparing the object with None, check PPC count, if that's 0.
    '''
    isp_a_name, isp_a_asn = isp_pair[0]
    isp_b_name, isp_b_asn = isp_pair[1]

    temp_a_city_state_list, temp_b_city_state_list = [], []
    isp_a_traffic_ratio_type = isp_b_traffic_ratio_type = None
    isp_a_ip_address_count = isp_a_prefix_count = isp_b_ip_address_count = isp_b_prefix_count = 0
    global_ip_address_count = global_prefix_count = 0
    # Look for cached file.
    isp_a_json_file_name = os.path.abspath(os.path.dirname(
        './compute/')) + "/data/cache/" + str(isp_a_asn) + "_peering_db_data_file.json"
    isp_b_json_file_name = os.path.abspath(os.path.dirname(
        './compute/')) + "/data/cache/" + str(isp_b_asn) + "_peering_db_data_file.json"

    if os.path.exists(isp_a_json_file_name) and os.path.exists(isp_b_json_file_name):
        fin = open(isp_a_json_file_name)
        data = json.load(fin)['data']
        # data = isp_data[str(isp_a_asn)]['data']
        temp_a_city_state_list = customizePoPs(data['pop_list'], customPoPList)
        if isp_a_asn == 174:
            isp_a_traffic_ratio_type = 'BALANCED'
        else:
            isp_a_traffic_ratio_type = data['traffic_ratio']

        isp_a_ip_address_count = data['address_space']
        isp_a_prefix_count = data['prefixes']
        global_ip_address_count = data['total_addresses_in_globe']
        global_prefix_count = data['total_prefixes_in_globe']
        # fin.close()

        fin = open(isp_b_json_file_name)
        data = json.load(fin)['data']
        # data = isp_data[str(isp_b_asn)]['data']

        temp_b_city_state_list = customizePoPs(data['pop_list'], customPoPList)
        if isp_b_asn == 174:
            isp_b_traffic_ratio_type = 'BALANCED'
        else:
            isp_b_traffic_ratio_type = data['traffic_ratio']
        isp_b_ip_address_count = data['address_space']
        isp_b_prefix_count = data['prefixes']
        # fin.close()
    else:
        print("Input file missing for either {} or {}".format(
            isp_a_name, isp_b_name))
        return None
    # print('Jaaying: ', temp_a_city_state_list)
    # print('Jaaying: ', temp_b_city_state_list)
    isp_a_pop_location_id_list = convert_city_state_to_pop_location_custom_requester(
        temp_a_city_state_list)
    isp_b_pop_location_id_list = convert_city_state_to_pop_location_custom_requester(
        temp_b_city_state_list)
    # print('AAying: ', isp_a_pop_location_id_list)
    # print('AAying: ', isp_b_pop_location_id_list)

    #common_pop_location_id_list = [
        #a for a in isp_a_pop_location_id_list if a in isp_b_pop_location_id_list]

    # set works bc the id is constructured with city, state, org name and name in place!
    #common_pop_location_id_list = []
    common_pop_location_set = set()
    for a in isp_a_pop_location_id_list:
        for b in isp_b_pop_location_id_list:
            if List_Of_POP_Locations[a].city == List_Of_POP_Locations[b].city and List_Of_POP_Locations[a].state == List_Of_POP_Locations[b].state:
                common_pop_location_set.add(a)
                common_pop_location_set.add(b)


    common_pop_location_id_list = list(common_pop_location_set)
    print("len of common = ", len(common_pop_location_id_list))
    # have a set and pass in the list of states in which common pops SHOULD be in. This should be done by finding common pops plus the pops the user doesnt want.
    # Now for each pop, create city-state-name-org_name

    print("common pop location id list edited: ", common_pop_location_set)

    isp_a_port_capacity_at_common_pop_dict = {}
    isp_b_port_capacity_at_common_pop_dict = {}

    # Edited for custom pop
    # tuple 5 : ('LA', 'California')
    # Figure out for port capacity enoigh id
    # TODO: check by testing!
    common_pop_location_isp_id_isp_type_in_peeringdb_tuple_list = {i: (
        List_Of_POP_Locations[i].city, List_Of_POP_Locations[i].state) for i in common_pop_location_id_list}
    print("common tuple list: ", common_pop_location_isp_id_isp_type_in_peeringdb_tuple_list)
        #List_Of_POP_Locations[i].isp_type_in_peering_db, List_Of_POP_Locations[i].isp_id_in_peering_db) for i in common_pop_location_id_list}
    temp_dict_for_isp_a_port_capacity = {
        (i['city'], i['state']): i['port_capacity'] for i in temp_a_city_state_list}
        #(i['isp_type_in_peering_db'], i['isp_id_in_peering_db']): i['port_capacity'] for i in temp_a_city_state_list}
    temp_dict_for_isp_b_port_capacity = {
        (i['city'], i['state']): i['port_capacity'] for i in temp_b_city_state_list}
        #(i['isp_type_in_peering_db'], i['isp_id_in_peering_db']): i['port_capacity'] for i in temp_b_city_state_list}

    for k, v in common_pop_location_isp_id_isp_type_in_peeringdb_tuple_list.items():
        isp_a_port_capacity_at_common_pop_dict[k] = temp_dict_for_isp_a_port_capacity[v]
        isp_b_port_capacity_at_common_pop_dict[k] = temp_dict_for_isp_b_port_capacity[v]

    '''
    Sort the common PoPs based on their capacity, higher ones are one the front.
    Based on PoP port capacity, higher the capacity, more preferred it is. Higher population as well.
    Since, sorting in dictionary is not possible, we get a sorted list of tuple after sorting, we cut the list to get top ones.
    Then, we convert that list to a dictionary again and use the keys as "common_pop_location_id_list"
    '''
    # isp_a_port_capacity_at_common_pop_dict = sorted(isp_a_port_capacity_at_common_pop_dict.items(), key=lambda (k, v):(v, k), reverse=True)
    # try: converting to python 3, above line gives error!
    # Note port capacity is not being used in peering_algorithm_implementation
    isp_a_port_capacity_at_common_pop_dict = sorted(
        isp_a_port_capacity_at_common_pop_dict.items(), key=lambda k_v: (k_v[1], k_v[0]), reverse=True)

    if len(common_pop_location_id_list) > Max_Common_Pop_Count:
        isp_a_port_capacity_at_common_pop_dict = isp_a_port_capacity_at_common_pop_dict[
            :Max_Common_Pop_Count]
    isp_a_port_capacity_at_common_pop_dict = {
        item[0]: item[1] for item in isp_a_port_capacity_at_common_pop_dict}
    common_pop_location_id_list = list(
        isp_a_port_capacity_at_common_pop_dict.keys())

    print("common_id_list", common_pop_location_id_list)

    isp_a = ISP(isp_a_asn, isp_a_name, (isp_a_ip_address_count * 100.0) / global_ip_address_count, (isp_a_prefix_count * 100.0) / global_prefix_count,
                isp_a_pop_location_id_list, isp_b_pop_location_id_list, common_pop_location_id_list, isp_a_port_capacity_at_common_pop_dict, isp_a_traffic_ratio_type)
    isp_b = ISP(isp_b_asn, isp_b_name, (isp_b_ip_address_count * 100.0) / global_ip_address_count, (isp_b_prefix_count * 100.0) / global_prefix_count,
                isp_b_pop_location_id_list, isp_a_pop_location_id_list, common_pop_location_id_list, isp_b_port_capacity_at_common_pop_dict, isp_b_traffic_ratio_type)

    isp_a.all_acceptable_peering_contracts, isp_a.all_acceptable_peering_contracts_count, isp_b.all_acceptable_peering_contracts, isp_b.all_acceptable_peering_contracts_count = compute_all_acceptable_peering_contracts(
        isp_a.sorting_strategy, isp_a.my_pop_locations_list, isp_a.offloaded_traffic_list_to_opponent_at_common_pops, isp_b.sorting_strategy, isp_b.my_pop_locations_list, isp_b.offloaded_traffic_list_to_opponent_at_common_pops, common_pop_location_id_list, isp_a.isp_traffic_ratio_type, isp_b.isp_traffic_ratio_type)

    willingness_score, affinity_score, felicity_score = peering_algorithm_implementation(isp_a, isp_b)

    print("here2")
    fout_for_apc_count = open(os.path.abspath(
        Output_Directory + "/" + "apc_count_" + str(Max_Common_Pop_Count) + ".txt"), "a+")
    fout_for_apc_count.write("ISP {:<12} has {:>3} PoP location, ISP {:<12} has {:>3} PoP location, Common location count: {:<3}\n".format(
        isp_a.name, len(isp_a.my_pop_locations_list), isp_b.name, len(isp_b.my_pop_locations_list), len(isp_a.common_pop_locations)))
    if isp_a.all_possible_peering_contracts_count == 0:
        fout_for_apc_count.write("APC Count: {}, PPC Count: {}, Nothing created\n".format(
            isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count))
    else:
        fout_for_apc_count.write("APC Count: {}, PPC Count: {}, APC/PPC Ratio: {:.2f}\n".format(isp_a.all_acceptable_peering_contracts_count,
                                                                                                isp_a.all_possible_peering_contracts_count, float(isp_a.all_acceptable_peering_contracts_count) / isp_a.all_possible_peering_contracts_count))
    fout_for_apc_count.close()

    similarity_score_based_on_pop_count = similarity_score_on_prefix = similarity_score_on_address = 0
    for i, isp_a_similarity_condition_value, isp_b_similarity_condition_value in zip(range(3),
                                                                                     [len(
                                                                                         isp_a.my_pop_locations_list), isp_a.prefix_coverage_percentage, isp_a.ip_address_coverage_percentage],
                                                                                     [len(isp_b.my_pop_locations_list), isp_b.prefix_coverage_percentage, isp_b.ip_address_coverage_percentage]):
        similarity_score = 0
        if isp_a_similarity_condition_value > isp_b_similarity_condition_value:
            similarity_score = float(
                isp_b_similarity_condition_value) / isp_a_similarity_condition_value
        else:
            if isp_b_similarity_condition_value != 0:
                similarity_score = float(
                    isp_a_similarity_condition_value) / isp_b_similarity_condition_value
        if i == 0:
            similarity_score_based_on_pop_count = similarity_score
        elif i == 1:
            similarity_score_on_prefix = similarity_score
        elif i == 2:
            similarity_score_on_address = similarity_score

    print("isp_a len: ", len(isp_a.my_pop_locations_list))
    print("isp_b list in dowork: ", isp_b.my_pop_locations_list)
    print("isp_a list in dowork: ", isp_a.my_pop_locations_list)
    print("isp_b len: ", len(isp_b.my_pop_locations_list))


    return {'isp_a': {'name': isp_a.name, 'asn': isp_a_asn, 'pop_count': len(isp_a.my_pop_locations_list)}, 'isp_b': {'name': isp_b.name, 'asn': isp_b_asn, 'pop_count': len(isp_b.my_pop_locations_list)}, 'apc_count': isp_a.all_acceptable_peering_contracts_count, 'willingness_score': willingness_score, 'affinity_score': affinity_score, 'felicity_score': felicity_score, 'ppc_count': isp_a.all_possible_peering_contracts_count, 'similarity_score': {'based_on_address': similarity_score_on_address, 'based_on_prefix': similarity_score_on_prefix, 'based_on_pop': similarity_score_based_on_pop_count}, }
