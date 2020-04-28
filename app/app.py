from flask import Flask, render_template, request, redirect, url_for
from flask import make_response
from flask_bootstrap import Bootstrap
import re
import subprocess
from subprocess import call
import json
from app.forms import PeeringQueryForm, ContactUsForm
from os import listdir
from os.path import isfile, join
from flask_s3 import FlaskS3
import boto3 
from app.config import AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DATABASE_URI
from zipfile import ZipFile

from .commands import create_tables
from .extension import db
from .models import Feedback

asn_name = {
	20940: 'Akamai',
	16509: 'Amazon',
	11492: 'Cableone',
	209: 'Centurylink',
	7843: 'Charter',
	174: 'Cogent',
	23520: 'Columbus',
	7922: 'Comcast',
	22773: 'Cox',
	62955: 'Ebay',
	32934: 'Facebook',
	15169: 'Google',
	6939: 'He',
	8075: 'Microsoft',
	2906: 'Netflix',
	2914: 'Ntt',
	3491: 'Pccw',
	1239: 'Sprint',
	4181: 'Tds',
	701: 'Verizon',
	7029: 'Windstream',
	6461: 'Zayo'
}


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

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

db.init_app(app)
app.cli.add_command(create_tables)


@app.route('/', methods=['GET','POST'])
def querry():
	form = PeeringQueryForm()
	if request.method == 'POST' and form.validate_on_submit():
		return peering_query_form_handler(request.form)
	return render_template('submit.html', form=form)

@app.route('/glossary')
def glossary():
	return render_template('glossary.html', title='Glossary')

@app.route('/feedback', methods=['GET','POST'])
def feedback():
	form = ContactUsForm()
	if request.method == 'POST' and form.validate_on_submit():
		feedback_form_handler(request.form)
		return redirect(url_for('success'))
	return render_template('feedback.html', title="Feedback", form=form)

@app.route('/success', methods=('GET', 'POST'))
def success():
    return render_template('success.html')

def feedback_form_handler(request):
	fullname = request['name']
	email = request['email']
	message = request['body']
	
	feedback = Feedback(fullname=fullname, 
				email=email,
				message=message)
	
	db.session.add(feedback)
	db.session.commit()
	return

def peering_query_form_handler(request):
	data = {}
	data['asn1'] = request['asn1']
	data['asn2'] = request['asn2']
	data['threshold'] = request['threshold']
	
	return request_handler(data)

def request_handler(data):
	requesterISP = (data['asn1'],asn_name[int(data['asn1'])])
	candidateISP = (data['asn2'],asn_name[int(data['asn2'])])
	ppc_data = None
	threshold_too_high = False
	asn1_asn2 = data['asn1']+'_'+data['asn2']

	with open('app/appdata/felicity.json') as f:
		felicity_scores = json.load(f)
		try:
			asn1_felicity_score = float(felicity_scores[asn1_asn2]['own'])
			if asn1_felicity_score >= 0.0 and asn1_felicity_score < float(data['threshold']):
				threshold_too_high = True
				
			"""
			Peering Recommended, but first, check if threshold not too high.
			Otherwise, Not Recommended.
			"""
			if not threshold_too_high:
				rc = call('mkdir app/static/'+asn1_asn2, shell=True)
				s3_resource = boto3.resource('s3')
				my_bucket = s3_resource.Bucket(AWS_STORAGE_BUCKET_NAME)
				
				aws_root = 'automatedpeering/AWS_Data/'
				file_to_download1 = aws_root+asn1_asn2+'/own_'+asn1_asn2+'.png'
				file_to_download2 = aws_root+asn1_asn2+'/diff_'+asn1_asn2+'.png'
				file_to_download3 = aws_root+asn1_asn2+'/ratio_'+asn1_asn2+'.png'
				file_to_download4 = aws_root+asn1_asn2+'/overlap.png'
				print(file_to_download1)
				resultFolder = 'app/static/'+data['asn1']+'_'+data['asn2']+'/'
				my_bucket.download_file(file_to_download1, resultFolder+'own_graph.png')
				my_bucket.download_file(file_to_download2, resultFolder+'diff_graph.png')
				my_bucket.download_file(file_to_download3, resultFolder+'ratio_graph.png')
				my_bucket.download_file(file_to_download4, resultFolder+'overlap.png')
		
				with ZipFile(resultFolder+'results.zip', 'w' ) as zipObj:
					zipObj.write(resultFolder+'own_graph.png')
					zipObj.write(resultFolder+'diff_graph.png')
					zipObj.write(resultFolder+'ratio_graph.png')
					zipObj.write(resultFolder+'overlap.png')
				
				with open('app/appdata/ppc_data.json') as f:
					ppc_data = json.load(f)[asn1_asn2]
		except Exception as e:
			pass
			
	r = make_response(render_template('result.html', title='Peering possibility', low_current_threshold=threshold_too_high, ppc=ppc_data, requester=requesterISP,candidate=candidateISP))

	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	r.headers["Pragma"] = "no-cache"
	r.headers["Expires"] = "0"
	r.headers['Cache-Control'] = 'public, max-age=0'
	return r
