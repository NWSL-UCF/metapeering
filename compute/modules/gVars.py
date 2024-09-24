import os, json, itertools



isp_dict = {'access': {'cableone': 11492, 'centurylink': 209, 'charter':7843, 'comcast':7922, 'cox':22773, 'tds':4181, 'windstream':7029, },
                'content': {'akamai':20940, 'amazon': 16509, 'ebay':62955, 'facebook': 32934, 'google': 15169, 'microsoft': 8075, 'netflix': 2906, },
                'transit': {'columbus':23520, 'cogent': 174, 'he':6939, 'ntt': 2914, 'pccw':3491, 'sprint': 1239, 'verizon':701, 'zayo':6461, }}  
# isp_dict = {'access': {'cableone': 11492},
#                 'content': {'akamai':20940},
#                 'transit': {'columbus':23520}}
# already_calculated_isp_combination = []

# These are combined list. We may need to check the content-access, content-transit, transit-access (opposite combination) as well.
isp_pair_lists = {}
isp_pair_lists['access'] = list(itertools.permutations(isp_dict['access'].items(), 2))
isp_pair_lists['content'] = list(itertools.permutations(isp_dict['content'].items(), 2))
isp_pair_lists['transit'] = list(itertools.permutations(isp_dict['transit'].items(), 2))
isp_pair_lists['access-content'] = [((name_a, asn_a), (name_c, asn_c)) for name_a,
                                            asn_a in isp_dict['access'].items() for name_c, asn_c in isp_dict['content'].items()]
isp_pair_lists['content-access'] = [((name_a, asn_a), (name_c, asn_c)) for name_a,
                                            asn_a in isp_dict['content'].items() for name_c, asn_c in isp_dict['access'].items()]
isp_pair_lists['access-transit'] = [((name_a, asn_a), (name_t, asn_t)) for name_a,
                                            asn_a in isp_dict['access'].items() for name_t, asn_t in isp_dict['transit'].items()]
isp_pair_lists['transit-access'] = [((name_a, asn_a), (name_t, asn_t)) for name_a,
                                            asn_a in isp_dict['transit'].items() for name_t, asn_t in isp_dict['access'].items()]
isp_pair_lists['transit-content'] = [((name_t, asn_t), (name_c, asn_c)) for name_t,
                                                asn_t in isp_dict['transit'].items() for name_c, asn_c in isp_dict['content'].items()]
isp_pair_lists['content-transit'] = [((name_t, asn_t), (name_c, asn_c)) for name_t,
                                                asn_t in isp_dict['content'].items() for name_c, asn_c in isp_dict['transit'].items()]


List_Of_POP_Locations = []
SORT_STRATEGY_DIFF = 0
SORT_STRATEGY_OWN = 1
SORT_STRATEGY_RATIO = 2
Sort_Strategy_Names = ['diff', 'own', 'ratio']
traffic_ratio_dict = {0: "NOT DISCLOSED", 1: "HEAVY INBOUND", 2: "MOSTLY INBOUND", 3: "BALANCED", 4: "MOSTLY OUTBOUND", 5: "HEAVY OUTBOUND"} # TODO!!!!!!!!!
traffic_ratio_min_max = {"HEAVY INBOUND": ['1_9'], "MOSTLY INBOUND": ['1_6'], "BALANCED": ['1_3', '3_1'], "MOSTLY OUTBOUND": ['6_1'], "HEAVY OUTBOUND": ['9_1']}
# traffic_ratio_min_max = {"HEAVY INBOUND": ['1_7'], "MOSTLY INBOUND": ['1_4', '1_6'], "BALANCED": ['1_3', '3_1'], "MOSTLY OUTBOUND": ['4_1', '6_1'], "HEAVY OUTBOUND": ['7_1']}

internet_usage_per_person = 0.01372 # in MB/s

Max_Process_To_Be_Used = 8
Max_Common_Pop_Count = 15

geometric_mean_without_any_weight = True
if geometric_mean_without_any_weight:
    # Geometric mean, no weight factors, nothing.
    beta_w_for_content_related = 1 
    beta_a_for_content_related = 1 
    beta_w = 1
    beta_a = 1
    weight_w_for_content_related = weight_a_for_content_related = 1
    weight_w = weight_a = 1 
else:
    # Adding weight to willingness and affinity
    beta_weight_for_content_related = 0.1
    beta_w_for_content_related = beta_weight_for_content_related
    beta_a_for_content_related = 1 - beta_weight_for_content_related
    # Weighted geometric mean for content related ISPs
    weight_w_for_content_related = 98
    weight_a_for_content_related = 23
    # Adding weight to willingness and affinity
    beta_weight = 0.1
    beta_w = beta_weight
    beta_a = 1 - beta_weight
    # Weighted geometric mean
    weight_w = 98
    weight_a = 23

Output_Directory = os.path.abspath(os.path.dirname('./compute/')) + "/" + "output"
Data_Directory = os.path.abspath(os.path.dirname('./compute/')) + "/" + "modules/ML/compute/data"

if not os.path.exists(Output_Directory):
    os.mkdir(Output_Directory)
scatter_plot_data_file = "scatter_plot_data_" + str(Max_Common_Pop_Count) + ".json"

########################################################################################
#Additions by Shahzeb
# exclusing from the custom peering querry, too much ram consumption!
# isp_data = {}
# for f in os.listdir('./compute/data'):
#     if 'peering_db_data_file' in f:
#         with open('./compute/data/'+f, 'r') as i:
#             isp_data[f.replace('_peering_db_data_file.json','')] = json.load(i)

willingness_score_for_all_isps = {}
affinity_score_for_all_isps = {}
felicity_score_for_all_isps = {}

########################################################################################

isp_pops = {}
with open('./compute/data/population_coverage.json', 'r') as f:
    isp_pops = json.load(f)

  