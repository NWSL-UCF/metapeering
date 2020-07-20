import json, os
from .gVars import Output_Directory, scatter_plot_data_file, Max_Common_Pop_Count, Sort_Strategy_Names
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt
# https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
matplotlib.use('Agg')
import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})


def draw_scatter_plot(scatter_plot_data=None):
    '''
    This is now will be called always to draw the plot and save the JSON file.
    Plots the scatter graph. Depending on whether the JSON file exists or not, it creates or reads from the file.
    '''
    if scatter_plot_data == None:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
        data = json.load(file_for_saving_scatter_plot_data)['data']
    else:
        file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'w')
        json.dump(scatter_plot_data, file_for_saving_scatter_plot_data)
        data = scatter_plot_data['data']
    file_for_saving_scatter_plot_data.close()
    
#     print("="*50)
#     print("Printing Felicity and Similarity scores for ISP pairs who have s_score > 0.4 but at least of of the f_score < 0.2")
#     for pair_type, pair_list in data.items():
#         if pair_type not in ['access', 'content', 'transit', 'transit-access', 'access-transit']:
#             continue
#         for k in pair_list:
#             f_score = k['felicity_score']
#             s_score = k['similarity_score']
#             if max([s_score['based_on_prefix'], s_score['based_on_address']]) > 0.4:
#                 if max(f_score.values()) < 0.2:
#                     print(pair_type, k['isp_a']['name'], k['isp_b']['name'], f_score, s_score)
#     print("="*50)
        
    fig, axarr = plt.subplots(3, 3, sharex=True, sharey=True, gridspec_kw={'hspace':0.1, 'wspace':0.1})
    subplot_position = {'access':(0, 0), 'content':(1, 1), 'transit':(2, 2), 'access-content':(0, 1), 'access-transit':(0, 2), 'content-access':(1, 0), 'content-transit':(1, 2), 'transit-access':(2, 0), 'transit-content':(2, 1)} 

    for k, result in data.items():
        k = str(k)
        (subplot_pos_x, subplot_pos_y) = subplot_position[k]
        # print("RESLUT---->",result)
        axarr[subplot_pos_x][subplot_pos_y].scatter([item['ppc_count'] for item in result if item['ppc_count'] != 0], [item['apc_count'] for item in result if item['ppc_count'] != 0], marker='o', color='b', facecolors='none')
    axarr[2][0].set_xlabel('Access')
    axarr[2][1].set_xlabel('Content')
    axarr[2][2].set_xlabel('Transit')
    axarr[0][0].set_ylabel('Access')
    axarr[1][0].set_ylabel('Content')
    axarr[2][0].set_ylabel('Transit')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.16, left=0.16)
    for_outside_x_y_label = fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none',top=False,left=False,right=False,bottom=False)
    for_outside_x_y_label.set_xlabel('Possible peering contracts count')
    plt.ylabel('Acceptable peering contracts count')
    for_outside_x_y_label.xaxis.labelpad = 15
    for_outside_x_y_label.yaxis.labelpad = 35
    
    fig.savefig(os.path.abspath(Output_Directory + "/" + "isp_pair_apc_" + str(Max_Common_Pop_Count) + ".png"))
    
# def helping_tool_get_max_r_squared_weights(scatter_plot_data=None):
#     '''
#     @note: Reads the JSON file or the JSON output of main() and identifies the max weight factors for beta_weight, weight_w, weight_a
#     for the maximum r-squared value. Which we then use for setting up the values manually.
#     This is dedicately a helping tool and can't be run to optimize the weights directly. And, these weights do not impact the APCs at all.
#     These weights can be used only for identifying the best pair with "willingness_score" and "affinity_score"
#     '''
#     if scatter_plot_data == None:
#         file_for_saving_scatter_plot_data = open(os.path.abspath(Output_Directory + "/" + scatter_plot_data_file), 'r')
#         data = json.load(file_for_saving_scatter_plot_data)['data']
#         file_for_saving_scatter_plot_data.close()
#     else:
#         data = scatter_plot_data['data']
    
#     max_r_squared_val_content_related = 0.0
#     max_r_squared_val_others = 0.0
#     max_beta_weight = max_beta_weight_for_content_related = 0.0
#     max_weight_w = max_weight_w_for_content_related = 0 
#     max_weight_a = max_weight_a_for_content_related = 0
    
#     for beta_w_i in range(1,10):
#         beta_weight = beta_weight_for_content_related = beta_w_i / 10.0
#         beta_w_for_content_related = beta_weight_for_content_related
#         beta_a_for_content_related = 1 - beta_weight_for_content_related
#         beta_w = beta_weight
#         beta_a = 1 - beta_weight
        
#         weight_max_value_for_loop = 500
#         for weight_w_i in range(1, weight_max_value_for_loop):
#             weight_w = weight_w_for_content_related = weight_w_i
#             for weight_a_i in range(1, weight_max_value_for_loop):
#                 weight_a = weight_a_for_content_related = weight_a_i
#                 for k, v in data.items():
#                     for i in range(len(v)):         
#                         w = data[k][i]['willingness_score']
#                         a = data[k][i]['affinity_score']
#                         for sort_type in Sort_Strategy_Names:
#                             if w[sort_type] > 0:
#                                 if 'content' in k:
#                                     data[k][i]['felicity_score'][sort_type] = ((beta_w_for_content_related * w[sort_type])**weight_w_for_content_related * (beta_a_for_content_related * a[sort_type])**weight_a_for_content_related) ** (1.0/(weight_w_for_content_related + weight_a_for_content_related))
#                                 else:
#                                     data[k][i]['felicity_score'][sort_type] = ((beta_w * w[sort_type])**weight_w * (beta_a * a[sort_type])**weight_a) ** (1.0/(weight_w + weight_a))

#                 for similarity_type in ['based_on_prefix', 'based_on_address', 'based_on_pop']:
#                     for sorting_type in Sort_Strategy_Names:
#                         x_axis_values_for_content_related_only = []
#                         y_axis_values_for_content_related_only = []
#                         x_axis_values_for_others = []
#                         y_axis_values_for_others = []
#                         no_felicity_score_for_this_sorting_type_count = 0
#                         min_pair = {}
#                         min_value = 10.0
#                         for k, v in data.items():
#                             for v_items in v:
#                                 if v_items['felicity_score'][sorting_type] > 0.0:
#                                     if 'content' in k:
#                                         x_axis_values_for_content_related_only.append(v_items['similarity_score'][similarity_type])
#                                         y_axis_values_for_content_related_only.append(v_items['felicity_score'][sorting_type])
#                                     else:
#                                         x_axis_values_for_others.append(v_items['similarity_score'][similarity_type])
#                                         y_axis_values_for_others.append(v_items['felicity_score'][sorting_type])
#                                         if v_items['felicity_score'][sorting_type] < min_value:
#                                             min_pair = v_items
#                                             min_value = v_items['felicity_score'][sorting_type]
#                                 else:
#                                     no_felicity_score_for_this_sorting_type_count += 1
                        
#                         if len(x_axis_values_for_content_related_only) > 0:
#                             # Trend line using scipy
#                             x_axis_values_for_content_related_only = np.array(x_axis_values_for_content_related_only) 
#                             y_axis_values_for_content_related_only = np.array(y_axis_values_for_content_related_only)
#                             try:
#                                 slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_content_related_only, y_axis_values_for_content_related_only)
                            
#                                 if r_value**2 > max_r_squared_val_content_related:
#                                     max_r_squared_val_content_related = r_value**2
#                                     max_beta_weight_for_content_related = beta_weight_for_content_related
#                                     max_weight_w_for_content_related = weight_w_for_content_related
#                                     max_weight_a_for_content_related = weight_a_for_content_related
#                             except Exception as e:
#                                 print(e)
                                
#                             x_axis_values_for_others = np.array(x_axis_values_for_others) 
#                             y_axis_values_for_others = np.array(y_axis_values_for_others)
                            
#                             try:
#                                 slope, intercept, r_value, p_value, std_err = stats.linregress(x_axis_values_for_others, y_axis_values_for_others)
    
#                                 if r_value**2 > max_r_squared_val_others:
#                                     max_r_squared_val_others = r_value**2
#                                     max_beta_weight = beta_weight
#                                     max_weight_w = weight_w
#                                     max_weight_a = weight_a
#                             except Exception as e:
#                                 print(e)
    
#     print("For Content related: Max R-squared: {}, max beta_weight: {}, max weight_w: {}, max weight_a: {}".format(max_r_squared_val_content_related, max_beta_weight_for_content_related, max_weight_w_for_content_related, max_weight_a_for_content_related))
#     print("For Others related: Max R-squared: {}, max beta_weight: {}, max weight_w: {}, max weight_a: {}".format(max_r_squared_val_others, max_beta_weight, max_weight_w, max_weight_a))
    