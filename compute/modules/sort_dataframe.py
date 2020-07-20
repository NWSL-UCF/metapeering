from .gVars import SORT_STRATEGY_DIFF, SORT_STRATEGY_OWN, SORT_STRATEGY_RATIO

def sort_dataframe(df, isp_sort_strategy):
    '''
    @note: Separated dataFrame column wise sorting into this method. Previously it was in generate_ppc_df().  
    '''
    if isp_sort_strategy == SORT_STRATEGY_DIFF:
        df.sort_values(by=df.columns[5], ascending=False, inplace=True)
    elif isp_sort_strategy == SORT_STRATEGY_OWN:
        df.sort_values(by=df.columns[2], ascending=False, inplace=True)
    elif isp_sort_strategy == SORT_STRATEGY_RATIO:
        df['possible_location_counts'] = df['Possible Location Combinations'].str.len()
        df.sort_values(by=[df.columns[6], df.columns[-1]], ascending=[False, False], inplace=True)  
        df.drop(columns=df.columns[-1], inplace=True)   
    
    return df
