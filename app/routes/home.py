from flask import Blueprint, render_template, request, session
from app.forms import PeeringQueryForm
import boto3, json
from subprocess import call
from zipfile import ZipFile
from app.config import (
    AWS_STORAGE_BUCKET_NAME,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    DATABASE_URI,
    USER1_PW,
    USER2_PW,
    USER3_PW,
)
Home = Blueprint("home", __name__, static_folder="static", template_folder="template")


@Home.route("/", methods=["GET", "POST"])
def querry():
    form = PeeringQueryForm()
    if request.method == "POST" and form.validate_on_submit():
        return peering_query_form_handler(request.form)
    return render_template("submit.html", form=form)

asn_name = {
    20940: "Akamai",
    16509: "Amazon",
    11492: "Cableone",
    209: "Centurylink",
    7843: "Charter",
    174: "Cogent",
    23520: "Columbus",
    7922: "Comcast",
    22773: "Cox",
    62955: "Ebay",
    32934: "Facebook",
    15169: "Google",
    6939: "He",
    8075: "Microsoft",
    2906: "Netflix",
    2914: "Ntt",
    3491: "Pccw",
    1239: "Sprint",
    4181: "Tds",
    701: "Verizon",
    7029: "Windstream",
    6461: "Zayo",
}

def peering_query_form_handler(request):
    data = {}
    data["asn1"] = request["asn1"]
    data["asn2"] = request["asn2"]
    data["threshold"] = request["threshold"]

    return request_handler(data)

def request_handler(data):
    requesterISP = (asn_name[int(data["asn1"])], data["asn1"])
    candidateISP = (asn_name[int(data["asn2"])], data["asn2"])
    ppc_data = None
    threshold_too_high = False
    peering_recommended = False
    asn1_asn2 = data["asn1"] + "_" + data["asn2"]

    with open("app/appdata/felicity.json") as f:
        felicity_scores = json.load(f)
        try:
            asn1_felicity_score = float(felicity_scores[asn1_asn2]["own"])
            if asn1_felicity_score >= 0.0:
                peering_recommended = True
                if asn1_felicity_score < float(data["threshold"]):
                    threshold_too_high = True
                """
				Peering Recommended, but first, check if threshold not too high.
				Otherwise, Not Recommended.
				"""
                if not threshold_too_high:
                    call("mkdir app/static/" + asn1_asn2, shell=True)
                    s3_resource = boto3.resource("s3")
                    my_bucket = s3_resource.Bucket(AWS_STORAGE_BUCKET_NAME)

                    aws_root = "automatedpeering/AWS_Data/"
                    file_to_download1 = (
                        aws_root + asn1_asn2 + "/own_" + asn1_asn2 + ".png"
                    )
                    file_to_download2 = (
                        aws_root + asn1_asn2 + "/diff_" + asn1_asn2 + ".png"
                    )
                    file_to_download3 = (
                        aws_root + asn1_asn2 + "/ratio_" + asn1_asn2 + ".png"
                    )
                    file_to_download4 = aws_root + asn1_asn2 + "/overlap.png"

                    resultFolder = (
                        "app/static/" + data["asn1"] + "_" + data["asn2"] + "/"
                    )
                    my_bucket.download_file(
                        file_to_download1, resultFolder + "own_graph.png"
                    )
                    my_bucket.download_file(
                        file_to_download2, resultFolder + "diff_graph.png"
                    )
                    my_bucket.download_file(
                        file_to_download3, resultFolder + "ratio_graph.png"
                    )
                    my_bucket.download_file(
                        file_to_download4, resultFolder + "overlap.png"
                    )

                    with ZipFile(resultFolder + "results.zip", "w") as zipObj:
                        zipObj.write(resultFolder + "own_graph.png")
                        zipObj.write(resultFolder + "diff_graph.png")
                        zipObj.write(resultFolder + "ratio_graph.png")
                        zipObj.write(resultFolder + "overlap.png")

                    with open("app/appdata/ppc_data.json") as f:
                        ppc_data = json.load(f)[asn1_asn2]
        except Exception as e:
            print(e)
    
    session['title'] = "Peering possibility"
    session['peering_recommended']=peering_recommended
    session['threshold_too_high']=threshold_too_high
    session['ppc']=ppc_data
    session['requester']=requesterISP
    session['candidate']=candidateISP

    return render_template("result.html")
