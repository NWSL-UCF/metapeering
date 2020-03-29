'''
Created on Sep 15, 2018

@author: prasun
'''

import requests, string
import os.path as path
import json

class PopulationInfo(object):
    '''
    This class handles the API calling from https://api.census.gov/
    Will be used for mainly getting population data.
    @note: City population of 2017, State population of 2015
    @var state_code_dict: These numbers are used in census.gov.
    @var location_not_in_census_gov_population: contains the population of the cities which are not available in census.gov  
    '''

    census_gov_state_code_dict = {"Alabama":1, "Alaska":2, "Arizona":4, "Arkansas":5, "California":6, "Colorado":8, "Connecticut":9, "Delaware":10,
                       "District of Columbia":11, "Florida":12, "Georgia":13, "Hawaii":15, "Idaho":16, "Illinois":17, "Indiana":18,
                       "Iowa":19, "Kansas":20, "Kentucky":21, "Louisiana":22, "Maine":23, "Maryland":24, "Massachusetts":25, "Michigan":26,
                       "Minnesota":27, "Mississippi":28, "Missouri":29, "Montana":30, "Nebraska":31, "Nevada":32, "New Hampshire":33,
                       "New Jersey":34, "New Mexico":35, "New York":36, "North Carolina":37, "North Dakota":38, "Ohio":39, "Oklahoma":40,
                       "Oregon":41, "Pennsylvania":42, "Rhode Island":44, "South Carolina":45, "South Dakota":46, "Tennessee":47, "Texas":48,
                       "Utah":49, "Vermont":50, "Virginia":51, "Washington":53, "West Virginia":54, "Wisconsin":55, "Wyoming":56}

    state_abbreviation_dict = {"AL":"Alabama", "AK":"Alaska", "AZ":"Arizona", "AR":"Arkansas", "CA":"California", "CO":"Colorado",
                               "CT":"Connecticut", "DE":"Delaware", "DC":"District of Columbia", "FL":"Florida", "GA":"Georgia", "HI":"Hawaii",
                               "ID":"Idaho", "IL":"Illinois", "IN":"Indiana", "IA":"Iowa", "KS":"Kansas", "KY":"Kentucky", "LA":"Louisiana",
                               "ME":"Maine", "MD":"Maryland", "MA":"Massachusetts", "MI":"Michigan", "MN":"Minnesota", "MS":"Mississippi",
                               "MO":"Missouri", "MT":"Montana", "NE":"Nebraska", "NV":"Nevada", "NH":"New Hampshire", "NJ":"New Jersey",
                               "NM":"New Mexico", "NY":"New York", "NC":"North Carolina", "ND":"North Dakota", "OH":"Ohio", "OK":"Oklahoma",
                               "OR":"Oregon", "PA":"Pennsylvania", "RI":"Rhode Island", "SC":"South Carolina", "SD":"South Dakota",
                               "TN":"Tennessee", "TX":"Texas", "UT":"Utah", "VT":"Vermont", "VA":"Virginia", "WA":"Washington",
                               "WV":"West Virginia", "WI":"Wisconsin", "WY":"Wyoming"}
    
    # https://www.statista.com/statistics/184691/internet-usage-in-the-us-by-state/
    internet_users_percentage = {"AL":78.7, "AK":83.6, "AZ":83.9, "AR":80.1, "CA":83.8, "CO":79.5, "CT":82.4, "DE":80.1, "DC":84.1, 
                                 "FL":84.2, "GA":84.7, "HI":83.6, "ID":87.6, "IL":86.5, "IN":81.5, "IA":84.3, "KS":82.2, "KY":79.0, 
                                 "LA":82.8, "ME":85.1, "MD":84.0, "MA":78.4, "MI":81.2, "MN":85.6, "MS":78.5, "MO":83.3, "MT":78.1, 
                                 "NE":83.1, "NV":87.5, "NH":88.3, "NJ":82.4, "NM":83.3, "NY":80.2, "NC":81.4, "ND":82.4, "OH":79.4, 
                                 "OK":80.2, "OR":87.4, "PA":78.2, "RI":83.1, "SC":82.7, "SD":79.0, "TN":78.2, "TX":81.7, "UT":87.7, 
                                 "VT":83.1, "VA":85.2, "WA":88.5, "WV":78.0, "WI":87.5, "WY":86.0,
                                 }

    
    location_not_in_census_gov_population = {"CA": {"San Antonio": 1512000}, "HI": {"Honolulu": 350395},"VA":{"Ashburn": 43511, "Northern Virginia": 2775354, "Reston": 60070, "Sandston": 7571, "Sterling": 29597}, 
                                             "MA": {"Billerica": 43962}, "NJ": {"Edison": 102450, "North Bergen": 63659, "Weehawken": 15342, "Piscataway": 57887}, "NY": {"Brooklyn": 2648771, "Staten Island": 479458}}
        
    # This is to reduce the API call to Census Gov.
    use_census_gov_api = False
    temp_census_gov_population = {"AL": {"Montgomery": 199518}, "AZ": {"Phoenix": 1626078, "Scottsdale": 249950, "Tempe": 185038},
                                  "CA": {"El Segundo": 16853, "Fremont": 234962, "Los Angeles": 3999759, "Milpitas": 78106, "Mountain View": 81438, "Palo Alto": 67178, "Sacramento": 501901, "San Diego": 1419516, "San Francisco": 884363, "San Jose": 1035317, "Santa Clara": 127134, "Sunnyvale": 153656, "Rancho Cordova": 73563},
                                  "CO": {"Denver": 704621, "Englewood": 34407}, "DC": {"Washington": 693972},
                                  "FL": {"Boca Raton": 98150, "Jacksonville": 892062, "Miami": 463347, "Talahassee": 191049, "Tampa": 385430}, 
                                  "GA": {"Atlanta": 486290, "Suwanee": 19549}, "ID": {"Boise": 226570}, 
                                  "IL": {"Chicago": 2716450, "Elk Grove Village": 32776, "Northlake": 12364}, 
                                  "IN": {"Indianapolis": 863002, "South Bend": 102245}, "MA": {"Boston": 685094, "Cambridge": 113630, "Somerville": 81360},
                                  "MD": {"Baltimore": 611648}, "ME": {"Portland": 66882}, "MI": {"Southfield": 73208}, 
                                  "MN": {"Belle Plaine":7119, "Eden Prairie": 64400, "Minneapolis": 422331, "Rochester": 115733, "St. Paul": 306621}, 
                                  "MO": {"Kansas City":488943, "St. Louis": 308626}, "NC": {"Charlotte": 859035}, "NE": {"Omaha": 466893}, 
                                  "NM": {"Albuquerque": 558545}, "NV": {"Las Vegas": 641676, "Reno": 248853}, "NJ": {"Newark": 285154, "Secaucus": 20215, "Somerset":22083},
                                  "NY": {"Buffalo": 258612, "Chappaqua": 1476, "New York": 8622698}, "OH": {"Cleveland": 385525, "Columbus": 879170}, 
                                  "OK": {"Oklahoma City": 643648}, "OR": {"Hillsboro": 106894, "Portland": 647805},
                                  "PA": {"Philadelphia": 1580863, "Pittsburgh": 302407}, "TN": {"Memphis": 652236, "Nashville": 667560}, 
                                  "TX": {"Austin": 950715, "Dallas": 1341075, "Houston": 2312717, "Katy": 18282, "McAllen": 142696, "San Antonio": 1511946},
                                  "UT": {"Salt Lake City": 200544}, "VA": {"Ashland": 7796, "Manassas": 41501, "Norfolk": 244703, "Richmond": 227032, "Vienna": 16544},
                                  "WA": {"Seattle": 724745, "Tukwila": 20144}, "WI": {"Madison": 255214}}
    
    def __init__(self):
        '''
        Constructor
        '''
        
    def compare_string(self, s1, s2):
        remove = string.punctuation + string.whitespace
        return string.lower(s1).translate(None, remove) == string.lower(s2).translate(None, remove)
        
    def get_state_population_from_online(self, state_abbreviation):
        '''
        @param state_abbreviation: USA states postal abbreviation, i.e., AL: Alabama, CA: California
        @return: the population of that state for year 2015 using census gov population api.  
        '''
        census_gov_population_api = "https://api.census.gov/data/2015/acs5?get=NAME,B01001_001E,B01001_001M&for=state:"
        state_population_api_url = census_gov_population_api + str(PopulationInfo.census_gov_state_code_dict[PopulationInfo.state_abbreviation_dict[state_abbreviation]])
         
        r = requests.get(state_population_api_url)
        data = r.json()
        return int(data[1][1].encode('ascii', 'ignore'))
        
    def get_state_population(self, state_abbreviation, from_file=True):
        '''
        @note: This reads from the file and returns the state population.
        @param from_file: Default is True. If false, then gets the population from CENSUS GOV api call. 
        '''
        if from_file:
            file_name = path.abspath(path.dirname(__file__) + "/" + "data/" + "state_population_15_from_census_gov.json")
            fin = open(file_name)
            data = json.load(fin)
            for item in data:
                if item[0] == PopulationInfo.state_abbreviation_dict[state_abbreviation]:
                    return int(item[1])
        else:
            return self.get_state_population_from_online(state_abbreviation)
    
    
        
    def get_city_population(self, city_name, state_abbreviation):
        '''
        Takes the city name and state abbreviations to return the population of that city.
        '''
        if PopulationInfo.use_census_gov_api:
            census_gov_population_for_all_city_in_state_api = "https://api.census.gov/data/2017/pep/population?get=POP,GEONAME&for=place:*&in=state:"
            all_city_in_state_population_api_url = census_gov_population_for_all_city_in_state_api + str(PopulationInfo.census_gov_state_code_dict[PopulationInfo.state_abbreviation_dict[state_abbreviation]])
            
            try:
                r = requests.get(all_city_in_state_population_api_url)
                data = r.json()
                
                # length of "city" = 4, "comma" = 1, " " = 1 + length of that state_name
                ignore_character_count = 4 + 1 + 1 + len(PopulationInfo.state_abbreviation_dict[state_abbreviation])  
            
                for city_info in data[1:]:
                    if self.compare_string((city_info[1][:-ignore_character_count]).encode('ascii', 'ignore'), city_name):
                        return int(city_info[0])
            except:
                print("Error: Couldn't process JSON call. City: {}, State: {}".format(city_name, state_abbreviation))
        else:
            try:
                return PopulationInfo.temp_census_gov_population[state_abbreviation][city_name]
            except:
                pass
            
        for k, v in PopulationInfo.location_not_in_census_gov_population.items():
            if k == state_abbreviation:
                return int(v[city_name])
        
        return None
