from flask_wtf import Form, FlaskForm
from wtforms import IntegerField, DecimalField, SelectField, StringField, TextAreaField, SubmitField, PasswordField, validators
from app.customoptgroupselect import ExtendedSelectField

class PeeringQueryForm(FlaskForm):
	options = [
				(20940, 'akamai'), 
				(16509, 'amazon'), 
				(11492, 'cableone'), 
				(209, 'centurylink'),
				(7843, 'charter'), 
				(174, 'cogent'), 
				(23520, 'columbus'), 
				(7922, 'comcast'), 
				(22773, 'cox'), 
				(62955, 'ebay'), 
				(32934, 'facebook'), 
				(15169, 'google'), 
				(6939, 'he'), 
				(8075, 'microsoft'), 
				(2906, 'netflix'),
				(2914, 'ntt'), 
				(3491, 'pccw'), 
				(1239, 'sprint'), 
				(4181, 'tds'), 
				(701, 'verizon'), 
				(7029, 'windstream'),
				(6461, 'zayo')
			]
    
	options_grouped_asn = [
				('Access ISPs', (
						(11492, 'Cable ONE, Inc.'), 
						(209, 'CenturyLink Communications, LLC'),
						(7843, 'Charter Communications Inc.'), 
						(7922, 'Comcast Cable Communications, LLC'), 
						(22773, 'Cox Communications Inc.'), 
						(4181, 'TDS Telecom'), 
						(7029, 'Windstream Communications LLC')
						)
			  	),
                ('Content ISPs', (
						(20940, 'Akamai International B.V.'), 
						(16509, 'Amazon'), 
						(62955, 'Ebay'), 
						(32934, 'Facebook'), 
						(15169, 'Google'), 
						(8075, 'Microsoft Corporation'), 
						(2906, 'Netflix')
						)
				),
               	('Transit ISPs', (
						(23520, 'Columbus Networks USA, Inc.'), 
						(174, 'Cogent Communications'), 
						(6939, 'Hurricane Electric LLC'), 
						(2914, 'NTT America, Inc.'), 
						(3491, 'PCCW Global Inc.'), 
						(1239, 'Sprint'), 
						(701, 'Verizon Communications, Inc.'), 
						(6461, 'Zayo (Abovenet Communications Inc.)')
						)
				)
			]
	
	asn1 = ExtendedSelectField('ASN 1', 
							choices= [('-1', 'Select your own ISP')] + options_grouped_asn, coerce=int)
	asn2 = ExtendedSelectField('ASN 2', 
							choices= [('-1', 'Select potential peer ISP')] + options_grouped_asn, coerce=int)
	threshold = DecimalField('Threshold',
							[validators.NumberRange(min=0.0, max=1.0, message="Value must be between 0.0 and 1.0")])
	submit = SubmitField('Submit')
	
	def validate(self):
		if not Form.validate(self):
			return False
		asn1_val = int(self.asn1.data) 
		asn2_val = int(self.asn2.data)
		if asn1_val == -1:
			self.asn1.errors.append("Please select ASN1.")
		if asn2_val == -1:
			self.asn1.errors.append("Please select ASN2.")
		if asn1_val == asn2_val:
			self.asn1.errors.append("ASN1 and ANS2 can not be same. Please choose different ASN1.")
			self.asn2.errors.append("ASN1 and ANS2 can not be same. Please choose different ASN2.")
			return False
		return True
	

class ContactUsForm(FlaskForm):
	name = StringField('Name', [validators.DataRequired()])
	email = StringField('Email', [validators.Email(message='Not a valid email address.'),
        							validators.DataRequired()])
	body = TextAreaField('Message', [validators.DataRequired(),
									validators.Length(min=4, message='Your message is too short')])
	submit = SubmitField('Submit')
	
	
class LoginForm(FlaskForm):
	username = StringField('Username', [validators.DataRequired()])
	password = PasswordField('Password', [validators.DataRequired()])
	submit = SubmitField('Login')