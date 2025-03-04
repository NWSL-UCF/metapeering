from .gVars import List_Of_POP_Locations
from .PopulationFromCensusGov import PopulationInfo
from .PoPLocation import PoPLocation

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
            pop = PoPLocation(c_s_temp['isp_type_in_peering_db'], c_s_temp['isp_id_in_peering_db'], c_s_temp['city'], c_s_temp['state'], c_s_temp['location'][0], c_s_temp['location'][1], c_s_temp['org_name'], c_s_temp['name'])
            pop.population = populationInfo.get_city_population(pop.city, pop.state)
            pop.internet_penetration_percentage = c_s_temp['internet_penetration_percentage']
            List_Of_POP_Locations.append(pop)
            isp_pop_location_id_list.append(pop.ID)
            temp_pop_location_key_dict.update({str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db'])):pop.ID})
        else:
            isp_pop_location_id_list.append(temp_pop_location_key_dict[str(c_s_temp['isp_type_in_peering_db'] + "_" + str(c_s_temp['isp_id_in_peering_db']))])
                   
    return list(set(isp_pop_location_id_list))
