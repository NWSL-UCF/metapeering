import pandas as pd

def find_output(asn1, asn2):
    df = pd.read_csv('./compute/modules/ML/ML/out.csv')
    pair = ''

    try:
        asn1 = asn1.replace('AS', '')
        asn2 = asn2.replace('AS', '')
        asn1_int = int(asn1)
        asn2_int = int(asn2)
        
    except ValueError:
        print('Not a valid input')
        res = 'Error: Pair not found'
        return res

    if asn1_int < asn2_int:
        pair = asn1 + '-' + asn2
    else:
        pair = asn2 + '-' + asn1

    res = 'Error: Pair not found'

    for idx in range(len(df.pair)):
        if df.at[idx, 'pair'] == pair:
            return df.at[idx, 'Pred']
    # if pair not found, return string error
    return res

# Test:
# assert find_output('42', '293') == 1, 'Error, expected output is 1'
