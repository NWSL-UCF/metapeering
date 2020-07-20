import requests, time

def get_total_prefixes_addresses_count_from_caida():
    # print("Entering get_total_prefixes_addresses_count_from_caida")
    '''
    @return: summation of prefixes count of all the organizations
    @return: summation of addresses count
    '''
    caida_api = "https://api.asrank.caida.org/v2/restful/organizations?populate=1"
    prefixes_count = 0
    address_count = 0

    while prefixes_count == 0:
        # try:
        caida_response = requests.get(caida_api).json()
        caida_response = caida_response['data']['organizations']['edges']
        for org_ in caida_response:
            try:
                prefixes_count += org_['node']['cone']['numberPrefixes']
            except:
                print('Could not find prefix information for organization: {}, organization id in CAIDA: {}'.format(org_['node']['orgName'], org_['node']['orgId']))
                print(org_)
            try:
                address_count += org_['node']['cone']['numberAddresses']
            except:
                print('Could not find address information for organization: {}, organization id in CAIDA: {}'.format(org_['node']['orgName'], org_['node']['orgId']))
        # except Exception as e:
        #     print(e)
        #     time.sleep(3)
    # print("Leaving get_total_prefixes_addresses_count_from_caida")
    return prefixes_count, address_count
