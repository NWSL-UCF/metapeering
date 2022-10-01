from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.quoprimime import body_check
#from inspect import _SourceObjectType
#from msilib.schema import MIME
import boto3
import json
from compute.peeringAlgorithm import getCommmonPops, getIndvPops, customPeeringAlgo
import json, os, copy
import pandas as pd
from subprocess import call
from zipfile import ZipFile
import shutil
import statistics

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName='Message-Queue-Metapeering', region_name='us-east-1')

def send_email_with_attachment(receiver, attachment_filename, attachment_path):

    message = MIMEMultipart()

    # Testing verified users first
    sender = "metapeering@gmail.com"
    subject = "Your Report is Ready"
    body = "Your generated report is attached."

    message["To"] = receiver
    message["From"] = sender
    message['Subject'] = subject
    message_body = MIMEText(body, "plain")

    message.attach(message_body)

    part = MIMEApplication(open(attachment_path, 'rb').read())
    part.add_header("Content-Disposition", "attachment", filename = attachment_filename)
    message.attach(part)

    ses_client = boto3.client("ses", region_name='us-east-1')

    response = ses_client.send_raw_email(Source = sender, Destinations = [receiver], RawMessage={"Data" : message.as_string()})

    return response


def compute_asns(isp1, isp2, threshold, email):

    commonPops = getCommmonPops(isp1[1], isp2[1])
    isp_a_pops, isp_b_pops = getIndvPops(isp1[1], isp2[1])

    with open("./compute/data/cache/"+str(isp1[1])+"_peering_db_data_file.json") as f:
        jsonData = json.load(f)
        isp1[0] = jsonData["data"]["name"]

    with open("./compute/data/cache/"+str(isp2[1])+"_peering_db_data_file.json") as f:
        jsonData = json.load(f)
        isp2[0] = jsonData["data"]["name"]

    asn1_asn2 = str(isp1[1]) + "_" + str(isp2[1])
    if not os.path.exists("./app/static/" + asn1_asn2):
        call("mkdir ./app/static/" + asn1_asn2, shell=True)
    data = []

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

            call("mv "+ asn1_asn2 + "_results.zip "+ resultFolder , shell=True)

        # results that are used for top 3 peering deals
        with open('./compute/output/'+asn1_asn2+'/ppc_data.json','r') as f:
            ppc_data = json.load(f)[asn1_asn2]
            print(ppc_data)

    call('cp ./compute/output/'+asn1_asn2+'/graph/'+asn1_asn2+'_results.zip ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/'+asn1_asn2+'_overlap.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/willingness_sorted/diff_'+asn1_asn2+'.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/willingness_sorted/own_'+asn1_asn2+'.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('cp ./compute/output/'+asn1_asn2+'/graph/willingness_sorted/ratio_'+asn1_asn2+'.png ./app/static/'+asn1_asn2+'/', shell=True)
    call('rm -r ./compute/output/'+asn1_asn2+'/', shell=True)

    # Add ppc data to the results zip file
    with open('./app/static/' + asn1_asn2 + '/ppc_data', 'w') as f:
        json.dump(ppc_data, f)

    # Clean up
    shutil.make_archive('result_zip_' + asn1_asn2, 'zip', './app/static/' + asn1_asn2)
    call('rm -r ./app/static/'+asn1_asn2+'/', shell=True)
    call('rm -r ./compute/data/cache/' + isp1[1] + '_peering_db_data_file.json', shell=True)

    print("sending email...")
    response = send_email_with_attachment(email, 'result_zip_' + asn1_asn2 + '.zip', './result_zip_' + asn1_asn2 + '.zip')
    call('rm -r ./result_zip_' + asn1_asn2 + '.zip', shell=True)
    print(response)


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

    print("successful generation")

def process_message(message_body):
    msg = json.loads(message_body)
    msg = msg['responsePayload']
    msg = json.loads(msg)

    data = {
    "asn1" : msg['id'],
    "asn1_string" : msg['asn1'],
    "asn2" : msg['asn2'],
    "threshold" : msg['threshold'],
    "receiver" : msg['email']
    }

    isp1 = ['', data["asn1"]]
    isp2 = ['',int(data["asn2"])]
    threshold = data['threshold']
    email = data['receiver']

    data["asn1"] = data["asn1"] + "_" + data["asn1_string"]
    print(data['asn1'])

    # create a file with asn name
    with open('./compute/data/cache/' + data['asn1'] + '_peering_db_data_file.json', "w") as f:
        json.dump(msg, f)

    compute_asns(isp1, isp2, int(float(threshold)), email)
    pass

if __name__ == "__main__":
    while True:
        messages = queue.receive_messages(WaitTimeSeconds=20)
        for message in messages:
            try:
                process_message(message.body)
            except Exception as e:
                print(e)
                # delete message that had an error for now
                message.delete()
                continue
            message.delete()
