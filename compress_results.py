import os
import json
import pandas as pd
import copy
import subprocess
from subprocess import call


pop_list = dict()
top_3_pops_details = {}

with open('output/pop_list_with_name.json') as f:
	pop_list = json.load(f)

for root, dirs, files in os.walk('output/'):
	if 'algorithm_report.csv' in files:

		isp_pair = root.split('/')[1]
		isp1 = root.split('/')[1].split('_')[0]
		sorting_strategy = root.split('/')[-1]

		df1 = pd.read_csv(os.path.join(root,'algorithm_report.csv'), delimiter='\t')
		total_APC = len(df1)
		# try:
		top_3_pop_indexes= [int(df1.head(3)['Index in PPC list'][i]) for i in range(min(3,len(df1)))]
		# except:
			# print(root,df1.head(3)['Index in PPC list'])

		df2 = pd.read_csv(os.path.join(root,isp1+'.csv'), delimiter='\t')
		top_3_pop_ids = list(df2.loc[df2['PPC Index'].isin(top_3_pop_indexes)]['Possible Location Combinations'])
		top_3_pop_ids = [i.strip(' ').strip('[').strip(']').split(',') for i in top_3_pop_ids]
		
		for i in range(len(top_3_pop_indexes)):
			top_3_pop_ids[i] = [int(top_3_pop_ids[i][j]) for j in range(len(top_3_pop_ids[i]))]
		
		temp_data = {}
		for i, lst  in enumerate(top_3_pop_ids):
			temp_lst = []
			for pop in pop_list['data']:
				if(pop['ID'] in lst):
					temp_lst.append(pop)
			temp_data[i+1] = copy.deepcopy(temp_lst)
		temp_data['total_apc'] = total_APC


		try:
			top_3_pops_details[isp_pair][sorting_strategy] = temp_data
		except:
			top_3_pops_details[isp_pair] = {}
			top_3_pops_details[isp_pair][sorting_strategy] = temp_data
		# break


	if 'willingness_sorted' in dirs:
		isp_pair = root.split('/')[1]
		# print('sudo mkdir /AWS_Data/'+isp_pair)
		call('sudo mkdir AWS_Data/'+isp_pair, shell=True)
		for root1, dirs1, files1, in os.walk(os.path.join(root,'willingness_sorted')):
			for f in files1:
				# print('cp '+os.path.join(root1,f)+' AWS_Data/'+root.split('/')[1]+'/'+f)
				rc = call('sudo cp '+os.path.join(root1,f)+' AWS_Data/'+root.split('/')[1]+'/'+f, shell=True)


with open('cut_this_to_AWS_data.json','w') as f:
	json.dump(top_3_pops_details, f)

for root, dirs, files in os.walk('Concave_png/'):
	for file in files:
		file_to_copy = os.path.join(root,file)
		folder1 = os.path.join('AWS_Data/',file.strip('.png'))+'/overlap.png'
		folder2 = os.path.join('AWS_Data/',file.strip('.png').split('_')[1]+'_'+file.strip('.png').split('_')[0])+'/overlap.png'
		rc = call('sudo cp '+file_to_copy+ ' ' +folder1, shell=True)
		rc = call('sudo cp '+file_to_copy+ ' ' + folder2, shell=True)



