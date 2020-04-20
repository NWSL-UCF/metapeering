from flask import Flask, render_template, request, redirect, url_for
from flask import make_response
from flask_bootstrap import Bootstrap
import re
import subprocess
from subprocess import call
import json
from app.forms import PeeringQueryForm
from os import listdir
from os.path import isfile, join
from flask_s3 import FlaskS3
import boto3 
from app.config import AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from zipfile import ZipFile

s3 = boto3.client(
	's3',
	aws_access_key_id=AWS_ACCESS_KEY_ID,
	aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'metapeering'
# app.config['FLASKS3_BUCKET_NAME'] = 'metapeering'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
Bootstrap(app)
# s3 = FlaskS3(app)


@app.route('/', methods=['GET','POST'])
def querry():
	form = PeeringQueryForm()
	if request.method == 'POST' and form.is_submitted():
		return form_handler(request.form)
	return render_template('submit.html', form=form)

@app.route('/results')
def showResult():
	return render_template('result.html', ppc={'diff':{'1': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 12, 'city': 'Chicago', 'internet_penetration_percentage': 0.865, 'isp_id_in_peering_db': 7, 'isp_type_in_peering_db': 'fac', 'latitude': 41.85365, 'longitude': -87.618342, 'population': 2716450, 'state': 'IL'}, {'ID': 16, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 19, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047942, 'longitude': -118.255564, 'population': 3999759, 'state': 'CA'}, {'ID': 26, 'city': 'Denver', 'internet_penetration_percentage': 0.795, 'isp_id_in_peering_db': 389, 'isp_type_in_peering_db': 'fac', 'latitude': 39.745636, 'longitude': -104.995636, 'population': 704621, 'state': 'CO'}], '2': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 9, 'city': 'Houston', 'internet_penetration_percentage': 0.8170000000000001, 'isp_id_in_peering_db': 1476, 'isp_type_in_peering_db': 'fac', 'latitude': 29.844182, 'longitude': -95.556656, 'population': 2312717, 'state': 'TX'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 13, 'city': 'Miami', 'internet_penetration_percentage': 0.8420000000000001, 'isp_id_in_peering_db': 15, 'isp_type_in_peering_db': 'fac', 'latitude': 25.782648, 'longitude': -80.193157, 'population': 463347, 'state': 'FL'}, {'ID': 20, 'city': 'New York', 'internet_penetration_percentage': 0.802, 'isp_id_in_peering_db': 16, 'isp_type_in_peering_db': 'fac', 'latitude': 40.741355, 'longitude': -74.003203, 'population': 8622698, 'state': 'NY'}], '3': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 12, 'city': 'Chicago', 'internet_penetration_percentage': 0.865, 'isp_id_in_peering_db': 7, 'isp_type_in_peering_db': 'fac', 'latitude': 41.85365, 'longitude': -87.618342, 'population': 2716450, 'state': 'IL'}, {'ID': 16, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 19, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047942, 'longitude': -118.255564, 'population': 3999759, 'state': 'CA'}, {'ID': 21, 'city': 'Dallas', 'internet_penetration_percentage': 0.8170000000000001, 'isp_id_in_peering_db': 4, 'isp_type_in_peering_db': 'fac', 'latitude': 32.800955, 'longitude': -96.81955, 'population': 1341075, 'state': 'TX'}]}, 
											'own':{'1': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 12, 'city': 'Chicago', 'internet_penetration_percentage': 0.865, 'isp_id_in_peering_db': 7, 'isp_type_in_peering_db': 'fac', 'latitude': 41.85365, 'longitude': -87.618342, 'population': 2716450, 'state': 'IL'}, {'ID': 16, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 19, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047942, 'longitude': -118.255564, 'population': 3999759, 'state': 'CA'}, {'ID': 26, 'city': 'Denver', 'internet_penetration_percentage': 0.795, 'isp_id_in_peering_db': 389, 'isp_type_in_peering_db': 'fac', 'latitude': 39.745636, 'longitude': -104.995636, 'population': 704621, 'state': 'CO'}], '2': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 9, 'city': 'Houston', 'internet_penetration_percentage': 0.8170000000000001, 'isp_id_in_peering_db': 1476, 'isp_type_in_peering_db': 'fac', 'latitude': 29.844182, 'longitude': -95.556656, 'population': 2312717, 'state': 'TX'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 13, 'city': 'Miami', 'internet_penetration_percentage': 0.8420000000000001, 'isp_id_in_peering_db': 15, 'isp_type_in_peering_db': 'fac', 'latitude': 25.782648, 'longitude': -80.193157, 'population': 463347, 'state': 'FL'}, {'ID': 20, 'city': 'New York', 'internet_penetration_percentage': 0.802, 'isp_id_in_peering_db': 16, 'isp_type_in_peering_db': 'fac', 'latitude': 40.741355, 'longitude': -74.003203, 'population': 8622698, 'state': 'NY'}], '3': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 12, 'city': 'Chicago', 'internet_penetration_percentage': 0.865, 'isp_id_in_peering_db': 7, 'isp_type_in_peering_db': 'fac', 'latitude': 41.85365, 'longitude': -87.618342, 'population': 2716450, 'state': 'IL'}, {'ID': 16, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 19, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047942, 'longitude': -118.255564, 'population': 3999759, 'state': 'CA'}, {'ID': 21, 'city': 'Dallas', 'internet_penetration_percentage': 0.8170000000000001, 'isp_id_in_peering_db': 4, 'isp_type_in_peering_db': 'fac', 'latitude': 32.800955, 'longitude': -96.81955, 'population': 1341075, 'state': 'TX'}]}, 
											'ratio': {'1': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 12, 'city': 'Chicago', 'internet_penetration_percentage': 0.865, 'isp_id_in_peering_db': 7, 'isp_type_in_peering_db': 'fac', 'latitude': 41.85365, 'longitude': -87.618342, 'population': 2716450, 'state': 'IL'}, {'ID': 16, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 19, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047942, 'longitude': -118.255564, 'population': 3999759, 'state': 'CA'}, {'ID': 26, 'city': 'Denver', 'internet_penetration_percentage': 0.795, 'isp_id_in_peering_db': 389, 'isp_type_in_peering_db': 'fac', 'latitude': 39.745636, 'longitude': -104.995636, 'population': 704621, 'state': 'CO'}], '2': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 9, 'city': 'Houston', 'internet_penetration_percentage': 0.8170000000000001, 'isp_id_in_peering_db': 1476, 'isp_type_in_peering_db': 'fac', 'latitude': 29.844182, 'longitude': -95.556656, 'population': 2312717, 'state': 'TX'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 13, 'city': 'Miami', 'internet_penetration_percentage': 0.8420000000000001, 'isp_id_in_peering_db': 15, 'isp_type_in_peering_db': 'fac', 'latitude': 25.782648, 'longitude': -80.193157, 'population': 463347, 'state': 'FL'}, {'ID': 20, 'city': 'New York', 'internet_penetration_percentage': 0.802, 'isp_id_in_peering_db': 16, 'isp_type_in_peering_db': 'fac', 'latitude': 40.741355, 'longitude': -74.003203, 'population': 8622698, 'state': 'NY'}], '3': [{'ID': 2, 'city': 'San Jose', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 6, 'isp_type_in_peering_db': 'fac', 'latitude': 37.241767, 'longitude': -121.782967, 'population': 1035317, 'state': 'CA'}, {'ID': 5, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 8, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047322, 'longitude': -118.25745, 'population': 3999759, 'state': 'CA'}, {'ID': 6, 'city': 'Atlanta', 'internet_penetration_percentage': 0.847, 'isp_id_in_peering_db': 1929, 'isp_type_in_peering_db': 'fac', 'latitude': 33.729369, 'longitude': -84.420099, 'population': 486290, 'state': 'GA'}, {'ID': 10, 'city': 'Seattle', 'internet_penetration_percentage': 0.885, 'isp_id_in_peering_db': 86, 'isp_type_in_peering_db': 'fac', 'latitude': 47.614358, 'longitude': -122.338864, 'population': 724745, 'state': 'WA'}, {'ID': 12, 'city': 'Chicago', 'internet_penetration_percentage': 0.865, 'isp_id_in_peering_db': 7, 'isp_type_in_peering_db': 'fac', 'latitude': 41.85365, 'longitude': -87.618342, 'population': 2716450, 'state': 'IL'}, {'ID': 16, 'city': 'Los Angeles', 'internet_penetration_percentage': 0.838, 'isp_id_in_peering_db': 19, 'isp_type_in_peering_db': 'fac', 'latitude': 34.047942, 'longitude': -118.255564, 'population': 3999759, 'state': 'CA'}, {'ID': 21, 'city': 'Dallas', 'internet_penetration_percentage': 0.8170000000000001, 'isp_id_in_peering_db': 4, 'isp_type_in_peering_db': 'fac', 'latitude': 32.800955, 'longitude': -96.81955, 'population': 1341075, 'state': 'TX'}]}})

@app.route('/glossary')
def glossary():
	return render_template('glossary.html')

@app.route('/feedback')
def feedback():
	return render_template('feedback.html')

def form_handler(request):
	data = {}
	if re.match(r"^[0-9]+$",request['asn1']):
		data['asn1'] = request['asn1']
	else:
		return "ERROR: ASN1 value invalid. Value needs to be an integer."
	if re.match(r"^[0-9]+$",request['asn2']):
		if request['asn2'] == data['asn1']:
			return "Error: Same ISP provided twice."
		data['asn2'] = request['asn2']
	elif request['asn2'] != '':
		return "ERROR: ASN2 value invalid. Value needs to be an integer"
	if re.match(r"^\d+\.?\d+$",request['threshold']) and float(request['threshold']) <= 1.0 and float(request['threshold']) >= 0.0:
		data['threshold'] = request['threshold']
	elif request['threshold'] == '':
		data['threshold'] = 0.5
	else:
		return "ERROR: Threshold value invalid. (Value needs to be decimal between 0.0 and 1.0)"

	return request_handler(data)

def request_handler(data):
	if len(data.values()) == 2:
		retScores = {}
		with open('app/appdata/felicity.json') as f:
			scores = json.load(f)
			for k,v in scores.items():
				if data['asn1'] in k:
					retScores[k] = v['own']
	else:
		retScores = {}
		with open('app/appdata/felicity.json') as f:
			scores = json.load(f)
			retScores[data['asn1']+'_'+data['asn2']] = scores[data['asn1']+'_'+data['asn2']]['own']
			retScores[data['asn2']+'_'+data['asn1']] = scores[data['asn2']+'_'+data['asn1']]['own']

	rm_keys = []
	for k,v in retScores.items():
		if float(v) < float(data['threshold']):
			rm_keys.append(k)
			rm_keys.append(k.split('_')[1]+'_'+k.split('_')[0])
	rm_keys = list(set(rm_keys))
	[retScores.pop(key) for key in rm_keys]

	# files = listdir('output/')
	if(len(retScores.values()) == 0):
		return 'Peering not Recommended at given threshold.'
	

	# return "Peering Recommended!"

	# rc = call('mkdir app/static', shell=True)
	# rc = call('rm -r app/static/*', shell=True)

	for k,v in retScores.items():
		if k.split('_')[0] == data['asn1']:
			s3_resource = boto3.resource('s3')
			my_bucket = s3_resource.Bucket(AWS_STORAGE_BUCKET_NAME)
			
			file_to_download1 = 'automatedpeering/AWS_Data/'+k+'/graph/willingness_sorted/own_'+k+'.pdf'
			file_to_download2 = 'automatedpeering/AWS_Data/'+k+'/graph/willingness_sorted/diff_'+k+'.pdf'
			file_to_download3 = 'automatedpeering/AWS_Data/'+k+'/graph/willingness_sorted/ratio_'+k+'.pdf'
			file_to_download4 = 'automatedpeering/AWS_Data/'+k+'/graph/overlap.png'
			
			my_bucket.download_file(file_to_download1, 'app/static/own_graph.pdf')
			my_bucket.download_file(file_to_download2, 'app/static/diff_graph.pdf')
			my_bucket.download_file(file_to_download3, 'app/static/ratio_graph.pdf')
			my_bucket.download_file(file_to_download4, 'app/static/overlap.png')


			with ZipFile('app/static/results.zip', 'w' ) as zipObj:
 
				zipObj.write('app/static/own_graph.pdf')
				zipObj.write('app/static/diff_graph.pdf')
				zipObj.write('app/static/ratio_graph.pdf')
				zipObj.write('app/static/overlap.png')
			
			ppc_data = {}
			with open('app/appdata/ppc_data.json') as f:
				ppc_data = json.load(f)

			ppc_data = ppc_data[k]
			# content = {}
			# for pair in ppc_data['data']:
			# 	if pair['ID']==k:
			# 		content[k]=pair
			# 		break

			r = make_response(render_template('result.html', ppc=ppc_data))

			r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
			r.headers["Pragma"] = "no-cache"
			r.headers["Expires"] = "0"
			r.headers['Cache-Control'] = 'public, max-age=0'
			return r
