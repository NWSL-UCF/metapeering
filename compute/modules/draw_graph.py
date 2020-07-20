import os, math
from .gVars import Sort_Strategy_Names
import matplotlib
import matplotlib.pyplot as plt
# https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
matplotlib.use('Agg')
import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})


def draw_graph(isp_a_asn, isp_b_asn, apc_data, sort_strategy, output_directory_for_isp):
    '''
    @note: This plots the graphs. 
    Plots APC graph of ISP A, B individually and another graph which plots these two as well as the combined APC 
    '''
    output_graph_ppc_id_sorted_filepath = os.path.abspath(output_directory_for_isp + "/" + "graph" + "/" + "ppc_id_sorted") 
    output_graph_willingness_sorted_filepath = os.path.abspath(output_directory_for_isp + "/" + "graph" + "/" + "willingness_sorted") 

    if not os.path.exists(output_graph_ppc_id_sorted_filepath):
        os.makedirs(output_graph_ppc_id_sorted_filepath)
    if not os.path.exists(output_graph_willingness_sorted_filepath):
        os.makedirs(output_graph_willingness_sorted_filepath)
    
    sort_by_ppc_id = False
    color = ['red', 'green', 'blue']
    line_style = [':', (0, (4, 6)), '--']
    
    fig1, ax1 = plt.subplots(figsize=(10,6))
    fig2, ax2 = plt.subplots(figsize=(10,6))
    fig, ax = plt.subplots(figsize=(10,6))
    order = []     
    if sort_by_ppc_id:
        # "order" is required. This will preserve the order for Y-axis as well.
        order = np.argsort(apc_data[apc_data.columns[0]])
        graph_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + "_" + str(isp_b_asn) + ".png")
    else:
        order = np.argsort(apc_data[apc_data.columns[-1]])[::-1]
        graph_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + "_" + str(isp_b_asn) + ".png")
    xs = np.array(apc_data[apc_data.columns[0]], int)[order]
    xs_tick_interval = int(math.ceil(float(len(xs)) / 12))  
    rDegree = 0
    if (len(xs[::xs_tick_interval]) > 10):
        rDegree = 45
    
    for i, j in zip(range(3), apc_data.columns.tolist()[-3:]):
        combined_label = ''

        if("=" in j):
            combined_label = str(isp_a_asn)+','+ str(isp_b_asn)
        elif("A" in j):
            combined_label = str(isp_a_asn)
        else:
            combined_label = str(isp_b_asn)

        ax.plot(np.array(apc_data[j])[order], linestyle=line_style[i], color=color[i], label=combined_label)
        ax.set_xlabel('Acceptable Contract ID')
        ax.set_ylabel('Willingness Score')
        ax.tick_params(axis ='x', rotation = rDegree)

        # These two plots the individual ISPs graphs
        if i == 0:
            if sort_by_ppc_id:               
                ax1.plot(xs, np.array(apc_data[j])[order], linestyle=line_style[i], color=color[i], label=str(isp_a_asn))
                graph_individual_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + ".png")
                ax1.set_xlabel('Acceptable Contract ID')
                ax1.set_ylabel('Willingness Score')
                ax1.tick_params(axis ='x', rotation = rDegree) 
            else:
                order_individual = np.argsort(apc_data[j])[::-1]  # This [::-1] reverses the order and gives the position of items in descending order.
                xs_individual = np.array(apc_data[apc_data.columns[0]], int)[order_individual]
                xs_tick_interval_individual = int(math.ceil(float(len(xs_individual)) / 12))  
                ax1.plot(np.array(apc_data[j])[order_individual], linestyle=line_style[i], color=color[i], label=str(isp_a_asn))
                ax1.set_xticks(range(len(xs_individual))[::xs_tick_interval_individual])
                ax1.set_xticklabels(xs_individual[::xs_tick_interval_individual])
                graph_individual_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_a_asn) + ".png")
                ax1.set_xlabel('Acceptable Contract ID')
                ax1.set_ylabel('Willingness Score')
                ax1.tick_params(axis ='x', rotation = rDegree) 
            ax1.legend()
            fig1.savefig(graph_individual_filename, bbox_inches = "tight")
        if i == 1:
            if sort_by_ppc_id:
                ax2.plot(xs, np.array(apc_data[j])[order], linestyle=line_style[i], color=color[i], label=str(isp_b_asn))
                graph_individual_filename = os.path.abspath(output_graph_ppc_id_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_b_asn) + ".png")
                ax2.set_xlabel('Acceptable Contract ID')
                ax2.set_ylabel('Willingness Score')
                ax2.tick_params(axis ='x', rotation = rDegree) 
            else:
                order_individual = np.argsort(apc_data[j])[::-1]
                xs_individual = np.array(apc_data[apc_data.columns[0]], int)[order_individual]
                xs_tick_interval_individual = int(math.ceil(float(len(xs_individual)) / 12))  
                ax2.plot(np.array(apc_data[j])[order_individual], linestyle=line_style[i], color=color[i], label=str(isp_b_asn))
                ax2.set_xticks(range(len(xs_individual))[::xs_tick_interval_individual])
                ax2.set_xticklabels(xs_individual[::xs_tick_interval_individual])
                graph_individual_filename = os.path.abspath(output_graph_willingness_sorted_filepath + "/" + Sort_Strategy_Names[sort_strategy] + "_" + str(isp_b_asn) + ".png")
                ax2.set_xlabel('Acceptable Contract ID')
                ax2.set_ylabel('Willingness Score')
                ax2.tick_params(axis ='x', rotation = rDegree) 
            ax2.legend()
            fig2.savefig(graph_individual_filename,bbox_inches = "tight")
              
    if not sort_by_ppc_id:
        ax.set_xticks(range(len(xs))[::xs_tick_interval])
        ax.set_xticklabels(xs[::xs_tick_interval])

    ax.legend()
    fig.savefig(graph_filename, bbox_inches = "tight")
    return
