from flask import Blueprint, render_template, request, session
from app.forms import PeeringQueryForm
#from compute.modules.get_isp_list import get_isp_lat_long
import boto3, json
from subprocess import call
from zipfile import ZipFile
from decimal import Decimal
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
    # If the form is submitted and also valid
    if request.method == "POST" and form.validate_on_submit():
        return peering_query_form_handler(request.form)
    # submit.html is essentially a blank page and the form is rendered in it
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
    data["threshold"] = Decimal(0)
    # data["threshold"] = request["threshold"]

    return request_handler(data)

def request_handler(data):
    # Takes in both selected ISPs
    requesterISP = (asn_name[int(data["asn1"])], data["asn1"])
    candidateISP = (asn_name[int(data["asn2"])], data["asn2"])
    # Setting default values / flags
    ppc_data = None
    threshold_too_high = False
    peering_recommended = False
    # This is how they're referenced in the JSON (i.e. asn1_asn2)
    asn1_asn2 = data["asn1"] + "_" + data["asn2"]
    felicity_scores = []

    #isp_a_pop_list, isp_b_pop_list = get_isp_lat_long(requesterISP[0],requesterISP[1], candidateISP[0], candidateISP[1])

    # Open felicity.json w/ all felicity scores
    with open("app/appdata/felicity.json") as f:
        # The entire JSON file information is loaded into this variable (big array)
        felicity_scores = json.load(f)
        try:
            # Each felicity score includes diff, own & ratio number values
            asn1_felicity_score = float(felicity_scores[asn1_asn2]["own"])
            # Make sure felicity score is a valid number before continuing
            if asn1_felicity_score >= 0.0:
                peering_recommended = True
                # If the felicity score is lower than the threshold, the threshold is too high
                if asn1_felicity_score < float(data["threshold"]):
                    threshold_too_high = True
                """
				Peering Recommended, but first, check if threshold not too high.
				Otherwise, Not Recommended.
				"""
                if not threshold_too_high:
                    # Making the folder that all the graphs will go inside
                    call("mkdir app/static/" + asn1_asn2, shell=True)
                    # Referencing the S3 bucket
                    s3_resource = boto3.resource("s3")
                    my_bucket = s3_resource.Bucket(AWS_STORAGE_BUCKET_NAME)

                    """
                    Taking all the info we have pre-generated, putting it into the folder,
                    and having it as a variable to use.
                    The graph data is stored in the S3 bucket on AWS
                    """
                    # Making the file names for the graphs
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

                    # The resutling folder where we will put this stuff on local
                    resultFolder = (
                        "app/static/" + data["asn1"] + "_" + data["asn2"] + "/"
                    )
                    # Download the actual images from AWS S3
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

                    # If you want your results emailed to you, this puts it in a zip folder (not currently active)
                    with ZipFile(resultFolder + "results.zip", "w") as zipObj:
                        zipObj.write(resultFolder + "own_graph.png")
                        zipObj.write(resultFolder + "diff_graph.png")
                        zipObj.write(resultFolder + "ratio_graph.png")
                        zipObj.write(resultFolder + "overlap.png")

                    # ppc_data.json = The data for each peering point (would be taken from Caida)
                    with open("app/appdata/ppc_data.json") as f:
                        ppc_data = json.load(f)[asn1_asn2]
                        #print(ppc_data)

        except Exception as e:
            print(e)

    # All these session variables can be used in the result.html
    session['title'] = "Peering possibility"
    session['peering_recommended']=peering_recommended
    session['threshold_too_high']=threshold_too_high
    session['ppc']=ppc_data
    session['requester']=requesterISP
    session['candidate']=candidateISP
    session['felicity_scores']=felicity_scores
    session['asn1_asn2']=asn1_asn2

    return render_template("result.html")
