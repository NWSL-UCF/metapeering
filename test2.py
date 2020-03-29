import os

Data_Directory = os.path.abspath(os.path.dirname(__file__)) + "/" + "data"

caida_data = dict()
with open(os.path.abspath(Data_Directory + "/" + "20190601.as-rel.txt"), 'r') as fin:
    f_lines = fin.readlines()
    for l in f_lines:
        if l[0] == '#':
            continue
        l = l.strip().split("|")
        if l[-1] == '0' :
            try:
                caida_data[int(l[0])].append(int(l[1]))
            except Exception as _:
                caida_data[int(l[0])] = [int(l[1])]
    fin.close()

d = caida_data[6128]
for k in caida_data.keys():
    if 6128 in caida_data[k]:
        d.append(k)

isps = {'access': {'cablevision': 6128, 'cableone': 11492, 'centurylink': 209, 'charter':7843, 'comcast':7922, 'cox':22773, 'tds':4181, 'windstream':7029, },
                'content': {'akamai':20940, 'amazon': 16509, 'ebay':62955, 'facebook': 32934, 'google': 15169, 'microsoft': 8075, 'netflix': 2906, },
                'transit': {'columbus':23520, 'cogent': 174, 'he':6939, 'ntt': 2914, 'pccw':3491, 'sprint': 1239, 'verizon':701, 'zayo':6461, }}  
asns = []

for v in isps.values():
    asns = asns + v.values()

print asns

lst3 = [value for value in asns if value in d]
print lst3
# print len(d)
