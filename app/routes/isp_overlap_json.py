from flask import Blueprint, jsonify
from flask import request
import os
import json

ISP_OVERLAP_JSON = Blueprint("isp_overlap", __name__, static_folder="static", template_folder="template")

DATA_DIR = "compute/modules/ML/compute/data/2021/isps"

@ISP_OVERLAP_JSON.route("/")
def isp_overlap_json():
    asn1 = request.args.get("asn1")
    asn2 = request.args.get("asn2")
    
    # File names
    asn1_file = os.path.join(DATA_DIR, f"{asn1}_peering_db_data_file.json")
    asn2_file = os.path.join(DATA_DIR, f"{asn2}_peering_db_data_file.json")
    print("Looking for\n\t", asn1_file, "\n\t", asn2_file)
    try:
        with open(asn1_file) as f1, open(asn2_file) as f2:
            asn1_data = json.load(f1)
            asn2_data = json.load(f2)

    except FileNotFoundError:
        return jsonify({"error": "Invalid ASN, no data file found for one of the ASNs."}), 404
    asn1_pops = asn1_data["pop_list"]
    asn2_pops = asn2_data["pop_list"]
    overlapping_pops = [pop for pop in asn1_pops if pop["isp_id_in_peering_db"] in [pop["isp_id_in_peering_db"] for pop in asn2_pops]]

    #Remove overlaps from original lists
    for pop in asn1_pops:
        if pop in overlapping_pops:
            pop['both_asn_here'] = True
        else:
            pop['both_asn_here'] = False
    for pop in asn2_pops:
        if pop in overlapping_pops:
            pop['both_asn_here'] = True
        else:
            pop['both_asn_here'] = False

    
    return jsonify({"overlapping_pops": overlapping_pops, "asn1_pops": asn1_pops, "asn2_pops": asn2_pops})