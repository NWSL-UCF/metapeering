from chalice import Chalice
import mysql.connector
from mysql.connector import Error
import json
import chalicelib.rds_config

app = Chalice(app_name='peeringdb_api')


@app.route('/', methods=['GET'])
def index():
    API_TYPE_IX = "ix"
    API_TYPE_FAC = "fac"
    API_TYPE_NET = "net"

    parameters = app.current_request.query_params
    api_type = parameters['type']
    isp_id = parameters['id']

    if api_type == API_TYPE_IX:
        try:
            return get_data_ix(isp_id)
        except Error as e:
            return json.dumps({'Error' : 'ASN does not exist in the database.'})
    elif api_type == API_TYPE_FAC:
        try:
            return get_data_fac(isp_id)
        except Error as e:
            return json.dumps({'Error' : 'ASN does not exist in the database.'})
    elif api_type == API_TYPE_NET:
        try:
            return get_data_net(isp_id)
        except Error as e:
            return json.dumps({'Error' : 'ASN does not exist in the database.'})
    else:
        return json.dumps({'Status' : 'Bad Request'})

def get_info_ratio(id):

    try:
        con = get_db_connection()

        peering_dict = {"data" : []}
        cur = con.cursor()

        query = """ SELECT info_ratio FROM peeringdb_network WHERE id = %s """
        data = (id,)
        cur.execute(query, data)
        res = cur.fetchall()
        res_out = [item for t in res for item in t]

        con.commit()
        cur.close()
        con.close()

        return res_out[0]

    except Error as e:
        print(e)

def get_data_net(id):

    try:
        con = get_db_connection()

        peering_dict = {"data" : []}
        cur = con.cursor(dictionary=True)

        query = """ SELECT * FROM peeringdb_network WHERE id = %s """
        data = (id,)
        cur.execute(query, data)
        rows = cur.fetchall()
        peering_dict["data"] = json.loads(json.dumps([dict(ix) for ix in rows], default=str))

        # get org data with org_id
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"] = get_org_data(cur, data)

        # get net_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"]["net_set"] = get_net_set(cur, data)

        # get fac_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["fac_set"] = get_fac_set(cur, data)

        # get ix_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"]["ix_set"] = get_ix_set(cur, data)

        # get netfac_set
        data = (peering_dict["data"][0]["asn"],)
        peering_dict["data"][0]["netfac_set"] = get_netfac_set(cur, data)

        #get netixlan_set
        data = (peering_dict["data"][0]["asn"],)
        peering_dict["data"][0]["netixlan_set"] = get_netixlan_set(cur, data)


        con.commit()
        cur.close()
        con.close()

        return peering_dict

    except Error as e:
        print(e)


def get_data_fac(id):

    try:
        con = get_db_connection()
        peering_dict = {"data" : []}
        cur = con.cursor(dictionary=True)

        # get data for fac type
        query = """ SELECT * FROM peeringdb_facility WHERE id = %s """
        data = (id,)
        cur.execute(query, data)
        rows = cur.fetchall()
        peering_dict["data"] = json.loads(json.dumps([dict(ix) for ix in rows], default=str))

        # get org data with org_id
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"] = get_org_data(cur, data)

        # get net_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"]["net_set"] = get_net_set(cur, data)

        # get fac_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["fac_set"] = get_fac_set(cur, data)

        # get ix_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"]["ix_set"] = get_ix_set(cur, data)

        con.commit()
        cur.close()
        con.close()

        return peering_dict

    except Error as e:
        print(e)

def get_data_ix(id):

    try:
        con = get_db_connection()

        peering_dict = {"data" : []}
        cur = con.cursor(dictionary=True)

        # get data for ix type
        query = """ SELECT * FROM peeringdb_ix WHERE id = %s """
        data = (id,)
        cur.execute(query, data)
        rows = cur.fetchall()
        peering_dict["data"] = json.loads(json.dumps([dict(ix) for ix in rows], default=str))

        # get org data with org_id
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"] = get_org_data(cur, data)

        # get net_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"]["net_set"] = get_net_set(cur, data)

        # get fac_set. PeeringInfo requires city, state, latitude, longitude for each fac in fac_set.
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["fac_set"] = get_fac_set(cur, data)

        # get ix_set
        data = (peering_dict["data"][0]["org_id"],)
        peering_dict["data"][0]["org"]["ix_set"] = get_ix_set(cur, data)

        con.commit()
        cur.close()
        con.close()

        return peering_dict

    except Error as e:
        print(e)

def get_ix_set(cursor, data):

    query = """ SELECT id FROM peeringdb_ix WHERE org_id = %s """
    cursor.execute(query, data)
    rows = cursor.fetchall()
    res = [dict(ix)['id'] for ix in rows]

    return res

def get_net_set(cursor, data):
    query = """ SELECT id FROM peeringdb_network WHERE org_id = %s """
    cursor.execute(query, data)
    rows = cursor.fetchall()
    res = [dict(ix)['id'] for ix in rows]

    return res

def get_fac_set(cursor, data):
    query = """ SELECT * FROM peeringdb_facility WHERE org_id = %s """
    cursor.execute(query, data)
    rows = cursor.fetchall()
    res = json.loads(json.dumps([dict(ix) for ix in rows], default=str))

    return res

def get_org_data(cursor, data):
    query = """ SELECT * FROM peeringdb_organization WHERE id = %s """
    cursor.execute(query, data)
    rows = cursor.fetchall()
    res = json.loads(json.dumps([dict(ix) for ix in rows], default=str))[0]

    return res

def get_netfac_set(cursor, data):
    query = """ SELECT * FROM peeringdb_network_facility WHERE local_asn = %s """
    cursor.execute(query, data)
    rows = cursor.fetchall()
    res = json.loads(json.dumps([dict(ix) for ix in rows], default=str))

    return res

def get_netixlan_set(cursor, data):
    query = """ SELECT * FROM peeringdb_network_ixlan WHERE asn = %s """
    cursor.execute(query, data)
    rows = cursor.fetchall()
    res = json.loads(json.dumps([dict(ix) for ix in rows], default=str))

    return res

def get_db_connection():

    try:
        con = mysql.connector.connect(
            host = chalicelib.rds_config.AWS_RDS_CONNECTION,
            user = chalicelib.rds_config.AWS_RDS_USER,
            password = chalicelib.rds_config.AWS_RDS_PASSWD,
            database= chalicelib.rds_config.AWS_RDS_DB
        )

        return con

    except Error as e:
        print(e)
