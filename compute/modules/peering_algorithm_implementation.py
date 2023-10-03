from .gVars import Sort_Strategy_Names, SORT_STRATEGY_DIFF, SORT_STRATEGY_OWN, SORT_STRATEGY_RATIO, Output_Directory, List_Of_POP_Locations
from .gVars import beta_w, weight_w, beta_a, weight_a, willingness_score_for_all_isps, affinity_score_for_all_isps, felicity_score_for_all_isps
from .affinityScore import affinityScore
from .sort_dataframe import sort_dataframe
from .write_acceptable_peering_contracts_to_file import write_acceptable_peering_contracts_to_file
from .draw_graph import draw_graph

import os
import numpy as np
# Handling the unnecessary long float exponentials
# https://stackoverflow.com/questions/9777783/suppress-scientific-notation-in-numpy-when-creating-array-from-nested-list
np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.2f}'.format})
import pandas as pd
from scipy import stats

def peering_algorithm_implementation(isp_a, isp_b):
    '''peering_algorithm_implementation
    Creates the algorithm_report file in CVS format.
    The columns are:
    'Index in PPC list': This are the Possible Peering Contracts. However, note that, not all the PPC will be included here.
    Check the get_all_acceptable_peering_contracts(). This has the conditions, based on which Acceptable Peering Contracts are selected.
    'Rank of PPC for ISP A': Rank of every PPC according to ISP A's preference.
    Same goes for B.
    '(Rank A - Rank B)^2': gives the relative position difference of every PPC from 2 ISPs' POV.
    We calculate the Max diff^ of PPC Rank. In the worst case, a PPC can be placed as position 1 for ISP A and at last(n) position for ISP B.
    To calculate n, we simply take the length of APC list, because a PPC can't be placed at any later position then last Index.
    So, '1-length(apc_list)' gives us the difference and then we square that value.
    'Willingness (AB) = 1 - diff^2/(1-n)^2': We divide (Rank A - Rank B)^2 by [1-length(apc_list)]^2 and subtract this value from 1 to
    calculate the willingness for that specific APC.
    We take the sum of willingness value for each APC and divide by APC count to get the willingness_score of that ISP pair for a specific sorting category.
    However, the willingness we get will not be in [0, 1]. The minimum value will be greater than 0. We need to scale the values from [0, 1].
    To do so, we need to calculate the willingness_min value. and then subtract all values by willingness_min value and divide those by (1- willingness_min)
    We calculate the ISPs coverage area overlap score (affinity score) as well.
    We take the geometric mean of willingness score and affinity score to calculate the final Felicity score.
    @note: [This needs checking in future. I'm not sure if this is what we're doing now]
    We don't update the actual APC list of each ISP, as this APC was prepared based on ISP's actual sorting strategy.
    So, we take APC list of each ISP and then sort them to run the algorithm for 3 sorting strategies and then save the output on file.
    @return: Felicity scores for each sorting strategy for these two ISPs. By default they is set -1. Meaning no peering, no APC.
    '''
    def generate_initial_apc_rank_list(isp_a_apc_list_index, isp_b_apc_list_index):
        apc_rank_list = [[v, i+1, isp_b_apc_list_index.index(v)+1] for i, v in enumerate(isp_a_apc_list_index) if v in isp_b_apc_list_index]
        not_in_b = set(isp_a_apc_list_index) - set(isp_b_apc_list_index)
        if len(not_in_b) > 0:
            for extra_item, i in zip(not_in_b, range(len(not_in_b))):
                apc_rank_list.append([extra_item, isp_a_apc_list_index.index(extra_item) + 1, max(isp_b_apc_list_index) + i])
        not_in_a = set(isp_b_apc_list_index) - set(isp_a_apc_list_index)
        if len(not_in_a) > 0:
            for extra_item, i in zip(not_in_a, range(len(not_in_a))):
                apc_rank_list.append([extra_item, max(isp_a_apc_list_index) + i, isp_b_apc_list_index.index(extra_item) + 1])

        return apc_rank_list

    willingness_score = {}
    affinity_score = {}
    felicity_score = {}

    if (isp_a.all_acceptable_peering_contracts_count == 0 and isp_b.all_acceptable_peering_contracts_count == 0):
#         print("0 APC for {} and {}. No APC folder created!".format(isp_a.as_number, isp_b.as_number))
        # Neither of the ISPs have any APC, so no peering.
        for _sort in Sort_Strategy_Names:
            willingness_score.update({_sort:-1})
            affinity_score.update({_sort:-1})
            felicity_score.update({_sort:-1})
        return willingness_score, affinity_score, felicity_score

    output_directory_for_isp = os.path.abspath(Output_Directory + "/" + str(isp_a.as_number) + "_" + str(isp_b.as_number))

    isp_a_pop_locations_list = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_a.my_pop_locations_list]
    isp_b_pop_locations_list = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_b.my_pop_locations_list]
    
    common_pop_locations = [(List_Of_POP_Locations[i].longitude, List_Of_POP_Locations[i].latitude) for i in isp_a.common_pop_locations]

    affinity_score_combined = affinityScore((isp_a.name,str(isp_a.as_number)), (isp_b.name, str(isp_b.as_number)), isp_a_pop_locations_list, isp_b_pop_locations_list, common_pop_locations)
    # affinity_score_combined = affinityScore(isp_a.name, isp_b.name, isp_a_pop_locations_list, isp_b_pop_locations_list, common_pop_locations)

    for sorting_strategy in [SORT_STRATEGY_DIFF, SORT_STRATEGY_OWN, SORT_STRATEGY_RATIO]:
        if isp_a.all_acceptable_peering_contracts_count > 0 and isp_b.all_acceptable_peering_contracts_count > 0:
            isp_a_all_apc = sort_dataframe(isp_a.all_acceptable_peering_contracts, sorting_strategy)
            isp_b_all_apc = sort_dataframe(isp_b.all_acceptable_peering_contracts, sorting_strategy)

            write_acceptable_peering_contracts_to_file(isp_a.as_number, sorting_strategy, isp_a_all_apc, output_directory_for_isp)
            write_acceptable_peering_contracts_to_file(isp_b.as_number, sorting_strategy, isp_b_all_apc, output_directory_for_isp)

            isp_a_apc_list_index = list(isp_a_all_apc.iloc[:, 0])
            isp_b_apc_list_index = list(isp_b_all_apc.iloc[:, 0])

            apc_rank_list = generate_initial_apc_rank_list(isp_a_apc_list_index, isp_b_apc_list_index)
            n = len(apc_rank_list)

            np_data = np.zeros((n, 7))
            np_data[:, :3] = np.array(apc_rank_list)
            np_data[:, 3] = np.square(np_data[:, 1] - np_data[:, 2])
            np_data[:, 4] = (max(np_data[:, 1]) - np_data[:, 1] + 1) / max(np_data[:, 1])
            np_data[:, 5] = (max(np_data[:, 2]) - np_data[:, 2] + 1) / max(np_data[:, 2])
            if n == 1:
                np_data[:, 6] = 1
            else:
                np_data[:, 6] = stats.gmean(np_data[:, 4:6], 1)

            df = pd.DataFrame(np_data)
#             df = df.round(4)
            df.columns = ['Index in PPC list', 'Rank of PPC for ISP A', 'Rank of PPC for ISP B', '(Rank A - Rank B)^2', 'Willingness (A)', 'Willingness (B)', 'Willingness (AB) = 1 - (diff^2/(1-n)^2)']
            df.sort_values(by=[df.columns[-1], df.columns[-3]], ascending=False, inplace=True)

            write_acceptable_peering_contracts_to_file(isp_a.as_number, sorting_strategy, df, output_directory_for_isp, peering_algorithm_implementation.__name__)
            draw_graph(isp_a.as_number, isp_b.as_number, df, sorting_strategy, output_directory_for_isp)

            w_score_without_normalization = sum(df[df.columns[-1]]) / isp_a.all_acceptable_peering_contracts_count

            willingness_min = 0.0
            w_score = (w_score_without_normalization - willingness_min) / (1 - willingness_min)
            # try:
            # We don't need this try-except block any more, as we're not rounding any value, so no -ve value should appear.
            # Instead we're using a weighted geometric-mean formula here. beta_w, and beta_a are the co-efficient, not part of geometric mean.
            # But, weight_w, weight_a are part of weighted geometric mean.
            # In future, we can remove beta_w, beta_a may be!
            f_score =  ((beta_w * w_score)**weight_w * (beta_a * affinity_score_combined)**weight_a) ** (1.0/(weight_w + weight_a))
            # except Exception as e:
                # print(e)
                # print("A: {}, B: {}, sort by: {}, w_score_before_norm: {}, w_score_min: {}, w_score: {}, affinity: {}".format(isp_a.name, isp_b.name, Sort_Strategy_Names[sorting_strategy], w_score_without_normalization, willingness_min, w_score, affinity_score_combined))
                # f_score = 0.0

            willingness_score.update({Sort_Strategy_Names[sorting_strategy]:w_score})
            affinity_score.update({Sort_Strategy_Names[sorting_strategy]:affinity_score_combined})
            felicity_score.update({Sort_Strategy_Names[sorting_strategy]:f_score})
        else:
            willingness_score.update({Sort_Strategy_Names[sorting_strategy]:-1})
            affinity_score.update({Sort_Strategy_Names[sorting_strategy]:affinity_score_combined})
            felicity_score.update({Sort_Strategy_Names[sorting_strategy]:-1})

    # willingness_score_for_all_isps[str(isp_a.as_number)+'_'+str(isp_b.as_number)] = willingness_score

    # affinity_score_for_all_isps[str(isp_a.as_number)+'_'+str(isp_b.as_number)] = affinity_score

    # felicity_score_for_all_isps[str(isp_a.as_number)+'_'+str(isp_b.as_number)] = felicity_score

    return willingness_score, affinity_score, felicity_score
