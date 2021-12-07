info_traffic = {
    "": -20,
    "0-20Mbps": 0,
    "20-100Mbps": 1,
    "100-1000Mbps": 2,
    "1-5Gbps": 3,
    "5-10Gbps": 4,
    "10-20Gbps": 5,
    "20-50Gbps": 6,
    "50-100Gbps": 7,
    "100-200Gbps": 8,
    "200-300Gbps": 9,
    "300-500Gbps": 10,
    "500-1000Gbps": 11,
    "1 Tbps+": 12,
    "1-5Tbps": 13,
    "5-10Tbps": 14,
    "10-20Tbps": 15,
    "20-50Tbps": 16,
    "50-100Tbps": 17,
    "100+Tbps": 18,
    "0-20 Mbps": 0,
    "20-100 Mbps": 1,
    "100-1000 Mbps": 2,
    "1-5 Gbps": 3,
    "5-10 Gbps": 4,
    "10-20 Gbps": 5,
    "20-50 Gbps": 6,
    "50-100 Gbps": 7,
    "100-200 Gbps": 8,
    "200-300 Gbps": 9,
    "300-500 Gbps": 10,
    "500-1000 Gbps": 11,
    "1 Tbps+": 12,
    "1-5 Tbps": 13,
    "5-10 Tbps": 14,
    "10-20 Tbps": 15,
    "20-50 Tbps": 16,
    "50-100 Tbps": 17,
    "100 Tbps+": 18
}

info_ratio = {
	"":-10,
	"Not Disclosed": -10,
	"Heavy Outbound": -2,
	"Mostly Outbound": -1,
	"Balanced": 0,
	"Mostly Inbound": 1,
	"Heavy Inbound": 2
}

policy_general = {
    "": -5,
	"Open": 2,
	"Selective": 1,
	"Restrictive": 0,
	"No": -1
}


policy_general_combo = {
    "Open Open": 14,
    "Open Selective": 13,
    "Selective Selective": 12,
    "Open Restrictive": 11,
    "Restrictive Selective": 10,
    "Restrictive Restrictive": 9,
    " Open": 8,
    "No Open": 7,
    " Selective": 6,
    "No Selective": 5,
    " Restrictive": 4,
    "No Restrictive": 3,
    " ": 2,
    " No": 1,
    "No No": 0
}




policy_contracts = {
    "": -5,
	"Not Required": 0,
	"Private Only": 1,
	"Required": 2
}

policy_locations = {
    "": -10,
	"Not Required": 0, 
	"Preferred": 1, 
	"Required - US": 2, 
	"Required - EU": 3, 
	"Required - International": 4
}

info_type_abv = {
    "transit": "T",
    "content": "C",
    "access": "A"
}

info_type_score = {
    "*":0,
    "T":2,
    "C":3,
    "A":4
}

info_ratio_abv = {
	"Heavy Inbound": "HO",
	"Mostly Inbound": "MO",
	"Balanced": "B",
	"Mostly Outbound": "MI",
	"Heavy Outbound": "MO"
}

info_scope = {
    "Regional": "R",
    "North America": "NA",
    "Asia Pacific": "AP",
    "Europe": "E",
    "South America": "SA",
    "Africa": "Af",
    "Australia": "Au",
    "Middle East": "ME",
    "Global": "G"
}

info_scope_score = {
    "*",
    "R",
    "NA",
    "AP",
    "E",
    "SA",
    "Af",
    "Au",
    "ME",
    "G"
}