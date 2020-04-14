from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import re
import subprocess
from subprocess import call
import json
from forms import PeeringQueryForm
from os import listdir
from os.path import isfile, join


app = Flask(__name__)
app.config['SECRET_KEY'] = 'metapeering'
Bootstrap(app)

isp_dict = {'cableone': 11492, 'centurylink': 209, 'charter':7843, 'comcast':7922, 'cox':22773, 'tds':4181, 'windstream':7029, 
			'akamai':20940, 'amazon': 16509, 'ebay':62955, 'facebook': 32934, 'google': 15169, 'microsoft': 8075, 'netflix': 2906,
			'columbus':23520, 'cogent': 174, 'he':6939, 'ntt': 2914, 'pccw':3491, 'sprint': 1239, 'verizon':701, 'zayo':6461 }

# @app.route('/')
# def default():
# 	print "Disabled Route"
# 	return "Disabled Route"
	# with open('runServer.sh', 'rb') as file:
	# 	script = file.read()
	# 	rc = call(script, shell=True)

	# with open('upload.json','r') as f:
	# 	j = json.load(f)
	# 	return j["link"]

	# return "Welcome to Meta Peering!"


@app.route('/', methods=['GET','POST'])
def querry():
	form = PeeringQueryForm()
	if request.method == 'POST' and form.is_submitted():
		return form_handler(request.form)
		# return render_template(form_handler(request.form), form=form)
	return render_template('submit.html', form=form)

@app.route('/isps')
def isps():
	return isp_dict

def form_handler(request):
	data = {}
	if re.match(r"^[0-9]+$",request['asn1']):
		data['asn1'] = request['asn1']
	else:
		return "ERROR: ASN1 value invalid. Value needs to be an integer."
	if re.match(r"^[0-9]+$",request['asn2']):
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
		with open('felicity.json') as f:
			scores = json.load(f)
			for k,v in scores.items():
				if data['asn1'] in k:
					retScores[k] = v['own']
	else:
		retScores = {}
		with open('felicity.json') as f:
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

	rc = call('mkdir result', shell=True)
	rc = call('rm -r result/*', shell=True)

	for k,v in retScores.items():
		rc = call('cp -R output/'+k+'/graph/willingness_sorted result/'+k, shell=True)
	rc = call('tar -cvzf result.tar.gz result', shell=True)
	output = subprocess.check_output('curl -F "file=@result.tar.gz" https://file.io', shell=True)
	output = json.loads(output)
	retVal = {}
	retVal['Download Link'] = output['link']
	return retVal




if __name__ == '__main__':
	# app.run(debug=True)
	app.run(debug=True,port=5001)
