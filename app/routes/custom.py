from flask import Blueprint, render_template, request ,redirect, url_for, session
from app.forms import CustomPeeringQuerryForm
from compute.peeringAlgorithm import getCommmonPops, getIndvPops, customPeeringAlgo
import json, os, copy
import pandas as pd
import shutil
from zipfile import ZipFile

import statistics

Custom = Blueprint("custom", __name__, static_folder="static", template_folder="template")

@Custom.route("/", methods=["GET", "POST"])
def custom():
    form = CustomPeeringQuerryForm()
    if request.method == "POST":
        if form.validate_on_submit():
            return custom_peering_query_form_handler(request.form)
        else:
            return render_template("custom.html", form=form)

    return render_template("custom.html", form=form)

@Custom.route("/result", methods=["GET","POST"])
def customResult():
    if request.method == "POST":
        # if len(request.form.getlist("selectedPop")) == 0:
        #     session['noCommonPops'] = True
        #     return redirect(url_for("custom.custom"))
        return custom_request_handler(request.form.getlist("selectedPop"))

    if(session.pop('authorized', False)):
        return render_template('result.html')
    else:
        raise Exception('401Unauthorized: You cannot access this page directly.')

    # else:
        # raise Exception('404: Page Not Found: The page you are looking for does not exist!')
    # return redirect(url_for("success.success"))

def custom_peering_query_form_handler(request):
    data = {}
    data["asn1"] = request["asn1"][2:]
    data["asn2"] = request["asn2"][2:]
    data["threshold"] = request["threshold"]

    commonPops = getCommmonPops(int(data["asn1"]), int(data["asn2"]))
    isp_a_pops, isp_b_pops = getIndvPops(int(data["asn1"]), int(data["asn2"]))

    #isp_locationA = []

    #for i in range(0, len(isp_a_pops)):
    #    isp_locationA.append(isp_a_pops[i].location)

    #print(isp_locationA)

    #isp_locationA = {'longitude': [pair[0] for pair in isp_a_pops], 'latitude': [pair[1] for pair in isp_a_pops]}
    #isp_center = (statistics.median(isp_locationA["longitude"]), statistics.median(isp_locationA["latitude"]))
    #print(isp_center)


    # commonPops = []
    if len(commonPops) == 0:
        session['noCommonPops'] = True
    session['commonPops'] = commonPops
    session['ispAPops'] = isp_a_pops
    session['ispBPops'] = isp_b_pops
    session['asn1'] = data["asn1"]
    session['asn2'] = data["asn2"]
    session['threshold'] = data["threshold"]
    session["authorized"] = True
    # print(session)
    return redirect(url_for("custom.custom"))
    # return custom_request_handler(data)


def custom_request_handler(data):
    isp1 = ['',session.pop('asn1')]
    isp2 = ['',session.pop('asn2')]
    threshold = session.pop('threshold',0.5)

    with open("./compute/data/cache/"+str(isp1[1])+"_peering_db_data_file.json") as f:
        jsonData = json.load(f)
        isp1[0] = jsonData["data"]["name"]

    with open("./compute/data/cache/"+str(isp2[1])+"_peering_db_data_file.json") as f:
        jsonData = json.load(f)
        isp2[0] = jsonData["data"]["name"]

    asn1_asn2 = str(isp1[1]) + "_" + str(isp2[1])
    app_static_as1_asn2_path = os.path.join("app", "static", asn1_asn2)
    if not os.path.exists(app_static_as1_asn2_path):
        os.makedirs(app_static_as1_asn2_path, exist_ok=True)

    if customPeeringAlgo(tuple(isp1),tuple(isp2), [int(num) for num in data]):

        generateContracts(str(isp1[1]), str(isp2[1]))

        ppc_data = None
        threshold_too_high = False
        peering_recommended = False
        felicity_score = 0.0

        with open("./compute/output/"+asn1_asn2+"/felicity.json") as f:
            felicity_score = float(json.load(f)["own"])

        if felicity_score > 0.0:
            peering_recommended = True
            if felicity_score < float(threshold):
                threshold_too_high = True


        if not threshold_too_high:
            resultFolder = './compute/output/'+asn1_asn2+'/graph/'
            with ZipFile(asn1_asn2 + "_results.zip", "w") as zipObj:
                zipObj.write(resultFolder + "willingness_sorted/own_"+asn1_asn2+".png")
                zipObj.write(resultFolder + "willingness_sorted/diff_"+asn1_asn2+".png")
                zipObj.write(resultFolder + "willingness_sorted/ratio_"+asn1_asn2+".png")
                zipObj.write(resultFolder + asn1_asn2+"_overlap.png")

            source_path = os.path.join(asn1_asn2 + "_results.zip")
            destination_path = os.path.join(resultFolder, asn1_asn2 + "_results.zip")
            shutil.move(source_path, destination_path)

        with open('./compute/output/'+asn1_asn2+'/ppc_data.json','r') as f:
            ppc_data = json.load(f)[asn1_asn2]
    compute_output_asn1_asn2_path = os.path.join("compute", "output", asn1_asn2)
    app_static_as1_asn2_path = os.path.join("app", "static", asn1_asn2)
    shutil.copy2(os.path.join(compute_output_asn1_asn2_path, "graph", asn1_asn2 + "_results.zip"), os.path.join(app_static_as1_asn2_path))
    shutil.copy2(os.path.join(compute_output_asn1_asn2_path, "graph", asn1_asn2+"_overlap.png"), os.path.join(app_static_as1_asn2_path))
    shutil.copy2(os.path.join(compute_output_asn1_asn2_path, "graph", "willingness_sorted", "diff_" + asn1_asn2 + ".png"), os.path.join(app_static_as1_asn2_path))
    shutil.copy2(os.path.join(compute_output_asn1_asn2_path, "graph", "willingness_sorted", "own_" + asn1_asn2 + ".png"), os.path.join(app_static_as1_asn2_path))
    shutil.copy2(os.path.join(compute_output_asn1_asn2_path, "graph", "willingness_sorted", "ratio_" + asn1_asn2 + ".png"), os.path.join(app_static_as1_asn2_path))
    shutil.rmtree(os.path.join(compute_output_asn1_asn2_path))

    session['title'] = "Peering possibility"
    session['peering_recommended']=peering_recommended
    session['threshold_too_high']=threshold_too_high
    session['ppc']=ppc_data
    session['requester']=isp1
    session['candidate']=isp2
    session['custom']=True

    return redirect(url_for("custom.customResult"))


def generateContracts(isp1_asn, isp2_asn):
    pop_list = dict()
    top_3_pops_details = {}
    isp_pair = isp1_asn+'_'+isp2_asn

    with open('./compute/output/'+isp_pair+'/pop_list.json') as f:
        pop_list = json.load(f)

    for root, dirs, files in os.walk('./compute/output/'+isp_pair+'/'):
        if('algorithm_report.csv' in files):
            sorting_strategy = root.split('/')[-1]

            df1 = pd.read_csv(os.path.join(root,'algorithm_report.csv'), delimiter='\t')
            total_APC = len(df1)

            top_3_pop_indexes= [int(df1.head(3)['Index in PPC list'][i]) for i in range(min(3,len(df1)))]

            df2 = pd.read_csv(os.path.join(root,isp1_asn+'.csv'), delimiter='\t')
            top_3_pop_ids = list(df2.loc[df2['PPC Index'].isin(top_3_pop_indexes)]['Possible Location Combinations'])
            top_3_pop_ids = [i.strip(' ').strip('[').strip(']').split(',') for i in top_3_pop_ids]

            for i in range(len(top_3_pop_indexes)):
                top_3_pop_ids[i] = [int(top_3_pop_ids[i][j]) for j in range(len(top_3_pop_ids[i]))]

            temp_data = {}
            for i, lst  in enumerate(top_3_pop_ids):
                temp_lst = []
                for pop in pop_list['data']:
                    if(pop['ID'] in lst):
                        temp_lst.append(pop)
                temp_data[i+1] = copy.deepcopy(temp_lst)
            temp_data['total_apc'] = total_APC


            try:
                top_3_pops_details[isp_pair][sorting_strategy] = temp_data
            except:
                top_3_pops_details[isp_pair] = {}
                top_3_pops_details[isp_pair][sorting_strategy] = temp_data

    with open('./compute/output/'+isp_pair+'/ppc_data.json','w') as f:
        json.dump(top_3_pops_details, f)
