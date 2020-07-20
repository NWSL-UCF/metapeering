from .gVars import traffic_ratio_min_max, traffic_ratio_dict
from .generate_ppc_df import generate_ppc_df

def compute_all_acceptable_peering_contracts(isp_a_sort_strategy, isp_a_pop_locations_list, isp_a_offloaded_traffic_list_at_common_pops, isp_b_sort_strategy, isp_b_pop_locations_list, isp_b_offloaded_traffic_list_at_common_pops, common_pop_locations, isp_a_traffic_ratio_type, isp_b_traffic_ratio_type):
    '''
    @note: We already have the offloaded traffic from ISP A to B using common PoPs and vice-versa.
    @note: We check the traffic_ratio_type according to PeeringDB to decide whether they will peer or not.
    They will peer only in the following conditions: 
    a. both of them are Balanced, 
    * They will not peer if both are Not Disclosed or Mostly In/ Out, Heavy In/ Out
    * If any of them are Not Disclosed, they will not peer.
    b. one is Balanced, other is Mostly In/ Out.
    c. one is Mostly In, other is Mostly Out or vice-versa. 
    d. one is Heavy In, other is Heavy Out or vice-versa.
    We base the traffic ratio value (for Max, Min ratio), and use them to filter out the PPC comparing the traffic amount of the two ISPs.
    @return: returns the row count as well. (all Acceptable Peering Contracts Count) 
    '''
    traffic_relation_between_isp_at_common_pop_dict = {}
    for common_pop_id, offloaded_by_a, offloaded_by_b in zip(common_pop_locations, isp_a_offloaded_traffic_list_at_common_pops, isp_b_offloaded_traffic_list_at_common_pops):        
        traffic_relation_between_isp_at_pop = {'isp_a_traffic': offloaded_by_a, 'isp_b_traffic': offloaded_by_b}
        traffic_relation_between_isp_at_common_pop_dict.update({common_pop_id: traffic_relation_between_isp_at_pop})
    
    data_isp_a = []
    data_isp_b = []
    
    l_lsb = common_pop_locations[len(common_pop_locations) // 2:]
    l_msb = common_pop_locations[:len(common_pop_locations) // 2]
    
    # This holds all the binary strings of least significant bits (right half of the list)
    l_lsb_bin_list = []
    
    for i in range(0, 2 ** len(l_lsb)):
        i_bin = format(i, '0' + str(len(l_lsb)) + 'b') 
        l_lsb_bin_list.append(i_bin)
        
    for i in range(0, 2 ** len(l_msb)):
        l_msb_bin = format(i, '0' + str(len(l_msb)) + 'b')
        for lsb_bits in l_lsb_bin_list:
            isp_a_traffic_sum = 0
            isp_b_traffic_sum = 0
            possible_location_combinations = []
            int_val = int(l_msb_bin + lsb_bits, 2)
            for pos in range(0, len(common_pop_locations)):
                if (int_val & (1 << pos) > 0):
                    common_pop_id = common_pop_locations[len(common_pop_locations) - pos - 1]
                    isp_a_traffic_sum += traffic_relation_between_isp_at_common_pop_dict[common_pop_id]['isp_a_traffic']
                    isp_b_traffic_sum += traffic_relation_between_isp_at_common_pop_dict[common_pop_id]['isp_b_traffic']
                    possible_location_combinations.append(common_pop_id)
            if isp_a_traffic_sum != 0 and isp_b_traffic_sum != 0:
                isp_a_outbound_inbound_ratio = float("{0:.2f}".format(isp_a_traffic_sum / isp_b_traffic_sum))
                isp_b_outbound_inbound_ratio = float("{0:.2f}".format(isp_b_traffic_sum / isp_a_traffic_sum))
#                 ############## V3: We do not consider the traffic ratio at all, just create all possible APCs and then see which one are feasible.
#                 data_isp_a.append([possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio])
#                 data_isp_b.append([possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio])                
#                 ############## V3: No traffic ratio consideration End

                ########## V2: This is new work! Begin ###########
                if isp_a_traffic_ratio_type == 0 or isp_b_traffic_ratio_type == 0: # If either one is "Not Disclosed", No peering.
                    continue
                if isp_a_traffic_ratio_type == 1: # Heavy Inbound
                    # isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    isp_a_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    if isp_b_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 2:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                            
                    elif isp_b_traffic_ratio_type == 4:    
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                if isp_a_traffic_ratio_type == 2: # Mostly Inbound
                    # isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    isp_a_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    if isp_b_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 1:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    if isp_b_traffic_ratio_type == 2:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                            
                    elif isp_b_traffic_ratio_type == 4:    
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)          
                if isp_a_traffic_ratio_type == 3: # Balanced
                    # isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    isp_a_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    if isp_b_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    elif isp_a_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 1:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    if isp_b_traffic_ratio_type == 2:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row) 
                    elif isp_b_traffic_ratio_type == 4:    
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                     
                    elif isp_b_traffic_ratio_type == 5:    
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                     
                if isp_a_traffic_ratio_type == 4: # Mostly Outbound
                    # isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[0])
                    isp_a_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[0])
                    if isp_a_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 1:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    if isp_b_traffic_ratio_type == 2:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row) 
                    elif isp_b_traffic_ratio_type == 4:    
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                     
                if isp_a_traffic_ratio_type == 5: # Heavy Outbound
                    # isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[0])
                    isp_a_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[0])
                    if isp_a_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 2:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        # isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        isp_b_max_traffic_ratio_to_compare = int(traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row) 
                ########## V2: This is new work! End ###########
                                     
    if len(data_isp_a) > 0 and len(data_isp_b) > 0:
        df_a = generate_ppc_df(data_isp_a, isp_a_sort_strategy)
        df_b = generate_ppc_df(data_isp_b, isp_b_sort_strategy) 
        return df_a, df_a.shape[0], df_b, df_b.shape[0]
    elif len(data_isp_a) > 0:
        df_a = generate_ppc_df(data_isp_a, isp_a_sort_strategy) 
        return df_a, df_a.shape[0], None, 0
    elif len(data_isp_b) > 0:
        df_b = generate_ppc_df(data_isp_b, isp_b_sort_strategy)
        return None, 0, df_b, df_b.shape[0]
    else:
        return None, 0, None, 0
    