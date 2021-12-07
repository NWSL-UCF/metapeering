import json

if __name__ == "__main__":

    with open("./compute/data/2021/peeringdb_dump.json", "r") as f:
        data = json.load(f)
        for key, value in data.items():
            temp_data = value["data"]
            dump_data = dict()
            try:
                for item in temp_data:
                    dump_data[item["id"]] = item
            except:
                continue
            with open("./compute/data/2021/{}.json".format(key), "w") as f2:
                json.dump(dump_data, f2)
