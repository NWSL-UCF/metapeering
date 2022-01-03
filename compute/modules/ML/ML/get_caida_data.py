import json

def cleanDict(any_dict):
    for k, v in any_dict.items():
        if v is None:
            any_dict[k] = 0
        elif type(v) == type(any_dict):
            cleanDict(v)

def get_caida_data():

    data = dict()
    with open("../compute/data/caida_restful_dump.json", "r") as f:
        data = json.load(f)

    # remKeys = ["asn", "asnName", "organization", "cliqueMember",
    #            "seen", "longitude", "latitude", "country", "announcing"]

    # for k in data.keys():
    #     for key in remKeys:
    #         del data[k][key]
    cleanDict(data)
    return data
