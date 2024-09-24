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

def ensure_isp_json_files(isp_a, isp_b, force=False):
    '''
    @param isp_pair_list: Takes isp_pair list \n
    @note: checks if json file for each ISP exists. If not, calls PeeringInfo to access PeeringDB,
    and generate the json file before those are used in do_work().
    '''

    isp_a_asn = isp_a[1]
    isp_b_asn = isp_b[1]

    isp_a_json_file_name = Data_Directory + "/2021/isps/" + str(isp_a_asn) + "_peering_db_data_file.json"
    isp_b_json_file_name = Data_Directory + "/2021/isps/" + str(isp_b_asn) + "_peering_db_data_file.json"

    if (os.path.exists(isp_a_json_file_name)):
        print("The filepath exists for: " + isp_a_json_file_name)
    else:
        return False

    if (os.path.exists(isp_b_json_file_name)):
        print("The filepath exists for: " + isp_b_json_file_name)
    else:
        return False
    
    return True
