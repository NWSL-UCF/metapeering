import os, json
from .gVars import Data_Directory
from .get_total_prefixes_addresses_count_from_caida import get_total_prefixes_addresses_count_from_caida
from .PopulationFromCensusGov import PopulationInfo
from .get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida import get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida
from .PeeringInfo import PeeringInfo

info_types = {
  "NSP": "transit",
  "Content": "content",
  "Non-Profit": "non_profit",
  "Cable/DSL/ISP": "access",
  "": "unknown",
  "Enterprise": "enterprise",
  "Educational/Research": "education",
  "Route Server": "route_server",
  "Not Disclosed": "unknown"
}

us_state_abbrev = {
    'alabama': 'AL',
    'alaska': 'exclude', #
    'american samoa': 'exclude', #
    'arizona': 'AZ',
    'arkansas': 'AR',
    'california': 'CA',
    'colorado': 'CO',
    'connecticut': 'CT',
    'delaware': 'DE',
    'district of columbia': 'DC',
    'florida': 'FL',
    'georgia': 'GA',
    'guam': 'exclude', #
    'hawaii': 'exclude', #
    'idaho': 'ID',
    'illinois': 'IL',
    'indiana': 'IN',
    'iowa': 'IA',
    'kansas': 'KS',
    'kentucky': 'KY',
    'louisiana': 'LA',
    'maine': 'ME',
    'maryland': 'MD',
    'massachusetts': 'MA',
    'michigan': 'MI',
    'minnesota': 'MN',
    'mississippi': 'MS',
    'missouri': 'MO',
    'montana': 'MT',
    'nebraska': 'NE',
    'nevada': 'NV',
    'new hampshire': 'NH',
    'new jersey': 'NJ',
    'new mexico': 'NM',
    'new york': 'NY',
    'north carolina': 'NC',
    'north dakota': 'ND',
    'northern mariana islands':'exclude', #
    'ohio': 'OH',
    'oklahoma': 'OK',
    'oregon': 'OR',
    'pennsylvania': 'PA',
    'puerto rico': 'exclude', #
    'rhode island': 'exclude', #
    'south carolina': 'SC',
    'south dakota': 'SD',
    'tennessee': 'TN',
    'texas': 'TX',
    'utah': 'UT',
    'vermont': 'VT',
    'virgin islands': 'exclude', #
    'virginia': 'VA',
    'washington': 'WA',
    'west virginia': 'WV',
    'wisconsin': 'WI',
    'wyoming': 'WY'
}

excludedStates = {
    "HI":"exclude",
    "AK":"exclude",
    "PR":"exclude",
    "MP":"exclude",
    "RI":"exclude",
    "VI":"exclude",
    "GU":"exclude",
    "AS":"exclude"
}

def clean(state):
    state = state.strip("B").strip("'")
    if(len(state) > 2):
        state = us_state_abbrev[state.lower()]
    return excludedStates.get(state,state)


# commented out because with the file upload, we are only considering isp_b as a possibility of missing data.
def ensure_isp_json_files(isp_a, isp_b, force=False):
    # print("Entering ensure_isp_json_files")
    '''
    @param isp_pair_list: Takes isp_pair list \n
    @note: checks if json file for each ISP exists. If not, calls PeeringInfo to access PeeringDB,
    and generate the json file before those are used in do_work().
    '''

    '''
    isp_a_asn = isp_a[1]
    isp_b_asn = isp_b[1]

    isp_a_json_file_name = Data_Directory + "/cache/" + str(isp_a_asn) + "_peering_db_data_file.json"
    isp_b_json_file_name = Data_Directory + "/cache/" + str(isp_b_asn) + "_peering_db_data_file.json"

    # With file upload, remove the need to verify isp_a_json_file_name
    if (not os.path.exists(isp_a_json_file_name)) or (not os.path.exists(isp_b_json_file_name)) or force:
        peeringInfo = PeeringInfo()

        total_prefixes_in_globe, total_addresses_in_globe = get_total_prefixes_addresses_count_from_caida()

        isp_a_pdb_net_id, info_type_a = peeringInfo.get_net_id_from_asn(isp_a_asn, get='info_type')
        isp_b_pdb_net_id, info_type_b = peeringInfo.get_net_id_from_asn(isp_b_asn, get='info_type')

        info_type_a = info_types[info_type_a]
        info_type_b = info_types[info_type_b]

        if (not os.path.exists(isp_a_json_file_name)) or force:
            remPop = []
            temp_a_city_state_list = peeringInfo.get_all_possible_peering_city(isp_a_pdb_net_id)
            # print('temp_a_city_state_list: ',temp_a_city_state_list)
            for i, p in enumerate(temp_a_city_state_list):
                p["state"] = clean(p["state"])
                if (p['state'] == 'exclude'):
                    remPop.append(i)
                else:
                    p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})
            temp_a_city_state_list = [i for j, i in enumerate(temp_a_city_state_list) if j not in remPop]

            with open(isp_a_json_file_name, "w") as fout:
                name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_a_asn)
                traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_a_pdb_net_id)
                data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_a_city_state_list,
                                    "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                    "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                    "neighbor": neighbor, "info_type":info_type_a}}
                # print('Data to be written in file: ',data)
                json.dump(data, fout)

        if (not os.path.exists(isp_b_json_file_name)) or force:
            remPop = []
            temp_b_city_state_list = peeringInfo.get_all_possible_peering_city(isp_b_pdb_net_id)
            # print('temp_b_city_state_list: ',temp_b_city_state_list)
            # print("HERE 2: -----> temp_b_city_state_list: ",temp_b_city_state_list)
            for i, p in enumerate(temp_b_city_state_list):
                p["state"] = clean(p["state"])
                if (p['state'] == 'exclude'):
                    remPop.append(i)
                else:
                    p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})

            temp_b_city_state_list = [i for j, i in enumerate(temp_b_city_state_list) if j not in remPop]

            with open(isp_b_json_file_name, "w") as fout:
                name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_b_asn)
                traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_b_pdb_net_id)
                data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_b_city_state_list,
                                    "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                    "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                    "neighbor": neighbor,"info_type":info_type_b}}
                # print('Data to be written in file (2): ',data)
                json.dump(data, fout)
    # print("Leaving ensure_isp_json_files")
    '''
    return

# Alternative function from above where we consider missining isp_b information onlyself.
# iisp_a should have the required information in the file upload by the user.
def ensure_isp_json_files_custom(isp_b, force=False):

    isp_b_asn = isp_b[1]
    isp_b_json_file_name = Data_Directory + "/cache/" + str(isp_b_asn) + "_peering_db_data_file.json"

    if (not os.path.exists(isp_b_json_file_name)) or force:
            peeringInfo = PeeringInfo()

            total_prefixes_in_globe, total_addresses_in_globe = get_total_prefixes_addresses_count_from_caida()

            isp_b_pdb_net_id, info_type_b = peeringInfo.get_net_id_from_asn(isp_b_asn, get='info_type')

            info_type_b = info_types[info_type_b]

            if (not os.path.exists(isp_b_json_file_name)) or force:
                remPop = []
                temp_b_city_state_list = peeringInfo.get_all_possible_peering_city(isp_b_pdb_net_id)

                for i, p in enumerate(temp_b_city_state_list):
                    p["state"] = clean(p["state"])
                    if (p['state'] == 'exclude'):
                        remPop.append(i)
                    else:
                        p.update({'internet_penetration_percentage': (PopulationInfo.internet_users_percentage[p['state']] / 100.0)})

                temp_b_city_state_list = [i for j, i in enumerate(temp_b_city_state_list) if j not in remPop]

                with open(isp_b_json_file_name, "w") as fout:
                    name, prefixes, address_space, neighbor = get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(isp_b_asn)
                    traffic_ratio = peeringInfo.get_isp_traffic_ratio(isp_b_pdb_net_id)
                    data = {"data": {"name":name, "traffic_ratio": traffic_ratio, "pop_list": temp_b_city_state_list,
                                        "prefixes": prefixes, "total_prefixes_in_globe": total_prefixes_in_globe,
                                        "address_space": address_space, "total_addresses_in_globe": total_addresses_in_globe,
                                        "neighbor": neighbor,"info_type":info_type_b}}
                    
                    json.dump(data, fout)
