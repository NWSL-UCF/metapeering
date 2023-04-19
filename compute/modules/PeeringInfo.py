'''
Created on Jul 2, 2018

@author: prasun
'''

import peeringdb, urllib.request, requests, json, math, numpy, warnings, itertools, os
from .ASNNotFoundError import ASNNotFoundError
from peeringdb import resource
from peeringdb.client import Client
from bs4 import BeautifulSoup
import os.path as path
from .PopulationFromCensusGov import PopulationInfo

warnings.filterwarnings("ignore")

'''
Conditions for JSON file update or figure plotting type!
@var is_update_data_files_required: Updates data files. Based on these files, final figures will be generated. JSON files will be stored in "/data" folder.
@var plot_all_peering_locations_required: Plots all Access, Content, Transit ISPs PoPs and their centroids.
If FALSE, it plots only the centroids of each type, If TRUE, plots the PoPs according to the frequency.
Requires "is_peering_location_frequency_required" to be TRUE.
@var is_peering_location_frequency_required: Represents the frequency of PoPs. Use this with "plot_all_peering_locations_required".
Higher the PoP frequency, bigger the MARKER on that location.
This is also used to decide whether or not to use "stringify_keys()" method.
@var is_microsoft_transit: Adds Microsoft either in transit ISP list or in Content ISP list.
@var is_state_name_required: Is required to get the name of the State and the PoPs count in that state. We no longer use it now.
@var is_public_private_classification_required: We never use it to plot. We use it to get the information about the PoP locations. Always FALSE.
@var small_access_isps: We mark small Access ISPs in US map separately.
@var annotation_needed_isps: These ISPs names appear on combined ISP centroid US map

@note: Set "is_peering_location_frequency_required" TRUE to access the files! Otherwise, the filename will not be same and can't access the source JSON files.
@note: Mark for Future Removal: We used these temporarily and will be removed later on. is_microsoft_transit, is_state_name_required, is_public_private_classification_required

'''

for_icc = True

is_update_data_files_required = False
plot_all_peering_locations_required = False
is_peering_location_frequency_required = False

is_microsoft_transit = False

is_state_name_required = False
is_public_private_classification_required = False


my_path = path.abspath(path.join(__file__, '..'))
data_file_path = my_path + "/data/"

peering_points_population = {}

isp_types = ['access', 'content', 'transit']

# These are the primary ASN for each ISP.
isp_dict = {'content':{'amazon':[16509], 'facebook':[32934], 'google':[15169, 36040], 'ibm':[36351], 'netflix':[2906], 'spotify':[8403],
                       'verizon':[15133], 'yahoo':[10310], 'yelp':[33445],
                       },
            'transit':{'att':[2688], 'cogent':[174], 'coresite':[2734, 19996], 'frontier':[5650], 'general':[8047], 'gtt':[21570, 4565],
                       'he':[6939], 'iij':[29791], 'level3':[3549], 'ntt':[2914], 'pccw':[3491], 'qwest':[209], 'sprint':[1239],
                       'verizon':[701], 'wow':[16724], 'zayo':[6461],
                       },
            'access':{'att':[15290], 'charter':[7843, 20115], 'centurylink':[209, 22561],
                      'comcast':[7922, 7725, 33657, 33660, 33666, 33651, 33650, 21508, 33490, 7016, 7015, 22909, 13367, 33668, 20214, 22258, 33489, 33662, 33652, 33491, 33667],
                      'cox':[22773], 'google':[16591], 'gtt':[3257, 4589, 8928], 'hotwire':[23089, 31793], 'liberty':[6830], 'mediacom':[30036],
                      'penteledata':[3737], 'sonic':[7065], 'tds': [4181], 'timewarner':[7843], 'wow':[12083],
                       }
            }

if is_microsoft_transit:
    isp_dict['transit'].update({'microsoft':[8075]})
else:
    isp_dict['content'].update({'microsoft':[8075]})

# These are special ISPs.
small_access_isps = ['hotwire', 'google', 'wow', 'sonic', 'penteledata']
# annotation_needed_isps = ['spotify', 'yelp']
annotation_needed_isps = ['yelp']

isp_names = {'amazon':'Amazon', 'att':'AT&T', 'centurylink':'CenturyLink', 'charter':'Charter', 'cogent':'Cogent', 'comcast':'Comcast',
             'coresite':'Coresite', 'cox':'Cox', 'cyrusone':'CyrusOne', 'facebook':'Facebook', 'frontier':'Frontier', 'general':'General',
             'google':'Google', 'google_fiber':'Google Fiber', 'gtt':'GTT', 'he':'Hurricane Electric', 'hotwire':'Hotwire', 'ibm':'IBM',
             'iij':'IIJ', 'level3':'Level3', 'liberty':'Liberty', 'mediacom':'Mediacom', 'microsoft':'Microsoft', 'netflix':'Netflix',
             'ntt':'NTT', 'pccw':'PCCW Global', 'penteledata':'PenTeleData', 'qwest':'Qwest', 'sonic':'Sonic.net', 'spotify':'Spotify',
             'sprint':'Sprint', 'tds':'TDS Telecom', 'timewarner':'Timewarner', 'verizon':'Verizon', 'wow':'WOW', 'yahoo':'Yahoo',
             'yelp':'Yelp!', 'zayo':'Zayo', }

if is_microsoft_transit:
    output_file_path = my_path + "/output_microsoft_as_transit/"
else:
    output_file_path = my_path + "/output/"


'''
@note: plt.figure(A_NEW_NUMBER_HERE) always wants unique figure number, otherwise a new figure replaces a previous one.
plt_figure_number is a global variable. For creating new figure using matplotlib, we shall always pass this variable and
after that, we have to increment the variable by 1 as following:
plt.figure(plt_figure_number)
plt_figure_number += 1
'''
plt_figure_number = 1

class PeeringInfo(object):
    '''
    classdocs
    '''


    def __init__(self):
        # print("Initializing PeeringInfo Object")
        '''
        Constructor
        '''
        self.peeringdb_link = "https://peeringdb.com/"
        self.peeringdb_api = "https://www.peeringdb.com/api/"

        self.API_TYPE_IX = "ix"
        self.API_TYPE_FAC = "fac"
        self.API_TYPE_NET = "net"

        self.only_usa = True

        #self.pdb = peeringdb.PerringDB()
        self.pdb = Client()
        self.unreported_states = 0
        # print("Successfully initialized PeeringInfo Object")

    def get_isp_by_name(self, name=None):
        # print("Entering get_isp_by_name.")
        '''
        Sample example:
        ix = self.pdb.all('ix', name='chix', country='us')[0]
        @note: From https://github.com/grizz/pdb-examples/blob/master/get_peerinfo.py
        '''
        try:
            data = self.pdb.fetch_all(resource.get_resource(self.API_TYPE_IX), 999, name=name, country='us')[0]
        except:
            raise ASNNotFoundError(name, message=str(name)+" is not a valid Autonomous System. It was not found in the Peering Database")


        # print('Got DATA from get_isp_by_name: ', data)
        # print("Leaving get_isp_by_name.")

        return data
        # ix = self.pdb.all(self.API_TYPE_IX, name=name, country='us')[0] #pylint: disable=unexpected-keyword-arg
        # return ix

    def get_isp_by_asn(self, asn):
        # print("Entering get_isp_by_asn.")
        '''
        Sample example:
        ix = self.pdb.all('net', asn=16509)
        @note: From https://github.com/grizz/pdb-examples/blob/master/get_peerinfo.py
        '''
        try:
            data = self.pdb.fetch_all(resource.get_resource(self.API_TYPE_NET), 999, asn=asn)[0]
        except:
            raise ASNNotFoundError(asn, "AS"+str(asn)+" is not a valid ASN. It was not found in the Peering Database")
        # print('Got DATA from get_isp_by_asn: ', data)
        # print("Leaving get_isp_by_asn.")

        return data
            # raise Exception('The provided ASN was not found in the Peering Data Base!')

        # net = self.pdb.all(self.API_TYPE_NET, asn=asn)[0] #pylint: disable=unexpected-keyword-arg
        # return net

    def get_net_id_from_asn(self, asn, get=None):
        # print("asn------>", asn)
        # print("Entering get_net_id_from_asn.")
        '''
        @param asn: AS Number of our interested ISP
        @return: ID in PeeringDB for this specific ASN
        '''
        net = self.get_isp_by_asn(asn)

        # print("Leaving get_net_id_from_asn.")
        # if error:
        #     return None, None
        if get:
            return net['id'], net[get]
        return net['id']



    def json_call_from_peeringdb_api(self, api_type, isp_id):
        # print("Entering json_call_from_peeringdb_api.")
        '''
        @param api_type: Any of the following:
        @param isp_id: ID of which ISP/IX/NET we're interested in.
        ix: for Public Internet Exchange Info,
        fac: for Private Peering Facility,
        net: for ISP Network information.
        @return: entire JSON object obtained from peeringdb api for IX.
        '''
        api_url = self.peeringdb_api + api_type + "/" + str(isp_id)
        r = requests.get(api_url)
        r = r.json()
        # print("Leaving json_call_from_peeringdb_api.")

        if(r.get('data',None)):
            return r
        else:
            raise ASNNotFoundError(isp_id)

    def get_isp_net_set_id(self, isp_id):
        # print("Entering get_isp_net_set_id.")
        '''
        @note: This calls JSON to https://peeringdb.com/api/net/1418
        and gets the list of all the ISP_ID (kind of colleague) from "net_set" in JSON object.
        '''
        data = self.json_call_from_peeringdb_api(self.API_TYPE_NET, isp_id)['data']
        net_set = data[0]['org']['net_set']

        # print("Leaving get_isp_net_set_id.")
        return net_set

    def get_isp_traffic_ratio(self, isp_id):
        # print("Entering get_isp_traffic_ratio")
        '''
        @note: This directly JSON calls the isp from peeringdb and returns the traffic ratio of that.
        @return: BALANCED, MOSTLY INBOUND, NOT DISCLOSED or others..
        '''
        res = requests.get(self.peeringdb_api + self.API_TYPE_NET + "/" + str(isp_id)).json()
        ratio = str(res['data'][0]['info_ratio']).upper()
        if ratio == "":
            ratio = "NOT DISCLOSED"
        # print("Leaving get_isp_traffic_ratio")
        return ratio

    def get_all_pops_net_id_for_single_isp_id(self, isp_id):
        # print("Entering get_all_pops_net_id_for_single_isp_id")
        '''
        @param isp_id: This is the id for "url"
        https:peeringdb.com/net/ISP_ID
        @note: netfac_set or netixlan_set contains list of each facility/ Network IX Lan information details. Not just the id.
        For "netixlan", we have to take ix_id, while for "netfac" we have to take fac_id.
        @return: 2 lists. One for public exchange points (ix_id in netixlan_set) and another for private facility (id in netfac_set)
        @note: Right now, we're interested in US facilities only. We shall not consider other locations.
        But, we don't distinguish that here, delegating that responsibility to get_peering_location_city_state_lat_long()
        @note: For getting IX id, we first find all netixlan and then get the ix_id from each.
        '''

        net_set = self.get_isp_net_set_id(isp_id)
        fac_id_set = list()
        ix_id_set = list()

        for net_id in net_set:
            data = self.json_call_from_peeringdb_api(self.API_TYPE_NET, net_id)['data']
            netfac_set_temp = data[0]['netfac_set']
            netixlan_set_temp = data[0]['netixlan_set']

            for temp in netfac_set_temp:
                fac_id_set.append(temp['fac_id'])
            for temp in netixlan_set_temp:
                ix_id_set.append(temp['ix_id'])

        # print("Leaving get_all_pops_net_id_for_single_isp_id")
        return ix_id_set, fac_id_set

    def get_all_pops_port_capacity_with_net_id_for_single_isp_id(self, isp_id):
        # print("Entering get_all_pops_port_capacity_with_net_id_for_single_isp_id")
        '''
        @note: This is exactly same as get_all_pops_with_net_id_for_single_isp_id().
        Except, this returns the "port_capacity" of public IXPs as well. Private facilities don't have "port_capacity"
        in PeeringDB.
        @param isp_id: This is the id for "url"
        https:peeringdb.com/net/ISP_ID
        @note: netfac_set or netixlan_set contains list of each facility/ Network IX Lan information details. Not just the id.
        For "netixlan", we have to take ix_id, while for "netfac" we have to take fac_id.
        @return: 2 dictionaries. One for public exchange points (ix_id in netixlan_set) and another for private facility (id in netfac_set)
        @note: Right now, we're interested in US facilities only. We shall not consider other locations.
        @note: For getting IX id, we first find all netixlan and then get the ix_id from each.
        @note: We set default "port_capacity" to 1000 (G), see our peering Algo paper.
        '''

        net_set = self.get_isp_net_set_id(isp_id)
        fac_id_port_cap_dict = dict()
        ix_id_port_cap_dict = dict()

        for net_id in net_set:
            data = self.json_call_from_peeringdb_api(self.API_TYPE_NET, net_id)['data']
            netfac_set_temp = data[0]['netfac_set']
            netixlan_set_temp = data[0]['netixlan_set']

            for temp in netfac_set_temp:
                if (isp_id) == 577:
                    print(temp['fac_id'])
                fac_id_port_cap_dict.update({temp['fac_id']:1000})
            for temp in netixlan_set_temp:
                try:
                    ix_id_port_cap_dict.update({temp['ix_id']:(temp['speed'] + ix_id_port_cap_dict[temp['ix_id']])})
                except:
                    ix_id_port_cap_dict.update({temp['ix_id']:temp['speed']})
        # print("Leaving get_all_pops_port_capacity_with_net_id_for_single_isp_id")
        return ix_id_port_cap_dict, fac_id_port_cap_dict

    def get_all_pops_locations_with_population_for_single_isp_id(self, isp_id):
        # print("Entering get_all_pops_locations_with_population_for_single_isp_id")
        '''
        @return a list of pops information as a dictionary with: {"city":"San Fransisco", "state":"CA", "location":(lat, long), "state_population":123456, "pop_freq_in_state":5}.
        '''
        populationInfo = PopulationInfo()

        ix_id_set, fac_id_set = self.get_all_pops_net_id_for_single_isp_id(isp_id)
        pop_city_state_loc_population_frequency_list = []

        for ix, fac in map(None, ix_id_set, fac_id_set):
            if fac != None:
                temp = self.get_peering_location_city_state_lat_long(self.API_TYPE_FAC, fac)
                if temp != None:
                    temp_state = temp['state']
                    state_population = populationInfo.get_state_population(temp_state)
                    temp.update({'state_population':state_population})
                    temp_city = temp['city']
                    city_population = populationInfo.get_city_population(temp_city, temp_state)
                    temp.update({'city_population':city_population})

                    pop_city_state_loc_population_frequency_list.append(temp)

            if ix != None:
                temp = self.get_peering_location_city_state_lat_long(self.API_TYPE_IX, ix)
                if temp != None:
                    temp_state = temp['state']
                    state_population = populationInfo.get_state_population(temp_state)
                    temp.update({'state_population':state_population})
                    temp_city = temp['city']
                    city_population = populationInfo.get_city_population(temp_city, temp_state)
                    temp.update({'city_population':city_population})

                    pop_city_state_loc_population_frequency_list.append(temp)

        state_list = [item['state'] for item in pop_city_state_loc_population_frequency_list]
        state_freq_dict = convert_list_to_frequency_dict(state_list)

        city_list = [item['city'] for item in pop_city_state_loc_population_frequency_list]
        city_freq_dict = convert_list_to_frequency_dict(city_list)

        location_list = [item['location'] for item in pop_city_state_loc_population_frequency_list]
        location_list_freq = convert_list_to_frequency_dict(location_list)

        for item in pop_city_state_loc_population_frequency_list:
            item.update({'pop_freq_in_state':state_freq_dict[item['state']]})
            item.update({'pop_freq_in_city':city_freq_dict[item['city']]})
            item.update({'same_pop_location_freq':location_list_freq[item['location']]})

        # print("Leaving get_all_pops_locations_with_population_for_single_isp_id")

        return [dict(s) for s in set(frozenset(pop_loc.items()) for pop_loc in pop_city_state_loc_population_frequency_list)]

    def get_all_peering_points_for_single_isp_id(self, isp_id):
        # print("Entering get_all_peering_points_for_single_isp_id")
        '''
        @param isp_id: Particular ISP that we're interested in. Finds the peering location in US only.
        @return: 2 lists of Locations (one for public exchanges and the other for private facility).
        @note: peering_location is actually the IX locations.
        '''
        ix_id_list, fac_id_list = self.get_all_pops_net_id_for_single_isp_id(isp_id)

        public_peering_exchange_locations_list = []
        for ix in ix_id_list:
            loc = self.get_peering_location(self.API_TYPE_IX, ix)
            if loc != None:
                public_peering_exchange_locations_list.append(loc)

        private_peering_facility_locations_list = []
        for fac in fac_id_list:
            loc = self.get_peering_location(self.API_TYPE_FAC, fac)
            if loc != None:
                private_peering_facility_locations_list.append(loc)

        # print("Leaving get_all_peering_points_for_single_isp_id")
        return public_peering_exchange_locations_list, private_peering_facility_locations_list


    def get_all_possible_peering_city(self, isp_a_net_id):
        # print("isp_a_net_id------>", isp_a_net_id)
        # print("Entering get_all_possible_peering_city")
        '''
        @note: This is exactly same as get_all_possible_peering_city_state_for_two_isp().
        We need this for one ISP information in PeeringAlgo.py
        @return: city_state list for isp_a.
        '''

        isp_a_ix_id_dict, isp_a_fac_id_dict = self.get_all_pops_port_capacity_with_net_id_for_single_isp_id(isp_a_net_id)
        isp_a_ix_id_list = isp_a_ix_id_dict.keys()
        isp_a_fac_id_list = isp_a_fac_id_dict.keys()
        isp_a_city_state_list = []

        for a_ix, a_fac in itertools.zip_longest(isp_a_ix_id_list, isp_a_fac_id_list):
            if a_ix != None:
                c_s_temp = self.get_peering_location_city_state_lat_long(self.API_TYPE_IX, a_ix)
                if c_s_temp != None:
                    c_s_temp.update({'port_capacity': isp_a_ix_id_dict[a_ix], 'isp_type_in_peering_db': self.API_TYPE_IX, 'isp_id_in_peering_db': a_ix})
                    isp_a_city_state_list.append(c_s_temp)

            if a_fac != None:
                c_s_temp = self.get_peering_location_city_state_lat_long(self.API_TYPE_FAC, a_fac)
                if c_s_temp != None:
                    c_s_temp.update({'port_capacity': isp_a_fac_id_dict[a_fac], 'isp_type_in_peering_db': self.API_TYPE_FAC, 'isp_id_in_peering_db': a_fac})
                    isp_a_city_state_list.append(c_s_temp)
        # print("Leaving get_all_possible_peering_city")
        return [dict(s) for s in set(frozenset(c_s.items()) for c_s in isp_a_city_state_list)]


    def get_peering_location_city_state_lat_long(self, api_type, isp_id):
        # print("Entering get_peering_location_city_state_lat_long")
        '''
        @param api_type: Any of the following: 'ix', 'fac', 'net'
        @param isp_id: ID of which ISP/IX/NET we're interested in.
        @note: Reads the JSON object.
        @note: We're now interested about only US ISP. Discarding others.
        @note: IX: 325 has city name: New York/New Jersey
        @return: City name of that IX/ facility.
        '''
        ix_or_fac_info = self.json_call_from_peeringdb_api(api_type, isp_id)
        name = ix_or_fac_info['data'][0]['name']
        org_name = ix_or_fac_info['data'][0].get('org_name',name)

        # print('HERE----> ix_or_fac_info', ix_or_fac_info)
        if ix_or_fac_info['data'][0]['country'] == 'US':
            city = None
            state = None
            latitude = None
            longitude = None
            if api_type == self.API_TYPE_IX:
                # try:
                city = ix_or_fac_info['data'][0]['city'] #.encode('ascii', 'ignore')
                if "," in city:
                    city = city.split(",")[0]
                if "/" in city:
                    city = city.split("/")[0]
                if " and " in city:
                    city = city.split(" and ")[0]
                for i in range(len(ix_or_fac_info['data'][0]['fac_set'])):
                    if ix_or_fac_info['data'][0]['fac_set'][i]['city'] == city:
                        state = ix_or_fac_info['data'][0]['fac_set'][i]['state'].encode('ascii', 'ignore')
                        latitude = ix_or_fac_info['data'][0]['fac_set'][i]['latitude']
                        longitude = ix_or_fac_info['data'][0]['fac_set'][i]['longitude']
                        break
                # except:
                #     print("Error: {}: {}".format(api_type, isp_id))
            if api_type == self.API_TYPE_FAC:
                # try:
                city = ix_or_fac_info['data'][0]['city'] #.encode('ascii', 'ignore')
                if "," in city:
                    city = city.split(",")[0]
                if "/" in city:
                    city = city.split("/")[0]
                if " and " in city:
                    city = city.split(" and ")[0]
                state = ix_or_fac_info['data'][0]['state'].encode('ascii', 'ignore')
                latitude = ix_or_fac_info['data'][0]['latitude']
                longitude = ix_or_fac_info['data'][0]['longitude']
                # except:
                #     print("Error: {}: {}".format(api_type, isp_id))

            # This is to match "North Virginia"
            tmp = city.split(" ")
            if len(tmp) > 1:
                for k, v in PopulationInfo.state_abbreviation_dict.items():
                    if tmp[1] == v:
                        state = k

            # This is to handle fac_id 2686, 4165: they use full name instead of abbreviation
            if state != None and len(state) > 2:
                print("Special Case [Don't worry!]: isp_id: {}, api_type: {}, state: {}".format(isp_id, api_type, state))
                for k, v in PopulationInfo.state_abbreviation_dict.items():
                    if state.upper() == str(v).upper():
                        state = k

            # This is last resort! Exceptional cases!
            if isp_id == 777:
                try:
                    city = ix_or_fac_info['data'][0]['fac_set'][0]['city'].decode('utf-8')
                except:
                    city = ix_or_fac_info['data'][0]['fac_set'][0]['city']
                try:
                    state = ix_or_fac_info['data'][0]['fac_set'][0]['state'].encode('utf-8')
                except:
                    state = ix_or_fac_info['data'][0]['fac_set'][0]['state']
                latitude = ix_or_fac_info['data'][0]['fac_set'][0]['latitude']
                longitude = ix_or_fac_info['data'][0]['fac_set'][0]['longitude']

            # print("Leaving get_peering_location_city_state_lat_long")
            if latitude == None or longitude == None:
                return None
            if city != None and state != None:
                state = str(state).upper()
                if city == "":
                    return {"city": None, "state": state, "location": (latitude, longitude), "org_name":org_name, 'name':name}
                elif state == "":
                    return {"city": city, "state": None, "location": (latitude, longitude), "org_name":org_name, 'name':name}
                return {"city": city, "state": state, "location": (latitude, longitude), "org_name":org_name, 'name':name}
            else:
                return None

    def get_peering_location_lat_long(self, api_type, isp_id):
        # print("Entering get_peering_location_lat_long")
        '''
        @param api_type: Any of the following:
        @param isp_id: ID of which ISP/IX/NET we're interested in.
        @note: Reads the JSON object.
        @return: tuple (latitude, longitude) of that IX facility location.
        '''

        temp = self.get_peering_location_city_state_lat_long(api_type, isp_id)

        # print("Leaving get_peering_location_lat_long")
        if temp != None:
            return temp['location']

    def get_peering_location_state_name(self, api_type, isp_id):
        # print("Entering get_peering_location_state_name")
        '''
        @param api_type: Any of the following: 'ix', 'fac', 'net'
        @param isp_id: ID of which ISP/IX/NET we're interested in.
        @note: Reads the JSON object.
        @return: State (location) of that IX facility.
        '''
        temp = self.get_peering_location_city_state_lat_long(api_type, isp_id)

        # print("Leaving get_peering_location_state_name")
        if temp != None:
            return temp['state']

    def get_peering_location(self, api_type, isp_id):
        # print("Entering get_peering_location")
        '''
        @note: we call get_peering_location_state_name() to get state name.
        or, we call get_peering_location_lat_long() to get (latitude, longitude) information.
        '''

        if is_state_name_required:
            loc = self.get_peering_location_state_name(api_type, isp_id)
            # print("Leaving get_peering_location")
            return loc
        else:
            loc = self.get_peering_location_lat_long(api_type, isp_id)
            # print("Leaving get_peering_location")
            if loc != None and (loc[0] != None or loc[1] != None):
                return loc
            else:
                return None

    def get_isp_name_from_net_id(self, isp_id):
        # print("Entering get_isp_name_from_net_id")
        html = urllib.request.urlopen(self.peeringdb_link + "net/" + str(isp_id)).read()
        soap = BeautifulSoup(html, "html.parser")
        soap.prettify()

#         name = soap.find_all('div', {'data-edit-name':'name'})
        name_list = soap.find_all('div', {'class': 'view_value col-xs-8 col-sm-7 col-md-8'})
        name = name_list[0].find('a').get_text().encode('ascii', 'ignore')
        also_known_as = name_list[1].get_text().encode('ascii', 'ignore')

        # print("Leaving get_isp_name_from_net_id")

        return {"name":name, "aka":also_known_as}


def convert_list_to_frequency_dict(list_of_items):
    # print("Entering convert_list_to_frequency_dict")
    '''
    @param list_of_items: Contains items that may occur multiple times.
    @return: dictionary with each item and their frequency count.
    @note: Converts the list into a frequency dictionary.
    '''
    state_freq = [list_of_items.count(state) for state in list_of_items]
    # print("Leaving convert_list_to_frequency_dict")
    return dict(zip(list_of_items, state_freq))


def get_peering_points_for_all_isps_of_one_type_in_detail(isp_dict):
    # print("Entering get_peering_points_for_all_isps_of_one_type_in_detail")
    '''
    @param isp_dict: Full list of ISPs of a certain type.
    @note: create PeeringInfo() object and then iterate through each ISP and their ASN list.
    For each ASN, get public exchange points and private facility locations.
    @note: isp_id is specific to PeeringDB.
    @note: if frequency of Peering location for each ISP (isp_id) is needed, is_peering_location_frequency_required is set to True.
    if public/ private classification is not required, set is_public_private_classification_required = False.
    For now, we don't need this classification and frequency as well, we just need unique location for per ISP by using "set" data type.
    @return: {'google': {
                        isp_id1:{'public':{'CA':3, 'FL':2}, 'private':{'MI':1}},
                        isp_id2:{}
                         },
              'microsoft': {
                            }
              }

              or,
              {'google': {
                        isp_id1:{'public':{(lat1, long1):3, (lat2, long2):2}, 'private':{(lat3, long3):1}},
                        isp_id2:{}
                         },
              'microsoft': {
                            }
              }

              or,
              {'google': {
                        isp_id1:[(lat1, long1), (lat2, long2), (lat3, long3)],
                        isp_id2:[]
                         },
              'microsoft': {
                            }
              }
              if both the conditions are False.
    '''
    peeringInfo = PeeringInfo()
    specific_type_isp_peering_points_complete_picture = {}

    public_peering_exchange_locations_list = []
    private_peering_facility_locations_list = []

    for isp_name, asn_list in isp_dict.items():
        all_peering_points_for_isp = {}
        print("ISP: {}".format(isp_name))
        for asn in asn_list:
            isp_id= peeringInfo.get_net_id_from_asn(asn)
            print("ISP_ID: {}, ASN: {}".format(isp_id, asn))
            if for_icc:
                all_peering_points_for_isp = peeringInfo.get_all_pops_locations_with_population_for_single_isp_id(isp_id)
            else:
                asn_public_peering_listing, asn_private_facility_listing = peeringInfo.get_all_peering_points_for_single_isp_id(isp_id)
                public_peering_exchange_locations_list.extend(asn_public_peering_listing)
                private_peering_facility_locations_list.extend(asn_private_facility_listing)
                if is_peering_location_frequency_required:
                    if is_public_private_classification_required:
                        all_peering_points_for_isp.update({isp_id: {'public':convert_list_to_frequency_dict(asn_public_peering_listing),
                                                                    'private':convert_list_to_frequency_dict(asn_private_facility_listing)}})
                    else:
                        all_peering_points_for_isp.update({isp_id: convert_list_to_frequency_dict(asn_public_peering_listing + asn_private_facility_listing)})
                else:
                    if is_public_private_classification_required:
                        all_peering_points_for_isp.update({isp_id: {'public':list(set(asn_public_peering_listing)),
                                                                    'private':list(set(asn_private_facility_listing))}})
                    else:
                        all_peering_points_for_isp.update({isp_id:list(set(asn_public_peering_listing + asn_private_facility_listing))})
        specific_type_isp_peering_points_complete_picture.update({isp_name:all_peering_points_for_isp})
    # print("Leaving get_peering_points_for_all_isps_of_one_type_in_detail")
    if for_icc:
        return specific_type_isp_peering_points_complete_picture

    if is_public_private_classification_required:
        if is_peering_location_frequency_required:
            return specific_type_isp_peering_points_complete_picture, dict({'public':convert_list_to_frequency_dict(public_peering_exchange_locations_list),
                                                   'private':convert_list_to_frequency_dict(private_peering_facility_locations_list)})
        else:
            return specific_type_isp_peering_points_complete_picture, dict({'public':list(set(public_peering_exchange_locations_list)),
                                                   'private':list(set(private_peering_facility_locations_list))})
    else:
        merged_peering_facility_list = public_peering_exchange_locations_list + private_peering_facility_locations_list
        if is_peering_location_frequency_required:
            return specific_type_isp_peering_points_complete_picture, convert_list_to_frequency_dict(merged_peering_facility_list)
        else:
            return specific_type_isp_peering_points_complete_picture, list(set(merged_peering_facility_list))

def get_total_distance_for_all_points_from_current_point(cur_point, peering_locations_list):
    # print("Entering get_total_distance_for_all_points_from_current_point")
    '''
    @var cur_point: is the point we want to check whether distance of all points from it, is the minimum.
    '''
    n = numpy.sum([get_distance_in_mile(cur_point[0], cur_point[1], pop['location'][0], pop['location'][1]) for pop in peering_locations_list])
    print("Leaving get_total_distance_for_all_points_from_current_point")
    return n
#     return numpy.sum([pop['state_population'] * get_distance_in_mile(cur_point[0], cur_point[1], pop['location'][0], pop['location'][1]) for pop in peering_locations_list])
#     return numpy.sum([pop['city_population'] * get_distance_in_mile(cur_point[0], cur_point[1], pop['location'][0], pop['location'][1]) for pop in peering_locations_list])

def calculate_center_point(peering_locations_list):
    # print("Entering calculate_center_point")
    '''
    @note: First, we calculate the centroid of the points. Then, using approximation, we return the point that minimizes the distance for all the points from itself.
    We're using Geometric Median. Check 'Weber problem' as well. (Single source facility location problem)
    algorithm: http://www.geomidpoint.com/calculation.html

    However, calculating centroid formula works with radians only. Latitude, Longitude on maps are on Degree. We need to convert them to Radian first,
    Apply the formula and finally convert them back to Latitude, Longitude as a Point.
    https://stackoverflow.com/questions/6671183/calculate-the-center-point-of-multiple-latitude-longitude-coordinate-pairs
    '''
    if for_icc:
        x = numpy.mean([numpy.cos(numpy.radians(pop['location'][0])) * numpy.cos(numpy.radians(pop['location'][1])) for pop in peering_locations_list])
        y = numpy.mean([numpy.cos(numpy.radians(pop['location'][0])) * numpy.sin(numpy.radians(pop['location'][1])) for pop in peering_locations_list])
        z = numpy.mean([numpy.sin(numpy.radians(pop['location'][0])) for pop in peering_locations_list])
    else:
        x = numpy.mean([numpy.cos(numpy.radians(lat)) * numpy.cos(numpy.radians(lon)) for (lat, lon) in peering_locations_list])
        y = numpy.mean([numpy.cos(numpy.radians(lat)) * numpy.sin(numpy.radians(lon)) for (lat, lon) in peering_locations_list])
        z = numpy.mean([numpy.sin(numpy.radians(lat)) for (lat, lon) in peering_locations_list])
    longitude = numpy.rad2deg(numpy.arctan2(y, x))
    hyp = numpy.sqrt(x * x + y * y)
    latitude = numpy.rad2deg(numpy.arctan2(z, hyp))
    cur_point = (latitude, longitude)

    if for_icc:
        peering_locations_list_with_centroid = []

        min_distance = get_total_distance_for_all_points_from_current_point(cur_point, peering_locations_list)
        for pop in peering_locations_list:
            new_point = (pop['location'][0], pop['location'][1])
            new_distance = get_total_distance_for_all_points_from_current_point(new_point, peering_locations_list)
            if new_distance < min_distance:
                min_distance = new_distance
                cur_point = new_point

        test_distance = 1.5708
        while test_distance > 0.00000002:
            '''
            circular pattern around the CurrentPoint at a distance of TestDistance to the north, northeast, east, southeast, south, southwest, west and northwest.
            '''
            test_points = [(cur_point[0], cur_point[1] + test_distance), (cur_point[0] + test_distance, cur_point[1] + test_distance),
                           (cur_point[0] + test_distance, cur_point[1]), (cur_point[0] + test_distance, cur_point[1] - test_distance),
                           (cur_point[0], cur_point[1] - test_distance), (cur_point[0] - test_distance, cur_point[1] - test_distance),
                           (cur_point[0] - test_distance, cur_point[1]), (cur_point[0] - test_distance, cur_point[1] + test_distance),]

            for new_point in test_points:
                new_distance = get_total_distance_for_all_points_from_current_point(new_point, peering_locations_list)
                if new_distance < min_distance:
                    min_distance = new_distance
                    cur_point = new_point

            test_distance /= 2

        peering_locations_list_with_centroid.append(cur_point)
        # print("Leaving calculate_center_point")
        return peering_locations_list_with_centroid
    else:
        # print("Leaving calculate_center_point")
        # This should be a tuple. But, after we read from a JSON object, all locations become list! Similar to tuple though!
        return [latitude, longitude]


def get_distance_in_mile(lat1, long1, lat2, long2):
    # print("Entering get_distance_in_mile")
    '''
    @return: distance between two location(lat, long) in miles.
    @note: Formula from:
    https://www.movable-type.co.uk/scripts/latlong.html
    '''
    earthRadious = 3959
    dlat = numpy.deg2rad(lat2 - lat1)
    dlong = numpy.deg2rad(long2 - long1)
    a = (numpy.sin(dlat / 2)) ** 2 + numpy.cos(numpy.deg2rad(lat1)) * numpy.cos(numpy.deg2rad(lat2)) * ((numpy.sin(dlong / 2)) ** 2)
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1 - a))
    # print("Leaving get_distance_in_mile")
    return c * earthRadious
