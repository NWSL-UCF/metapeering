'''
Created on Jan 23, 2019

@author: prasun
'''
import os, glob, json, requests

data_folder_path = os.path.abspath(os.path.dirname(__file__) + "/" + "data")
output_folder_path = os.path.abspath(os.path.dirname(__file__) + "/" + "output")

def get_country_count_from_caida():
    country_list = []
    caida_api = "http://as-rank.caida.org/api/v1/" + str("orgs") + str("?populate=1")
    caida_response = requests.get(caida_api).json()
    for org_ in caida_response['data']:
        country = org_['country']
        if country not in country_list: 
            country_list.append(country)
    return len(country_list)


def get_total_prefixes_addresses_count_from_caida():
    '''
    @return: summation of prefixes count of all the organizations
    @return: summation of addresses count
    '''
    caida_api = "http://as-rank.caida.org/api/v1/" + str("orgs") + str("?populate=1")
    caida_response = requests.get(caida_api).json()
    prefixes_count = 0
    address_count = 0
    for org_ in caida_response['data']:
        try:
            prefixes_count += org_['cone']['prefixes']
        except:
            print('Could not find prefix information for organization: {}, organization id in CAIDA: {}'.format(org_['name'], org_['id']))
        try:
            address_count += org_['cone']['addresses']
        except:
            print('Could not find address information for organization: {}, organization id in CAIDA: {}'.format(org_['name'], org_['id']))

    return prefixes_count, address_count 


# need manual check: 2914, 22773, 174 
def add_prefix_count_address_count_and_neighbor_count_to_json():
    
    total_prefixes_in_globe, total_addresses_in_globe = get_total_prefixes_addresses_count_from_caida()
    
    asn_list = []  # 7029, 32934, 16509, 6461, 15169, 4181, 20940, 62955, 209, 6939, 2914, 7922, 2906, 8075, 7843, 22773, 1239, 3491, 174]
    ripe_url_for_routing_status = "https://stat.ripe.net/data/routing-status/data.json?resource=AS"
    caida_url_for_routing_status = "http://as-rank.caida.org/api/v1/asns/"
    for f in glob.glob(data_folder_path + "/" + "*_peering_db_data_file.json"):
        if 'temp' in f:
            continue
        asn = int(f[len(data_folder_path + "/"):-len("_peering_db_data_file.json")])
        if asn in asn_list:
            continue
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
             
        with open(f, 'r+') as fp:
            data = json.load(fp)['data']
            for k, v in data.items():
                if k == 'total_prefixes_in_globe':
                    data[k] = total_prefixes_in_globe
                else:
                    data.update({'total_prefixes_in_globe':total_prefixes_in_globe})
                if k == 'prefixes':
                    data[k] = prefixes
                else:
                    data.update({'prefixes':prefixes})
                if k == 'total_addresses_in_globe':
                    data[k] = total_addresses_in_globe
                else:
                    data.update({'total_addresses_in_globe':total_addresses_in_globe})
                if k == 'address_space':
                    data[k] = address_space
                else:
                    data.update({'address_space':address_space})
                if k == 'neighbor':
                    data[k] = neighbor
                else:
                    data.update({'neighbor':neighbor})
                if k == 'name':
                    data[k] = name
                else:
                    data.update({'name':name})
            fp.seek(0)
            json.dump({"data": data}, fp)
        fp.close()


def add_traffic_ratio_to_json():
    traffic_ratio_dict = {0: "Not Disclosed", 1: "Heavy Inbound", 2: "Mostly Inbound", 3: "Balanced", 4: "Mostly Outbound", 5: "Heavy Outbound"}
    asn_traffic_ratio_dict = {15169: 4, 2914: 3, 8075: 4, 32934: 5, 62955: 4, 20940: 5, 3491: 3, 174: 0, 16509: 3, 209: 3, 7922: 3, 7843: 3, 4181: 2, 1239: 3, 2906: 5, 6939: 3, 22773: 2, 6461: 3, 7029: 2}
    for f in glob.glob(data_folder_path + "/" + "*_peering_db_data_file.json"):
        asn = int(f[len(data_folder_path + "/"):-len("_peering_db_data_file.json")])
        data = None
        with open(f, 'r+') as fin:
            pop_list = json.load(fin)['data']
            data = {"data": {"traffic_ratio": str.upper(traffic_ratio_dict[asn_traffic_ratio_dict[asn]]), "pop_list": pop_list}}
            fin.seek(0)
            json.dump(data, fin)
            #### Or, a lame one! ####
            '''
            for l in fin.readlines():
                if "\"data\": " in l:
                    l = l.replace("\"data\": ", "\"data\": {\"traffic_ratio\": \"BALANCED\", \"pop_list\": ")
                l_for_write += l
                print(l_for_write)
            fin.seek(0)
            fin.write(l_for_write+"}")
            '''
        fin.close()

def add_internet_penetration_percentage_of_state_to_json():
    from PopulationFromCensusGov import PopulationInfo
    for f in glob.glob(data_folder_path + "/" + "*_peering_db_data_file.json"):
        with open(f, 'r+') as fin:
            data = json.load(fin)['data']
            pop_list = data['pop_list']
            for p in pop_list:
                p['internet_penetration_percentage'] = PopulationInfo.internet_users_percentage[p['state']] / 100.0
            data['pop_list'] = pop_list
            data = {'data':data}
            fin.seek(0)
            json.dump(data, fin)
        fin.close()
        
def peering_pairs_based_on_types_using_peeringdb_caida():
    import MySQLdb, numpy
    
    conn = MySQLdb.connect(host='localhost', user='root', passwd='')
    cursor = conn.cursor()
    cursor.execute('use peeringdb')
       
    traffic_ratio_type = ['Heavy Inbound', 'Mostly Inbound', 'Balanced', 'Mostly Outbound', 'Heavy Outbound']
    traffic_ratio_type_short_form = ['HI', 'MI', 'B', 'MO', 'HO']

    isp_dict = dict()
    for ratio_type in traffic_ratio_type:      
        q = 'SELECT asn FROM peeringdb.peeringdb_network WHERE info_ratio = %s'
        cursor.execute(q,[ratio_type])
        cursor_result = cursor.fetchall()
        isp_dict[ratio_type] = sorted([int(c[0]) for c in cursor_result])
   
    with open(data_folder_path + "/" + "peeringdb_isp_asn_by_traffic_ratio.json", 'w') as fout:
        json.dump({'data':isp_dict}, fout)
        fout.close()
      
    peering_pairs_category_count_array = numpy.zeros([len(traffic_ratio_type), len(traffic_ratio_type)])
    peering_pair_not_present_in_peering_db_count = 0
    total_pairs_in_caida_p2c_and_p2p = 0
    with open(data_folder_path + "/" + "20190601.as-rel.txt", 'r') as fin:
        for f in fin.readlines():
            if f[0] == '#':
                continue
            f = f.strip().split("|")
            if int(f[-1]) == 0: # Means peer
                isp_a_ratio_type = isp_b_ratio_type = -1
                for k, v in isp_dict.items():
                    if int(f[0]) in v:
                        isp_a_ratio_type = traffic_ratio_type.index(k)
                    if int(f[1]) in v:
                        isp_b_ratio_type = traffic_ratio_type.index(k) 
                if isp_a_ratio_type != -1 and isp_b_ratio_type != -1:
                    peering_pairs_category_count_array[isp_a_ratio_type][isp_b_ratio_type] += 1
                else:
                    peering_pair_not_present_in_peering_db_count += 1
            total_pairs_in_caida_p2c_and_p2p += 1
        fin.close()
    numpy.set_printoptions(precision = 3)
 
    peering_pairs_category_count_array_percentage = peering_pairs_category_count_array / peering_pairs_category_count_array.sum() * 100 
    print(peering_pairs_category_count_array_percentage)
    print('Pairs that peer in CAIDA, but info not found for either of ISPs count: {}'.format(peering_pair_not_present_in_peering_db_count))
    print("Total pairs in CAIDA that peer: {}".format(peering_pair_not_present_in_peering_db_count + peering_pairs_category_count_array.sum()))
    print("Total pairs in CAIDA regardless or p2c or peering: {}".format(total_pairs_in_caida_p2c_and_p2p))
    
    print('\\begin{tabular}{|l|c|c|c|c|c|c|}')
    print('\\hline')
    table_row = ""
    for r_type in traffic_ratio_type_short_form:
        table_row += "& "
        table_row += r_type
        table_row += " "
    table_row += "\\\\" + "\n" + "\hline"
    print(table_row)
    for i in range(len(peering_pairs_category_count_array_percentage)):
        table_row = traffic_ratio_type_short_form[i] + " "
        for j in range(len(peering_pairs_category_count_array_percentage[i,:])):
            table_row += "& "
            table_row += str(peering_pairs_category_count_array_percentage[i,j])
            table_row += " "
        table_row += "\\\\" + "\n" + "\hline"
        print(table_row)
    print('\\end{tabular}')
    
def get_country_continent():
    """
    Creates the country-continent dictionary from PeeringDB IX. But there are some countries where FAC is present. Their info is missing.
    We update those countries continents manually. 
    We need this, because, IX (peeringdb_ix) has country and continent information. But, Facilities (peeringdb_facility) don't have those. 
    """
    import MySQLdb, numpy
    
    conn = MySQLdb.connect(host='localhost', user='root', passwd='')
    cursor = conn.cursor()
    cursor.execute('use peeringdb')
    
    country_continent_dict = {}
#     q = 'SELECT country FROM peeringdb.peeringdb_facility'
    q = 'SELECT country, region_continent FROM peeringdb.peeringdb_ix'
    cursor.execute(q)
    country_continet_list_from_peeringdb_ix = list(set(cursor.fetchall()))
    
    for _country_continent in country_continet_list_from_peeringdb_ix:
        country_continent_dict[_country_continent[0]] = _country_continent[1]

    q1 = 'SELECT country FROM peeringdb.peeringdb_facility'
    cursor.execute(q1)
    country_list_from_peeringdb_facility = list(set(cursor.fetchall()))
    
    cursor.close()
    
#     for _country in country_list_from_peeringdb_facility:
#         if _country[0] not in country_continent_dict.keys():
#             # print("country_continent_dict['{}'] = region_names[1]".format(_country[0]))
#             print(_country[0])
            
    region_names = {'af':'Africa', 'ap':'Asia Pacific', 'au':'Australia', 'eu':'Europe', 'me':'Middle East', 'na':'North America', 'sa':'South America'}
    
    # These countries info is not present in PeeringDB. So we manually do these!
    country_continent_dict['IQ'] = region_names['ap']
    country_continent_dict['PA'] = region_names['na']
    country_continent_dict['CM'] = region_names['af']
    country_continent_dict['GT'] = region_names['na']
    country_continent_dict['AZ'] = region_names['eu']
    country_continent_dict['BN'] = region_names['ap']
    country_continent_dict['IR'] = region_names['ap']
    country_continent_dict['UY'] = region_names['sa']
    country_continent_dict['BF'] = region_names['af']
    country_continent_dict['DO'] = region_names['na']
    country_continent_dict['MO'] = region_names['ap']
    country_continent_dict['NI'] = region_names['na']
    country_continent_dict['GP'] = region_names['na']
    country_continent_dict['PK'] = region_names['ap']
    country_continent_dict['MF'] = region_names['na']
    country_continent_dict['FJ'] = region_names['au']
    country_continent_dict['ZW'] = region_names['af']
    country_continent_dict['BA'] = region_names['eu']
    country_continent_dict['OM'] = region_names['me']
    country_continent_dict['MA'] = region_names['af']
    country_continent_dict['YE'] = region_names['me']
    country_continent_dict['GM'] = region_names['af']
    country_continent_dict['MP'] = region_names['au']
    country_continent_dict['GE'] = region_names['eu']
    
    return country_continent_dict
        
def get_continent_count_for_each_isp_from_peeringdb():
    """
    Identifies the number of ISPs operating in a certain region. 
    Use "info_scope" in peeringdb. Global, Africa, Asia Pacific, Australia, Europe, Middle East, North America, South America, Not Disclosed, Regional, "" (NOTE THIS)
    Also finds out how many ISPs are operating only in 1 continent, how many are operating in more than 1. 
    """
    
    import MySQLdb, numpy
    
    conn = MySQLdb.connect(host='localhost', user='root', passwd='')
    cursor = conn.cursor()
    cursor.execute('use peeringdb')

    country_continent_dict = get_country_continent()
    
    # This are the names of ISPs info_scope (business areas). Just to check if there is any new regions! Note: Not Disclosed and "" are different!
    # q = 'SELECT info_scope from peeringdb.peeringdb_network'
    # cursor.execute(q)
    # cursor_result = cursor.fetchall()
    # print(list(set(cursor_result)))

    info_scope_names_dict = {'global':'Global', 'africa':'Africa', 'asia':'Asia Pacific', 'australia':'Australia', 'europe':'Europe', 'middle_east':'Middle East', 'north_america':'North America', 'south_america':'South America', 'not_disclosed':'Not Disclosed', 'regional':'Regional', 'empty':''}
    total_isp = 0
    info_scope_detail_all = {}
    for k, v in info_scope_names_dict.items():
        info_scope_detail_for_one_region = {}
        isp_present_in_only_one_continet_count = 0
        isp_present_in_more_than_one_continet_count = 0
        
        # Get ISPs of a region
        q1 = 'SELECT id FROM peeringdb.peeringdb_network WHERE info_scope = %s'
        cursor.execute(q1,[v])
        isp_id_list = cursor.fetchall()
#         isp_dict[ratio_type] = sorted([int(c[0]) for c in cursor_result])
#         print("{} ISPs are operating in {}".format(len(isp_id_list), k))
        info_scope_detail_for_one_region.update({'isp_count':len(isp_id_list)})

        for net_id in isp_id_list:
            isp_info = {'net_id': net_id}
            country_list = []
            continet_list = []

            # Get list of ixlan_id and fac_id for public IXPs and private Facilities.
            # IX:
            q2 = 'SELECT ixlan_id FROM peeringdb.peeringdb_network_ixlan WHERE net_id = %s'
            cursor.execute(q2, [net_id])
            ixlan_id_list = cursor.fetchall()
            isp_info.update({'ixlan_count':len(ixlan_id_list)})
#             print("net_id: {} has {} ixlan".format(net_id, isp_info['ixlan_count']))
            
            for ixlan_id in ixlan_id_list:
                # Get ix_id from ixlan_id
                q3 = 'SELECT ix_id FROM peeringdb.peeringdb_ixlan WHERE id = %s'  
                cursor.execute(q3, [ixlan_id])
                ix_id = cursor.fetchall()[0]
                
                # Get IX detail (country, region_continent) from ix_id
                q4 = 'SELECT country, region_continent FROM peeringdb.peeringdb_ix WHERE id = %s'
                cursor.execute(q4, [ix_id])
                ix_country_continet = cursor.fetchall()[0]
                country_list.append(ix_country_continet[0])
                continet_list.append(ix_country_continet[1])
                
            # FACILITY:
            q5 = 'SELECT fac_id FROM peeringdb.peeringdb_network_facility WHERE net_id = %s'
            cursor.execute(q5, [net_id])
            fac_id_list = cursor.fetchall()
            isp_info.update({'fac_count':len(fac_id_list)})
            
            for fac_id in fac_id_list:
                q6 = 'SELECT country FROM peeringdb.peeringdb_facility WHERE id = %s'
                cursor.execute(q6, [fac_id])
                _res = cursor.fetchall()[0]
                fac_country = _res[0]
                country_list.append(fac_country)
                continet_list.append(country_continent_dict[fac_country])
             
            temp = list(set(country_list))
            country_list = temp
            temp = list(set(continet_list))
            continet_list = temp
            isp_info.update({'country_list':country_list, 'continent_list':continet_list})
            if len(continet_list) > 1:
                isp_present_in_more_than_one_continet_count += 1
            else:
                isp_present_in_only_one_continet_count += 1
        
        info_scope_detail_for_one_region.update({'one_continet_count':isp_present_in_only_one_continet_count, 'more_than_one_continet_count':isp_present_in_more_than_one_continet_count})
        info_scope_detail_all.update({k:info_scope_detail_for_one_region})
    
    print("{:<20} {:<20} {:<25} {:<20} {:<30}".format("ISP operating area", "Total ISP count", "Only in 1 continent", "In more than 1", "Only in 1 continent (in %)"))
    print("*"*100)
    for k, v in info_scope_detail_all.items():
        only_in_one_continet_in_percent = "{:0.2f}%".format(float(info_scope_detail_all[k]['one_continet_count'])/ info_scope_detail_all[k]['isp_count'] * 100)
        if k == 'empty':
            print("{:<20} {:<20} {:<25} {:<20} {:<30}".format('No Info', info_scope_detail_all[k]['isp_count'], info_scope_detail_all[k]['one_continet_count'], info_scope_detail_all[k]['more_than_one_continet_count'], only_in_one_continet_in_percent))
        else:
            print("{:<20} {:<20} {:<25} {:<20} {:<30}".format(info_scope_names_dict[k], info_scope_detail_all[k]['isp_count'], info_scope_detail_all[k]['one_continet_count'], info_scope_detail_all[k]['more_than_one_continet_count'], only_in_one_continet_in_percent))

def copy_graph_files_to_one_folder():
    '''
    Copies all the diff_XXXX_YYYY.pdf or own_XXXX_YYYY.pdf or ratio files to a common folder to compare them at a glance.  
    '''
    from fnmatch import fnmatch 
    from shutil import copyfile
    
    for ratio_type in ['diff', 'own', 'ratio']:
        graph_folder = os.path.join(output_folder_path, "graphs_"+ratio_type)
        if not os.path.exists(graph_folder):
            os.makedirs(graph_folder)
        for path, _, my_files in os.walk(output_folder_path):
            for my_file_names in my_files:
                file_name_pattern = ratio_type + "_*_*"
                if fnmatch(my_file_names, file_name_pattern):
                    try:
                        copyfile(os.path.join(path, my_file_names), os.path.join(graph_folder, my_file_names))
                    except Exception as e:
                        pass
    
if __name__ == '__main__':
#     add_traffic_ratio_to_json()
#     add_prefix_count_address_count_and_neighbor_count_to_json()
#     get_total_prefixes_addresses_count_from_caida()
#     add_internet_penetration_percentage_of_state_to_json()
#     peering_pairs_based_on_types_using_peeringdb_caida()
#     copy_graph_files_to_one_folder()
    get_continent_count_for_each_isp_from_peeringdb()
