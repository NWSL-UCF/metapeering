from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField

class submitQuerry(FlaskForm):
	asn1 = IntegerField('ASN 1')
	asn2 = IntegerField('ASN 2')
	threshold = IntegerField('Threshold')
	submit = SubmitField('Submit')