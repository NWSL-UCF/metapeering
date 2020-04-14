from flask_wtf import Form
from wtforms import IntegerField, SelectField, SubmitField
from customoptgroupselect import ExtendedSelectField

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
	
# 	asn1 = SelectField('ASN 1 (Your own ISP)', choices=options)
# 	asn2 = SelectField('ASN 2 (Potential peer ISP)', choices=options)
# 	asn2 = IntegerField('ASN 2')
	asn1 = ExtendedSelectField('ASN 1', choices= [('', 'Select your own ISP')] + options_grouped_asn)
	asn2 = ExtendedSelectField('ASN 2', choices= [('', 'Select potential peer ISP')] + options_grouped_asn)
	threshold = IntegerField('Threshold')
	submit = SubmitField('Submit')
