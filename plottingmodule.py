'''
Created on Jan 3, 2019

@author: prasun
'''
# Libraries
import matplotlib.pyplot as plt
from matplotlib.colorbar import ColorbarBase
from matplotlib import gridspec
# import os, xlrd
import os
import pandas as pd
import numpy as np


def pie_plot_traffic_ratio():
     
    # Make data: I have 3 groups and 7 subgroups
    group_names = ['Access', 'Content', 'Transit', 'Others']
    subgroup_names = ['Heavily \nOutbound', 'Mostly \nOutbound', 'Balanced', 'Mostly \nInbound', 'Heavy \nInbound', 'Not \nDisclosed']
    
    subgroup_size_for_only_us_and_global = [190, 406, 718, 240, 47, 164,
                   46, 173, 696, 426, 115, 178,
                   181, 338, 568, 317, 99, 168,
                   23, 67, 258, 99, 17, 118]
#     # This is following are total ISPs in PeeringDB.
#     subgroup_size_globally = [82, 227, 1529, 2308, 607, 711, 
#                      327, 747, 434, 44, 12, 101,
#                      51, 291, 1134, 663, 109, 213,
#                      63, 220, 904, 459, 84, 3758]

    # This is for easiness to set the threshold!
    us_and_global_only = True
    if us_and_global_only:
        subgroup_size = subgroup_size_for_only_us_and_global
    else:
        subgroup_size = subgroup_size_globally

    group_size = [sum(subgroup_size[i:i+6]) for i in range(0, len(subgroup_size), 6)]

    subgroup_size = subgroup_size[:-6]
    subgroup_size.append(group_size[-1])
    
    subgroup_labels = []
    for i in range(len(group_size) - 1):
        for j in range(6):
            val = subgroup_size[i * 6 + j]
            if us_and_global_only: 
                if val > 50:
                    subgroup_labels.append("{:.2f}%".format((val * 100.) / group_size[i])) 
                else:
                    subgroup_labels.append('')
            else:
                if val > 300:
                    subgroup_labels.append("{:.2f}%".format((val * 100.) / group_size[i])) 
                else:
                    subgroup_labels.append('')
    subgroup_labels.append('')
    print(subgroup_labels)
     
    # Create colors
    a, b, c, d = [plt.cm.Reds, plt.cm.Greens, plt.cm.Blues, plt.cm.Purples]
      
    # First Ring (outside)
    fig, ax = plt.subplots()
    ax.axis('equal')
    # mypie, _ = ax.pie(group_size, radius=1.3, labels=group_names, colors=[a(0.8), b(0.8), c(0.8)] )
    mypie, _ = ax.pie(group_size, radius=0.5, labels=group_size, labeldistance=0.5, colors=[a(0.8), b(0.8), c(0.8), d(0.8)])
    plt.setp(mypie, width=0.35, edgecolor='white')
      
    # For angling the text!
    # https://stackoverflow.com/questions/52020474/matplotlib-pie-chart-how-to-center-label
    # Second Ring (Outside)
    mypie2, _ = ax.pie(subgroup_size, radius=1, labels=subgroup_labels, labeldistance=0.57, rotatelabels=True, colors=[a(0.7), a(0.6), a(0.5), a(0.4), a(0.3), a(0.2), b(0.7), b(0.6), b(0.5), b(0.4), b(0.3), b(0.2), c(0.7), c(0.6), c(0.5), c(0.4), c(0.3), c(0.2), 'white'])
    plt.setp(mypie2, width=0.5, edgecolor='white')
    plt.margins(0, 0)
     
    plt.legend(labels=group_names, bbox_to_anchor=(0.58, 0.36), loc='upper left')
     
    cax = fig.add_axes([0.76, 0.25, 0.03, 0.5])
    cmap = plt.cm.Greens
    cmaplist = [cmap(i / 10.) for i in range(2, 8, 1)]
    cmap = cmap.from_list('Custom cmap', cmaplist)
    cb = ColorbarBase(cax, cmap=cmap, spacing='proportional', ticks=[1, 0.8, 0.6, 0.4, 0.2, 0],)
    cb.ax.set_yticklabels(subgroup_names)
    cb.ax.set_label('Traffic Ratio')
     
    # show it
    plt.show()
    
    
def plot_2_by_1_format():
    import numpy
    
    from collections import Counter
    
    US_only_count_list, non_US_only_count_list, global_count_list, US_count_in_global_footprint_list, isp_pair_count = get_peering_location_frequency_from_caida_data()
    
    US_only_count_dict = dict(Counter(US_only_count_list)) 
    non_US_only_count_dict = dict(Counter(non_US_only_count_list))
    global_count_dict = dict(Counter(global_count_list))
    US_count_in_global_footprint_dict = dict(Counter(US_count_in_global_footprint_list))
    
    peering_point_max_location_count = max(max(US_only_count_dict.keys()), max(non_US_only_count_dict.keys()), max(global_count_dict.keys()), max(US_count_in_global_footprint_dict.keys()))
    US_only_count_list = [float(US_only_count_dict[i]) / sum(US_only_count_dict.values()) * 100 if i in US_only_count_dict.keys() else 0 for i in range(peering_point_max_location_count)]    
    non_US_only_count_list = [float(non_US_only_count_dict[i]) / sum(non_US_only_count_dict.values()) * 100 if i in non_US_only_count_dict.keys() else 0 for i in range(peering_point_max_location_count)]    
    global_count_list = [float(global_count_dict[i]) / sum(global_count_dict.values()) * 100 if i in global_count_dict.keys() else 0 for i in range(peering_point_max_location_count)]    
    US_count_in_global_footprint_list = [float(US_count_in_global_footprint_dict[i]) / sum(US_count_in_global_footprint_dict.values()) * 100 if i in US_count_in_global_footprint_dict.keys() else 0 for i in range(peering_point_max_location_count)]

    # We're setting this value manually.
    peering_point_max_location_count = 10
    temp = sum(US_only_count_list[peering_point_max_location_count:])
    US_only_count_list = US_only_count_list[:peering_point_max_location_count]
    US_only_count_list.append(temp)
    
    temp = sum(non_US_only_count_list[peering_point_max_location_count:])
    non_US_only_count_list = non_US_only_count_list[:peering_point_max_location_count]
    non_US_only_count_list.append(temp)
    
    peering_point_for_global_max_location_count = 15
    temp = sum(global_count_list[peering_point_for_global_max_location_count:])
    global_count_list = global_count_list[:peering_point_for_global_max_location_count]
    global_count_list.append(temp)

    temp = sum(US_count_in_global_footprint_list[peering_point_for_global_max_location_count:])
    US_count_in_global_footprint_list = US_count_in_global_footprint_list[:peering_point_for_global_max_location_count]
    US_count_in_global_footprint_list.append(temp)
    
    fig = plt.figure()
    gs = gridspec.GridSpec(2,2)
    US_only_peering_plot = plt.subplot(gs[0, 0]) 
    non_US_only_peering_plot = plt.subplot(gs[0, 1])
    global_peering_plot = plt.subplot(gs[1, :])

    X = numpy.arange(peering_point_max_location_count + 1)
    X_for_global = numpy.arange(peering_point_for_global_max_location_count + 1)

#     US_only_peering_plot.bar(X, US_only_count_list, color='black', edgecolor='black', fill = False, hatch='/')
    US_only_peering_plot.bar(X, US_only_count_list, color='r')
    US_only_peering_plot.set_xlim(0)
    US_only_peering_plot.set_ylim(0, 100)
    
    non_US_only_peering_plot.bar(X, non_US_only_count_list, color='g')
    non_US_only_peering_plot.set_xlim(0)    
    non_US_only_peering_plot.set_ylim(0, 100)
    
    global_peering_plot.bar(X_for_global-0.2, global_count_list, width=0.4, color='b')
    global_peering_plot.bar(X_for_global+0.2, US_count_in_global_footprint_list, width=0.4, color='r')
    global_peering_plot.set_xlim(0)
    global_peering_plot.set_ylim(0, 50)

    peering_plot_labels = [i if i % 5 == 1 else "" for i in X]
    peering_plot_labels[-1] = '>' + str(peering_point_max_location_count)
    US_only_peering_plot.set_xticks(X)
    US_only_peering_plot.set_xticklabels(peering_plot_labels)
    US_only_peering_plot.legend(['Peer only\nin USA\n({} pairs)'.format(int(sum(US_only_count_dict.values())))])
    non_US_only_peering_plot.set_xticks(X)
    non_US_only_peering_plot.set_xticklabels(peering_plot_labels)
    non_US_only_peering_plot.legend(['Exclusively\noutside USA\n({} pairs)'.format(int(sum(non_US_only_count_dict.values())))])

    peering_plot_labels = [i if i % 5 == 1 else "" for i in X_for_global]
    peering_plot_labels[-1] = '>' + str(peering_point_for_global_max_location_count)
    global_peering_plot.set_xticks(X_for_global)
    global_peering_plot.set_xticklabels(peering_plot_labels)
    global_peering_plot.legend(['Global footprint\n({} pairs)'.format(int(sum(global_count_dict.values()))), 'Peer in\nUSA location'])

    fig.suptitle('Peering PoP frequency between ISP pair (count of {})'.format(isp_pair_count))
    ax = plt.gcf().add_subplot(111, frameon=False)
    y_label_text = ('Frequency count (in %)')
    ax.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
    ax.set_ylabel(y_label_text)
    plt.show()

        
def plot_2_by_2_format():
    '''
    @note: This uses a 2 * 2 cartesian x-y kind plot. 
    '''
    import os, numpy
    from collections import Counter
    
    US_only_count_list, non_US_only_count_list, global_count_list, US_count_in_global_footprint_list, isp_pair_count = get_peering_location_frequency_from_caida_data()
    
    US_only_count_dict = dict(Counter(US_only_count_list)) 
    non_US_only_count_dict = dict(Counter(non_US_only_count_list))
    global_count_dict = dict(Counter(global_count_list))
    US_count_in_global_footprint_dict = dict(Counter(US_count_in_global_footprint_list))

    
    peering_point_max_location_count = max(max(US_only_count_dict.keys()), max(non_US_only_count_dict.keys()), max(global_count_dict.keys()), max(US_count_in_global_footprint_dict.keys()))
    US_only_count_list = [float(US_only_count_dict[i]) / sum(US_only_count_dict.values()) * 100 if i in US_only_count_dict.keys() else 0 for i in range(peering_point_max_location_count)]    
    non_US_only_count_list = [float(non_US_only_count_dict[i]) / sum(non_US_only_count_dict.values()) * 100 if i in non_US_only_count_dict.keys() else 0 for i in range(peering_point_max_location_count)]    
    global_count_list = [float(global_count_dict[i]) / sum(global_count_dict.values()) * 100 if i in global_count_dict.keys() else 0 for i in range(peering_point_max_location_count)]    
    US_count_in_global_footprint_list = [float(US_count_in_global_footprint_dict[i]) / sum(US_count_in_global_footprint_dict.values()) * 100 if i in US_count_in_global_footprint_dict.keys() else 0 for i in range(peering_point_max_location_count)]

    # We're setting this value manually.
    peering_point_max_location_count = 10
    temp = sum(US_only_count_list[peering_point_max_location_count:])
    US_only_count_list = US_only_count_list[:peering_point_max_location_count]
    US_only_count_list.append(temp)
    
    temp = sum(non_US_only_count_list[peering_point_max_location_count:])
    non_US_only_count_list = non_US_only_count_list[:peering_point_max_location_count]
    non_US_only_count_list.append(temp)
    
    temp = sum(global_count_list[peering_point_max_location_count:])
    global_count_list = global_count_list[:peering_point_max_location_count]
    global_count_list.append(temp)
    
    fig, ((US_only_peering_plot, global_peering_plot), (_, non_US_only_peering_plot)) = plt.subplots(2, 2, sharex=True, sharey=True)
    X = numpy.arange(peering_point_max_location_count + 1)

    US_only_peering_plot.bar(X, US_only_count_list)
    US_only_peering_plot.set_xlim(0)
    US_only_peering_plot.set_ylim(0, 100)
    
    non_US_only_peering_plot.bar(X, non_US_only_count_list)
    non_US_only_peering_plot.set_xlim(0)    
    non_US_only_peering_plot.set_ylim(0, 100)
    
    global_peering_plot.bar(X, global_count_list)
    global_peering_plot.set_xlim(0)
    global_peering_plot.set_ylim(0, 100)

    peering_plot_labels = [i for i in X]
    peering_plot_labels[-1] = '>' + str(peering_point_max_location_count)

    US_only_peering_plot.set_xticks(X)
    US_only_peering_plot.set_xticklabels(peering_plot_labels)
    US_only_peering_plot.legend(['Only in USA'])

    non_US_only_peering_plot.set_xticks(X)
    non_US_only_peering_plot.set_xticklabels(peering_plot_labels)
    non_US_only_peering_plot.legend(['Exclusively \noutside USA'])

    global_peering_plot.set_xticks(X)
    global_peering_plot.set_xticklabels(peering_plot_labels)
    global_peering_plot.legend(['Globally'])

    fig.suptitle('Peering PoP frequency between ISP pair')     
    ax = fig.add_subplot(111, frameon=False)
#     ax.plot([0.5, 0.5], [0.05,0.9], color='r', transform=plt.gcf().transFigure, clip_on=False)
#     ax.plot([0.08,0.9], [0.5, 0.5], color='r', transform=plt.gcf().transFigure, clip_on=False)
    y_label_text = ('Count (in % of total {} ISP pair)').format(isp_pair_count)
    plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
    plt.grid(False)
    plt.ylabel(y_label_text)
    plt.show()



def get_peering_location_frequency_from_caida_data():
    US_only_count_list = []    
    non_US_only_count_list = []   
    global_count_list = [] 
    US_count_in_global_footprint_list = []
    isp_pair_count = 0
    with open(os.path.abspath((os.path.dirname(__file__) + "/data/" + '201603.as-rel-geo.txt'))) as fin:
        for line in fin.readlines()[15:]:
            isp_pair_count += 1
            US_pop_count = non_US_pop_count = 0
            peering_pop_info = line.split("|")[2:]
            for p in peering_pop_info:
                location = p.split(",")[0]
                if location.strip()[-2:] == 'US':
                    US_pop_count += 1
                else:
                    non_US_pop_count += 1
            if US_pop_count != 0:
                if non_US_pop_count != 0:
                    global_count_list.append((US_pop_count + non_US_pop_count))
                    US_count_in_global_footprint_list.append(US_pop_count)    
                else:
                    US_only_count_list.append(US_pop_count)
            else:
                non_US_only_count_list.append(non_US_pop_count)

    return US_only_count_list, non_US_only_count_list, global_count_list, US_count_in_global_footprint_list, isp_pair_count

def plot_peering_pop_frequency_cdf():    
    plt.rcParams.update({'font.size':12}) 
    US_only_count_list, non_US_only_count_list, global_count_list, US_count_in_global_footprint_list, isp_pair_count = get_peering_location_frequency_from_caida_data()
    
    count, bin_edges = np.histogram(US_only_count_list, density=True)
    cdf = np.cumsum(count)
    cdf /= cdf[-1]
    plt.plot(bin_edges[:-1], cdf, color='r', label='Peer only in USA')
     
    count, bin_edges = np.histogram(non_US_only_count_list, density=True)
    cdf = np.cumsum(count)
    cdf /= cdf[-1]
    plt.plot(bin_edges[:-1], cdf, color='g', label='Exclusively outside USA')
    
    count, bin_edges = np.histogram(global_count_list, density=True)
    cdf = np.cumsum(count)
    cdf /= cdf[-1]
    plt.plot(bin_edges[:-1], cdf, color='b', label='Global peering')
    
    count, bin_edges = np.histogram(US_count_in_global_footprint_list, density=True)
    cdf = np.cumsum(count)
    cdf /= cdf[-1]
    plt.plot(bin_edges[:-1], cdf, color='k', label='Global peering (locations only in USA)')

    plt.legend()
    plt.xlabel('ISPs\' peering points per peer')
    plt.ylabel('CDF')
    plt.show()
    return    
    
def plot_pop_frequency_cdf():
    '''
    Reads Excel file, uses Panda and then plot CDF.
    @note: Each category has 4 columns, (ISP_ID, IXP_Count, Facility_Count, Total_Count)
    We want only total_count from each category. So, we need to know the column index of the Title first and then add 3 to get the 4th index which is 'total_count'
    Since, not all category has same isp count, so some of the category will have empty (NaN) rows. We delete them by using 'dropna()'. 
    'how' says we remove any row which is empty.
    we remove the 1st row as that has the name 'total_count'. We just need the values as list.
    '''
    plt.rcParams.update({'font.size':12})
    file_name = os.path.abspath("/Users/prasunkantidey/DropBox1/Dropbox/Prasun/meta-peering/sigcomm19-v1/figures/"+ "PeeringDB_Analysis.xlsx")
    df = pd.read_excel(open(file_name, 'rb'), sheetname=2)
    category_names = ['NSP', 'Content', 'Access', 'Others']
    category_color = {'Access':'r', 'Content':'g', 'NSP':'b', 'Others':'k'}
    for c in category_names:
        category_wise_total_pop_frequency_column_index = df.columns.get_loc(c) + 3
        pop_frequency = df[df.columns[category_wise_total_pop_frequency_column_index]].dropna(how='any')
        pop_frequency = pop_frequency[1:].values
        count, bin_edges = np.histogram(pop_frequency, density=True)
        cdf = np.cumsum(count)
        cdf /= cdf[-1]
        plt.plot(bin_edges[:-1], cdf, label=c if c != 'NSP' else 'Transit', color=category_color[c])
    plt.legend()
    plt.xlabel('ISPs\' PoP frequency')
    plt.ylabel('CDF')
    plt.show()
    return

if __name__ == '__main__':
    pie_plot_traffic_ratio()
#     plot_peering_pop_frequency_cdf()
#     plot_pop_frequency_cdf()