'''
Created on Sep 10, 2018

@author: prasun

@bug: 1. Since, we're just looking for city and state names while creating a new PoP location, this prevents us creating multiple PoPs located in the same city. 
We should check the name or Lat/Long or whatever in future to fix this.
@note: I think, we've fixed. Need to check.

@attention: We need to add a list of PoPs in each pair of ISPs folder. Otherwise, we don't know the exact location of the PoP IDs, 
as those IDs are generated run-time.
'''

import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})
from PopulationFromCensusGov import PopulationInfo
import os, json, itertools, math, warnings, requests, sys, time
import pandas as pd
# https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from multiprocessing import Pool
from scipy import stats

warnings.filterwarnings("ignore")

List_Of_POP_Locations = []
SORT_STRATEGY_DIFF = 0
SORT_STRATEGY_OWN = 1
SORT_STRATEGY_RATIO = 2
Sort_Strategy_Names = ['diff', 'own', 'ratio']
traffic_ratio_dict = {0: "NOT DISCLOSED", 1: "HEAVY INBOUND", 2: "MOSTLY INBOUND", 3: "BALANCED", 4: "MOSTLY OUTBOUND", 5: "HEAVY OUTBOUND"}
traffic_ratio_min_max = {"HEAVY INBOUND": ['1_9'], "MOSTLY INBOUND": ['1_6'], "BALANCED": ['1_3', '3_1'], "MOSTLY OUTBOUND": ['6_1'], "HEAVY OUTBOUND": ['9_1']}
# traffic_ratio_min_max = {"HEAVY INBOUND": ['1_7'], "MOSTLY INBOUND": ['1_4', '1_6'], "BALANCED": ['1_3', '3_1'], "MOSTLY OUTBOUND": ['4_1', '6_1'], "HEAVY OUTBOUND": ['7_1']}

internet_usage_per_person = 0.01372 # in MB/s

Max_Process_To_Be_Used = 8
Max_Common_Pop_Count = 15

geometric_mean_without_any_weight = True
if geometric_mean_without_any_weight:
    # Geometric mean, no weight factors, nothing.
    beta_w_for_content_related = 1 
    beta_a_for_content_related = 1 
    beta_w = 1
    beta_a = 1
    weight_w_for_content_related = weight_a_for_content_related = 1
    weight_w = weight_a = 1 
else:
    # Adding weight to willingness and affinity
    beta_weight_for_content_related = 0.1
    beta_w_for_content_related = beta_weight_for_content_related
    beta_a_for_content_related = 1 - beta_weight_for_content_related
    # Weighted geometric mean for content related ISPs
    weight_w_for_content_related = 98
    weight_a_for_content_related = 23
    # Adding weight to willingness and affinity
    beta_weight = 0.1
    beta_w = beta_weight
    beta_a = 1 - beta_weight
    # Weighted geometric mean
    weight_w = 98
    weight_a = 23

Output_Directory = os.path.abspath(os.path.dirname(__file__)) + "/" + "output"

Data_Directory = os.path.abspath(os.path.dirname(__file__)) + "/" + "data"


if not os.path.exists(Output_Directory):
    os.mkdir(Output_Directory)
scatter_plot_data_file = "scatter_plot_data_" + str(Max_Common_Pop_Count) + ".json"

willingness_score_for_all_isps = {}
affinity_score_for_all_isps = {}
felicity_score_for_all_isps = {}

class ISP(object):
    '''
    @param as_number: Though an ISP may have multiple ASes, but right now, we're considering only one for each. 
    @param common_pop_locations: This may not always be the common subset of two ISPs. Because, ISPs may have their
    PoPs in same city, but interacting in different IXP or Private facility.
    @param isp_traffic_ratio_type: Not Disclosed/ Heavy Inbound [> 1:6]/ Mostly Inbound[1:4 ~ 1:6]/ Balanced[1:1 ~ 1:3]/ Mostly Outbound[4:1 ~ 6:1]/ Heavy Outbound[> 6:1] 
    @var sorting_strategy: is set to prioritize OWN traffic towards the opponent always. But, will be changed from other section. 
    @var list_for_offloaded_traffic_from_my_each_pop_to_opponent: stores the traffic leaving from each PoPs to the destination ISP. Not specific to any common PoP. 
    @var my_offloaded_traffic_matrix_from_pops_to_opponent_at_common_pops: This matrix holds the traffic that is offloaded to the opponent ISP 
    at different (common) PoPs 
    '''

    def __init__(self, as_number, name, ip_address_coverage_percentage, prefix_coverage_percentage, my_pop_locations_list, opponent_pop_locations_list, common_pop_locations, isp_port_capacity_at_common_pop_dict, isp_traffic_ratio_type):
        self.as_number = as_number
        self.name = name
        self.sorting_strategy = SORT_STRATEGY_OWN
        self.ip_address_coverage_percentage = ip_address_coverage_percentage
        self.prefix_coverage_percentage = prefix_coverage_percentage
        self.my_pop_locations_list = my_pop_locations_list
        self.opponent_pop_locations_list = opponent_pop_locations_list
        self.common_pop_locations = common_pop_locations
        self.port_capacity_at_common_pop_dict = isp_port_capacity_at_common_pop_dict
        self.isp_traffic_ratio_type = traffic_ratio_dict.keys()[traffic_ratio_dict.values().index(isp_traffic_ratio_type)] 
        self.my_traffic_matrix_to_opponent = self.gravity_model(self.my_pop_locations_list, self.opponent_pop_locations_list) 
        self.opponent_traffic_matrix_to_me = self.gravity_model(self.opponent_pop_locations_list, self.my_pop_locations_list)
#         self.my_traffic_matrix = self.gravity_model(self.my_pop_locations_list, self.opponent_pop_locations_list) 
#         self.my_internal_traffic = self.generate_local_traffic()
        self.list_for_offloaded_traffic_from_my_each_pop_to_opponent = np.sum(self.my_traffic_matrix_to_opponent, axis=1)
        self.my_offloaded_traffic_matrix_from_pops_to_opponent_at_common_pops, self.offloaded_traffic_list_to_opponent_at_common_pops = self.get_offloaded_traffic_matrix() 
        self.my_bit_mileage_matrix, self.my_average_bit_mileage_at_common_pops = self.calculate_bit_mileage()
        self.all_possible_peering_contracts_count = 2 ** len(self.common_pop_locations) - 1
        self.all_acceptable_peering_contracts = None
        self.all_acceptable_peering_contracts_count = 0         
                
    def __str__(self):
        return "ASN: {}, Name: {} ({}), My_PoPs_Id: {}, Opp_PoPs_Id: {}\nMy internal traffic: {}".format(self.as_number, self.name, self.aka, self.my_pop_locations_list, self.opponent_pop_locations_list, self.my_internal_traffic)
    
    def gravity_model(self, my_p_l_list, oppo_p_l_list):
        '''
        @param my_p_l_list: Takes the list of PoP locations and returns the traffic matrix based on those locations.
        @param oppo_p_l_list: is the list of opponent PoP locations.
        @note: Uses Gravity model F = G * m1 * m2 / d^2. We assume G = 1 here.
        Again, F = m1 * a1 = m2 * a2. So, a1 = m2 / d^2. The traffic flows from m1 population towards m2 population destination. 
        Heavy population attracts more traffic.  
        @note: DO NOT confuse with the index of this traffic matrix with the actual PoP IDs.
        The index are same for Traffic Matrix and PoP_ID holding list, where "my_pop_locations_list" and "opponent_pop_locations_list" actually has the PoP IDs.
        '''
        traffic_matrix = np.zeros(shape=(len(my_p_l_list), len(oppo_p_l_list)))
        for i in range(len(my_p_l_list)):
            for j in range(len(oppo_p_l_list)):
                if i != j:
                    try:
                        traffic_amount = List_Of_POP_Locations[oppo_p_l_list[j]].population / (get_distance_between_two_pop_location(List_Of_POP_Locations[my_p_l_list[i]], List_Of_POP_Locations[oppo_p_l_list[j]]) ** 2)
                        traffic_amount *= List_Of_POP_Locations[oppo_p_l_list[j]].internet_penetration_percentage / List_Of_POP_Locations[my_p_l_list[i]].internet_penetration_percentage * internet_usage_per_person
                    except Exception as e:
                        print(e)
                        print(traffic_amount, List_Of_POP_Locations[my_p_l_list[i]].__dict__, List_Of_POP_Locations[oppo_p_l_list[j]].__dict__)
                    if traffic_amount == float('Inf'):
                        traffic_matrix[i][j] = 0.0
                    else:
                        traffic_matrix[i][j] = traffic_amount
                else:
                    # We just split the population.
                    traffic_matrix[i][j] = List_Of_POP_Locations[my_p_l_list[i]].population / 2
        return traffic_matrix
            
    def generate_local_traffic(self):
        '''
        @note: Squares the population of each PoP location and assumes as Locally generated traffic.
        @status: We don't use this now. Will be used in future if we consider overlapping issue.
        @return: A Dictionary of PoP_ID and Network traffic
        '''
        temp = []
        for pop_location_id in self.my_pop_locations_list:
            temp.append((List_Of_POP_Locations[pop_location_id]).population ** 2)
        return np.array(temp)
    
    def calculate_bit_mileage(self):
        '''
        @note: This matrix is known to the ISP. Internal data.
        @note: This is exactly same as traffic_matrix of off-loaded traffic from each pops to opponent at common pops, as of now. 
        Except, that traffic is multiplied by the air distance to calculate the bit mileage.
        @return: bit_mileage matrix and average bit mileage at each common PoP.
        '''
        bit_mileage_matrix = np.zeros(shape=(len(self.my_pop_locations_list), len(self.common_pop_locations)))
        for i, my_pop_id in zip(range(len(self.my_pop_locations_list)), self.my_pop_locations_list):
            for j, common_pop_id in zip(range(len(self.common_pop_locations)), self.common_pop_locations):
                bit_mileage_matrix[i][j] = self.my_offloaded_traffic_matrix_from_pops_to_opponent_at_common_pops[i][j] * get_distance_between_two_pop_location(List_Of_POP_Locations[my_pop_id], List_Of_POP_Locations[common_pop_id])
        
        average_bit_mileage_at_pops = np.sum(bit_mileage_matrix, axis=0)
        average_bit_mileage_at_pops = [i / len(self.my_pop_locations_list) for i in average_bit_mileage_at_pops]
        return bit_mileage_matrix, average_bit_mileage_at_pops

    def get_offloaded_traffic_matrix(self):
        '''
        @note: This distributes the traffic leaving from each PoP to opponent ISP based on Common PoPs port capacity.
        If common pop has higher capacity, each PoP will try to send more traffic through it.
        In practice, this will not happen. ISP knows its internal topology and they know how much traffic each PoP sends to 
        a common PoP. However, for simplicity, we think ISP will carry all traffic to all common PoPs proportionately.
        This is true for the opponent as well. It also announces all its prefixes at all PoPs. 
        So, 'closer to geo-location' phenomenon is not considered here!
        @return: traffic_matrix: from each PoP, distributed portion traffic send via each common PoP,
        @return: a list of total traffic amount off-loaded via common PoPs. 
        '''
        pop_capacity_ratio = [float(self.port_capacity_at_common_pop_dict[i]) / np.sum(self.port_capacity_at_common_pop_dict.values()) for i in self.common_pop_locations]
        temp_list = []
        for item in self.list_for_offloaded_traffic_from_my_each_pop_to_opponent:
            temp = [i * item for i in pop_capacity_ratio]
            temp_list.append(temp)
        traffic_matrix = np.array(temp_list)
        return traffic_matrix, np.sum(traffic_matrix, axis=0) 
    
    def get_all_possible_pop_locations(self):
        '''
        @note: This just returns the common PoPs for both ISPs, without considering anything.
        '''
        return self.common_pop_locations
    
    
class PoPLocation(object):
    '''
    @note: We've initialized ID with -1. And, then increase as we continue adding new PoP. Thus we get ID starting from 0.
    This helps us to access the "List_Of_POP_Locations" more easily, as we are adding PoPs there after we create one.
    So, List_Of_POP_Locations[0] will always give us the PoP with ID = 0 and so on. 
    @param list_of_asn_who_has_their_pop_here: is a list of ISP AS numbers, who has their Point Of Presence (POP) establishment here. 
    '''
    ID = -1

    def __init__(self, isp_type_in_peering_db, isp_id_in_peering_db, city, state, latitude, longitude):
        PoPLocation.ID += 1
        self.ID = PoPLocation.ID
        self.isp_type_in_peering_db = isp_type_in_peering_db
        self.isp_id_in_peering_db = isp_id_in_peering_db
        self.city = city
        self.state = state
        self.population = 0
        self.internet_penetration_percentage = 1.0
        self.latitude = latitude
        self.longitude = longitude
        self.list_of_asn_who_has_their_pop_here = [] 
        
    def __str__(self):
        return "PoPLocation ID: {}, (PeeringDB) ISP Type: {}, (PeeringDB) ISP ID: {}, City: {}, State: {}, Population: {}".format(self.ID, self.isp_type_in_peering_db, self.isp_id_in_peering_db, self.city, self.state, self.population)
    
    
def generate_ppc_df(isp_ppc_data, isp_sort_strategy):
    '''
    @note: This is a helping tool. This generates the panda dataframe to store the PPC information with all the details.
    @note: It is called from compute_all_acceptable_peering_contracts() and returns the DF there. 
    @param isp_ppc_data: This is basically the data we want to save. This is a list of lists containing all informations regarding the PPC, traffic.
    @param isp_sort_strategy: This is how ISP want to sort the PPC. whether, its own traffic priority, minimize in/ out-bound traffic difference, minimize out/in-bound traffic ratio. 
    @returns Data Frame with 'PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Total Traffic', 'Traffic Difference', 'Traffic Ratio'
    '''
    df = pd.DataFrame(isp_ppc_data)
    df.transpose()
    df.insert(0, "", df.index)
    
    df.columns = ['PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Total Traffic', 'Traffic Difference', 'Traffic Ratio']
    
    return df

def sort_dataframe(df, isp_sort_strategy):
    '''
    @note: Separated dataFrame column wise sorting into this method. Previously it was in generate_ppc_df().  
    '''
    if isp_sort_strategy == SORT_STRATEGY_DIFF:
        df.sort_values(by=df.columns[5], ascending=False, inplace=True)
    elif isp_sort_strategy == SORT_STRATEGY_OWN:
        df.sort_values(by=df.columns[2], ascending=False, inplace=True)
    elif isp_sort_strategy == SORT_STRATEGY_RATIO:
        df['possible_location_counts'] = df['Possible Location Combinations'].str.len()
        df.sort_values(by=[df.columns[6], df.columns[-1]], ascending=[False, False], inplace=True)  
        df.drop(columns=df.columns[-1], inplace=True)   
    
    return df

def get_willingness(df, isp_sort_strategy):
    '''
    @note: We receive the sorted dataframe here. so, if sorting strategy is 'own' we divide by the top most item. 
    If it is 'diff', if all +ve, top most is the max profit, so divide by it, 
    if all -ve, top most is the least loss, so we divide by the top most and make all the values invert, so top most gets 1 and then 0.9, 0.8, ... 
    [-20, -20, -40, -50, -100] => [1, 1, 2, 2.5, 5] => [1, 1, 0.5, 0.5, 0.2]
    If, 1st +ve, last -ve, we shift all values by the last value so that last one becomes 0 and thus all other values become +ve. we divide by top-most.
    '''
    if isp_sort_strategy == SORT_STRATEGY_DIFF:
        data_array = df[df.columns[5]].to_numpy(copy=True)
        if data_array[0] < 0:
            data_array /= data_array[0]
            data_array = 1/data_array
        else:
            if data_array[0]/data_array[-1] < 0:
                data_array += (-1)*data_array[-1] # This makes all the data positive. We now treat this data as if they were +ve from beginning
            data_array /= data_array[0]
    elif isp_sort_strategy == SORT_STRATEGY_OWN:
        data_array = df[df.columns[2]].to_numpy(copy=True)
        data_array /= data_array[0]
    elif isp_sort_strategy == SORT_STRATEGY_RATIO:
        data_array = df[df.columns[6]].to_numpy(copy=True)
        if data_array[0] == data_array[-1]:
            data_array = df[df.columns[2]].to_numpy(copy=True)
            data_array /= data_array[0]
        else:
            data_array /= data_array[0]

    return data_array

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
    
    l_lsb = common_pop_locations[len(common_pop_locations) / 2:]
    l_msb = common_pop_locations[:len(common_pop_locations) / 2]
    
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
                    isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    if isp_b_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 2:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                            
                    elif isp_b_traffic_ratio_type == 4:    
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                if isp_a_traffic_ratio_type == 2: # Mostly Inbound
                    isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    if isp_b_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 1:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    if isp_b_traffic_ratio_type == 2:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                            
                    elif isp_b_traffic_ratio_type == 4:    
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)          
                if isp_a_traffic_ratio_type == 3: # Balanced
                    isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[1])
                    if isp_b_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    elif isp_a_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 1:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    if isp_b_traffic_ratio_type == 2:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row) 
                    elif isp_b_traffic_ratio_type == 4:    
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                     
                    elif isp_b_traffic_ratio_type == 5:    
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                     
                if isp_a_traffic_ratio_type == 4: # Mostly Outbound
                    isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[0])
                    if isp_a_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 1:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    if isp_b_traffic_ratio_type == 2:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)    
                        elif isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare:                    
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row) 
                    elif isp_b_traffic_ratio_type == 4:    
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[0])
                        if isp_b_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                     
                if isp_a_traffic_ratio_type == 5: # Heavy Outbound
                    isp_a_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_a_traffic_ratio_type]][0].split("_")[0])
                    if isp_a_outbound_inbound_ratio <= isp_a_max_traffic_ratio_to_compare: # ISP A receives ISP B's out-bound ratio traffic.
                        data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, isp_a_outbound_inbound_ratio]
                        data_isp_a.append(data_row)
                    if isp_b_traffic_ratio_type == 2:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
                        if isp_a_outbound_inbound_ratio <= isp_b_max_traffic_ratio_to_compare: # ISP B receives ISP A's out-bound ratio traffic.
                            data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, isp_b_outbound_inbound_ratio]
                            data_isp_b.append(data_row)                        
                    elif isp_b_traffic_ratio_type == 3:
                        isp_b_max_traffic_ratio_to_compare = map(int, traffic_ratio_min_max[traffic_ratio_dict[isp_b_traffic_ratio_type]][0].split("_")[1])
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


def convert_city_state_to_pop_location(city_state_list):
    '''
    @param city_state_list: list of PoPs with city, state, PeeringDB ISP (PoP) type [IX/ Facility], 
    ISP (PoP) ID, location, port capacity at that PoP for an ISP.
    @note: Takes the list of PoPs with information from PeeringDB, we create PoPLocation object. 
    @return: List of PoPLocation objects.
    @note: Since ISPs may have their PoPs in same city, but interacting in different IXP or Private facility.
    While creating new PoPLocation object,we check based on ISP_ID AND ISP_TYPE to prevent creating same IXP/ FACILITY again.
    '''
    populationInfo = PopulationInfo()
    isp_pop_location_id_list = []
 
    temp_pop_location_key_dict = {str(p.isp_type_in_peering_db + "_" + str(p.isp_id_in_peering_db)):p.ID for p in List_Of_POP_Locations}
    for c_s_temp in city_state_list:
        if str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db'])) not in temp_pop_location_key_dict.keys():
            # Check here. We've updated the code to use 'location' tuple instead of separate lat and long.
            pop = PoPLocation(c_s_temp['isp_type_in_peering_db'], c_s_temp['isp_id_in_peering_db'], c_s_temp['city'], c_s_temp['state'], c_s_temp['location'][0], c_s_temp['location'][1])
            pop.population = populationInfo.get_city_population(pop.city, pop.state)
            pop.internet_penetration_percentage = c_s_temp['internet_penetration_percentage']
            List_Of_POP_Locations.append(pop)
            isp_pop_location_id_list.append(pop.ID)
            temp_pop_location_key_dict.update({str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db'])):pop.ID})
        else:
            isp_pop_location_id_list.append(temp_pop_location_key_dict[str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db']))])
                   
    return list(set(isp_pop_location_id_list))


def isp_overlap_score(isp_a_name, isp_b_name, isp_a_pop_locations_list, isp_b_pop_locations_list, common_pop_locations):
    '''
    @note: takes all the PoP locations and generates a Convex-Hull for each ISPs.
    Based on the Convex-hull points, generates the polygons. These polygons are the coverage areas.
    Using, shapely, we calculate the intersection (common areas)
    Use the set theory, total coverage, A U B = A\B + A^B + B\C
    Calculate the 'gained' coverage area for A, if A wants to peer with B.
    '''
    import shapely.geometry as sgeom
    from scipy.spatial import ConvexHull
    
    polygons = {}
    for p in [isp_a_name, isp_b_name]:
        if p == isp_a_name:
            for_convex_hull_peering_point = isp_a_pop_locations_list                 
        elif p == isp_b_name:
            for_convex_hull_peering_point = isp_b_pop_locations_list 
        convex_hull = ConvexHull(for_convex_hull_peering_point)
        x = [for_convex_hull_peering_point[i][0] for i in convex_hull.vertices]
        y = [for_convex_hull_peering_point[i][1] for i in convex_hull.vertices]
        x.append(x[0])
        y.append(y[0])
        poly_points = [(i, j) for i, j in zip(x, y)]  
        polygons[p] = sgeom.Polygon(poly_points)
        polygons[p] = polygons[p].buffer(0)
    
    intersection_poly = polygons[isp_a_name].intersection(polygons[isp_b_name])
    total_coverage_area_of_two_isps = polygons[isp_a_name].area + polygons[isp_b_name].area - intersection_poly.area
    affinity_score_isp_a = max(0.0,(1 - (polygons[isp_a_name].area / total_coverage_area_of_two_isps)))
    affinity_score_isp_b = max(0.0, (1 - (polygons[isp_b_name].area / total_coverage_area_of_two_isps)))

    return math.sqrt(affinity_score_isp_a * affinity_score_isp_b)       #this is the affinity_score_combined

def peering_algorithm_implementation(isp_a, isp_b):
    '''
    Creates the algorithm_report file in CVS format.
    The columns are:
    'Index in PPC list': This are the Possible Peering Contracts. However, note that, not all the PPC will be included here.
    Check the get_all_acceptable_peering_contracts(). This has the conditions, based on which Acceptable Peering Contracts are selected.
    'Rank of PPC for ISP A': Rank of every PPC according to ISP A's preference. 
    Same goes for B.
    '(Rank A - Rank B)^2': gives the relative position difference of every PPC from 2 ISPs' POV.
    We calculate the Max diff^ of PPC Rank. In the worst case, a PPC can be placed as position 1 for ISP A and at last(n) position for ISP B.
    To calculate n, we simply take the length of APC list, because a PPC can't be placed at any later position then last Index.
    So, '1-length(apc_list)' gives us the difference and then we square that value.
    'Willingness (AB) = 1 - diff^2/(1-n)^2': We divide (Rank A - Rank B)^2 by [1-length(apc_list)]^2 and subtract this value from 1 to 
    calculate the willingness for that specific APC.
    We take the sum of willingness value for each APC and divide by APC count to get the willingness_score of that ISP pair for a specific sorting category.
    However, the willingness we get will not be in [0, 1]. The minimum value will be greater than 0. We need to scale the values from [0, 1]. 
    To do so, we need to calculate the willingness_min value. and then subtract all values by willingness_min value and divide those by (1- willingness_min)
    We calculate the ISPs coverage area overlap score (affinity score) as well.
    We take the geometric mean of willingness score and affinity score to calculate the final Felicity score. 
    @note: [This needs checking in future. I'm not sure if this is what we're doing now] 
    We don't update the actual APC list of each ISP, as this APC was prepared based on ISP's actual sorting strategy.
    So, we take APC list of each ISP and then sort them to run the algorithm for 3 sorting strategies and then save the output on file.
    @return: Felicity scores for each sorting strategy for these two ISPs. By default they is set -1. Meaning no peering, no APC.
    '''    
    def generate_initial_apc_rank_list(isp_a_apc_list_index, isp_b_apc_list_index):
        apc_rank_list = [[v, i+1, isp_b_apc_list_index.index(v)+1] for i, v in enumerate(isp_a_apc_list_index) if v in isp_b_apc_list_index]
        not_in_b = set(isp_a_apc_list_index) - set(isp_b_apc_list_index)
        if len(not_in_b) > 0:
            for extra_item, i in zip(not_in_b, range(len(not_in_b))):
                apc_rank_list.append([extra_item, isp_a_apc_list_index.index(extra_item) + 1, max(isp_b_apc_list_index) + i])
        not_in_a = set(isp_b_apc_list_index) - set(isp_a_apc_list_index)
        if len(not_in_a) > 0:
            for extra_item, i in zip(not_in_a, range(len(not_in_a))):
                apc_rank_list.append([extra_item, max(isp_a_apc_list_index) + i, isp_b_apc_list_index.index(extra_item) + 1])

        return apc_rank_list

    willingness_score = {}    
    affinity_score = {}
    felicity_score = {}
    
    if (isp_a.all_acceptable_peering_contracts_count == 0 and isp_b.all_acceptable_peering_contracts_count == 0):
#         print("0 APC for {} and {}. No APC folder created!".format(isp_a.as_number, isp_b.as_number))
        # Neither of the ISPs have any APC, so no peering.
        for _sort in Sort_Strategy_Names:
            willingness_score.update({_sort:-1})    
            affinity_score.update({_sort:-1})
            felicity_score.update({_sort:-1})
        return willingness_score, affinity_score, felicity_score

    output_directory_for_isp = os.path.abspath(Output_Directory + "/" + str(isp_a.as_number) + "_" + str(isp_b.as_number))
    
    isp_a_pop_locations_list = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_a.my_pop_locations_list] 
    isp_b_pop_locations_list = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_b.my_pop_locations_list]
    common_pop_locations = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_a.common_pop_locations]

    affinity_score_combined = isp_overlap_score(isp_a.name, isp_b.name, isp_a_pop_locations_list, isp_b_pop_locations_list, common_pop_locations)

    for sorting_strategy in [SORT_STRATEGY_DIFF, SORT_STRATEGY_OWN, SORT_STRATEGY_RATIO]: 
        if isp_a.all_acceptable_peering_contracts_count > 0 and isp_b.all_acceptable_peering_contracts_count > 0:
            isp_a_all_apc = sort_dataframe(isp_a.all_acceptable_peering_contracts, sorting_strategy) 
            isp_b_all_apc = sort_dataframe(isp_b.all_acceptable_peering_contracts, sorting_strategy)
                        
            write_acceptable_peering_contracts_to_file(isp_a.as_number, sorting_strategy, isp_a_all_apc, output_directory_for_isp)
            write_acceptable_peering_contracts_to_file(isp_b.as_number, sorting_strategy, isp_b_all_apc, output_directory_for_isp)
        
            isp_a_apc_list_index = list(isp_a_all_apc.iloc[:, 0])
            isp_b_apc_list_index = list(isp_b_all_apc.iloc[:, 0])        
            
            apc_rank_list = generate_initial_apc_rank_list(isp_a_apc_list_index, isp_b_apc_list_index)
            n = len(apc_rank_list)        
                
            np_data = np.zeros((n, 7))
            np_data[:, :3] = np.array(apc_rank_list)
            np_data[:, 3] = np.square(np_data[:, 1] - np_data[:, 2])
            np_data[:, 4] = (max(np_data[:, 1]) - np_data[:, 1] + 1) / max(np_data[:, 1])
            np_data[:, 5] = (max(np_data[:, 2]) - np_data[:, 2] + 1) / max(np_data[:, 2])
            if n == 1:
                np_data[:, 6] = 1
            else:
                np_data[:, 6] = stats.gmean(np_data[:, 4:6], 1) 

            df = pd.DataFrame(np_data)
#             df = df.round(4)
            df.columns = ['Index in PPC list', 'Rank of PPC for ISP A', 'Rank of PPC for ISP B', '(Rank A - Rank B)^2', 'Willingness (A)', 'Willingness (B)', 'Willingness (AB) = 1 - (diff^2/(1-n)^2)']
            df.sort_values(by=[df.columns[-1], df.columns[-3]], ascending=False, inplace=True)
    
            write_acceptable_peering_contracts_to_file(isp_a.as_number, sorting_strategy, df, output_directory_for_isp, peering_algorithm_implementation.__name__)
            draw_graph(isp_a.as_number, isp_b.as_number, df, sorting_strategy, output_directory_for_isp)
            
            w_score_without_normalization = sum(df[df.columns[-1]]) / isp_a.all_acceptable_peering_contracts_count
            
            willingness_min = 0.0
            w_score = (w_score_without_normalization - willingness_min) / (1 - willingness_min)
            try:
                # We don't need this try-except block any more, as we're not rounding any value, so no -ve value should appear.
                # Instead we're using a weighted geometric-mean formula here. beta_w, and beta_a are the co-efficient, not part of geometric mean.
                # But, weight_w, weight_a are part of weighted geometric mean.
                # In future, we can remove beta_w, beta_a may be!
                f_score =  ((beta_w * w_score)**weight_w * (beta_a * affinity_score_combined)**weight_a) ** (1.0/(weight_w + weight_a))
                print ("HELLO -> ",affinity_score_combined)
                print ("HELLO AGAIN -> ",w_score)
            except Exception as e:
                print(e)
                print("A: {}, B: {}, sort by: {}, w_score_before_norm: {}, w_score_min: {}, w_score: {}, affinity: {}".format(isp_a.name, isp_b.name, Sort_Strategy_Names[sorting_strategy], w_score_without_normalization, willingness_min, w_score, affinity_score_combined))
                f_score = 0.0
            willingness_score.update({Sort_Strategy_Names[sorting_strategy]:w_score})
            affinity_score.update({Sort_Strategy_Names[sorting_strategy]:affinity_score_combined})
            felicity_score.update({Sort_Strategy_Names[sorting_strategy]:f_score})
        else:
            willingness_score.update({Sort_Strategy_Names[sorting_strategy]:-1})
            affinity_score.update({Sort_Strategy_Names[sorting_strategy]:affinity_score_combined})
            felicity_score.update({Sort_Strategy_Names[sorting_strategy]:-1})
                
    willingness_score_for_all_isps[isp_a.name+'_'+isp_b.name] = willingness_score

    affinity_score_for_all_isps[isp_a.name+'_'+isp_b.name] = affinity_score
    
    felicity_score_for_all_isps[isp_a.name+'_'+isp_b.name] = felicity_score
    
    return willingness_score, affinity_score, felicity_score

            
def draw_graph(isp_a_asn, isp_b_asn, apc_data, sort_strategy, output_directory_for_isp):
    '''
    @note: This plots the graphs. 
    Plots APC graph of ISP A, B individually and another graph which plots these two as well as the combined APC 
    '''
    output_graph_ppc_id_sorted_filepath = os.path.abspath(output_directory_for_isp + "/" + "graph" + "/" + "ppc_id_sorted") 
    output_graph_willingness_sorted_filepath = os.path.abspath(output_directory_for_isp + "/" + "graph" + "/" + "willingness_sorted") 

    if not os.path.exists(output_graph_ppc_id_sorted_filepath):
        os.makedirs(output_graph_ppc_id_sorted_filepath)
    if not os.path.exists(output_graph_willingness_sorted_filepath):
        os.makedirs(output_graph_willingness_sorted_filepath)
    
    sort_by_ppc_id = False
    color = ['red', 'green', 'blue']
    line_style = [':', (0, (4, 6)), '--']
    
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig, ax = plt.subplots()
    order = []     
    if sort_by_ppc_id:
        # "order" is required. This will preserve the order for Y-axis as well.
        order = np.argsort(apc_data[apc_data.columns[0]])
        graph_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + "_" + str(isp_b_asn) + ".pdf")
    else:
        order = np.argsort(apc_data[apc_data.columns[-1]])[::-1]
        graph_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + "_" + str(isp_b_asn) + ".pdf")
    xs = np.array(apc_data[apc_data.columns[0]], int)[order]
    xs_tick_interval = int(math.ceil(float(len(xs)) / 12))  
    
    for i, j in zip(range(3), apc_data.columns.tolist()[-3:]):
        ax.plot(np.array(apc_data[j])[order], linestyle=line_style[i], color=color[i], label=j.split("=")[0])
    
        # These two plots the individual ISPs graphs
        if i == 0:
            if sort_by_ppc_id:               
                ax1.plot(xs, np.array(apc_data[j])[order], linestyle=line_style[i], color=color[i], label=j)
                graph_individual_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + ".pdf")
            else:
                order_individual = np.argsort(apc_data[j])[::-1]  # This [::-1] reverses the order and gives the position of items in descending order.
                xs_individual = np.array(apc_data[apc_data.columns[0]], int)[order_individual]
                xs_tick_interval_individual = int(math.ceil(float(len(xs_individual)) / 12))  
                ax1.plot(np.array(apc_data[j])[order_individual], linestyle=line_style[i], color=color[i], label=j)
                ax1.set_xticks(range(len(xs_individual))[::xs_tick_interval_individual])
                ax1.set_xticklabels(xs_individual[::xs_tick_interval_individual])
                graph_individual_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + ".pdf")
            ax1.legend()
            fig1.savefig(graph_individual_filename)
        if i == 1:
            if sort_by_ppc_id:
                ax2.plot(xs, np.array(apc_data[j])[order], linestyle=line_style[i], color=color[i], label=j)
                graph_individual_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_b_asn) + ".pdf")
            else:
                order_individual = np.argsort(apc_data[j])[::-1]
                xs_individual = np.array(apc_data[apc_data.columns[0]], int)[order_individual]
                xs_tick_interval_individual = int(math.ceil(float(len(xs_individual)) / 12))  
                ax2.plot(np.array(apc_data[j])[order_individual], linestyle=line_style[i], color=color[i], label=j)
                ax2.set_xticks(range(len(xs_individual))[::xs_tick_interval_individual])
                ax2.set_xticklabels(xs_individual[::xs_tick_interval_individual])
                graph_individual_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_b_asn) + ".pdf")
            ax2.legend()
            fig2.savefig(graph_individual_filename)
              
    if not sort_by_ppc_id:
        ax.set_xticks(range(len(xs))[::xs_tick_interval])
        ax.set_xticklabels(xs[::xs_tick_interval])

    ax.legend()
    fig.savefig(graph_filename)
    return


def write_acceptable_peering_contracts_to_file(isp_asn, sort_strategy, apc_list_df, output_directory_for_isp, function_name=None):
    '''
    @note: saves the Dataframe in a .csv format file
    @note: Neither CSV files have the index. 
    '''    
    Output_Directory = os.path.abspath(output_directory_for_isp + "/" + Sort_Strategy_Names[sort_strategy] + "/")
    if not os.path.exists(Output_Directory):
        os.makedirs(Output_Directory)
    if function_name == 'peering_algorithm_implementation':
        file_name = Output_Directory + "/" + "algorithm_report.csv"
        apc_list_df.to_csv(file_name, sep='\t', index=False)
    else:
        file_name = Output_Directory + "/" + str(isp_asn) + ".csv"
        apc_list_df.to_csv(file_name, sep='\t', index=False)

    
def get_total_prefixes_addresses_count_from_caida():
    '''
    @return: summation of prefixes count of all the organizations
    @return: summation of addresses count
    '''
    caida_api = "http://as-rank.caida.org/api/v1/" + str("orgs") + str("?populate=1")
    prefixes_count = 0
    address_count = 0
    while prefixes_count == 0:
        try:
            caida_response = requests.get(caida_api).json()
            for org_ in caida_response['data']:
                try:
                    prefixes_count += org_['cone']['prefixes']
                except:
                    print('Could not find prefix information for organization: {}, organization id in CAIDA: {}'.format(org_['name'], org_['id']))
                    print(org_)
                try:
                    address_count += org_['cone']['addresses']
                except:
                    print('Could not find address information for organization: {}, organization id in CAIDA: {}'.format(org_['name'], org_['id']))
        except Exception as e:
            print(e)
            time.sleep(3)
    
    return prefixes_count, address_count  


def get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(asn):
    '''
    @note: Calls CAIDA first to get the ISP name, how many prefixes, IP addresses it has and how many neighbors it is connected with.
    if CAIDA data is not available, we try RIPE. RIPE is not always available, so CAIDA is first choice.
    @return: name, prefixes, address_space, neighbor
    '''
    ripe_url_for_routing_status = "https://stat.ripe.net/data/routing-status/data.json?resource=AS"
    caida_url_for_routing_status = "http://as-rank.caida.org/api/v1/asns/"
    try:
        caida_response = requests.get(caida_url_for_routing_status + str(asn)).json()
        prefixes = caida_response['data']['cone']['prefixes']
        address_space = caida_response['data']['cone']['addresses']
        neighbor = caida_response['data']['degree']['globals']
        name = caida_response['data']['org']['name']
    except:
        print("Couldn't get RIPE response for AS {}".format(asn))
        try:
            ripe_response = requests.get(ripe_url_for_routing_status + str(asn)).json()
            prefixes = ripe_response['data']['announced_space']['v4']['prefixes']
            address_space = ripe_response['data']['announced_space']['v4']['ips']
            neighbor = ripe_response['data']['observed_neighbours']
        except:
            print("Couldn't get RIPE response either for AS {}".format(asn))   
    
    return name, prefixes, address_space, neighbor      


def ensure_isp_json_files(isp_pair_list):
    '''
    @param isp_pair_list: Takes isp_pair list 
    @note: checks if json file for each ISP exists. If not, calls PeeringInfo to access PeeringDB,
    and generate the json file before those are used in do_work(). 
    '''
    print("--------------------------------")
    print("| Ensuring all ISPs JSON files |")
    print("--------------------------------")
    if __package__ is None:
        import sys
        cur_dir = os.path.dirname(__file__)
        temp_dir = os.path.abspath(cur_dir + "/..")
        sys.path.append(os.path.abspath(temp_dir + "/" + "peering/"))
        from PeeringInfo import PeeringInfo
    else:
        from ..peering.PeeringInfo import PeeringInfo

    peeringInfo = PeeringInfo()
    
    total_prefixes_in_globe, total_addresses_in_globe = get_total_prefixes_addresses_count_from_caida()
    for isp_pair_for_file_check in isp_pair_list:
        isp_a_asn = isp_pair_for_file_check[0][1]
        isp_b_asn = isp_pair_for_file_check[1][1]
        isp_a_json_file_name = os.path.abspath(os.path.dirname(__file__)) + "/data" + "/" + str(isp_a_asn) + "_peering_db_data_file.json"
        isp_b_json_file_name = os.path.abspath(os.path.dirname(__file__)) + "/data" + "/" + str(isp_b_asn) + "_peering_db_data_file.json"
        isp_a_pdb_net_id = peeringInfo.get_net_id_from_asn(isp_a_asn)
        isp_b_pdb_net_id = peeringInfo.get_net_id_from_asn(isp_b_asn)

        if os.path.exists(isp_a_json_file_name) and os.path.exists(isp_b_json_file_name):
            continue
        if not (os.path.exists(isp_a_json_file_name) or os.path.exists(isp_b_json_file_name)):
            print("Creating JSON files for {} and {}".format(isp_pair_for_file_check[0][0], isp_pair_for_file_check[1][0]))
            # None exists, call for both ISP and save in 2 files.
            temp_a_city_state_list, temp_b_city_state_list, _ = peeringInfo.get_all_possible_peering_city_state_for_two_isp(isp_a_pdb_net_id, isp_b_pdb_net_id)
            for p in temp_a_city_state_list:
                p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})
            for p in temp_b_city_state_list:
                p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})
            
            with open(isp_a_json_file_name, "w") as fout:
                name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_a_asn)
                traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_a_pdb_net_id)
                data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_a_city_state_list,
                                 "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                 "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                 "neighbor": neighbor}}
                json.dump(data, fout)
            fout.close()
            with open(isp_b_json_file_name, "w") as fout:
                name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_b_asn)
                traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_b_pdb_net_id)
                data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_b_city_state_list,
                                 "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                 "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                 "neighbor": neighbor}}
                json.dump(data, fout)
            fout.close()
        else:
            if os.path.exists(isp_a_json_file_name):
                # Create ISP B, Since, if B also exist, then program would never reach here!
                print("Creating JSON files for {}".format(isp_pair_for_file_check[1][0]))
                temp_b_city_state_list = peeringInfo.get_all_possible_peering_city_state_for_single_isp(isp_b_pdb_net_id)
                for p in temp_b_city_state_list:
                    p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})
                with open(isp_b_json_file_name, "w") as fout:
                    name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_b_asn)
                    traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_b_pdb_net_id)
                    data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_b_city_state_list,
                                     "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                     "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                     "neighbor": neighbor}}
                    json.dump(data, fout)
                fout.close()
            else:
                # ISP B must exist. Since, ISP A doesn't. Create A.
                print("Creating JSON files for {}".format(isp_pair_for_file_check[0][0]))
                temp_a_city_state_list = peeringInfo.get_all_possible_peering_city_state_for_single_isp(isp_a_pdb_net_id)
                for p in temp_a_city_state_list:
                    p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})
                with open(isp_a_json_file_name, "w") as fout:
                    name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_a_asn)
                    traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_a_pdb_net_id)
                    data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_a_city_state_list,
                                     "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                     "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                     "neighbor": neighbor}}
                    json.dump(data, fout)
                fout.close()
    print("----- JSON file check done -----")
    
    
def do_work(isp_pair):
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
    isp_a_json_file_name = os.path.abspath(os.path.dirname(__file__)) + "/data" + "/" + str(isp_a_asn) + "_peering_db_data_file.json"
    isp_b_json_file_name = os.path.abspath(os.path.dirname(__file__)) + "/data" + "/" + str(isp_b_asn) + "_peering_db_data_file.json"
    
    if os.path.exists(isp_a_json_file_name) and os.path.exists(isp_b_json_file_name):
        fin = open(isp_a_json_file_name)
        data = json.load(fin)['data']
        temp_a_city_state_list = data['pop_list']
        if isp_a_asn == 174:
            isp_a_traffic_ratio_type = 'BALANCED'
        else:
            isp_a_traffic_ratio_type = data['traffic_ratio']
        isp_a_ip_address_count = data['address_space']
        isp_a_prefix_count = data['prefixes']
        global_ip_address_count = data['total_addresses_in_globe'] 
        global_prefix_count = data['total_prefixes_in_globe']
        fin.close()
        
        fin = open(isp_b_json_file_name)
        data = json.load(fin)['data']
        temp_b_city_state_list = data['pop_list']
        if isp_b_asn == 174:
            isp_b_traffic_ratio_type = 'BALANCED'
        else:
            isp_b_traffic_ratio_type = data['traffic_ratio']
        isp_b_ip_address_count = data['address_space']
        isp_b_prefix_count = data['prefixes']
        fin.close()       
    else:
        print("Input file missing for either {} or {}".format(isp_a_name, isp_b_name))
        return None
               
    isp_a_pop_location_id_list = convert_city_state_to_pop_location(temp_a_city_state_list)
    isp_b_pop_location_id_list = convert_city_state_to_pop_location(temp_b_city_state_list)
    
    common_pop_location_id_list = [a for a in isp_a_pop_location_id_list if a in isp_b_pop_location_id_list]

    isp_a_port_capacity_at_common_pop_dict = {}
    isp_b_port_capacity_at_common_pop_dict = {}
         
    common_pop_location_isp_id_isp_type_in_peeringdb_tuple_list = {i: (List_Of_POP_Locations[i].isp_type_in_peering_db, List_Of_POP_Locations[i].isp_id_in_peering_db) for i in common_pop_location_id_list}
    temp_dict_for_isp_a_port_capacity = {(i['isp_type_in_peering_db'], i['isp_id_in_peering_db']):i['port_capacity'] for i in temp_a_city_state_list}
    temp_dict_for_isp_b_port_capacity = {(i['isp_type_in_peering_db'], i['isp_id_in_peering_db']):i['port_capacity'] for i in temp_b_city_state_list}
    
    for k, v in common_pop_location_isp_id_isp_type_in_peeringdb_tuple_list.iteritems():
        isp_a_port_capacity_at_common_pop_dict[k] = temp_dict_for_isp_a_port_capacity[v]
        isp_b_port_capacity_at_common_pop_dict[k] = temp_dict_for_isp_b_port_capacity[v]
    
    '''
    Sort the common PoPs based on their capacity, higher ones are one the front.
    Based on PoP port capacity, higher the capacity, more preferred it is. Higher population as well.
    Since, sorting in dictionary is not possible, we get a sorted list of tuple after sorting, we cut the list to get top ones.
    Then, we convert that list to a dictionary again and use the keys as "common_pop_location_id_list"
    '''  
    isp_a_port_capacity_at_common_pop_dict = sorted(isp_a_port_capacity_at_common_pop_dict.iteritems(), key=lambda (k, v):(v, k), reverse=True)
    if len(common_pop_location_id_list) > Max_Common_Pop_Count:
        isp_a_port_capacity_at_common_pop_dict = isp_a_port_capacity_at_common_pop_dict[:Max_Common_Pop_Count]
    isp_a_port_capacity_at_common_pop_dict = {item[0]:item[1] for item in isp_a_port_capacity_at_common_pop_dict}
    common_pop_location_id_list = isp_a_port_capacity_at_common_pop_dict.keys()
      
    isp_a = ISP(isp_a_asn, isp_a_name, (isp_a_ip_address_count * 100.0) / global_ip_address_count, (isp_a_prefix_count * 100.0) / global_prefix_count, isp_a_pop_location_id_list, isp_b_pop_location_id_list, common_pop_location_id_list, isp_a_port_capacity_at_common_pop_dict, isp_a_traffic_ratio_type)
    isp_b = ISP(isp_b_asn, isp_b_name, (isp_b_ip_address_count * 100.0) / global_ip_address_count, (isp_b_prefix_count * 100.0) / global_prefix_count, isp_b_pop_location_id_list, isp_a_pop_location_id_list, common_pop_location_id_list, isp_b_port_capacity_at_common_pop_dict, isp_b_traffic_ratio_type)
    
    isp_a.all_acceptable_peering_contracts, isp_a.all_acceptable_peering_contracts_count, isp_b.all_acceptable_peering_contracts, isp_b.all_acceptable_peering_contracts_count = compute_all_acceptable_peering_contracts(isp_a.sorting_strategy, isp_a.my_pop_locations_list, isp_a.offloaded_traffic_list_to_opponent_at_common_pops, isp_b.sorting_strategy, isp_b.my_pop_locations_list, isp_b.offloaded_traffic_list_to_opponent_at_common_pops, common_pop_location_id_list, isp_a.isp_traffic_ratio_type, isp_b.isp_traffic_ratio_type)
    willingness_score, affinity_score, felicity_score = peering_algorithm_implementation(isp_a, isp_b)

    fout_for_apc_count = open(os.path.abspath(Output_Directory + "/" + "apc_count_" + str(Max_Common_Pop_Count) + ".txt"), "a+")            
    fout_for_apc_count.write("ISP {:<12} has {:>3} PoP location, ISP {:<12} has {:>3} PoP location, Common location count: {:<3}\n".format(isp_a.name, len(isp_a.my_pop_locations_list), isp_b.name, len(isp_b.my_pop_locations_list), len(isp_a.common_pop_locations))) 
    if isp_a.all_possible_peering_contracts_count == 0:
        fout_for_apc_count.write("APC Count: {}, PPC Count: {}, Nothing created\n".format(isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count))
    else:
        fout_for_apc_count.write("APC Count: {}, PPC Count: {}, APC/PPC Ratio: {:.2f}\n".format(isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count, float(isp_a.all_acceptable_peering_contracts_count) / isp_a.all_possible_peering_contracts_count))
    fout_for_apc_count.close()  
    
    similarity_score_based_on_pop_count = similarity_score_on_prefix = similarity_score_on_address = 0     
    for i, isp_a_similarity_condition_value, isp_b_similarity_condition_value in zip(range(3),
                                                                                     [len(isp_a.my_pop_locations_list), isp_a.prefix_coverage_percentage, isp_a.ip_address_coverage_percentage],
                                                                                     [len(isp_b.my_pop_locations_list), isp_b.prefix_coverage_percentage, isp_b.ip_address_coverage_percentage]):
        similarity_score = 0
        if isp_a_similarity_condition_value > isp_b_similarity_condition_value:
            similarity_score = float(isp_b_similarity_condition_value) / isp_a_similarity_condition_value
        else:
            if isp_b_similarity_condition_value != 0:
                similarity_score = float(isp_a_similarity_condition_value) / isp_b_similarity_condition_value
        if i == 0:
            similarity_score_based_on_pop_count = similarity_score
        elif i == 1:
            similarity_score_on_prefix = similarity_score
        elif i == 2:
            similarity_score_on_address = similarity_score
            
    return {'isp_a':{'name': isp_a.name, 'asn': isp_a_asn, 'pop_count': len(isp_a.my_pop_locations_list)}, 'isp_b':{'name': isp_b.name, 'asn': isp_b_asn, 'pop_count': len(isp_b.my_pop_locations_list)}, 'apc_count': isp_a.all_acceptable_peering_contracts_count, 'willingness_score': willingness_score, 'affinity_score': affinity_score, 'felicity_score': felicity_score, 'ppc_count': isp_a.all_possible_peering_contracts_count, 'similarity_score': {'based_on_address': similarity_score_on_address, 'based_on_prefix': similarity_score_on_prefix, 'based_on_pop': similarity_score_based_on_pop_count}, }

def draw_scatter_plot(scatter_plot_data=None):
    '''
    This is now will be called always to draw the plot and save the JSON file.
    Plots the scatter graph. Depending on whether the JSON file exists or not, it creates or reads from the file.
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'w')
        json.dump(scatter_plot_data, file_for_saving_scatter_plot_data)
        data = scatter_plot_data['data']
    file_for_saving_scatter_plot_data.close()
    
#     print("="*50)
#     print("Printing Felicity and Similarity scores for ISP pairs who have s_score > 0.4 but at least of of the f_score < 0.2")
#     for pair_type, pair_list in data.items():
#         if pair_type not in ['access', 'content', 'transit', 'transit-access', 'access-transit']:
#             continue
#         for k in pair_list:
#             f_score = k['felicity_score']
#             s_score = k['similarity_score']
#             if max([s_score['based_on_prefix'], s_score['based_on_address']]) > 0.4:
#                 if max(f_score.values()) < 0.2:
#                     print(pair_type, k['isp_a']['name'], k['isp_b']['name'], f_score, s_score)
#     print("="*50)
        
    fig, axarr = plt.subplots(3, 3, sharex=True, sharey=True, gridspec_kw={'hspace':0.1, 'wspace':0.1})
    subplot_position = {'access':(0, 0), 'content':(1, 1), 'transit':(2, 2), 'access-content':(0, 1), 'access-transit':(0, 2), 'content-access':(1, 0), 'content-transit':(1, 2), 'transit-access':(2, 0), 'transit-content':(2, 1)} 

    for k, result in data.items():
        k = str(k)
        (subplot_pos_x, subplot_pos_y) = subplot_position[k]
        axarr[subplot_pos_x][subplot_pos_y].scatter([item['ppc_count'] for item in result if item['ppc_count'] != 0], [item['apc_count'] for item in result if item['ppc_count'] != 0], marker='o', color='b', facecolors='none')
    axarr[2][0].set_xlabel('Access')
    axarr[2][1].set_xlabel('Content')
    axarr[2][2].set_xlabel('Transit')
    axarr[0][0].set_ylabel('Access')
    axarr[1][0].set_ylabel('Content')
    axarr[2][0].set_ylabel('Transit')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.16, left=0.16)
    for_outside_x_y_label = fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none',top=False,left=False,right=False,bottom=False)
    for_outside_x_y_label.set_xlabel('Possible peering contracts count')
    plt.ylabel('Acceptable peering contracts count')
    for_outside_x_y_label.xaxis.labelpad = 15
    for_outside_x_y_label.yaxis.labelpad = 35
    
    fig.savefig(os.path.abspath(Output_Directory + "/" + "isp_pair_apc_" + str(Max_Common_Pop_Count) + ".pdf"))
    
def helping_tool_get_max_r_squared_weights(scatter_plot_data=None):
    '''
    @note: Reads the JSON file or the JSON output of main() and identifies the max weight factors for beta_weight, weight_w, weight_a
    for the maximum r-squared value. Which we then use for setting up the values manually.
    This is dedicately a helping tool and can't be run to optimize the weights directly. And, these weights do not impact the APCs at all.
    These weights can be used only for identifying the best pair with "willingness_score" and "affinity_score"
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
        file_for_saving_scatter_plot_data.close()
    else:
        data = scatter_plot_data['data']
    
    max_r_squared_val_content_related = 0.0
    max_r_squared_val_others = 0.0
    max_beta_weight = max_beta_weight_for_content_related = 0.0
    max_weight_w = max_weight_w_for_content_related = 0 
    max_weight_a = max_weight_a_for_content_related = 0
    
    for beta_w_i in range(1,10):
        beta_weight = beta_weight_for_content_related = beta_w_i / 10.0
        beta_w_for_content_related = beta_weight_for_content_related
        beta_a_for_content_related = 1 - beta_weight_for_content_related
        beta_w = beta_weight
        beta_a = 1 - beta_weight
        
        weight_max_value_for_loop = 500
        for weight_w_i in range(1, weight_max_value_for_loop):
            weight_w = weight_w_for_content_related = weight_w_i
            for weight_a_i in range(1, weight_max_value_for_loop):
                weight_a = weight_a_for_content_related = weight_a_i
                for k, v in data.items():
                    for i in range(len(v)):         
                        w = data[k][i]['willingness_score']
                        a = data[k][i]['affinity_score']
                        for sort_type in Sort_Strategy_Names:
                            if w[sort_type] > 0:
                                if 'content' in k:
                                    data[k][i]['felicity_score'][sort_type] = ((beta_w_for_content_related * w[sort_type])**weight_w_for_content_related * (beta_a_for_content_related * a[sort_type])**weight_a_for_content_related) ** (1.0/(weight_w_for_content_related + weight_a_for_content_related))
                                else:
                                    data[k][i]['felicity_score'][sort_type] = ((beta_w * w[sort_type])**weight_w * (beta_a * a[sort_type])**weight_a) ** (1.0/(weight_w + weight_a))

                for similarity_type in ['based_on_prefix', 'based_on_address', 'based_on_pop']:
                    for sorting_type in Sort_Strategy_Names:
                        x_axis_values_for_content_related_only = []
                        y_axis_values_for_content_related_only = []
                        x_axis_values_for_others = []
                        y_axis_values_for_others = []
                        no_felicity_score_for_this_sorting_type_count = 0
                        min_pair = {}
                        min_value = 10.0
                        for k, v in data.items():
                            for v_items in v:
                                if v_items['felicity_score'][sorting_type] > 0.0:
                                    if 'content' in k:
                                        x_axis_values_for_content_related_only.append(v_items['similarity_score'][similarity_type])
                                        y_axis_values_for_content_related_only.append(v_items['felicity_score'][sorting_type])
                                    else:
                                        x_axis_values_for_others.append(v_items['similarity_score'][similarity_type])
                                        y_axis_values_for_others.append(v_items['felicity_score'][sorting_type])
                                        if v_items['felicity_score'][sorting_type] < min_value:
                                            min_pair = v_items
                                            min_value = v_items['felicity_score'][sorting_type]
                                else:
                                    no_felicity_score_for_this_sorting_type_count += 1
                        
                        if len(x_axis_values_for_content_related_only) > 0:
                            # Trend line using scipy
                            x_axis_values_for_content_related_only = np.array(x_axis_values_for_content_related_only) 
                            y_axis_values_for_content_related_only = np.array(y_axis_values_for_content_related_only)
                            try:
                                slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_content_related_only, y_axis_values_for_content_related_only)
                            
                                if r_value**2 > max_r_squared_val_content_related:
                                    max_r_squared_val_content_related = r_value**2
                                    max_beta_weight_for_content_related = beta_weight_for_content_related
                                    max_weight_w_for_content_related = weight_w_for_content_related
                                    max_weight_a_for_content_related = weight_a_for_content_related
                            except Exception as e:
                                print(e)
                                
                            x_axis_values_for_others = np.array(x_axis_values_for_others) 
                            y_axis_values_for_others = np.array(y_axis_values_for_others)
                            
                            try:
                                slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_others, y_axis_values_for_others)
    
                                if r_value**2 > max_r_squared_val_others:
                                    max_r_squared_val_others = r_value**2
                                    max_beta_weight = beta_weight
                                    max_weight_w = weight_w
                                    max_weight_a = weight_a
                            except Exception as e:
                                print(e)
    
    print("For Content related: Max R-squared: {}, max beta_weight: {}, max weight_w: {}, max weight_a: {}".format(max_r_squared_val_content_related, max_beta_weight_for_content_related, max_weight_w_for_content_related, max_weight_a_for_content_related))
    print("For Others related: Max R-squared: {}, max beta_weight: {}, max weight_w: {}, max weight_a: {}".format(max_r_squared_val_others, max_beta_weight, max_weight_w, max_weight_a))
    
    
def draw_brittleness(scatter_plot_data=None):
    '''
    @note: Reads the JSON file or draw from the output of main() and plots a scatter plot 
    @note: We use similarity_score[0].keys() to populate all the similarity criteria names. 
    We can manually list the names, but that may cause typo in future if we change the names.
    @note: sorting_type are actually the Sort_Strategy_Names. So we use that list.
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'w')
        json.dump(scatter_plot_data, file_for_saving_scatter_plot_data)
        data = scatter_plot_data['data']
    file_for_saving_scatter_plot_data.close()
    
    ### Here we update the beta scores (weights) to see how willingness_score and affinity_score impacts the ultimate felicity_score.
    for k, v in data.items():
        for i in range(len(v)):         
            w = data[k][i]['willingness_score']
            a = data[k][i]['affinity_score']
            for sort_type in Sort_Strategy_Names:
                if w[sort_type] > 0:
                    if 'content' in k:
                        data[k][i]['felicity_score'][sort_type] = ((beta_w_for_content_related * w[sort_type])**weight_w_for_content_related * (beta_a_for_content_related * a[sort_type])**weight_a_for_content_related) ** (1.0/(weight_w_for_content_related + weight_a_for_content_related))
                    else:
                        data[k][i]['felicity_score'][sort_type] = ((beta_w * w[sort_type])**weight_w * (beta_a * a[sort_type])**weight_a) ** (1.0/(weight_w + weight_a))
    
    felicity_score = []
    similarity_score = []
    max_diff = max_own = max_ratio = 0.0
    max_pair = {}
    for k, v in data.items():
        for i in v:
            if 1 in i['felicity_score'].values():
                print(i['isp_a']['name'], i['isp_a']['asn'], i['isp_b']['name'], i['isp_b']['asn'])
            for b, a in i['felicity_score'].items():
                if a < 0 and a != -1:
                    print('< 0 for ISP A: {}, ASN: {}, ISP B: {}, ASN: {}, Felicity_score: {} in sort category: {}'.format(i['isp_a']['name'], i['isp_a']['asn'], i['isp_b']['name'], i['isp_b']['asn'], a, b))
                elif a == 0:
                    print('= 0 for ISP A: {}, ASN: {}, ISP B: {}, ASN: {}'.format(i['isp_a']['name'], i['isp_a']['asn'], i['isp_b']['name'], i['isp_b']['asn']))
            if sum([y for x, y in i['felicity_score'].items()]) == -3:
                continue
            else:
                if i['felicity_score']['diff'] > max_diff and i['apc_count'] > 1:
                    max_diff = i['felicity_score']['diff']
                    max_pair['diff'] = i
                if i['felicity_score']['own'] > max_own and i['apc_count'] > 1:
                    max_own = i['felicity_score']['own']
                    max_pair['own'] = i
                if i['felicity_score']['ratio'] > max_ratio and i['apc_count'] > 1:
                    max_ratio = i['felicity_score']['ratio']
                    max_pair['ratio'] = i
                felicity_score.append(i['felicity_score'])
                similarity_score.append(i['similarity_score'])
      
    print("=========================== Print peering pairs status =================")
    peering_status_count_dict = {}
    fig1, axarr_for_content_pairs_check = plt.subplots(2, 3, sharey=True, squeeze=False)
    for k, v in data.items():
        if 'content' in k:
            similarity_prefix_x_axis = [c_v_items['similarity_score']['based_on_prefix'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_ip_address_x_axis = [c_v_items['similarity_score']['based_on_address'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_pop_count_x_axis = [c_v_items['similarity_score']['based_on_pop'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            content_y_axis =[c_v_items['felicity_score']['diff'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
        else:
            similarity_prefix_x_axis = [c_v_items['similarity_score']['based_on_prefix'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_ip_address_x_axis = [c_v_items['similarity_score']['based_on_address'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_pop_count_x_axis = [c_v_items['similarity_score']['based_on_pop'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            content_y_axis =[c_v_items['felicity_score']['diff'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
        for i, similarity_list_j in zip(range(3), [similarity_prefix_x_axis, similarity_ip_address_x_axis, similarity_pop_count_x_axis]):
            if 'content' in k:
                axarr_for_content_pairs_check[0][i].scatter(similarity_list_j, content_y_axis, s=1, label=k)
            else:
                axarr_for_content_pairs_check[1][i].scatter(similarity_list_j, content_y_axis, s=1, label=k)
            
        peering_status_count_dict[k] = {}
        ## We use 'ratio' as the only sort_type because we found that all the other sort_type produce the exact same results. We don't need to run a loop for three times to get similar values.
        sort_type = 'ratio'
        count_below_zero = 0
        count_zero = 0
        count_between_zero_and_point_zero_one = 0
        count_beyond = 0
        count_others = 0
        for v_items in v:
            if v_items['felicity_score'][sort_type] < 0:
                count_below_zero += 1
            elif v_items['felicity_score'][sort_type] == 0:
                count_zero += 1
            elif 0 < v_items['felicity_score'][sort_type] and v_items['felicity_score'][sort_type] < 0.01:
                count_between_zero_and_point_zero_one += 1
            elif v_items['felicity_score'][sort_type] >= 0.01:
                count_beyond += 1
            else:
                count_others += 1
        peering_status_count_dict[k].update({sort_type : {'< 0:': count_below_zero, '= 0:': count_zero, '0 < count < 0.0.1: ':count_between_zero_and_point_zero_one, '>= 0.01': count_beyond, 'others: ': count_others}})
    
    for k, v in peering_status_count_dict.items():
        print(k)
        for v_items in v:
            print("\n".join("{}\t".format(v) for _, v in v.items())) 
      
    plt.subplots_adjust(right=0.7)
    for i, similar_type_name in zip(range(3), ['based_on_prefix', 'based_on_address', 'based_on_pop']):
        axarr_for_content_pairs_check[1][i].set_xlabel(similar_type_name)
    axarr_for_content_pairs_check[0][2].legend(bbox_to_anchor=(2.6,1.05), loc='upper right')          
    axarr_for_content_pairs_check[1][2].legend(bbox_to_anchor=(2.53,1.045), loc='upper right')          
    fig1.savefig(os.path.abspath(Output_Directory + "/" + "Content_vs_non_content_felicity_" + str(Max_Common_Pop_Count) + ".pdf"))
    print("=========================== END: Print peering pairs status =================")
              
    print("=================")
    print("Highest felicity score pairs: {}".format(max_pair))
    print("=================")
    similarity_criteria_list = similarity_score[0].keys()
    brittleness_color_list = ['r', 'g', 'b']
    brittleness_marker_list = ['<', '>', '^']
  
    fig, axarr = plt.subplots(2, 3, sharey=True, squeeze=False)
    temp_list_for_0_felicity_score_isps_pair = []
    for i, similarity_type in zip(range(3), similarity_criteria_list):
        for sorting_type, brittleness_color, brittleness_marker in zip(Sort_Strategy_Names, brittleness_color_list, brittleness_marker_list):
            x_axis_values_for_content_related_only = []
            y_axis_values_for_content_related_only = []
            x_axis_values_for_others = []
            y_axis_values_for_others = []
            no_felicity_score_for_this_sorting_type_count = 0
            min_pair = {}
            min_value = 10.0
            for k, v in data.items():
                for v_items in v:
                    if v_items['felicity_score'][sorting_type] > 0.0:
                        if 'content' in k:
                            x_axis_values_for_content_related_only.append(v_items['similarity_score'][similarity_type])
                            y_axis_values_for_content_related_only.append(v_items['felicity_score'][sorting_type])
                        else:
                            x_axis_values_for_others.append(v_items['similarity_score'][similarity_type])
                            y_axis_values_for_others.append(v_items['felicity_score'][sorting_type])
                            if v_items['felicity_score'][sorting_type] < min_value:
                                min_pair = v_items
                                min_value = v_items['felicity_score'][sorting_type]
                    else:
                        temp_list_for_0_felicity_score_isps_pair.append((v_items['isp_a']['name'], v_items['isp_b']['name'], sorting_type))
                        no_felicity_score_for_this_sorting_type_count += 1
            print("In sorting type {} and similarity type {}, Min (>0) felicity score: {} between {} and {}".format(sorting_type, similarity_type, min_pair['felicity_score'][sorting_type], min_pair['isp_a']['name'], min_pair['isp_b']['name']))
            axarr[0,i].scatter(x_axis_values_for_content_related_only, y_axis_values_for_content_related_only, marker=brittleness_marker, color=brittleness_color, facecolor='none', s=1, label=sorting_type)
            axarr[1,i].scatter(x_axis_values_for_others, y_axis_values_for_others, marker=brittleness_marker, color=brittleness_color, facecolor='none', s=1, label=sorting_type)
             
            # Trend line using scipy
            x_axis_values_for_content_related_only = np.array(x_axis_values_for_content_related_only) 
            y_axis_values_for_content_related_only = np.array(y_axis_values_for_content_related_only)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_content_related_only, y_axis_values_for_content_related_only)
            print("R-squared: {}, P-value: {} for sort_type: {} in similarity_type: {}".format(r_value**2, p_value, sorting_type, similarity_type))
            axarr[0,i].plot(x_axis_values_for_content_related_only, intercept + slope*x_axis_values_for_content_related_only, color=brittleness_color, linestyle='-', linewidth=0.5)
 
            x_axis_values_for_others = np.array(x_axis_values_for_others) 
            y_axis_values_for_others = np.array(y_axis_values_for_others)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_others, y_axis_values_for_others)
            print("R-squared: {}, P-value: {} for sort_type: {} in similarity_type: {}".format(r_value**2, p_value, sorting_type, similarity_type))
            axarr[1,i].plot(x_axis_values_for_others, intercept + slope*x_axis_values_for_others, color=brittleness_color, linestyle='-', linewidth=0.5)
  
            print("No felicity score for {} similarity type based on {} is: {}".format(similarity_type, sorting_type, no_felicity_score_for_this_sorting_type_count))
            # Specify the position of legend. bbox_to_anchor is the reference point and upper_left means it's the upper left corner of the legend box. 
            # https://stackoverflow.com/questions/44413020/how-to-specify-legend-position-in-matplotlib-in-graph-coordinates
            l0 = axarr[0,i].legend()
            l1 = axarr[1,i].legend()
            axarr[1,i].set_xlabel(similarity_type.split("_")[-1] + " " + "count")
        for handler in l0.legendHandles:
            handler.set_sizes([18.0])
        for handler in l1.legendHandles:
            handler.set_sizes([18.0])
    print("----Print the ISPs pair who have 0 Felicity score in some sort strategy----")
    print(temp_list_for_0_felicity_score_isps_pair)
    print("----0 Felicity score printing ended----")
    axarr[0,0].set_ylabel('at least one is Content')
    axarr[1,0].set_ylabel('other ISP pairs')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.14, left=0.125)
    fig.text(0.03, 0.73, 'Felicity scores for ISP pairs', rotation='vertical', ha='center')
    fig.text(0.53, 0.02, 'Similarity score based on', ha='center')
      
    fig.savefig(os.path.abspath(Output_Directory + "/" + "felicity_" + str(Max_Common_Pop_Count) + ".pdf"))
    
    
def find_best_deals(scatter_plot_data=None):
    '''
    This identifies the best pairs using highest felicity_score.
    For each pair, it also suggests top 3 APCs. [Suggests the PoP using PeeringDB data, fac_id/ix_ip, type]
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        data = scatter_plot_data['data']
    
    max_val_pair = dict()
    max_felicity_score = dict()
    sort_type_preferred_by_maximum_isp = dict()
    for s in Sort_Strategy_Names:
        max_felicity_score[s] = 0.0
        sort_type_preferred_by_maximum_isp[s] = 0
    for k, v in data.items():
        for v_item in v:
            sort_type_preferred_for_this_pair = max(v_item['felicity_score'], key=v_item['felicity_score'].get)
            sort_type_preferred_by_maximum_isp[sort_type_preferred_for_this_pair] += 1
            if v_item['ppc_count'] > 1:
                if v_item['isp_a']['name'] == 'ebay' or v_item['isp_b']['name'] == 'ebay':  # 'Ebay' has only 1 common PoP, so we skipped it!
                    continue
                for s in Sort_Strategy_Names:
                    if v_item['felicity_score'][s] > 0:
                        if v_item['felicity_score'][s] > max_felicity_score[s]: 
                            max_felicity_score[s] = v_item['felicity_score'][s]
                            try:
                                max_val_pair[s] = v_item
                            except Exception as _:
                                max_val_pair.update({s:v_item})
    print("===== BEGIN: Maximum Felicity scores in different sorting criteria =====")
    for s in Sort_Strategy_Names:
        print("Max felicity in {} category: {}".format(s, max_val_pair[s]))
        print("This sorting preferred by: {}".format(sort_type_preferred_by_maximum_isp[s]))
    print("===== END: Maximum Felicity scores in different sorting criteria =====")
        
    max_preffered_sort_type = max(sort_type_preferred_by_maximum_isp, key=sort_type_preferred_by_maximum_isp.get)
    
    max_pair_list = []
    for k, v in data.items():
        for v_item in v:
            if v_item['felicity_score'][max_preffered_sort_type] > 0.0 and v_item['willingness_score'][max_preffered_sort_type]<1.0:
                if v_item['isp_a']['name'] != v_item['isp_b']['name']:
                    if max_val_pair[max_preffered_sort_type]['isp_a']['name'] == v_item['isp_a']['name'] or max_val_pair[max_preffered_sort_type]['isp_a']['name'] == v_item['isp_b']['name']:
                        max_pair_list.append([v_item['isp_a']['name'], v_item['isp_b']['name'], v_item['felicity_score'][max_preffered_sort_type]])
    
    max_pair_list_sorted = sorted(max_pair_list, key=lambda x: x[2], reverse=True)
    print("ISP with highest felicity scores and it\'s potential pairs: {}".format(max_pair_list_sorted[:]))
    
def caida_comparison(scatter_plot_data=None):
    '''
    @note: Reads the JSON file or from the output of main() and compare with CAIDA data. 
    If match is found, plots YES, otherwise NO.
    @note: '20190601.as-rel' and '201603.as-rel-geo' are two options for matching. 
    Source URL: http://data.caida.org/datasets/2013-asrank-data-supplement/data/
    1st shows provider2customer or peer2peer relations, 2nd one shows peering location data.
    We use 1st one, as this is latest and only considers the peering locations.
    @note: In CAIDA, smallest number ASN always comes first in the pair. So, we searched by the smallest of ISP A and ISP B.
    If match found for (A or B), we then checked if other is in the list of that ISPs peers.
    @note: willingness_type are actually the Sort_Strategy_Names. So we use that list.
    @note: It appears, some ISPs peer outside US, so CAIDA lists them, but as we don't use any PoPs outside US, we set their
    willingness score to -1. The figure looks bad! To avoid this, we don't plot -1 in figure and just list those ISPs pair later.
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'w')
        json.dump(scatter_plot_data, file_for_saving_scatter_plot_data)
        data = scatter_plot_data['data']
    file_for_saving_scatter_plot_data.close()
    caida_data = dict()
    with open(os.path.abspath(Data_Directory + "/" + "20190601.as-rel.txt"), 'r') as fin:
        f_lines = fin.readlines()
        for l in f_lines:
            if l[0] == '#':
                continue
            l = l.strip().split("|")
            if l[-1] == '0':
                try:
                    caida_data[int(l[0])].append(int(l[1]))
                except Exception as _:
                    caida_data[int(l[0])] = [int(l[1])]
        fin.close()

    print "HELLO ->", caida_data
    asn_keys = caida_data.keys()
    pair_match_dict = {}
    no_pair_match_dict = {}
    
    for k, v in data.items():
        pair_match_with_caida_in_isp_type = 0
        pair_match_asn_list = []
        no_pair_match_asn_list = []
        for v_item in v:
            isp_a_asn = v_item['isp_a']['asn']
            isp_b_asn = v_item['isp_b']['asn']
            if isp_a_asn < isp_b_asn:
                if isp_a_asn in asn_keys:
                    if isp_b_asn in caida_data[isp_a_asn]:
                        pair_match_asn_list.append(v_item)
                        pair_match_with_caida_in_isp_type += 1
                        if sum(v_item['felicity_score'].values()) == -3:
                            print('ISP pairs with felicity score -1: [{}({}), {}({})]'.format(v_item['isp_a']['name'], isp_a_asn, v_item['isp_b']['name'], isp_b_asn))
                    else:
                        no_pair_match_asn_list.append(v_item)
                else:
                    no_pair_match_asn_list.append(v_item)
            else:
                if isp_b_asn in asn_keys:
                    if isp_a_asn in caida_data[isp_b_asn]:
                        pair_match_asn_list.append(v_item)
                        pair_match_with_caida_in_isp_type += 1
                        if sum(v_item['felicity_score'].values()) == -3:
                            print('ISP pairs with felicity score -1: [{}({}), {}({})]'.format(v_item['isp_a']['name'], isp_a_asn, v_item['isp_b']['name'], isp_b_asn))
                    else:
                        no_pair_match_asn_list.append(v_item)
                else:
                    no_pair_match_asn_list.append(v_item)
        print("Total ISPs pair in {} for {} category. Peering in CAIDA: {}, Not peering according to CAIDA (may include our suggested): {}".format(len(v), k, len(pair_match_asn_list), len(no_pair_match_asn_list)))        
        
        pair_match_dict[k] = pair_match_asn_list
        no_pair_match_dict[k] = no_pair_match_asn_list
    
    print("===== BEGIN: ISP pairs comparison with CAIDA=======")
    for k in pair_match_dict.keys():
        print("{} has {} potential pairs. Among them".format(k, len(data[k])))
        v = pair_match_dict[k]
        our_suggestion = [y for y in v if sum(y['felicity_score'].values()) > 0.0]
        print("======>>>>>>")
        print("Our suggested list of ISP pairs: {}".format(our_suggestion))
        print("======>>>>>>")
        not_recommended = [y for y in v if sum(y['felicity_score'].values()) <= 0.0] 
        print("peering in CAIDA: {}, we suggest correctly: {}, we don't suggest: {}".format(len(v), len(our_suggestion), len(not_recommended)))
        if len(not_recommended) > 0:
            print("Our not recommended list: {}".format([(not_recommended_pair['isp_a']['name'], not_recommended_pair['isp_b']['name'], not_recommended_pair['apc_count'], not_recommended_pair['felicity_score']) for not_recommended_pair in not_recommended]))
        v = no_pair_match_dict[k]
        our_suggestion = [y for y in v if sum(y['felicity_score'].values()) > 0.0]
        not_recommended = [y for y in v if sum(y['felicity_score'].values()) <= 0.0]
        print("not peering yet but we suggest: {}, and we don't suggest: {}".format(len(our_suggestion), len(not_recommended)))
    print("===== END: ISP pairs comparison with CAIDA=======")
    fig, axarr = plt.subplots(nrows=3, ncols=1, sharex=True)
    for i, willingness_type in zip(range(3), Sort_Strategy_Names):
        peer_in_caida_x = [y['felicity_score'][willingness_type] for v in pair_match_dict.values() for y in v if sum(y['felicity_score'].values()) > 0]
        axarr[i].scatter(peer_in_caida_x, [0.75 for _ in peer_in_caida_x], s = 3, color='r', label=willingness_type)
        not_peer_in_caida_but_we_suggest_x = [y['felicity_score'][willingness_type] for v in no_pair_match_dict.values() for y in v if sum(y['felicity_score'].values()) > 0]
        axarr[i].scatter(not_peer_in_caida_but_we_suggest_x, [0.25 for _ in not_peer_in_caida_but_we_suggest_x], s = 3, color='g')
        print("Sort type: {}: peering in CAIDA: {}, Not peering, but we suggest: {}".format(willingness_type, len(peer_in_caida_x), len(not_peer_in_caida_but_we_suggest_x)))
        axarr[i].set_ylim([0, 1])
        axarr[i].set_yticks([0.25, 0.75])
        axarr[i].set_yticklabels(('S', 'E')) # Suggested or Established
        axarr[i].legend(loc=5,handlelength=0,markerscale=0)
    fig.add_subplot(111,frameon=False)
    plt.tick_params(labelcolor='none',top=False,left=False,right=False,bottom=False)
    plt.xlabel('Felicity scores')  
    plt.ylabel('Peering status (E: Already established, S: Suggested)')
    fig.savefig(os.path.abspath(Output_Directory + "/" + "CAIDA_felicity_match_" + str(Max_Common_Pop_Count) + ".pdf"))
    
    # print "HELLO-> ", pair_match_dict
    return

def save_pop_locations():
    pop_list = []
    for l in List_Of_POP_Locations:
        _item = {}
        _item['ID'] = l.ID
        _item['isp_type_in_peering_db'] = l.isp_type_in_peering_db
        _item['isp_id_in_peering_db'] = l.isp_id_in_peering_db
        _item['city'] = l.city
        _item['state'] = l.state
        _item['population'] = l.population
        _item['internet_penetration_percentage'] = l.internet_penetration_percentage
        _item['latitude'] = l.latitude
        _item['longitude'] = l.longitude
        pop_list.append(_item)
    with open(os.path.join(Output_Directory, 'pop_list.json'), 'w') as fout:
        data = {}
        data['data'] = pop_list
        json.dump(data, fout)
        fout.close()

        
################## START OF SIGMETRICS PAPER WRITING TOOLS ############################            
def temp_method_for_readinig_isp_peeringdb_data_file(isp_pair):
    """
    This file will never be used for anything except for Sigmetrics paper submission.
    This file reads ISPs' peeringdb file from data/ folder and return the common pops.
    """
    isp_a_name, isp_a_asn = isp_pair[0]
    isp_b_name, isp_b_asn = isp_pair[1]
    
    temp_a_city_state_list, temp_b_city_state_list = [], []
    isp_a_traffic_ratio_type = isp_b_traffic_ratio_type = None 
    isp_a_ip_address_count = isp_a_prefix_count = isp_b_ip_address_count = isp_b_prefix_count = 0
    global_ip_address_count = global_prefix_count = 0
    # Look for cached file.
    isp_a_json_file_name = os.path.abspath(os.path.dirname(__file__)) + "/data" + "/" + str(isp_a_asn) + "_peering_db_data_file.json"
    isp_b_json_file_name = os.path.abspath(os.path.dirname(__file__)) + "/data" + "/" + str(isp_b_asn) + "_peering_db_data_file.json"
    if os.path.exists(isp_a_json_file_name) and os.path.exists(isp_b_json_file_name):
        fin = open(isp_a_json_file_name)
        data = json.load(fin)['data']
        temp_a_city_state_list = data['pop_list']
        if isp_a_asn == 174:
            isp_a_traffic_ratio_type = 'BALANCED'
        else:
            isp_a_traffic_ratio_type = data['traffic_ratio']
        isp_a_ip_address_count = data['address_space']
        isp_a_prefix_count = data['prefixes']
        global_ip_address_count = data['total_addresses_in_globe'] 
        global_prefix_count = data['total_prefixes_in_globe']
        fin.close()
        
        fin = open(isp_b_json_file_name)
        data = json.load(fin)['data']
        temp_b_city_state_list = data['pop_list']
        if isp_b_asn == 174:
            isp_b_traffic_ratio_type = 'BALANCED'
        else:
            isp_b_traffic_ratio_type = data['traffic_ratio']
        isp_b_ip_address_count = data['address_space']
        isp_b_prefix_count = data['prefixes']
        fin.close()       
    else:
        print("Input file missing for either {} or {}".format(isp_a_name, isp_b_name))
        return None
               
    isp_a_pop_location_id_list = convert_city_state_to_pop_location(temp_a_city_state_list)
    isp_b_pop_location_id_list = convert_city_state_to_pop_location(temp_b_city_state_list)
    common_pop_location_id_list = [a for a in isp_a_pop_location_id_list if a in isp_b_pop_location_id_list]

    return {"isp_a":isp_a_name, "isp_b":isp_b_name, "common_pop":common_pop_location_id_list}

def calculate_common_pops_for_paper(isp_dict):
    """
    This is a helper tool for writing paper.
    This uses another paper tool temp_method_for_readinig_isp_peeringdb_data_file()
    Q. Why we need this?
    A. We are not saving the actual common PoP count between 2 ISPs, we're now saving the Max_PoP_Count in the file. 
    Now, we read everything from apc_count_15.txt but use the actual ISPs peeringDB files to calculate the common PoPs between them. 
    """
    from collections import defaultdict
    apc_file_info = defaultdict(lambda: None)
    
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "output/", "apc_count_15.txt"))) as fin:
        while True:
            l1 = fin.readline()
            if not l1:
                break
            l1 = l1.strip("\n")
            l2 = fin.readline().strip("\n")

            isp_a_pop, isp_b_pop, common_pop = [int(s) for s in l1.split() if s.isdigit()]
            isp_a, isp_b = [s.split(" ")[1] for s in l1.split(", ")[:-1]]

            _numbers = [s.split(" ")[-1] for s in l2.split(", ")]
            apc_count = int(_numbers[0])
            ppc_count = int(_numbers[1])
            apc_ppc_ratio = float(_numbers[2])
            isp_pair_apc_ppc_info = {"isp_a":isp_a, "isp_b":isp_b, "isp_a_pop":isp_a_pop, "isp_b_pop":isp_a_pop, "apc_count": apc_count, "ppc_count":ppc_count, "apc_ppc_ratio":apc_ppc_ratio}
            apc_file_info[(isp_a, isp_b)] = isp_pair_apc_ppc_info
                
    result = []
    for k, v in isp_dict.iteritems():
        isp_pair_list = list(itertools.combinations(v.items(), 2))
                  
        for isp_pair in isp_pair_list:
            try:
                isp_pair_info = temp_method_for_readinig_isp_peeringdb_data_file(isp_pair)
                isp_pair_apc_info = apc_file_info[(isp_pair_info["isp_a"], isp_pair_info["isp_b"])]
                # This is the update we need!
                isp_pair_apc_info.update({"common_pop":len(isp_pair_info["common_pop"])})
                result.append(isp_pair_apc_info)
            except Exception as e:
                print(e)  

    # These are combined list. We may need to check the content-access, content-transit, transit-access (opposite combination) as well.
    isp_pair_combined_list = {}
    isp_pair_combined_list['access-content'] = [((name_a, asn_a), (name_c, asn_c)) for name_a, asn_a in isp_dict['access'].items() for name_c, asn_c in isp_dict['content'].items()] 
    isp_pair_combined_list['content-access'] = [((name_a, asn_a), (name_c, asn_c)) for name_a, asn_a in isp_dict['content'].items() for name_c, asn_c in isp_dict['access'].items()] 
    isp_pair_combined_list['access-transit'] = [((name_a, asn_a), (name_t, asn_t)) for name_a, asn_a in isp_dict['access'].items() for name_t, asn_t in isp_dict['transit'].items()]
    isp_pair_combined_list['transit-access'] = [((name_a, asn_a), (name_t, asn_t)) for name_a, asn_a in isp_dict['transit'].items() for name_t, asn_t in isp_dict['access'].items()]
    isp_pair_combined_list['transit-content'] = [((name_t, asn_t), (name_c, asn_c)) for name_t, asn_t in isp_dict['transit'].items() for name_c, asn_c in isp_dict['content'].items()]
    isp_pair_combined_list['content-transit'] = [((name_t, asn_t), (name_c, asn_c)) for name_t, asn_t in isp_dict['content'].items() for name_c, asn_c in isp_dict['transit'].items()]
                         
    for k, v in isp_pair_combined_list.items():
        for isp_pair in v:
            try:
                isp_pair_info = temp_method_for_readinig_isp_peeringdb_data_file(isp_pair)
                isp_pair_apc_info = apc_file_info[(isp_pair_info["isp_a"], isp_pair_info["isp_b"])]
                # This is the update we need!
                isp_pair_apc_info.update({"common_pop":len(isp_pair_info["common_pop"])})
                result.append(isp_pair_apc_info)
            except Exception as e:
                print(e)
    
    new_result = sorted(result, key=lambda k: k["common_pop"], reverse=True)
    
    for i in new_result:
        print("ISP {:<12} has {:>3} PoP location, ISP {:<12} has {:>3} PoP location, Common location count: {:<3}, APC: {:<8}, PPC: {:<8}, APC/ PPC Ratio: {}".format(i["isp_a"], i["isp_a_pop"], i["isp_b"], i["isp_b_pop"], i["common_pop"], i["apc_count"], i["ppc_count"], i["apc_ppc_ratio"])) 
    
################## END OF SIGMETRICS PAPER WRITING TOOLS ############################    
    

# Running code from Eclipse and Terminal:
# https://stackoverflow.com/questions/11536764/how-to-fix-attempted-relative-import-in-non-package-even-with-init-py
# To run from Terminal, nevigate to "src/com/nwsl/python" then "python automatedpeering/PeeringAlgorithm.py"
# Note: in access, 'cablevision': 6128 has only 2 PoPs, we can't calculate the Convex-hull. So, we ignore it for now. May be later on!
if __name__ == '__main__':
    isp_dict = {'access': {'cableone': 11492, 'centurylink': 209, 'charter':7843, 'comcast':7922, 'cox':22773, 'tds':4181, 'windstream':7029, },
                'content': {'akamai':20940, 'amazon': 16509, 'ebay':62955, 'facebook': 32934, 'google': 15169, 'microsoft': 8075, 'netflix': 2906, },
                'transit': {'columbus':23520, 'cogent': 174, 'he':6939, 'ntt': 2914, 'pccw':3491, 'sprint': 1239, 'verizon':701, 'zayo':6461, }}  
    
#     calculate_common_pops_for_paper(isp_dict) 
    # my_debug = False
    # if my_debug:
    if False:
        do_work((('columbus',23520), ('tds', 4181)))
        save_pop_locations()
       
    '''
    This following is just for time-saving. Main code is in the 'else' block.
    draw_scatter_plot() will be called anyway after all the calculations have been done and JSON file is created.           
    '''
    caida_comparison()

    # is_only_scatter_plot = False
    # if is_only_scatter_plot:
    if False:
        draw_scatter_plot()
#         helping_tool_get_max_r_squared_weights()
        draw_brittleness()
        caida_comparison()
        find_best_deals()
    else:
        scatter_plot_data = {"data":{}}
        for k, v in isp_dict.iteritems():
            # print(k,v)
            isp_pair_list = list(itertools.permutations(v.items(), 2))
            
            # print isp_pair_list
            # print '\n\n\n'            
#             ensure_isp_json_files(isp_pair_list)      #comment this line if you want to use the previous data.

            result = []
            if Max_Common_Pop_Count >= 20:        
                # Use of multi-processing.
                pool = Pool(processes=Max_Process_To_Be_Used) 
                result = pool.map(do_work, isp_pair_list[0:10])
            else:
                for isp_pair in isp_pair_list:
                    try:
                        result.append(do_work(isp_pair[0,10]))
                    except Exception as e:
                        print(e)  
           
            scatter_plot_data["data"][k] = result
            print("Initial trial (all possible combination) pairs: {} in {}, APCs generated for {} pairs. No PPC at all for {}".format(len(result), k.upper(), len([item for item in result if item['ppc_count'] != 0 and item['apc_count'] != 0]), len([item for item in result if item['ppc_count'] == 0])))      
                
        # These are combined list. We may need to check the content-access, content-transit, transit-access (opposite combination) as well.
        isp_pair_combined_list = {}
        isp_pair_combined_list['access-content'] = [((name_a, asn_a), (name_c, asn_c)) for name_a, asn_a in isp_dict['access'].items() for name_c, asn_c in isp_dict['content'].items()] 
        isp_pair_combined_list['content-access'] = [((name_a, asn_a), (name_c, asn_c)) for name_a, asn_a in isp_dict['content'].items() for name_c, asn_c in isp_dict['access'].items()] 
        isp_pair_combined_list['access-transit'] = [((name_a, asn_a), (name_t, asn_t)) for name_a, asn_a in isp_dict['access'].items() for name_t, asn_t in isp_dict['transit'].items()]
        isp_pair_combined_list['transit-access'] = [((name_a, asn_a), (name_t, asn_t)) for name_a, asn_a in isp_dict['transit'].items() for name_t, asn_t in isp_dict['access'].items()]
        isp_pair_combined_list['transit-content'] = [((name_t, asn_t), (name_c, asn_c)) for name_t, asn_t in isp_dict['transit'].items() for name_c, asn_c in isp_dict['content'].items()]
        isp_pair_combined_list['content-transit'] = [((name_t, asn_t), (name_c, asn_c)) for name_t, asn_t in isp_dict['content'].items() for name_c, asn_c in isp_dict['transit'].items()]
                               
        for k, v in isp_pair_combined_list.items():
            result = []
            if Max_Common_Pop_Count >= 20:
                pool = Pool(processes=Max_Process_To_Be_Used)
                result = pool.map(do_work, v)
            else:
                for isp_pair in v[0:10]:
                    try:
                        result.append(do_work(isp_pair))
                    except Exception as e:
                        print(e)
            
            scatter_plot_data["data"][k] = result
            print("Initial trial (all possible combination) pairs: {} in {}, APCs generated for {} pairs. No PPC at all for {}".format(len(result), k.upper(), len([item for item in result if item['ppc_count'] != 0 and item['apc_count'] != 0]), len([item for item in result if item['ppc_count'] == 0])))      
             
        draw_scatter_plot(scatter_plot_data)
        draw_brittleness(scatter_plot_data)
        caida_comparison(scatter_plot_data)
        save_pop_locations()
        find_best_deals(scatter_plot_data)


    with open('willingness.json','w') as json_file:
        json.dump(willingness_score_for_all_isps, json_file)
    
    with open('affinity.json','w') as json_file:
        json.dump(affinity_score_for_all_isps, json_file)
    
    with open('felicity.json','w') as json_file:
        json.dump(felicity_score_for_all_isps, json_file)