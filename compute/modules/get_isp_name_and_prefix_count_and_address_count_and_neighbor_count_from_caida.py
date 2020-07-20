import requests

def get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida(asn):
    # print("Entering get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida")
    '''
    @note: Calls CAIDA first to get the ISP name, how many prefixes, IP addresses it has and how many neighbors it is connected with.
    if CAIDA data is not available, we try RIPE. RIPE is not always available, so CAIDA is first choice.
    @return: name, prefixes, address_space, neighbor
    '''
    ripe_url_for_routing_status = "https://stat.ripe.net/data/routing-status/data.json?resource=AS"
    caida_url_for_routing_status = "https://api.asrank.caida.org/v2/restful/asns/" # Update: Version 2
    # caida_url_for_routing_status = "http://as-rank.caida.org/api/v1/asns/"
    
    try:
        caida_response = requests.get(caida_url_for_routing_status + str(asn)).json()['data']['asn']
        prefixes = caida_response['cone']['numberPrefixes']
        address_space = caida_response['cone']['numberAddresses']
        neighbor = caida_response['asnDegree']['total']
        name = caida_response['asnName']
    except:
        print("Couldn't get CAIDA response for AS {}".format(asn))
        try:
            ripe_response = requests.get(ripe_url_for_routing_status + str(asn)).json()
            prefixes = ripe_response['data']['announced_space']['v4']['prefixes']
            address_space = ripe_response['data']['announced_space']['v4']['ips']
            neighbor = ripe_response['data']['observed_neighbours']
        except:
            print("Couldn't get RIPE response either for AS {}".format(asn))   
    # print("Leaving get_isp_name_and_prefix_count_and_address_count_and_neighbor_count_from_caida")
    return name, prefixes, address_space, neighbor      
