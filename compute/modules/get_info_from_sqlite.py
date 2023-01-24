'''
Created on Jan 18, 2023

@author: Natalia Colmenares
'''

import sqlite3
import json

'''
Contains the queries required to retrieve the data for PeeringInfo.py from peeringdb local sqlite.

@note return of these methods were modeled to imitate data returned from a normal api call.
Example: https://www.peeringdb.com/api/net/1418
'''

def get_info_ratio(id):

    con = sqlite3.connect("peeringdb.sqlite3")
    peering_dict = {"data" : []}
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    res = cur.execute("SELECT info_ratio FROM peeringdb_network WHERE id = ?", (id,)).fetchall()
    res_out = [item for t in res for item in t]

    con.commit()
    con.close()

    return res_out[0]

def get_data_net(id):

    con = sqlite3.connect("peeringdb.sqlite3")
    peering_dict = {"data" : []}
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    rows = cur.execute("SELECT * FROM peeringdb_network WHERE id = ?", (id,)).fetchall()
    peering_dict["data"] = json.loads(json.dumps([dict(ix) for ix in rows]))

    # get org data with org_id
    rows = cur.execute("SELECT * FROM peeringdb_organization WHERE id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    peering_dict["data"][0]["org"] = json.loads(json.dumps([dict(ix) for ix in rows]))[0]

    # get net_set
    res = cur.execute("SELECT id FROM peeringdb_network WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["net_set"] = res_out

    # get fac_set
    res = cur.execute("SELECT id FROM peeringdb_facility WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["fac_set"] = res_out

    # get ix_set
    res = cur.execute("SELECT id FROM peeringdb_ix WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["ix_set"] = res_out

    rows = cur.execute("SELECT * FROM peeringdb_network_facility WHERE local_asn = ?", (peering_dict["data"][0]["asn"],)).fetchall()
    peering_dict["data"][0]["netfac_set"] = json.loads(json.dumps([dict(ix) for ix in rows]))

    rows = cur.execute("SELECT * FROM peeringdb_network_ixlan WHERE asn = ?", (peering_dict["data"][0]["asn"],)).fetchall()
    peering_dict["data"][0]["netixlan_set"] = json.loads(json.dumps([dict(ix) for ix in rows]))

    con.commit()
    con.close()

    return peering_dict

def get_data_fac(id):

    con = sqlite3.connect("peeringdb.sqlite3")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # get data for fac type
    peering_dict = {"data" : []}
    rows = cur.execute("SELECT * FROM peeringdb_facility WHERE id = ?", (id,)).fetchall()
    peering_dict["data"] = json.loads(json.dumps([dict(ix) for ix in rows]))

    # get org data with org_id
    rows = cur.execute("SELECT * FROM peeringdb_organization WHERE id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    peering_dict["data"][0]["org"] = json.loads(json.dumps([dict(ix) for ix in rows]))[0]

    # get net_set
    res = cur.execute("SELECT id FROM peeringdb_network WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["net_set"] = res_out

    # get fac_set
    res = cur.execute("SELECT id FROM peeringdb_facility WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["fac_set"] = res_out

    # get ix_set
    res = cur.execute("SELECT id FROM peeringdb_ix WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["ix_set"] = res_out

    con.commit()
    con.close()

    return peering_dict

def get_data_ix(id):

    con = sqlite3.connect("peeringdb.sqlite3")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # get data for ix type
    peering_dict = {"data" : []}
    rows = cur.execute("SELECT * FROM peeringdb_ix WHERE id = ?", (id,)).fetchall()
    peering_dict["data"] = json.loads(json.dumps([dict(ix) for ix in rows]))
    print(peering_dict["data"])

    # get org data with org_id
    rows = cur.execute("SELECT * FROM peeringdb_organization WHERE id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    peering_dict["data"][0]["org"] = json.loads(json.dumps([dict(ix) for ix in rows]))[0]

    # get net_set
    res = cur.execute("SELECT id FROM peeringdb_network WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["net_set"] = res_out

    # get fac_set. PeeringInfo requires city, state, latitude, longitude for each fac in fac_set.
    rows = cur.execute("SELECT * FROM peeringdb_facility WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = json.loads(json.dumps([dict(ix) for ix in rows]))
    peering_dict["data"][0]["fac_set"] = res_out

    # get ix_set
    res = cur.execute("SELECT id FROM peeringdb_ix WHERE org_id = ?", (peering_dict["data"][0]["org_id"],)).fetchall()
    res_out = [item for t in res for item in t]
    peering_dict["data"][0]["org"]["ix_set"] = res_out

    con.commit()
    con.close()

    return peering_dict
