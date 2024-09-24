import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})
from .gVars import SORT_STRATEGY_OWN, traffic_ratio_dict, List_Of_POP_Locations, internet_usage_per_person
from .get_distance_between_two_pop_location import get_distance_between_two_pop_location

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
        self.isp_traffic_ratio_type = list(traffic_ratio_dict.keys())[list(traffic_ratio_dict.values()).index(isp_traffic_ratio_type)] 
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
        return "ASN: {}, Name: {}, My_PoPs_Id: {}, Opp_PoPs_Id: {}".format(self.as_number, self.name, self.my_pop_locations_list, self.opponent_pop_locations_list)
    
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
                    # try:
                    traffic_amount = 0.0
                    if List_Of_POP_Locations[oppo_p_l_list[j]].population is not None:
                        traffic_amount = List_Of_POP_Locations[oppo_p_l_list[j]].population / (get_distance_between_two_pop_location(List_Of_POP_Locations[my_p_l_list[i]], List_Of_POP_Locations[oppo_p_l_list[j]]) ** 2)
                        traffic_amount *= List_Of_POP_Locations[oppo_p_l_list[j]].internet_penetration_percentage / List_Of_POP_Locations[my_p_l_list[i]].internet_penetration_percentage * internet_usage_per_person
                    # except Exception as e:
                        # print(e)
                        # print(traffic_amount, List_Of_POP_Locations[my_p_l_list[i]].__dict__, List_Of_POP_Locations[oppo_p_l_list[j]].__dict__)
                    if traffic_amount == float('Inf'):
                        traffic_matrix[i][j] = 0.0
                    else:
                        traffic_matrix[i][j] = traffic_amount
                else:
                    # We just split the population.
                    if List_Of_POP_Locations[my_p_l_list[i]].population is not None:
                        traffic_matrix[i][j] = List_Of_POP_Locations[my_p_l_list[i]].population / 2
                    else:
                        traffic_matrix[i][j] =0.0
        
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
        for i, my_pop_id in enumerate(self.my_pop_locations_list):
            for j, common_pop_id in enumerate(self.common_pop_locations):
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
        print("\n -------------- get_offloaded_traffic_matrix --------------\n")
        print(float(self.port_capacity_at_common_pop_dict[i]) / np.sum(list(self.port_capacity_at_common_pop_dict.values())) for i in self.common_pop_locations)
        pop_capacity_ratio = [float(self.port_capacity_at_common_pop_dict[i]) / np.sum(list(self.port_capacity_at_common_pop_dict.values())) for i in self.common_pop_locations]
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
