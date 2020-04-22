from flask_wtf import Form
from wtforms import IntegerField, DecimalField, SelectField, SubmitField, validators
from app.customoptgroupselect import ExtendedSelectField

class PeeringQueryForm(Form):
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
						(11492, 'cableone'), 
						(209, 'centurylink'),
						(7843, 'charter'), 
						(7922, 'comcast'), 
						(22773, 'cox'), 
						(4181, 'tds'), 
						(7029, 'windstream')
						)
			  	),
                ('Content ISPs', (
						(20940, 'akamai'), 
						(16509, 'amazon'), 
						(62955, 'ebay'), 
						(32934, 'facebook'), 
						(15169, 'google'), 
						(8075, 'microsoft'), 
						(2906, 'netflix')
						)
				),
               	('Transit ISPs', (
						(23520, 'columbus'), 
						(174, 'cogent'), 
						(6939, 'he'), 
						(2914, 'ntt'), 
						(3491, 'pccw'), 
						(1239, 'sprint'), 
						(701, 'verizon'), 
						(6461, 'zayo')
						)
				)
			]
	
	asn1 = ExtendedSelectField('ASN 1', 
							choices= [('-1', 'Select your own ISP')] + options_grouped_asn, coerce=int)
	asn2 = ExtendedSelectField('ASN 2', 
							choices= [('-1', 'Select potential peer ISP')] + options_grouped_asn, coerce=int)
	threshold = DecimalField('Threshold',
							[validators.NumberRange(min=0.1, max=1.0, message="Value must be between 0.1 and 1.0")])
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