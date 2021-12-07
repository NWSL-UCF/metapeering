from flask import Blueprint, render_template, request ,redirect, url_for, session
from app.forms import MLPeeringQuerryForm
from compute.mlResult import find_output
import json, os, copy
import pandas as pd
from subprocess import call

ML = Blueprint("ml", __name__, static_folder="static", template_folder="template")

@ML.route("/", methods=["GET", "POST"])
def ml():
    form = MLPeeringQuerryForm()
    if request.method == "POST":
        if form.validate_on_submit():
            return ml_peering_query_form_handler(request.form)
        else:
            return render_template("ml.html", form=form)

    return render_template("ml.html", form=form)

def ml_peering_query_form_handler(request):
    data = {}
    data["asn1"] = request["asn1"][2:]
    data["asn2"] = request["asn2"][2:]
    session['valid'] = True
    session['peering_recommended'] = False

    pred = find_output(data["asn1"], data["asn2"])
    if pred == 1:
        session['peering_recommended'] = True
    elif pred == 0:
        session['peering_recommended'] = False
    else:
        session['valid'] = False

    session['requester'] = data["asn1"]
    session['candidate'] = data["asn2"]

    return render_template("resultML.html")
