import json, os, sys
from itertools import permutations
from get_caida_data import get_caida_data
import pandas as pd
import traceback
from collections import defaultdict
from scores import policy_general, policy_contracts, policy_locations, info_ratio, info_traffic, info_type_abv, info_scope, info_scope_score, info_type_score, policy_general_combo

PRED_YEAR = 2021

info_types = {
	"access": "A",
	"content": "C",
	"transit": "T"
}

def getInfoScope(d1, d2):
	scope = "{}-{}".format(min(info_scope.get(d1,"*"), info_scope.get(d2,"*")), max(info_scope.get(d1,"*"), info_scope.get(d2,"*")))
	# scope = info_scope_score[scope.split("-")[0]] + info_scope_score[scope.split("-")[1]]
	if "*" in scope:
		return "*"
	return scope

def getInfoType(d1, d2):
	Type = "{}-{}".format(min(info_type_abv.get(d1,"*"), info_type_abv.get(d2, "*")), max(info_type_abv.get(d1,"*"), info_type_abv.get(d2, "*")))
	# Type = info_type_score[Type.split("-")[0]] + info_type_score[Type.split("-")[1]]
	# if Type <= 4:
	# 	return 0
	if "*" in Type:
		return "*"
	return Type

def getInfoRatioDiff(d1, d2):
	return abs(info_ratio[d1] + info_ratio[d2])


def getInfoTrafficDiff(d1, d2):
	return abs(info_traffic[d1] - info_traffic[d2])


def getPolicyContractsDiff(d1, d2):
	return abs(policy_contracts[d1] - policy_contracts[d2])

def getPolicyGeneralDiff(d1, d2):
	return policy_general_combo[f"{min(d1,d2)} {max(d1,d2)}"]
	# return abs(policy_general[d1] - policy_general[d2])

def getPolicyLocationsDiff(d1, d2):
	return abs(policy_locations[d1] - policy_locations[d2])

def convertToLocation(pop_list):
	locs = set()
	for pop in pop_list:
		loc = tuple(pop["location"])
		locs.add(loc)
	return locs

def ratio(a, b):
	a = max(1, a)
	b = max(1, b)

	return min(a,b)/max(a,b)

def getCommonPopCount(d1, d2):
	pl1 = convertToLocation(d1)
	pl2 = convertToLocation(d2)

	commonPopCount = len([a for a in pl1 if a in pl2])
	return commonPopCount

def getPopCountDiff(d1, d2):
	return abs(len(d1) - len(d2))

def getPopAffinity(pR, pC, c):
	den = ((pR-c) + (pC-c) + c)
	aR = (pC - c) / den
	aC = (pR - c) / den

	return (aR*aC)**0.5

def cleanDict(any_dict):
	for k, v in any_dict.items():
		if v is None:
			any_dict[k] = 0
		elif type(v) == type(any_dict):
			cleanDict(v)

def addPeeringDBData(data, ASrel, nets):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]

	for pair in ASrel["peering"]:
		data["peering"].append(1)

	for pair in ASrel["not_peering"]:
		data["peering"].append(0)

	for pair in ASrelC:
		# print(nets[pair[0]]["info_prefixes4"], nets[pair[1]]["info_prefixes4"], nets[pair[0]]["info_prefixes6"],  nets[pair[1]]["info_prefixes6"])
		#No Need
		# data["ipv6"].append(bool(nets[pair[0]]["info_ipv6"] == nets[pair[1]]["info_ipv6"]))	###
		# data["multicast"].append(int(nets[pair[0]]["info_multicast"] == nets[pair[1]]["info_multicast"])) ###
		# data["unicast"].append(int(nets[pair[0]]["info_unicast"] == nets[pair[1]]["info_unicast"])) ###
		# data["same_org"].append(bool((nets[pair[0]]["org_id"] == nets[pair[1]]["org_id"]) == (nets[pair[0]]["org_id"] != ""))) ###
		# data["same_irr_as_set"].append(bool((nets[pair[0]]["irr_as_set"] == nets[pair[1]]["irr_as_set"]) == (nets[pair[0]]["irr_as_set"] != "")))
		#BOOLS:
		data["policy_ratio"].append(bool(nets[pair[0]]["policy_ratio"] == nets[pair[1]]["policy_ratio"])) ###

		#INTS:
		data["traffic_ratio_diff"].append(getInfoRatioDiff(nets[pair[0]]["info_ratio"], nets[pair[1]]["info_ratio"])) ###
		data["traffic_diff"].append(getInfoTrafficDiff(nets[pair[0]]["info_traffic"], nets[pair[1]]["info_traffic"])) ###
		data["policy_contracts"].append(getPolicyContractsDiff(nets[pair[0]]["policy_contracts"], nets[pair[1]]["policy_contracts"])) ###
		try:
			data["policy_general"].append(getPolicyGeneralDiff(nets[pair[0]]["policy_general"], nets[pair[1]]["policy_general"])) ###
		except Exception as e:
			print(nets[pair[0]])
			raise e
		data["policy_locations"].append(getPolicyLocationsDiff(nets[pair[0]]["policy_locations"], nets[pair[1]]["policy_locations"])) ###
		data["common_pop_count"].append(getCommonPopCount(nets[pair[0]]["pop_list"], nets[pair[1]]["pop_list"])) ###
		data["prefixes4"].append(abs(nets[pair[0]]["info_prefixes4"] - nets[pair[1]]["info_prefixes4"]))
		data["prefixes6"].append(abs(nets[pair[0]]["info_prefixes6"] - nets[pair[1]]["info_prefixes6"]))
		data["pop_count_diff"].append(getPopCountDiff(nets[pair[0]]["pop_list"], nets[pair[1]]["pop_list"]))
		data["non_common_pops"].append((len(nets[pair[0]]["pop_list"])+len(nets[pair[1]]["pop_list"])) - (2 * data["common_pop_count"][-1]))
		data["pop_affinity"].append(getPopAffinity(len(nets[pair[0]]["pop_list"]), len(nets[pair[1]]["pop_list"]), data["common_pop_count"][-1]))
		#STRINGS:
		# data["scope"].append(getInfoScope(nets[pair[0]]["info_scope"], nets[pair[1]]["info_scope"]))
		# data["type"].append(getInfoType(nets[pair[0]]["info_type"], nets[pair[1]]["info_type"]))

	return data

def addCAIDAData(data, ASrel, CAIDA):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]
	ASrelC = [tuple([str(pair[0]),str(pair[1])]) for pair in ASrelC]
	for pair in ASrelC:
		try:
			#not needed:
			# data["cliqueMember"].append(bool(CAIDA[pair[0]]["cliqueMember"] == CAIDA[pair[1]]["cliqueMember"])) ###
			# data["seen"].append(bool(CAIDA[pair[0]]["seen"] == CAIDA[pair[1]]["seen"])) ###
			# data["same_country"].append(bool(CAIDA[pair[0]]["country"]["iso"] == CAIDA[pair[1]]["country"]["iso"])) ###
			# data["same_source"].append(bool(CAIDA[pair[0]]["source"] == CAIDA[pair[1]]["source"])) ###

			#STRINGS:
			# None

			#INTS:

			data["rank_diff"].append(abs(CAIDA[pair[0]]["rank"] - CAIDA[pair[1]]["rank"])) ###
			data["total_diff"].append(abs(CAIDA[pair[0]]["asnDegree"]["total"] - CAIDA[pair[1]]["asnDegree"]["total"])) ###
			data["customer_diff"].append(abs(CAIDA[pair[0]]["asnDegree"]["customer"] - CAIDA[pair[1]]["asnDegree"]["customer"])) ###
			data["peer_diff"].append(abs(CAIDA[pair[0]]["asnDegree"]["peer"] - CAIDA[pair[1]]["asnDegree"]["peer"])) ###
			data["provider_diff"].append(abs(CAIDA[pair[0]]["asnDegree"]["provider"] - CAIDA[pair[1]]["asnDegree"]["provider"])) ###

			data["ASN_count_diff"].append(abs(CAIDA[pair[0]]["cone"]["numberAsns"] - CAIDA[pair[1]]["cone"]["numberAsns"])) ###
			data["num_prefixes_diff"].append(abs(CAIDA[pair[0]]["cone"]["numberPrefixes"] - CAIDA[pair[1]]["cone"]["numberPrefixes"]))
			data["num_addresses_diff"].append(abs(CAIDA[pair[0]]["cone"]["numberAddresses"] - CAIDA[pair[1]]["cone"]["numberAddresses"]))

			# data["ASN_count_ratio"].append(ratio(CAIDA[pair[0]]["cone"]["numberAsns"], CAIDA[pair[1]]["cone"]["numberAsns"]))
			# data["num_prefixes_ratio"].append(ratio(CAIDA[pair[0]]["cone"]["numberPrefixes"], CAIDA[pair[1]]["cone"]["numberPrefixes"]))
			# data["num_addresses_ratio"].append(ratio(CAIDA[pair[0]]["cone"]["numberAddresses"], CAIDA[pair[1]]["cone"]["numberAddresses"]))


		except Exception as e:
			data["rank_diff"].append(float('inf'))
			data["total_diff"].append(float('inf'))
			data["customer_diff"].append(float('inf'))
			data["peer_diff"].append(float('inf'))
			data["provider_diff"].append(float('inf'))

			data["ASN_count_diff"].append(float('inf'))
			data["num_prefixes_diff"].append(float('inf'))
			data["num_addresses_diff"].append(float('inf'))
			for k in data.keys():
				data[k].pop()
			# traceback.print_exc()
			# raise e
	return data

def addMetaPeeringScores(data, ASrel, MPResults):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]
	for pair in ASrelC:
		data["affinity"].append(MPResults[pair][0])
		data["willingness_diff"].append(abs(MPResults[tuple([pair[0], pair[1]])][1] - MPResults[tuple([pair[1], pair[0]])][1]))

	return data

def generateCustomerCones(year, US):
	print("Generating Customer Cones...", end="\t")
	class Node:
		def __init__(self,ASN):
			self.ASN = ASN
			self.customers = set()
			self.customerASNs = set()
			self.customerCone = None
		def getCustomerCount(self,ex=None):
			if self.customerCone:
				return len(self.customerCone)
			cc = set([self.ASN])
			if ex:
				for c in self.customers:
					if c.ASN != ex:
						cc = cc.union(c.getCustomerCone())
			else:
				for c in self.customers:
					cc = cc.union(c.getCustomerCone())
			self.customerCone = cc
			return len(cc)
		def getCustomerCone(self,ex=None):
			if self.customerCone:
				return self.customerCone
			cc = set([self.ASN])
			if ex:
				for c in self.customers:
					if c.ASN != ex:
						cc = cc.union(c.getCustomerCone())
			else:
				for c in self.customers:
					cc = cc.union(c.getCustomerCone())
			self.customerCone = cc
			return cc

	cones = dict()
	with open("../compute/data/{}/as-relation.txt".format(year), 'r') as fin:

		for l in fin:
			if l[0] == '#':
				continue
			l = l.strip().split("|")
			l = [int(x) for x in l]
			if l[0] not in cones:
				cones[l[0]] = Node(l[0])
			if l[1] not in cones:
				cones[l[1]] = Node(l[1])

			# if l[0] in US and l[1] in US:
			if l[-1] == -1:

				cones[l[0]].customers.add(cones[l[1]])
				cones[l[0]].customerASNs.add(l[1])
				# if l[0] == 10886:
				# 	print(l[1],cones[10886].getCustomerCone(), cones[10886].customerASNs)

	print("Done")
	# print(cones[42].getCustomerCone(), cones[42].customerASNs)
	# print(cones[10886].getCustomerCone(), cones[10886].customerASNs)


	return cones

def addPCSRatio(data, ASrel, cones):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]
	for pair in ASrelC:
		if pair[0] in cones[pair[1]].customerASNs:
			p1 = cones[pair[1]].getCustomerCount(ex=pair[0])
			p0 = cones[pair[0]].getCustomerCount()
			data["PCSR"].append(min(p0,p1)/max(p0,p1))
		elif pair[1] in cones[pair[0]].customerASNs:
			p0 = cones[pair[0]].getCustomerCount(ex=pair[1])
			p1 = cones[pair[1]].getCustomerCount()
			data["PCSR"].append(min(p0,p1)/max(p0,p1))
		else:
			data["PCSR"].append(1)

	return data

def addCustomerOverlap(data, ASrel, cones):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]
	for pair in ASrelC:

		p0 = cones[pair[0]].getCustomerCone()
		p1 = cones[pair[1]].getCustomerCone()
		data["cone_overlap"].append(len(p0.intersection(p1))/len(p0.union(p1)))


		# data["ccone"].append(s)
		# data["overlap"].append(len(cones[pair[0]].getCustomerCone().intersection(cones[pair[1]].getCustomerCone()))/(min(cones[pair[0]].getCustomerCount(), cones[pair[1]].getCustomerCount())))
		# print(cones[pair[0]].getCustomerCone(), cones[pair[1]].getCustomerCone())
	return data

def getMetaPeeringResults(year):
	print("Generating Meta-Peering Data...", end="\t")
	MPdata = dict()

	with open("../compute/output/{}/stokes.output.txt".format(year), "r") as fin:
		for l in fin:
			ld = json.loads(l)
			MPdata[tuple([
				ld["isp_a"]["asn"],
				ld["isp_b"]["asn"]
			])] = tuple([
				ld["affinity_score"]["own"],
				ld["willingness_score"]["ratio"]
			])
	print("Done", len(MPdata))
	return MPdata


def getNetsWithUSCoverage(year):
	print("Generating NETS Data...", end="\t")
	nets = dict()
	for root, _, files in os.walk(f"../compute/data/{year}/isps/"):
		for fName in files:
			if "peering_db_data_file" in fName:
				with open(os.path.join(root, fName), "r") as f:
					try:
						data = json.load(f)
						nets[int(fName.replace(
							"_peering_db_data_file.json", ""))] = data
					except Exception as e:
						print(fName)
						raise(e)

	print("Done")
	cleanDict(nets)
	return nets

def generateNetsData(year):
	print("Generating NETS Data...", end="\t")
	nets = dict()

	with open(f"../compute/data/{year}/isps.json", "r") as f:
		data = json.load(f)
		for item in data:
			nets[item["asn"]] = item
	cleanDict(nets)
	return nets


def generateCaidaData(year, US):
	print("Generating CAIDA Data...", end="\t")
	caidaData = {"peering": list(), "not_peering": list()}
	with open("../compute/data/{}/as-relation.txt".format(year), 'r') as fin:

		for l in fin:
			if l[0] == '#':
				continue
			l = l.strip().split("|")
			l = [int(x) for x in l]
			if l[0] in US and l[1] in US:
				if l[-1] == 0:
					caidaData["peering"].append(tuple([l[0], l[1]]))
				else:
					caidaData["not_peering"].append(tuple([l[0], l[1]]))

	print("Done", "Peering: ", len(
		caidaData["peering"]), "Not Peering: ", len(caidaData["not_peering"]))

	return caidaData

def addASTypes(data, ASrel, nets):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]
	for pair in ASrelC:

		t1 = info_types.get(nets[pair[0]]["info_type"],"")
		t2 = info_types.get(nets[pair[1]]["info_type"],"")
		data["type"].append("{}-{}".format(min(t1,t2),max(t1,t2)))
	return data

def addASNs(data, ASrel, nets):
	ASrelC = ASrel["peering"] + ASrel["not_peering"]
	for pair in ASrelC:

		data["pair"].append("{}-{}".format(min(pair[0],pair[1]),max(pair[0],pair[1])))
	return data


def gather(year):
	nets = getNetsWithUSCoverage(year)
	# print(nets)
	# nets = generateNetsData(year)

	# pairs = set(permutations(list(nets.keys()), 2))
	ASrel = generateCaidaData(year, set(nets.keys()))
	cones = generateCustomerCones(year, set(nets.keys()))

	# MPResults = getMetaPeeringResults(year)

	CAIDA = get_caida_data()

	data = defaultdict(list)

	data = addPeeringDBData(data, ASrel, nets)
	data = addASTypes(data, ASrel, nets)
	data = addASNs(data, ASrel, nets)
	data = addCustomerOverlap(data, ASrel, cones)
	data = addCAIDAData(data, ASrel, CAIDA)
	# data = addPCSRatio(data, ASrel, cones)

	# data = addMetaPeeringScores(data, ASrel, MPResults)

	df = pd.DataFrame(data)

	return df
