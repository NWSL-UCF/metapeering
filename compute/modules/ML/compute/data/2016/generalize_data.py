import urllib.parse
import http.client
import json
import os
import sys
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
load_dotenv()


def add_location_from_cache(facs, facs_with_locs):
    if os.path.exists("./compute/data/2016/geo_api_calls.json"):
        with open("./compute/data/2016/geo_api_calls.json", "r") as f:
            api_calls = json.load(f)
    else:
        api_calls = dict()

    for ID, fac in facs.items():
        if fac.get("latitude", False):
            continue
        address = "{},{},{},{},{}".format(
            fac["address1"], fac["city"], fac["state"], fac["zipcode"], fac["country"])
        fac_ = facs_with_locs.get(ID, None)
        if fac_:
            address_ = "{},{},{},{},{}".format(fac_["address1"], fac_[
                "city"], fac_["state"], fac["zipcode"], fac_["country"])
        else:
            if address.endswith("US"):
                api_calls[ID] = {"address": address,
                                 "location": api_calls.get(ID, {"location": []})["location"]}
            continue

        matchRatio = fuzz.token_set_ratio(address, address_)
        if matchRatio >= 90:
            facs[ID]["latitude"] = facs_with_locs[ID]["latitude"]
            facs[ID]["longitude"] = facs_with_locs[ID]["longitude"]
        else:
            if address.endswith("US"):
                api_calls[ID] = {"address": address,
                                 "location": api_calls.get(ID, {"location": []})["location"]}
            continue

    return api_calls


def add_location_from_API(facs, api_calls):

    excluded = ["611", "2029", "2601", "2078", "2077"]
    conn = http.client.HTTPConnection('api.positionstack.com')
    API_KEY = os.getenv("POSITIONSTACK_API_KEY")

    print("Not including results for {} due to bad address".format(excluded))

    for key in excluded:
        del api_calls[key]

    for ID, fac in api_calls.items():
        if fac["location"]:
            facs[ID]["latitude"] = fac["location"][0]
            facs[ID]["longitude"] = fac["location"][1]
            continue
        params = urllib.parse.urlencode({
            'access_key': API_KEY,
            'query': fac["address"],
            'region': 'United States',
            'limit': 1,
        })
        try:
            conn.request('GET', '/v1/forward?{}'.format(params))
            res = conn.getresponse()
            geocode_result = json.loads(res.read().decode('utf-8'))
            api_calls[ID]["location"] = [geocode_result["data"][0]
                                         ["latitude"], geocode_result["data"][0]["longitude"]]
            facs[ID]["latitude"] = api_calls[ID]["location"][0]
            facs[ID]["longitude"] = api_calls[ID]["location"][1]
        except:
            print(fac["address"])

    with open("./compute/data/2016/geo_api_calls.json", "w") as f:
        json.dump(api_calls, f)


if __name__ == "__main__":
    '''
    for root, dirs, files in os.walk("./2016/"):
        for fName in files:
            if ".json" in fName:

                dictData = dict()
                with open(os.path.join(root, fName), "r") as f:
                    data = json.load(f)
                    for item in data:
                        dictData[item["id"]] = item
                        # del dictData[item["id"]]["id"]
                with open(os.path.join(root, fName), "w") as f:
                    json.dump(dictData, f)
    '''
    # Adding lat/long values for facilities
    with open("./compute/data/2016/fac.json", "r") as f:
        facs = json.load(f)

    with open("./compute/data/2021/fac.json", "r") as f:
        facs_with_locs = json.load(f)

    api_calls = add_location_from_cache(facs, facs_with_locs)
    add_location_from_API(facs, api_calls)

    input("Press Enter to proceed with Geocoding")

    with open("./compute/data/2016/fac_loc.json", "w") as f:
        json.dump(facs, f)
