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
