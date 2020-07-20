from .gVars import Sort_Strategy_Names
import os

def write_acceptable_peering_contracts_to_file(isp_asn, sort_strategy, apc_list_df, output_directory_for_isp, function_name=None):
    '''
    @note: saves the Dataframe in a .csv format file
    @note: Neither CSV files have the index. 
    '''    
    Output_Directory = os.path.abspath(output_directory_for_isp + "/" + Sort_Strategy_Names[sort_strategy] + "/")
    if not os.path.exists(Output_Directory):
        os.makedirs(Output_Directory)
    if function_name == 'peering_algorithm_implementation':
        file_name = Output_Directory + "/" + "algorithm_report.csv"
        apc_list_df.to_csv(file_name, sep='\t', index=False)
    else:
        file_name = Output_Directory + "/" + str(isp_asn) + ".csv"
        apc_list_df.to_csv(file_name, sep='\t', index=False)
