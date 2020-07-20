import json, os
from .gVars import Output_Directory, scatter_plot_data_file, Sort_Strategy_Names
def find_best_deals(scatter_plot_data=None):
    '''
    This identifies the best pairs using highest felicity_score.
    For each pair, it also suggests top 3 APCs. [Suggests the PoP using PeeringDB data, fac_id/ix_ip, type]
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        data = scatter_plot_data['data']
    
    max_val_pair = dict()
    max_felicity_score = dict()
    sort_type_preferred_by_maximum_isp = dict()
    for s in Sort_Strategy_Names:
        max_felicity_score[s] = 0.0
        sort_type_preferred_by_maximum_isp[s] = 0
    for k, v in data.items():
        for v_item in v:
            sort_type_preferred_for_this_pair = max(v_item['felicity_score'], key=v_item['felicity_score'].get)
            sort_type_preferred_by_maximum_isp[sort_type_preferred_for_this_pair] += 1
            if v_item['ppc_count'] > 1:
                if v_item['isp_a']['name'] == 'ebay' or v_item['isp_b']['name'] == 'ebay':  # 'Ebay' has only 1 common PoP, so we skipped it!
                    continue
                for s in Sort_Strategy_Names:
                    if v_item['felicity_score'][s] > 0:
                        if v_item['felicity_score'][s] > max_felicity_score[s]: 
                            max_felicity_score[s] = v_item['felicity_score'][s]
                            try:
                                max_val_pair[s] = v_item
                            except Exception as _:
                                max_val_pair.update({s:v_item})
    print("===== BEGIN: Maximum Felicity scores in different sorting criteria =====")
    for s in Sort_Strategy_Names:
        print("Max felicity in {} category: {}".format(s, max_val_pair[s]))
        print("This sorting preferred by: {}".format(sort_type_preferred_by_maximum_isp[s]))
    print("===== END: Maximum Felicity scores in different sorting criteria =====")
        
    max_preffered_sort_type = max(sort_type_preferred_by_maximum_isp, key=sort_type_preferred_by_maximum_isp.get)
    
    max_pair_list = []
    for k, v in data.items():
        for v_item in v:
            if v_item['felicity_score'][max_preffered_sort_type] > 0.0 and v_item['willingness_score'][max_preffered_sort_type]<1.0:
                if v_item['isp_a']['name'] != v_item['isp_b']['name']:
                    if max_val_pair[max_preffered_sort_type]['isp_a']['name'] == v_item['isp_a']['name'] or max_val_pair[max_preffered_sort_type]['isp_a']['name'] == v_item['isp_b']['name']:
                        max_pair_list.append([v_item['isp_a']['name'], v_item['isp_b']['name'], v_item['felicity_score'][max_preffered_sort_type]])
    
    max_pair_list_sorted = sorted(max_pair_list, key=lambda x: x[2], reverse=True)
    print("ISP with highest felicity scores and it\'s potential pairs: {}".format(max_pair_list_sorted[:]))
    