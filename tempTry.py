from os import listdir
from os.path import isfile, join
import json

isp_data = {}

for f in listdir('data/'):
	if 'peering_db_data_file' in f:
		with open('data/'+f, 'r') as i:
			isp_data[f.replace('_peering_db_data_file.json','')] = json.load(i)

print(isp_data[isp_data.keys()[0]][u'pop_list'])
