from .gVars import List_Of_POP_Locations, Output_Directory
import os, json

def save_pop_locations(asn1, asn2):
    pop_list = []
    for l in List_Of_POP_Locations:
        _item = {}
        _item['ID'] = l.ID
        _item['isp_type_in_peering_db'] = l.isp_type_in_peering_db
        _item['isp_id_in_peering_db'] = l.isp_id_in_peering_db
        _item['city'] = l.city
        _item['state'] = l.state
        _item['population'] = l.population
        _item['internet_penetration_percentage'] = l.internet_penetration_percentage
        _item['latitude'] = l.latitude
        _item['longitude'] = l.longitude
        _item['org_name'] = l.org_name
        _item['name'] = l.name
        pop_list.append(_item)

    file_path = os.path.join(Output_Directory, asn1 + '_' + asn2, 'pop_list.json')
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with open(file_path, 'w') as fout:
            data = {}
            data['data'] = pop_list
            json.dump(data, fout)
            fout.close()
        print("File created or opened successfully:", file_path)
    except Exception as e:
        print("Error:", e)
    # with open(os.path.join(Output_Directory, asn1+'_'+asn2+'/pop_list.json'), 'w') as fout:
    #     data = {}
    #     data['data'] = pop_list
    #     json.dump(data, fout)
    #     fout.close()

