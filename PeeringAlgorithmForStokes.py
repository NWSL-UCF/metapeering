'''
Created on Sep 10, 2018

@author: prasun

@note: This file is dedicated for running in Stokes on UCF server. It may not include some feature, but also has some updated codes, that's not in original PeeringAlgorithm.py file.
Once we're done, I'll have to update all the new features to PeeringAlgorithm.py
'''

import numpy as np
from PopulationFromCensusGov import PopulationInfo
import os, json, itertools, math, warnings, time
import pandas as pd
# https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from multiprocessing import Pool

warnings.filterwarnings("ignore")

List_Of_POP_Locations = []
SORT_STRATEGY_DIFF = 0
SORT_STRATEGY_OWN = 1
SORT_STRATEGY_RATIO = 2
Sort_Strategy_Names = ['diff', 'own', 'ratio']
Max_Process_To_Be_Used = 8

Output_Directory = os.path.abspath(os.path.dirname(__file__) + "/" + "output")
if not os.path.exists(Output_Directory):
    os.mkdir(Output_Directory)


class ISP(object):
    '''
    @param as_number: Though an ISP may have multiple ASes, but right now, we're considering only one for each. 
    @param common_pop_locations: This may not always be the common subset of two ISPs. Because, ISPs may have their
    PoPs in same city, but interacting in different IXP or Private facility.
    @var sorting_strategy: is set to prioritize OWN traffic towards the opponent always. But, will be changed from other section. 
    '''
    def __init__(self, as_number, name, my_pop_locations_list, opponent_pop_locations_list, common_pop_locations, isp_port_capacity_at_common_pop_dict):
        self.as_number = as_number
        self.name = name
        self.sorting_strategy = SORT_STRATEGY_OWN
        self.my_pop_locations_list = my_pop_locations_list
        self.opponent_pop_locations_list = opponent_pop_locations_list
        self.common_pop_locations = common_pop_locations
        self.isp_port_capacity_at_common_pop_dict = isp_port_capacity_at_common_pop_dict
        self.my_traffic_matrix = self.gravity_model(self.my_pop_locations_list) 
        self.opponent_traffic_matrix = self.gravity_model(self.opponent_pop_locations_list)
        self.internal_traffic = self.generate_local_traffic()
        self.all_possible_peering_contracts_count = 2 ** len(self.common_pop_locations) - 1
        self.all_acceptable_peering_contracts = None
        self.all_acceptable_peering_contracts_count = 0         
                
    def __str__(self):
        return "ASN: {}, Name: {} ({}), My_PoPs_Id: {}, Opp_PoPs_Id: {}\nMy internal traffic: {}".format(self.as_number, self.name, self.aka, self.my_pop_locations_list, self.opponent_pop_locations_list, self.internal_traffic)
    
    def gravity_model(self, p_l_list):
        '''
        @param p_l_list: Takes the list of PoP locations and returns the traffic matrix based on those locations.
        @note: Uses Gravity model F = G * m1 * m2 / d^2. We assume G = 1 here.
        Again, F = m1 * a1 = m2 * a2. So, a1 = m2 / d^2. The traffic that flows towards destination. Heavy population attracts more traffic. 
        @note: DO NOT confuse with the index of this traffic matrix with the actual PoP IDs.
        The index are same for Traffic Matrix and PoP_ID holding list, where "my_pop_locations_list" and "opponent_pop_locations_list" actually has the PoP IDs.
        '''
        traffic_matrix = np.zeros(shape=(len(p_l_list), len(p_l_list)))
        for i in range(len(p_l_list)):
            for j in range(len(p_l_list)):
                if i != j:
                    traffic_amount = List_Of_POP_Locations[p_l_list[j]].population / (get_distance_between_two_pop_location(List_Of_POP_Locations[p_l_list[i]], List_Of_POP_Locations[p_l_list[j]]) ** 2)
                    if traffic_amount == float('Inf'):
                        traffic_matrix[i][j] = 0.0
                    else:
                        traffic_matrix[i][j] = traffic_amount
                        
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
        
    def get_all_possible_pop_locations(self):
        '''
        @note: This just returns the common PoPs for both ISPs, without considering anything.
        
        '''
        return self.common_pop_locations
    
def compute_all_acceptable_peering_contracts(isp_a_sort_strategy, isp_a_pop_locations_list, isp_a_traffic_matrix, isp_b_sort_strategy, isp_b_pop_locations_list, isp_b_traffic_matrix, common_pop_locations):
    '''
    @var my_inter_city_traffic: keeps a list of sum of traffic from all cities to any specific city for my pop location.
    @note: numpy.sum takes axis parameter to define the row or column wise sum. 
    We need (for all i) -> j wise traffic. So, we take column (axis = 0) sum of the traffic_matrix.
    @note: keep only the rows who has ratio 25% < Ratio < 400%
    Meaning, 1:4 traffic ratio or 4:1 traffic ratio is acceptable.
    @return: returns the row count as well. (all Acceptable Peering Contracts Count) 
    '''
    isp_a_inter_city_traffic_list = np.sum(isp_a_traffic_matrix, axis=0)
    isp_b_inter_city_traffic_list = np.sum(isp_b_traffic_matrix, axis=0)        
    
    traffic_relation_between_isp_at_common_pop_dict = {}
    for common_pop_id in common_pop_locations:
        common_pop_id_index_in_isp_a_pop_locations_list = isp_a_pop_locations_list.index(common_pop_id)   
        common_pop_id_index_in_isp_b_pop_locations_list = isp_b_pop_locations_list.index(common_pop_id)
        
        isp_a_traffic = isp_a_inter_city_traffic_list[common_pop_id_index_in_isp_a_pop_locations_list]
        isp_b_traffic = isp_b_inter_city_traffic_list[common_pop_id_index_in_isp_b_pop_locations_list]
        
        traffic_relation_between_isp_at_pop = {'isp_a_traffic': isp_a_traffic, 'isp_b_traffic': isp_b_traffic} 
        
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
            if isp_b_traffic_sum != 0:
                traffic_ratio = float("{0:.2f}".format(isp_a_traffic_sum / isp_b_traffic_sum * 100))
                if 25 <= traffic_ratio and traffic_ratio <= 400: 
                    data_row = [possible_location_combinations, isp_a_traffic_sum, isp_b_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_a_traffic_sum - isp_b_traffic_sum, traffic_ratio]
                    data_isp_a.append(data_row)
            if isp_a_traffic_sum != 0:
                traffic_ratio = float("{0:.2f}".format(isp_b_traffic_sum / isp_a_traffic_sum * 100))
                if 25 <= traffic_ratio and traffic_ratio <= 400: 
                    data_row = [possible_location_combinations, isp_b_traffic_sum, isp_a_traffic_sum, isp_a_traffic_sum + isp_b_traffic_sum, isp_b_traffic_sum - isp_a_traffic_sum, traffic_ratio]
                    data_isp_b.append(data_row)
                    
    if len(data_isp_a) > 0 and len(data_isp_b) > 0:
        df = pd.DataFrame(data_isp_a)
        df.transpose()
        df.insert(0, "", df.index)

        df.columns = ['PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Tatal Traffic', 'Traffic Difference', 'Traffic Ratio']

        if isp_a_sort_strategy == SORT_STRATEGY_DIFF:
            df = df.sort_values(by=df.columns[5], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_OWN:
            df = df.sort_values(by=df.columns[2], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_RATIO:
            df = df.sort_values(by=df.columns[6], ascending=False)

        df2 = pd.DataFrame(data_isp_b)
        df2.transpose()
        df2.insert(0, "", df2.index)

        df2.columns = ['PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Tatal Traffic', 'Traffic Difference', 'Traffic Ratio']

        if isp_a_sort_strategy == SORT_STRATEGY_DIFF:
            df2 = df2.sort_values(by=df2.columns[5], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_OWN:
            df2 = df2.sort_values(by=df2.columns[2], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_RATIO:
            df2 = df2.sort_values(by=df2.columns[6], ascending=False)

        return df, df.shape[0], df2, df2.shape[0]
    elif len(data_isp_a) > 0:
        df = pd.DataFrame(data_isp_a)
        df.transpose()
        df.insert(0, "", df.index)

        df.columns = ['PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Tatal Traffic', 'Traffic Difference', 'Traffic Ratio']

        if isp_a_sort_strategy == SORT_STRATEGY_DIFF:
            df = df.sort_values(by=df.columns[5], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_OWN:
            df = df.sort_values(by=df.columns[2], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_RATIO:
            df = df.sort_values(by=df.columns[6], ascending=False)        

        return df, df.shape[0], None, 0
    elif len(data_isp_b) > 0:
        df2 = pd.DataFrame(data_isp_b)
        df2.transpose()
        df2.insert(0, "", df2.index)

        df2.columns = ['PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Tatal Traffic', 'Traffic Difference', 'Traffic Ratio']

        if isp_a_sort_strategy == SORT_STRATEGY_DIFF:
            df2 = df2.sort_values(by=df2.columns[5], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_OWN:
            df2 = df2.sort_values(by=df2.columns[2], ascending=False)
        elif isp_a_sort_strategy == SORT_STRATEGY_RATIO:
            df2 = df2.sort_values(by=df2.columns[6], ascending=False)
        
        return None, 0, df2, df2.shape[0]
    else:
        return None, 0, None, 0
        
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
        self.latitude = latitude
        self.longitude = longitude
        self.list_of_asn_who_has_their_pop_here = [] 
        
    def __str__(self):
        return "PoPLocation ID: {}, (PeeringDB) ISP Type: {}, (PeeringDB) ISP ID: {}, City: {}, State: {}, Population: {}".format(self.ID, self.isp_type_in_peering_db, self.isp_id_in_peering_db, self.city, self.state, self.population)


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
    @note: Takes 2 ISP AS Numbers and connect to PeeringDB to get the common IX/ Facility id's. 
    We're not directly taking the common locations at first. This is because, ISPs may have their
    PoPs in same city, but interacting in different IXP or Private facility.
    '''
 
    populationInfo = PopulationInfo()
    isp_pop_location_id_list = []
 
    temp_pop_location_key_dict = {str(p.isp_type_in_peering_db + "_" + str(p.isp_id_in_peering_db)):p.ID for p in List_Of_POP_Locations}

    for c_s_temp in city_state_list: 
        if str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db'])) not in temp_pop_location_key_dict.keys():
            # Check here. We've updated the code to use 'location' tuple instead of separate lat and long.
            pop = PoPLocation(c_s_temp['isp_type_in_peering_db'], c_s_temp['isp_id_in_peering_db'], c_s_temp['city'], c_s_temp['state'], c_s_temp['location'][0], c_s_temp['location'][1])
            pop.population = populationInfo.get_city_population(pop.city, pop.state)
            List_Of_POP_Locations.append(pop)
            isp_pop_location_id_list.append(pop.ID)
            temp_pop_location_key_dict.update({str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db'])):pop.ID})
        else:
            isp_pop_location_id_list.append(temp_pop_location_key_dict[str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db']))])
                    
    return list(set(isp_pop_location_id_list))
            
def peering_algorithm_implementation(isp_a, isp_b):
    '''
    Creates the algorithm_report file in CVS format.
    The columns are:
    'Index in PPC list': This are the Possible Peering Contracts. However, note that, not all the PPC will be included here.
    Check the get_all_acceptable_peering_contracts(). This has the conditions, based on which Acceptable Peering Contracts are selected.
    'Rank of PPC for ISP A': The most preferable PPC will be listed on top. So, it's position in list will 0 > 10 > 83 > ..
    Same goes for B.
    Preference A (Max A - A): This is for calculation. So, we first identify the least preferred PPC has and then subtract every PPC index from that value.
    This gives the most preferred PPC index highest value, which we use for calculating "Willingness to Peer"
    Willingness A: This is basically normalized value [0..1] of Preference. We make sure we have the max willingness to 1 for 2 ISP combined.
    So, we consider Preference A, Preference B and Preference (A+B). Otherwise, it's possible that (A+B) has higher value that A and B individually. 
    @var isp_a_apc_list_index: takes the values of "PPC INDEX" (column 0). Remember, this is actually the exact copy of the Index, but we don't save the index, 
    instead we created a new column to save the index values. 
    '''
    
    output_directory_for_isp = os.path.abspath(Output_Directory + "/" + str(isp_a.as_number) + "_" + str(isp_b.as_number))
    
    for sorting_strategy in [SORT_STRATEGY_DIFF, SORT_STRATEGY_OWN, SORT_STRATEGY_RATIO]: 
        isp_a.sorting_strategy = isp_b.sorting_strategy = sorting_strategy       
        if isp_a.all_acceptable_peering_contracts_count > 0 and isp_b.all_acceptable_peering_contracts_count > 0:        
            write_acceptable_peering_contracts_to_file(isp_a.as_number, isp_a.sorting_strategy, isp_a.all_acceptable_peering_contracts, output_directory_for_isp)
            write_acceptable_peering_contracts_to_file(isp_b.as_number, isp_b.sorting_strategy, isp_b.all_acceptable_peering_contracts, output_directory_for_isp)
        
            isp_a_apc_list_index = list(isp_a.all_acceptable_peering_contracts.iloc[:, 0])
            isp_b_apc_list_index = list(isp_b.all_acceptable_peering_contracts.iloc[:, 0])
        
            '''
            @note: 
            PPC index, Rank of PPC for ISP A,  B, (A + B): column 0, 1, 2, 3
            '''
            
            # This is for isp_a. We need to create another for isp_b as well. Check ISP ASN 3549 and 6939
            apc_rank_list = [[v, i, isp_b_apc_list_index.index(v), (i + isp_b_apc_list_index.index(v))] for i, v in enumerate(isp_a_apc_list_index) if v in isp_b_apc_list_index]
            apc_rank_list.sort(key=lambda x:x[3])
                
            if len(apc_rank_list) != 0:
                
                np_data = np.zeros((len(apc_rank_list), 10))
                smallarr = np_data[:, :4]
                smallarr[...] = np.array(apc_rank_list)
                
                '''
                @note: 
                Preference of ISP A, B, (A+B): column 4, 5, 6
                '''
                max_1 = np.max(np_data[:, 1])
                max_2 = np.max(np_data[:, 2])
                np_data[:, 4] = np.array(max_1) - np_data[:, 1]
                np_data[:, 5] = np.array(max_2) - np_data[:, 2]
                np_data[:, 6] = np_data[:, 4] + np_data[:, 5]
        
                '''
                @note: 
                Willingness of ISP A, B, (A+B): column 7, 8, 9
                '''                
                np_data[:, 7:10] = np_data[:, 4:7]
                willingnessarr = np_data[:, 7:10] 
                
                col_min = min(willingnessarr.min(axis=0))
                min_max_diff = max(willingnessarr.max(axis=0)) - col_min
                min_max_diff = min_max_diff if min_max_diff != 0 else col_min
                    
                willingnessarr[...] = (willingnessarr - col_min) / min_max_diff
                df = pd.DataFrame(np_data)
        
                df = df.round(4)
                df.columns = ['Index in PPC list', 'Rank of PPC for ISP A', 'ISP B', 'Rank (A + B)', 'Preference A (Max (Rank A) - Rank A)',
                              'Preference B (Max (Rank B) - Rank B)', 'Preference (A + B)', 'Willingness A', 'Willingness B', 'Willingness (A + B)']
        
                write_acceptable_peering_contracts_to_file(isp_a.as_number, sorting_strategy, df, output_directory_for_isp, peering_algorithm_implementation.__name__)
                draw_graph(isp_a.as_number, isp_b.as_number, df, sorting_strategy, output_directory_for_isp)
        else:
            print("0 APC for {} and {}. No APC folder created!".format(isp_a.as_number, isp_b.as_number))
                
    return
            
def draw_graph(isp_a_asn, isp_b_asn, apc_data, sort_strategy, output_directory_for_isp):
    output_graph_ppc_id_sorted_filepath = os.path.abspath(output_directory_for_isp + "/" + "graph" + "/" + "ppc_id_sorted") 
    output_graph_willingness_sorted_filepath = os.path.abspath(output_directory_for_isp + "/" + "graph" + "/" + "willingness_sorted") 

    if not os.path.exists(output_graph_ppc_id_sorted_filepath):
        os.makedirs(output_graph_ppc_id_sorted_filepath)
    if not os.path.exists(output_graph_willingness_sorted_filepath):
        os.makedirs(output_graph_willingness_sorted_filepath)
    
    sort_by_ppc_id = False
    color = ['red', 'blue', 'green']
    
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig, ax = plt.subplots()
                 
    if sort_by_ppc_id:
        # "order" is required. This will preserve the order for Y-axis as well.
        order = np.argsort(apc_data[apc_data.columns[0]])
        xs = np.array(apc_data[apc_data.columns[0]], int)[order]
    else:
        xs = np.array(apc_data[apc_data.columns[0]], int)
        xs_tick_interval = int(math.ceil(float(len(xs)) / 12))  # This makes sure we have exactly 12 ticks.
    for i, j in zip(range(3), apc_data.columns.tolist()[-3:]):
        if sort_by_ppc_id:
            ax.plot(xs, np.array(apc_data[j])[order], '-', color=color[i], label=j)
            graph_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + ".pdf")
        else:
            ax.plot(apc_data[j], '-', color=color[i], label=j)
            graph_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + ".pdf")
        if i == 0:
            if sort_by_ppc_id:               
                ax1.plot(xs, np.array(apc_data[j])[order], '-', color=color[i], label=j)
                graph_individual_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + ".pdf")
            else:
                ax1.plot(np.array(apc_data[j]), '-', color=color[i], label=j)
                ax1.set_xticks(range(len(xs))[::xs_tick_interval])
                ax1.set_xticklabels(xs[::xs_tick_interval])
                graph_individual_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + ".pdf")
            ax1.legend()
            fig1.savefig(graph_individual_filename)
        if i == 1:
            if sort_by_ppc_id:
                ax2.plot(xs, np.array(apc_data[j])[order], '-', color=color[i], label=j)
                graph_individual_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_b_asn) + ".pdf")
            else:
                ax2.plot(np.array(apc_data[j]), '-', color=color[i], label=j)
                ax2.set_xticks(range(len(xs))[::xs_tick_interval])
                ax2.set_xticklabels(xs[::xs_tick_interval])
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
    
def do_work(isp_pair):
    isp_a_name, isp_a_asn = isp_pair[0]
    isp_b_name, isp_b_asn = isp_pair[1]
    
    output_directory_for_isp = os.path.abspath(Output_Directory + "/" + str(isp_a_asn) + "_" + str(isp_b_asn))
    if not os.path.exists(output_directory_for_isp):
        os.mkdir(output_directory_for_isp)
    
    temp_a_city_state_list, temp_b_city_state_list = [], []
     
    # Look for cached file.
    isp_a_json_file_name = os.path.abspath(os.path.dirname(__file__) + "/data" + "/" + str(isp_a_asn) + "_peering_db_data_file.json")
    isp_b_json_file_name = os.path.abspath(os.path.dirname(__file__) + "/data" + "/" + str(isp_b_asn) + "_peering_db_data_file.json")
    if os.path.exists(isp_a_json_file_name) and os.path.exists(isp_b_json_file_name):
        fin = open(isp_a_json_file_name)
        temp_a_city_state_list = json.load(fin)['data']
        fin.close()
        fin = open(isp_b_json_file_name)
        temp_b_city_state_list = json.load(fin)['data']
        fin.close()       
    else:
        print("Input file missing for either {} or {}".format(isp_a_name, isp_b_name))
        return
               
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
    
    # ToDo: We'll do a pagerank here to identify my preferred PoPs sorted.
    # Based on PoP port capacity, higher the capacity, more preferred it is. Higher population as well.    
    
    if len(common_pop_location_id_list) > max_common_pop_count:
        common_pop_location_id_list = common_pop_location_id_list[:max_common_pop_count]
    
    isp_a = ISP(isp_a_asn, isp_a_name, isp_a_pop_location_id_list, isp_b_pop_location_id_list, common_pop_location_id_list, isp_a_port_capacity_at_common_pop_dict)
    isp_b = ISP(isp_b_asn, isp_b_name, isp_b_pop_location_id_list, isp_a_pop_location_id_list, common_pop_location_id_list, isp_b_port_capacity_at_common_pop_dict)
    
    print("ISP {:<12} has {:>3} PoP location, ISP {:<12} has {:>3} PoP location, Common location count: {:<3}".format(isp_a.name, len(isp_a.my_pop_locations_list), isp_b.name, len(isp_b.my_pop_locations_list), len(isp_a.common_pop_locations))) 
                 
    isp_a.all_acceptable_peering_contracts, isp_a.all_acceptable_peering_contracts_count, isp_b.all_acceptable_peering_contracts, isp_b.all_acceptable_peering_contracts_count = compute_all_acceptable_peering_contracts(isp_a.sorting_strategy, isp_a.my_pop_locations_list, isp_a.my_traffic_matrix, isp_b.sorting_strategy, isp_b.my_pop_locations_list, isp_b.my_traffic_matrix, common_pop_location_id_list)
                 
    peering_algorithm_implementation(isp_a, isp_b)
    print("APC Count: {}, PPC Count: {}, APC/PPC Ratio: {:.2f}".format(isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count, float(isp_a.all_acceptable_peering_contracts_count) / isp_a.all_possible_peering_contracts_count))
    fout_for_apc_count = open(os.path.abspath(Output_Directory + "/" + "apc_count_" + str(max_common_pop_count) + ".txt"), "a+")            
    fout_for_apc_count.write("ISP {:<12} has {:>3} PoP location, ISP {:<12} has {:>3} PoP location, Common location count: {:<3}\n".format(isp_a.name, len(isp_a.my_pop_locations_list), isp_b.name, len(isp_b.my_pop_locations_list), len(isp_a.common_pop_locations))) 
    if isp_a.all_possible_peering_contracts_count > 0:
        fout_for_apc_count.write("APC Count: {}, PPC Count: {}, APC/PPC Ratio: {:.2f}\n".format(isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count, float(isp_a.all_acceptable_peering_contracts_count) / isp_a.all_possible_peering_contracts_count))
    else:
        fout_for_apc_count.write("APC Count: {}, PPC Count: {}, APC/PPC Ratio: {:.2f}\n".format(isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count, 0))
    fout_for_apc_count.close()     
    
    return (isp_a.all_acceptable_peering_contracts_count, isp_a.all_possible_peering_contracts_count)
    
# Running code from Eclipse and Terminal:
# https://stackoverflow.com/questions/11536764/how-to-fix-attempted-relative-import-in-non-package-even-with-init-py
# To run from Terminal, nevigate to "src/com/nwsl/python" then "python automatedpeering/PeeringAlgorithm.py"
if __name__ == '__main__':  
    
    isp_dict = {'access': {'centurylink': 209, 'comcast':7922, 'charter':7843, 'windstream':7029, 'cox':22773, 'tds':4181},
                'content': {'google': 15169, 'microsoft': 8075, 'amazon': 16509, 'akamai':20940, 'facebook': 32934, 'ebay':62955, 'netflix': 2906,},
                'transit': {'cogent': 174, 'ntt': 2914, 'he':6939, 'pccw':7961, 'zayo':6461, 'sprint': 1239}}  
    
    fig, ax = plt.subplots()
    colors = {'access':'red', 'content':'green', 'transit':'blue', 'access-content':'pink', 'access-transit':'black', 'transit-content':'orange'}
    marker = {'access-content':'x', 'access-transit':'1', 'transit-content':'_'}
    
    max_common_pop_count = 20
    already_calculated_isp_combination = []
    
    start_time = time.time()
    for k, v in isp_dict.iteritems():
        isp_pair_ppc_count_list = []
        isp_pair_apc_count_list = []
          
        apc_count_list = []
        ppc_count_list = []
    
        isp_pair_list = list(itertools.combinations(v.items(), 2))
        isp_pair_list = [i for i in isp_pair_list if i not in already_calculated_isp_combination]
            
        # Use of multi-processing.
        pool = Pool(processes=Max_Process_To_Be_Used) 
        result = pool.map(do_work, isp_pair_list)
            
        ax.scatter([item[1] for item in result], [item[0] for item in result], facecolors='none', edgecolors=colors[k], label=k)     
        
    # This are combined list. We may need to check the content-access, content-transit, transit-access (opposite combination) as well.
    isp_pair_combined_list = {}
    isp_pair_combined_list['access-content'] = [((name_a, asn_a), (name_c, asn_c)) for name_a, asn_a in isp_dict['access'].items() for name_c, asn_c in isp_dict['content'].items()] 
    isp_pair_combined_list['access-transit'] = [((name_a, asn_a), (name_t, asn_t)) for name_a, asn_a in isp_dict['access'].items() for name_t, asn_t in isp_dict['transit'].items()]
    isp_pair_combined_list['transit-content'] = [((name_t, asn_t), (name_c, asn_c)) for name_t, asn_t in isp_dict['transit'].items() for name_c, asn_c in isp_dict['content'].items()]
   
    for k,v in isp_pair_combined_list.items():
        pool = Pool(processes=Max_Process_To_Be_Used)
        result = pool.map(do_work, v)
          
        ax.scatter([item[1] for item in result], [item[0] for item in result], c=colors[k], marker=marker[k], label=k)      
   
    ax.legend()
    ax.set_xlabel("Possible Peering Contracts Count")
    ax.set_ylabel("Acceptable Peering Contracts Count")
    fig.savefig(os.path.abspath(Output_Directory + "/" + "isp_pair_apc_" + str(max_common_pop_count) + ".pdf"))
    end_time = time.time()
      
    print("time elapsed: {} minutes".format((end_time-start_time)/60))
