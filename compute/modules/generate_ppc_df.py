import pandas as pd

def generate_ppc_df(isp_ppc_data, isp_sort_strategy):
    '''
    @note: This is a helping tool. This generates the panda dataframe to store the PPC information with all the details.
    @note: It is called from compute_all_acceptable_peering_contracts() and returns the DF there. 
    @param isp_ppc_data: This is basically the data we want to save. This is a list of lists containing all informations regarding the PPC, traffic.
    @param isp_sort_strategy: This is how ISP want to sort the PPC. whether, its own traffic priority, minimize in/ out-bound traffic difference, minimize out/in-bound traffic ratio. 
    @returns Data Frame with 'PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Total Traffic', 'Traffic Difference', 'Traffic Ratio'
    '''
    df = pd.DataFrame(isp_ppc_data)
    df.transpose()
    df.insert(0, "", df.index)
    
    df.columns = ['PPC Index', 'Possible Location Combinations', 'My Traffic', 'Opponent Traffic', 'Total Traffic', 'Traffic Difference', 'Traffic Ratio']
    
    return df