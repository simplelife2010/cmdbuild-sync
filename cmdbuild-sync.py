from chef import ChefAPI, Node, Search, Role
import inspect
import psycopg2
import json
import os
import sys

def appName():
	return os.path.basename(__file__).split(".")[0]

def connect(conf):
	cs = "dbname="
	cs += conf["dbName"]
	cs += " user="
	cs += conf["dbUser"]
	cs += " password="
	cs += conf["dbPassword"]
	cs += " host="
	cs += conf["dbHost"]
	print("Connecting to database (" + cs + ")...")
	conn = psycopg2.connect(cs)
	conn.set_session(autocommit=False)
	print("Connecting to database...Done.")
	return conn

def createImportTable(cur, conf):
	cs = "CREATE TABLE \""
	cs += conf["tableName"]
	cs += "\" ("
	for column in conf["column"]:
		cs += "\""
		cs += column["name"]
		cs += "\" "
		cs += column["dataType"]
		cs += ", "
	cs = cs[0:-2]
	cs += ");"
	print("Creating import table...")
	print(cs);
	cur.execute(cs)
	print("Creating import table...Done.")

def dropImportTable(cur, conf):
	ds = "DROP TABLE \""
	ds += conf["tableName"]
	ds += "\""
	print("Dropping import table...")
	print(ds)
	cur.execute(ds)
	print("Dropping import table...Done.")
	
def config(configFileName):
	print("Reading config file...")
	with open(configFileName) as file:
		conf = json.load(file)
	print("Reading config file...Done.")
	return conf
	
def nodeInfo(api, nodeName, conf):
	restPath = "/organizations/"
	restPath += conf["chefOrganization"]
	restPath += "/nodes/"
	restPath += nodeName
	return api.request("GET", restPath).json()
	
def clientInfo(api, nodeName, conf):
	restPath = "/organizations/"
	restPath += conf["chefOrganization"]
	restPath += "/clients/"
	restPath += nodeName
	restPath += "/keys/default"
	return api.request("GET", restPath).json()
	
def value(info, path):
	pathItems = path.split(".")
	p = info
	try:
		for item in pathItems:
			p = p.get(item)
	except:
		p = None
	return p
	
def valueString(column, ni, ci, conf):
	co = column["chefObject"]
	v = ""
	path = column["chefPath"]
	if co == "node":
		v = value(ni, path)
	elif co == "client":
		v = value(ci, path)
	if v == None:
		return None
	dt = column["dataType"]
	if dt[0:7] == "varchar":
		vs = "'" + v + "'"
	elif dt[0:7] == "decimal":
		vs = float(v)
	elif dt == "integer":
		vs = int(v)
	return vs
	
def row(api, node, conf):
	row = {}
	ni = nodeInfo(api, node, conf)
	ci = clientInfo(api, node, conf)
	for column in conf["column"]:
		columnName = column["name"]
		vs = valueString(column, ni, ci, conf)
		if vs != None:
			row[columnName] = valueString(column, ni, ci, conf)
	return row
	
def fillImportTable(cur, conf):
	print("Filling import table...");
	api = ChefAPI(conf["chefURL"],
				  conf["chefKey"],
				  conf["chefUser"],
				  ssl_verify=conf["chefSSLVerify"])
	nodes = api.request("GET", "/organizations/aim/nodes").json()
	for node in nodes:
		r = row(api, node, conf)
		
	print("Filling import table...Done.")
				  
configFileName = appName() + ".json"
conf = config(configFileName)
conn = connect(conf)
cur = conn.cursor()
dropImportTable(cur, conf)
createImportTable(cur, conf)
fillImportTable(cur, conf)
conn.commit()

sys.exit(0)	
	
for node_name in nodes:
	print(node_name)
	node_info = api.request("GET", "/organizations/aim/nodes/" + node_name).json()
	node_info_row = {}
	node_info_row["NodeName"] = node_name
	node_info_row["ChefEnvironment"] = node_info.get("chef_environment", "")
	automatic = node_info.get("automatic", {})
	node_info_row["CPU0ModelName"] = automatic.get("cpu", {}).get("0", {}).get("model_name", "")
	filesystem = automatic.get("filesystem", {}).get("by_mountpoint", {})
	node_info_row["FSRootPercentUsed"] = filesystem.get("/", {}).get("percent_used", "")
	node_info_row["FSRootInodesPercentUsed"] = filesystem.get("/", {}).get("inodes_percent_used", "")
	node_info_row["FSSDPercentUsed"] = filesystem.get("/media/sd", {}).get("percent_used", "")
	node_info_row["FSSDInodesPercentUsed"] = filesystem.get("/media/sd", {}).get("inodes_percent_used", "")
	node_info_row["KernelRelease"] = automatic.get("kernel", {}).get("release", "")
	node_info_row["OSDescription"] = automatic.get("lsb", {}).get("description", "")
	node_info_row["OhaiTime"] = automatic.get("ohai_time", "")
	node_info_row["FQDN"] = automatic.get("fqdn", "")
	node_info_row["Uptime"] = automatic.get("uptime", "")
	node_info_row["ChefVersion"] = automatic.get("chef_packages", {}).get("chef", {}).get("version", "")
	node_info_row["Timezone"] = automatic.get("time", {}).get("timezone", "")
	node_info_row["RootSSHKey"] = automatic.get("i4i", {}).get("root_ssh_key", "")
	node_info_row["CookbookI4IDeviceVersion"] = automatic.get("cookbooks", {}).get("i4i-device", {}).get("version", "")
	normal = node_info.get("normal", {})
	node_info_row["ReverseTunnelPort"] = normal.get("i4i", {}).get("reverse_tunnel_port", "")
	key = api.request("GET", "/organizations/aim/clients/" + node_name + "/keys/default").json()
	node_info_row["ChefClientPublicKey"] = key.get("public_key", "")
	node_info_row["ChefClientPublicKeyExpDate"] = key.get("expiration_date", "")
	
	column_names = ""
	values = ""
	for column_name, value in node_info_row.items():
		column_names += column_name + ", "
		values += "'" + str(value) + "', "
	insert_string = "INSERT INTO ChefImport ("
	insert_string += column_names[0:-2] + ") VALUES ("
	insert_string += values[0:-2] + ");"
	cur.execute(insert_string)
conn.commit()
conn.close()

#create_string = "CREATE TABLE IF NOT EXISTS ChefImport ("
#create_string += "NodeName CHAR(50), "
#create_string += "ChefEnvironment CHAR(50), "
#create_string += "CPU0ModelName CHAR(50), "
#create_string += "FSRootPercentUsed CHAR(5), "
#create_string += "FSRootInodesPercentUsed CHAR(5), "
#create_string += "FSSDPercentUsed CHAR(5), "
#create_string += "FSSDInodesPercentUsed CHAR(5), "
#create_string += "KernelRelease CHAR(50), "
#create_string += "OSDescription CHAR(100), "
#create_string += "OhaiTime CHAR(50), "
#create_string += "FQDN CHAR(100), "
#create_string += "Uptime CHAR(50), "
#create_string += "ChefVersion CHAR(50), "
#create_string += "Timezone CHAR(50), "
#create_string += "RootSSHKey CHAR(500), "
#create_string += "CookbookI4IDeviceVersion CHAR(50), "
#create_string += "ReverseTunnelPort CHAR(10), "
#create_string += "ChefClientPublicKey CHAR(500), "
#create_string += "ChefClientPublicKeyExpDate CHAR(50));"
#cur.execute(create_string)