class PoPLocation(object):
    '''
    @note: We've initialized ID with -1. And, then increase as we continue adding new PoP. Thus we get ID starting from 0.
    This helps us to access the "List_Of_POP_Locations" more easily, as we are adding PoPs there after we create one.
    So, List_Of_POP_Locations[0] will always give us the PoP with ID = 0 and so on. 
    @param list_of_asn_who_has_their_pop_here: is a list of ISP AS numbers, who has their Point Of Presence (POP) establishment here. 
    '''
    ID = -1

    def __init__(self, isp_type_in_peering_db, isp_id_in_peering_db, city, state, latitude, longitude, org_name, name):
        PoPLocation.ID += 1
        self.ID = PoPLocation.ID
        self.org_name = org_name
        self.name = name # TODO: What is this supposed to be?
        self.isp_type_in_peering_db = isp_type_in_peering_db
        self.isp_id_in_peering_db = isp_id_in_peering_db
        self.city = city
        self.state = state
        self.population = 0
        self.internet_penetration_percentage = 1.0
        self.latitude = latitude
        self.longitude = longitude
        self.list_of_asn_who_has_their_pop_here = []
        
    def __str__(self):
        return "PoPLocation ID: {}, (PeeringDB) ISP Type: {}, (PeeringDB) ISP ID: {}, City: {}, State: {}, Population: {}".format(self.ID, self.isp_type_in_peering_db, self.isp_id_in_peering_db, self.city, self.state, self.population)
 