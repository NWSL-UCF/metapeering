from .gVars import Data_Directory, Output_Directory, scatter_plot_data_file, Sort_Strategy_Names, Max_Common_Pop_Count
import json
import os
import matplotlib
import matplotlib.pyplot as plt
# https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
matplotlib.use('Agg')

def caida_comparison(scatter_plot_data=None):
    '''
    @note: Reads the JSON file or from the output of main() and compare with CAIDA data. 
    If match is found, plots YES, otherwise NO.
    @note: '20190601.as-rel' and '201603.as-rel-geo' are two options for matching. 
    Source URL: http://data.caida.org/datasets/2013-asrank-data-supplement/data/
    1st shows provider2customer or peer2peer relations, 2nd one shows peering location data.
    We use 1st one, as this is latest and only considers the peering locations.
    @note: In CAIDA, smallest number ASN always comes first in the pair. So, we searched by the smallest of ISP A and ISP B.
    If match found for (A or B), we then checked if other is in the list of that ISPs peers.
    @note: willingness_type are actually the Sort_Strategy_Names. So we use that list.
    @note: It appears, some ISPs peer outside US, so CAIDA lists them, but as we don't use any PoPs outside US, we set their
    willingness score to -1. The figure looks bad! To avoid this, we don't plot -1 in figure and just list those ISPs pair later.
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'w')
        json.dump(scatter_plot_data, file_for_saving_scatter_plot_data)
        data = scatter_plot_data['data']
    file_for_saving_scatter_plot_data.close()
    caida_data = dict()
    with open(os.path.abspath(Data_Directory + "/" + "20190601.as-rel.txt"), 'r') as fin:
        f_lines = fin.readlines()
        for l in f_lines:
            if l[0] == '#':
                continue
            l = l.strip().split("|")
            if l[-1] == '0':
                try:
                    caida_data[int(l[0])].append(int(l[1]))
                except Exception as _:
                    caida_data[int(l[0])] = [int(l[1])]
        fin.close()

    asn_keys = caida_data.keys()
    pair_match_dict = {}
    no_pair_match_dict = {}

    

    for k, v in data.items():
        pair_match_with_caida_in_isp_type = 0
        pair_match_asn_list = []
        no_pair_match_asn_list = []
        for v_item in v:
            isp_a_asn = v_item['isp_a']['asn']
            isp_b_asn = v_item['isp_b']['asn']
            if isp_a_asn < isp_b_asn:
                if isp_a_asn in asn_keys:
                    if isp_b_asn in caida_data[isp_a_asn]:
                        pair_match_asn_list.append(v_item)
                        pair_match_with_caida_in_isp_type += 1
                        if sum(v_item['felicity_score'].values()) == -3:
                            print('ISP pairs with felicity score -1: [{}({}), {}({})]'.format(v_item['isp_a']['name'], isp_a_asn, v_item['isp_b']['name'], isp_b_asn))
                    else:
                        no_pair_match_asn_list.append(v_item)
                else:
                    no_pair_match_asn_list.append(v_item)
            else:
                if isp_b_asn in asn_keys:
                    if isp_a_asn in caida_data[isp_b_asn]:
                        pair_match_asn_list.append(v_item)
                        pair_match_with_caida_in_isp_type += 1
                        if sum(v_item['felicity_score'].values()) == -3:
                            print('ISP pairs with felicity score -1: [{}({}), {}({})]'.format(v_item['isp_a']['name'], isp_a_asn, v_item['isp_b']['name'], isp_b_asn))
                    else:
                        no_pair_match_asn_list.append(v_item)
                else:
                    no_pair_match_asn_list.append(v_item)
        print("Total ISPs pair in {} for {} category. Peering in CAIDA: {}, Not peering according to CAIDA (may include our suggested): {}".format(len(v), k, len(pair_match_asn_list), len(no_pair_match_asn_list)))        
        pair_match_dict[k] = pair_match_asn_list
        no_pair_match_dict[k] = no_pair_match_asn_list
    
    print("===== BEGIN: ISP pairs comparison with CAIDA=======")
    for k in pair_match_dict.keys():
        print("{} has {} potential pairs. Among them".format(k, len(data[k])))
        v = pair_match_dict[k]
        our_suggestion = [y for y in v if sum(y['felicity_score'].values()) > 0.0]
        print("======>>>>>>")
        print("Our suggested list of ISP pairs: {}".format(our_suggestion))
        print("======>>>>>>")
        not_recommended = [y for y in v if sum(y['felicity_score'].values()) <= 0.0] 
        print("peering in CAIDA: {}, we suggest correctly: {}, we don't suggest: {}".format(len(v), len(our_suggestion), len(not_recommended)))
        if len(not_recommended) > 0:
            print("Our not recommended list: {}".format([(not_recommended_pair['isp_a']['name'], not_recommended_pair['isp_b']['name'], not_recommended_pair['apc_count'], not_recommended_pair['felicity_score']) for not_recommended_pair in not_recommended]))
        v = no_pair_match_dict[k]
        our_suggestion = [y for y in v if sum(y['felicity_score'].values()) > 0.0]
        not_recommended = [y for y in v if sum(y['felicity_score'].values()) <= 0.0]
        print("not peering yet but we suggest: {}, and we don't suggest: {}".format(len(our_suggestion), len(not_recommended)))
    print("===== END: ISP pairs comparison with CAIDA=======")
    fig, axarr = plt.subplots(nrows=3, ncols=1, sharex=True)
    for i, willingness_type in zip(range(3), Sort_Strategy_Names):
        peer_in_caida_x = [y['felicity_score'][willingness_type] for v in pair_match_dict.values() for y in v if sum(y['felicity_score'].values()) > 0]
        axarr[i].scatter(peer_in_caida_x, [0.75 for _ in peer_in_caida_x], s = 3, color='r', label=willingness_type)
        not_peer_in_caida_but_we_suggest_x = [y['felicity_score'][willingness_type] for v in no_pair_match_dict.values() for y in v if sum(y['felicity_score'].values()) > 0]
        axarr[i].scatter(not_peer_in_caida_but_we_suggest_x, [0.25 for _ in not_peer_in_caida_but_we_suggest_x], s = 3, color='g')
        print("Sort type: {}: peering in CAIDA: {}, Not peering, but we suggest: {}".format(willingness_type, len(peer_in_caida_x), len(not_peer_in_caida_but_we_suggest_x)))
        axarr[i].set_ylim([0, 1])
        axarr[i].set_yticks([0.25, 0.75])
        axarr[i].set_yticklabels(('S', 'E')) # Suggested or Established
        axarr[i].legend(loc=5,handlelength=0,markerscale=0)
    
    ##########################################################################################
    '''
    @author: Shahzeb
    Saving pair_match_dict and no_pair_match_dict to a file
    '''
    with open('./compute/output/caida_comparison.json', 'w') as f:
        data_to_write = {'pair_match':pair_match_dict, 'no_pair_match': no_pair_match_dict}
        json.dump(data_to_write, f)

    ##########################################################################################
    fig.add_subplot(111,frameon=False)
    plt.tick_params(labelcolor='none',top=False,left=False,right=False,bottom=False)
    plt.xlabel('Felicity scores')  
    plt.ylabel('Peering status (E: Already established, S: Suggested)')
    fig.savefig(os.path.abspath(Output_Directory + "/" + "CAIDA_felicity_match_" + str(Max_Common_Pop_Count) + ".png"))
    return