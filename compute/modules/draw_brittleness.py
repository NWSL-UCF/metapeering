import os, json
from .gVars import Output_Directory, scatter_plot_data_file, Sort_Strategy_Names, Max_Common_Pop_Count, beta_w_for_content_related
from .gVars import beta_w, weight_w, weight_a, beta_a, weight_w_for_content_related, beta_a_for_content_related, weight_a_for_content_related

import matplotlib
import matplotlib.pyplot as plt
# https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
matplotlib.use('Agg')

import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})

from scipy import stats

def draw_brittleness(scatter_plot_data=None):
    '''
    @note: Reads the JSON file or draw from the output of main() and plots a scatter plot 
    @note: We use similarity_score[0].keys() to populate all the similarity criteria names. 
    We can manually list the names, but that may cause typo in future if we change the names.
    @note: sorting_type are actually the Sort_Strategy_Names. So we use that list.
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'w')
        json.dump(scatter_plot_data, file_for_saving_scatter_plot_data)
        data = scatter_plot_data['data']
    file_for_saving_scatter_plot_data.close()
    
    ### Here we update the beta scores (weights) to see how willingness_score and affinity_score impacts the ultimate felicity_score.
    for k, v in data.items():
        for i in range(len(v)):         
            w = data[k][i]['willingness_score']
            a = data[k][i]['affinity_score']
            for sort_type in Sort_Strategy_Names:
                if w[sort_type] > 0:
                    if 'content' in k:
                        data[k][i]['felicity_score'][sort_type] = ((beta_w_for_content_related * w[sort_type])**weight_w_for_content_related * (beta_a_for_content_related * a[sort_type])**weight_a_for_content_related) ** (1.0/(weight_w_for_content_related + weight_a_for_content_related))
                    else:
                        data[k][i]['felicity_score'][sort_type] = ((beta_w * w[sort_type])**weight_w * (beta_a * a[sort_type])**weight_a) ** (1.0/(weight_w + weight_a))
    
    felicity_score = []
    similarity_score = []
    max_diff = max_own = max_ratio = 0.0
    max_pair = {}
    for k, v in data.items():
        for i in v:
            if 1 in i['felicity_score'].values():
                print(i['isp_a']['name'], i['isp_a']['asn'], i['isp_b']['name'], i['isp_b']['asn'])
            for b, a in i['felicity_score'].items():
                if a < 0 and a != -1:
                    print('< 0 for ISP A: {}, ASN: {}, ISP B: {}, ASN: {}, Felicity_score: {} in sort category: {}'.format(i['isp_a']['name'], i['isp_a']['asn'], i['isp_b']['name'], i['isp_b']['asn'], a, b))
                elif a == 0:
                    print('= 0 for ISP A: {}, ASN: {}, ISP B: {}, ASN: {}'.format(i['isp_a']['name'], i['isp_a']['asn'], i['isp_b']['name'], i['isp_b']['asn']))
            if sum([y for x, y in i['felicity_score'].items()]) == -3:
                continue
            else:
                if i['felicity_score']['diff'] > max_diff and i['apc_count'] > 1:
                    max_diff = i['felicity_score']['diff']
                    max_pair['diff'] = i
                if i['felicity_score']['own'] > max_own and i['apc_count'] > 1:
                    max_own = i['felicity_score']['own']
                    max_pair['own'] = i
                if i['felicity_score']['ratio'] > max_ratio and i['apc_count'] > 1:
                    max_ratio = i['felicity_score']['ratio']
                    max_pair['ratio'] = i
                felicity_score.append(i['felicity_score'])
                similarity_score.append(i['similarity_score'])
      
    print("=========================== Print peering pairs status =================")
    peering_status_count_dict = {}
    fig1, axarr_for_content_pairs_check = plt.subplots(2, 3, sharey=True, squeeze=False)
    for k, v in data.items():
        if 'content' in k:
            similarity_prefix_x_axis = [c_v_items['similarity_score']['based_on_prefix'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_ip_address_x_axis = [c_v_items['similarity_score']['based_on_address'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_pop_count_x_axis = [c_v_items['similarity_score']['based_on_pop'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            content_y_axis =[c_v_items['felicity_score']['diff'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
        else:
            similarity_prefix_x_axis = [c_v_items['similarity_score']['based_on_prefix'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_ip_address_x_axis = [c_v_items['similarity_score']['based_on_address'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            similarity_pop_count_x_axis = [c_v_items['similarity_score']['based_on_pop'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
            content_y_axis =[c_v_items['felicity_score']['diff'] for c_v_items in v if 0.0 < c_v_items['felicity_score']['diff'] and c_v_items['felicity_score']['diff'] < 0.1]
        for i, similarity_list_j in zip(range(3), [similarity_prefix_x_axis, similarity_ip_address_x_axis, similarity_pop_count_x_axis]):
            if 'content' in k:
                axarr_for_content_pairs_check[0][i].scatter(similarity_list_j, content_y_axis, s=1, label=k)
            else:
                axarr_for_content_pairs_check[1][i].scatter(similarity_list_j, content_y_axis, s=1, label=k)
            
        peering_status_count_dict[k] = {}
        ## We use 'ratio' as the only sort_type because we found that all the other sort_type produce the exact same results. We don't need to run a loop for three times to get similar values.
        sort_type = 'ratio'
        count_below_zero = 0
        count_zero = 0
        count_between_zero_and_point_zero_one = 0
        count_beyond = 0
        count_others = 0
        for v_items in v:
            if v_items['felicity_score'][sort_type] < 0:
                count_below_zero += 1
            elif v_items['felicity_score'][sort_type] == 0:
                count_zero += 1
            elif 0 < v_items['felicity_score'][sort_type] and v_items['felicity_score'][sort_type] < 0.01:
                count_between_zero_and_point_zero_one += 1
            elif v_items['felicity_score'][sort_type] >= 0.01:
                count_beyond += 1
            else:
                count_others += 1
        peering_status_count_dict[k].update({sort_type : {'< 0:': count_below_zero, '= 0:': count_zero, '0 < count < 0.0.1: ':count_between_zero_and_point_zero_one, '>= 0.01': count_beyond, 'others: ': count_others}})
    
    for k, v in peering_status_count_dict.items():
        print(k)
        for v_items in v:
            print("\n".join("{}\t".format(v) for _, v in v.items())) 
      
    plt.subplots_adjust(right=0.7)
    for i, similar_type_name in zip(range(3), ['based_on_prefix', 'based_on_address', 'based_on_pop']):
        axarr_for_content_pairs_check[1][i].set_xlabel(similar_type_name)
    axarr_for_content_pairs_check[0][2].legend(bbox_to_anchor=(2.6,1.05), loc='upper right')          
    axarr_for_content_pairs_check[1][2].legend(bbox_to_anchor=(2.53,1.045), loc='upper right')          
    fig1.savefig(os.path.abspath(Output_Directory + "/" + "Content_vs_non_content_felicity_" + str(Max_Common_Pop_Count) + ".png"))
    print("=========================== END: Print peering pairs status =================")
              
    print("=================")
    print("Highest felicity score pairs: {}".format(max_pair))
    print("=================")
    similarity_criteria_list = similarity_score[0].keys()
    brittleness_color_list = ['r', 'g', 'b']
    brittleness_marker_list = ['<', '>', '^']
  
    fig, axarr = plt.subplots(2, 3, sharey=True, squeeze=False)
    temp_list_for_0_felicity_score_isps_pair = []
    for i, similarity_type in zip(range(3), similarity_criteria_list):
        for sorting_type, brittleness_color, brittleness_marker in zip(Sort_Strategy_Names, brittleness_color_list, brittleness_marker_list):
            x_axis_values_for_content_related_only = []
            y_axis_values_for_content_related_only = []
            x_axis_values_for_others = []
            y_axis_values_for_others = []
            no_felicity_score_for_this_sorting_type_count = 0
            min_pair = {}
            min_value = 10.0
            for k, v in data.items():
                for v_items in v:
                    if v_items['felicity_score'][sorting_type] > 0.0:
                        if 'content' in k:
                            x_axis_values_for_content_related_only.append(v_items['similarity_score'][similarity_type])
                            y_axis_values_for_content_related_only.append(v_items['felicity_score'][sorting_type])
                        else:
                            x_axis_values_for_others.append(v_items['similarity_score'][similarity_type])
                            y_axis_values_for_others.append(v_items['felicity_score'][sorting_type])
                            if v_items['felicity_score'][sorting_type] < min_value:
                                min_pair = v_items
                                min_value = v_items['felicity_score'][sorting_type]
                    else:
                        temp_list_for_0_felicity_score_isps_pair.append((v_items['isp_a']['name'], v_items['isp_b']['name'], sorting_type))
                        no_felicity_score_for_this_sorting_type_count += 1
            print("MIN PAIR: ",min_pair)
            print("In sorting type {} and similarity type {}, Min (>0) felicity score: {} between {} and {}".format(sorting_type, similarity_type, min_pair['felicity_score'][sorting_type], min_pair['isp_a']['name'], min_pair['isp_b']['name']))
            axarr[0,i].scatter(x_axis_values_for_content_related_only, y_axis_values_for_content_related_only, marker=brittleness_marker, color=brittleness_color, facecolor='none', s=1, label=sorting_type)
            axarr[1,i].scatter(x_axis_values_for_others, y_axis_values_for_others, marker=brittleness_marker, color=brittleness_color, facecolor='none', s=1, label=sorting_type)
             
            # Trend line using scipy
            x_axis_values_for_content_related_only = np.array(x_axis_values_for_content_related_only) 
            y_axis_values_for_content_related_only = np.array(y_axis_values_for_content_related_only)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_content_related_only, y_axis_values_for_content_related_only)
            print("R-squared: {}, P-value: {} for sort_type: {} in similarity_type: {}".format(r_value**2, p_value, sorting_type, similarity_type))
            axarr[0,i].plot(x_axis_values_for_content_related_only, intercept + slope*x_axis_values_for_content_related_only, color=brittleness_color, linestyle='-', linewidth=0.5)
 
            x_axis_values_for_others = np.array(x_axis_values_for_others) 
            y_axis_values_for_others = np.array(y_axis_values_for_others)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_others, y_axis_values_for_others)
            print("R-squared: {}, P-value: {} for sort_type: {} in similarity_type: {}".format(r_value**2, p_value, sorting_type, similarity_type))
            axarr[1,i].plot(x_axis_values_for_others, intercept + slope*x_axis_values_for_others, color=brittleness_color, linestyle='-', linewidth=0.5)
  
            print("No felicity score for {} similarity type based on {} is: {}".format(similarity_type, sorting_type, no_felicity_score_for_this_sorting_type_count))
            # Specify the position of legend. bbox_to_anchor is the reference point and upper_left means it's the upper left corner of the legend box. 
            # https://stackoverflow.com/questions/44413020/how-to-specify-legend-position-in-matplotlib-in-graph-coordinates
            l0 = axarr[0,i].legend()
            l1 = axarr[1,i].legend()
            axarr[1,i].set_xlabel(similarity_type.split("_")[-1] + " " + "count")
        for handler in l0.legendHandles:
            handler.set_sizes([18.0])
        for handler in l1.legendHandles:
            handler.set_sizes([18.0])
    print("----Print the ISPs pair who have 0 Felicity score in some sort strategy----")
    print(temp_list_for_0_felicity_score_isps_pair)
    print("----0 Felicity score printing ended----")
    axarr[0,0].set_ylabel('at least one is Content')
    axarr[1,0].set_ylabel('other ISP pairs')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.14, left=0.125)
    fig.text(0.03, 0.73, 'Felicity scores for ISP pairs', rotation='vertical', ha='center')
    fig.text(0.53, 0.02, 'Similarity score based on', ha='center')
      
    fig.savefig(os.path.abspath(Output_Directory + "/" + "felicity_" + str(Max_Common_Pop_Count) + ".png"))
  