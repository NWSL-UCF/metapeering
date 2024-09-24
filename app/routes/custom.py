from flask import Blueprint, render_template, request ,redirect, url_for, session
from app.forms import CustomPeeringQuerryForm
from compute.peeringAlgorithm import getCommmonPops, getIndvPops, customPeeringAlgo
import json, os, copy
import pandas as pd
from subprocess import call
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
        return custom_request_handler(request.form.getlist("selectedPop"))

    # If session is NOT authorized, return return.html form
    if(session.pop('authorized', False)):
        return render_template('result.html')
    else:
        raise Exception('401 Unauthorized: You cannot access this page directly.')

    # else:
        # raise Exception('404: Page Not Found: The page you are looking for does not exist!')
    # return redirect(url_for("success.success"))

def custom_peering_query_form_handler(request):
    data = {}
    try:
        data["asn1"] = request["asn1"][2:]
        data["asn2"] = request["asn2"][2:]

        # Get common Points of Presence / individual PoPs
        commonPops = getCommmonPops(int(data["asn1"]), int(data["asn2"]))
        isp_a_pops, isp_b_pops = getIndvPops(int(data["asn1"]), int(data["asn2"]))

        if len(commonPops) == 0:
            session['noCommonPops'] = True
        session['commonPops'] = commonPops
        session['ispAPops'] = isp_a_pops
        session['ispBPops'] = isp_b_pops
        session['asn1'] = data["asn1"]
        session['asn2'] = data["asn2"]
        session["authorized"] = True
    except Exception as e:
        print(e)
        return render_template(
            "errorPage.html", 
            error_message=str(e)
        )
    
    return redirect(url_for("custom.custom"))

def custom_request_handler(data):
    isp1 = ['',session.pop('asn1')]
    isp2 = ['',session.pop('asn2')]
    threshold = session.pop('threshold',0.0)

    try:
        # Check if required data is present
        if not isp1[1] or not isp2[1]:
            raise ValueError("ASN1 or ASN2 not found in session data.")

        # Pull the first ISP's data from the corresponding JSON file in the isps folder
        with open('./compute/modules/ML/compute/data/2021/isps/'+str(isp1[1])+'_peering_db_data_file.json') as f:
            jsonData = json.load(f)
            isp1[0] = jsonData["name"]

        with open('./compute/modules/ML/compute/data/2021/isps/'+str(isp2[1])+'_peering_db_data_file.json') as f:
            jsonData = json.load(f)
            print(jsonData["name"])
            isp2[0] = jsonData["name"]

        asn1_asn2 = str(isp1[1]) + "_" + str(isp2[1])

        # Making a folder for this peer pair if it doesn't already exist
        if not os.path.exists("./app/static/" + asn1_asn2):
            call("mkdir ./app/static/" + asn1_asn2, shell=True)

        # customPeeringAlgo calls ensure_isp_json_files calls PeeringInfo()
        if customPeeringAlgo(tuple(isp1),tuple(isp2), [int(num) for num in data]):
            generateContracts(str(isp1[1]), str(isp2[1]))

            ppc_data = None
            threshold_too_high = False
            peering_recommended = False
            felicity_score = 0.0

            print("\ngoing into felicity.json...")
            with open("./compute/output/"+asn1_asn2+"/felicity.json") as f:
                felicity_data = json.load(f)
                session['felicity_scores'] = {asn1_asn2: felicity_data}
                felicity_score = float(felicity_data["own"])
                print("felicity_score: ", felicity_score)

            print("\nleaving felicity.json...")  

            if felicity_score > 0.0:
                peering_recommended = True
                print("peering_recommended: ", peering_recommended)

            if felicity_score < float(threshold):
                threshold_too_high = True
                print("threshold_too_high: ", threshold_too_high)

            print("\ngoing into threshold stuff...")
            if not threshold_too_high:
                file_path = os.path.abspath(os.path.dirname('./compute/')) + "/" + "output/" + asn1_asn2 + '/graph/id.json'
                print(f"file_path: {file_path}")
                directory = os.path.dirname(file_path)
                print(f"directory: {directory}")
                if not os.path.exists(directory):
                    os.makedirs(directory)
                resultFolder = directory
                # Debugging prints
                print(f"resultFolder: {resultFolder}")
                print(f"os.path.exists(resultFolder): {os.path.exists(resultFolder)}")
                # TODO: Are these png files supposed to be created already? If so, where were they created?
                with ZipFile(asn1_asn2 + "_results.zip", "w") as zipObj:
                    zipObj.write(resultFolder + "/willingness_sorted/own_"+asn1_asn2+".png")
                    zipObj.write(resultFolder + "/willingness_sorted/diff_"+asn1_asn2+".png")
                    zipObj.write(resultFolder + "/willingness_sorted/ratio_"+asn1_asn2+".png")
                    zipObj.write(resultFolder + "/" + asn1_asn2+"_overlap.png")

                call("mv "+ asn1_asn2 + "_results.zip "+ resultFolder , shell=True)

                with open('./compute/output/'+asn1_asn2+'/ppc_data.json','r') as f:
                    ppc_data = json.load(f)[asn1_asn2]
            print("\leaving treshold stuff...")
    except Exception as e:
        print(e)
        return render_template(
            "errorPage.html", 
            error_message=str(e)
        )

    print("\ngoing into final stretch...")
        
    call('cp ./compute/output/'+asn1_asn2+'/graph/'+asn1_asn2+'_results.zip ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/'+asn1_asn2+'_overlap.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/willingness_sorted/diff_'+asn1_asn2+'.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/willingness_sorted/own_'+asn1_asn2+'.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/willingness_sorted/ratio_'+asn1_asn2+'.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('rm -r ./compute/output/'+asn1_asn2+'/', shell=True)

    print("\leaving final stretch...")

    print("peering recommended: ", peering_recommended)
    session['title'] = "Peering possibility"
    session['peering_recommended']=peering_recommended
    session['threshold_too_high']=threshold_too_high
    session['ppc']=ppc_data
    session['requester']=isp1
    session['candidate']=isp2
    session['custom']=True
    session['asn1_asn2'] = asn1_asn2

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
            print("\ndf1")
            print(df1)
            total_APC = len(df1)

            top_3_pop_indexes= [int(df1.head(3)['Index in PPC list'][i]) for i in range(min(3,len(df1)))]
            print("\ntop 3 pop indexes")
            print(top_3_pop_indexes)
            print(len(top_3_pop_indexes))

            df2 = pd.read_csv(os.path.join(root,isp1_asn+'.csv'), delimiter='\t')
            top_3_pop_ids = list(df2.loc[df2['PPC Index'].isin(top_3_pop_indexes)]['Possible Location Combinations'])
            top_3_pop_ids = [i.strip(' ').strip('[').strip(']').split(',') for i in top_3_pop_ids]
            print("\ntop 3 pop ids")
            print(top_3_pop_ids)
            print(len(top_3_pop_ids))

            for i in range(min(len(top_3_pop_indexes), len(top_3_pop_ids))):
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
