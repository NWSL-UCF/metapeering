from flask import Flask, make_response, render_template, request, redirect, url_for, abort, flash
from flask_bootstrap import Bootstrap
from flask_login import current_user, login_user, login_required, logout_user
import re
import subprocess
from subprocess import call
import json
from os import listdir
from os.path import isfile, join
from zipfile import ZipFile
from flask_s3 import FlaskS3
import boto3 

from .forms import PeeringQueryForm, ContactUsForm, LoginForm
from .config import AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DATABASE_URI, USER1_PW, USER2_PW, USER3_PW
from .commands import create_tables
from .extension import db, login_manager
from .models import Feedback, User

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

uname_dict = {'my':'user3', 'sm':'user2', 'pkd':'user1', 'murat':'user3', 'shahzeb':'user2', 'prasun':'user1'}

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

app.config['USER1_PW'] = USER1_PW
app.config['USER2_PW'] = USER2_PW
app.config['USER3_PW'] = USER3_PW
login_manager.init_app(app)


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

@app.route('/user/<username>')
@login_required
def user(username):
	issues = get_issues()
	return render_template('user.html', title="Internal User", username=username, issues=issues)

@app.route('/user/<username>/login', methods=['GET', 'POST'])
def login(username):
	if current_user.is_authenticated:
		return redirect(url_for('user', username=username))
	if username not in ['murat', 'shahzeb', 'prasun']:
		return abort(404)
	login_form = LoginForm()
	if request.method == 'POST' and login_form.validate_on_submit():
		if not login_success(request.form, username):
			flash('Invalid username or password.')
			return redirect(url_for('login', username=username))
		user = User()
		user.id = username
		login_user(user)
		return redirect(url_for('user', username=username))
	return render_template('login.html', title='Login', form=login_form)
	
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('querry'))

@app.route('/success', methods=('GET', 'POST'))
def success():
    return render_template('success.html')

@app.errorhandler(401)
@app.errorhandler(404)
def page_not_found(e):
	e = str(e).split(":")
	error_code = e[0][:3]
	error_name = e[0][3:]
	error_message = e[1]
	return render_template('errorpage.html', error_code=error_code, error_name=error_name, error_message=error_message, title='Error')

@login_manager.user_loader
def user_loader(username):
	if username not in uname_dict:
		return
 	
	user = User()
	user.id = username
	return user

@login_manager.unauthorized_handler
def unauthorized_handler():
	username = request.path.split("/")[-1]
	if username in uname_dict:
		return redirect(url_for('login', username=username))
	else:
		return abort(401)
	
def login_success(request, username):
	form_username = request['username']
	password = request['password']
	if form_username not in uname_dict or form_username != username:
		return False
	return app.config[uname_dict[username].upper()+'_PW'] == password

def get_issues():
	issues = Feedback.query.all()
	return issues

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
	return request_handler_v2(data)

def request_handler_v2(data):
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
				
				aws_root = 'automatedpeering/AWS_Data_new/'
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


def request_handler_v1(data):
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

	rc = call('mkdir app/static/'+data['asn1']+'_'+data['asn2'], shell=True)
	# rc = call('rm -r app/static/*', shell=True)

	for k,v in retScores.items():
		if k.split('_')[0] == data['asn1']:
			s3_resource = boto3.resource('s3')
			my_bucket = s3_resource.Bucket(AWS_STORAGE_BUCKET_NAME)
			
			file_to_download1 = 'automatedpeering/AWS_Data/'+k+'/graph/willingness_sorted/own_'+k+'.png'
			file_to_download2 = 'automatedpeering/AWS_Data/'+k+'/graph/willingness_sorted/diff_'+k+'.png'
			file_to_download3 = 'automatedpeering/AWS_Data/'+k+'/graph/willingness_sorted/ratio_'+k+'.png'
			file_to_download4 = 'automatedpeering/AWS_Data/'+k+'/graph/overlap.png'
			
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
			
			ppc_data = {}
			with open('app/appdata/ppc_data.json') as f:
				ppc_data = json.load(f)

			ppc_data = ppc_data[k]
			# content = {}
			# for pair in ppc_data['data']:
			# 	if pair['ID']==k:
			# 		content[k]=pair
			# 		break
			requesterISP = (data['asn1'],asn_name[int(data['asn1'])])
			candidateISP = (data['asn2'],asn_name[int(data['asn2'])])
			
			r = make_response(render_template('result.html', ppc=ppc_data, title='Peering possibility', requester=requesterISP,candidate=candidateISP))

			r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
			r.headers["Pragma"] = "no-cache"
			r.headers["Expires"] = "0"
			r.headers['Cache-Control'] = 'public, max-age=0'
			return r
