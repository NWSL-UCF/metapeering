'''
Created on Sep 10, 2018

@author: prasun

@bug: 1. Since, we're just looking for city and state names while creating a new PoP location, this prevents us creating multiple PoPs located in the same city.
We should check the name or Lat/Long or whatever in future to fix this.
@note: I think, we've fixed. Need to check.

@attention: We need to add a list of PoPs in each pair of ISPs folder. Otherwise, we don't know the exact location of the PoP IDs,
as those IDs are generated run-time.
'''
#pylint: disable=relative-beyond-top-level
from .modules.gVars import isp_pair_lists #, willingness_score_for_all_isps, affinity_score_for_all_isps, felicity_score_for_all_isps
from .modules.save_pop_locations import save_pop_locations
from .modules.caida_comparison import caida_comparison
from .modules.find_best_deals import find_best_deals
from .modules.draw_brittleness import draw_brittleness
from .modules.draw_scatter_plot import draw_scatter_plot
from .modules.do_work import do_work
from .modules.ensure_isp_json_files import ensure_isp_json_files, ensure_isp_json_files_custom
import json, warnings, sys


warnings.filterwarnings("ignore")

def save_felicity_score_to_file(isp_a_asn, isp_b_asn, felicityScore):
    fileName = "./compute/output/"+str(isp_a_asn)+"_"+str(isp_b_asn)+"/felicity.json"
    with open(fileName, "w") as f:
        json.dump(felicityScore, f)

def getIndvPops(isp_a_asn, isp_b_asn):
    ensure_isp_json_files(('',isp_a_asn),('',isp_b_asn))

    isp_a_pops = []
    with open('./compute/data/cache/'+str(isp_a_asn)+'_peering_db_data_file.json', 'r') as f:
        isp_a_pops = json.load(f)['data']['pop_list']
    isp_b_pops = []
    with open('./compute/data/cache/'+str(isp_b_asn)+'_peering_db_data_file.json', 'r') as f:
        isp_b_pops = json.load(f)['data']['pop_list']

    return isp_a_pops, isp_b_pops

def getCommmonPops(isp_a_asn, isp_b_asn):
    isp_a_pops = []
    isp_b_pops = []

    isp_a_pops, isp_b_pops = getIndvPops(isp_a_asn, isp_b_asn)

    common_pops = []
    count = 0
    for a_pop in isp_a_pops:
        for b_pop in isp_b_pops:
            if (a_pop['isp_id_in_peering_db'] == b_pop['isp_id_in_peering_db']) and (a_pop['isp_type_in_peering_db'] == b_pop['isp_type_in_peering_db']):
                count += 1
                common_pops.append(a_pop)

    return common_pops

def customPeeringAlgo(isp_a, isp_b, pop_list):

    ensure_isp_json_files_custom(isp_a, isp_b)
    # common_pop_list = getCommmonPops(isp_a[1], isp_b[1])

    scatter_plot_data = {"data": {}}
    scatter_plot_data["data"]['access'] = [do_work((isp_a, isp_b), customPoPList=pop_list)]


    draw_scatter_plot(scatter_plot_data)
    # draw_brittleness(scatter_plot_data)
    # caida_comparison(scatter_plot_data)
    save_pop_locations(str(isp_a[1]), str(isp_b[1]))
    # find_best_deals(scatter_plot_data)
    # print("scatter_plot_data--->",scatter_plot_data)
    save_felicity_score_to_file(isp_a[1], isp_b[1], scatter_plot_data["data"]["access"][0]["felicity_score"])
    return True
