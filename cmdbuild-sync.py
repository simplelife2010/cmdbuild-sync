from chef import ChefAPI
import inspect
import psycopg2
import json
import os

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
		vs = str(v)
	elif dt == "integer":
		vs = str(v)
	elif dt == "timestamptz":
		vs = "to_timestamp(" + str(v) + ")"
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
	
def insertRow(cur, row, conf):
	cols = ""
	vals = ""
	for col, val in row.items():
		cols += "\"" + col + "\", "
		vals += val + ", "
	cols = cols[0:-2]
	vals = vals[0:-2]
	ig = "INSERT INTO \""
	ig += conf["tableName"]
	ig += "\" ("
	ig += cols
	ig += ") VALUES ("
	ig += vals
	ig += ");"
	print(ig)
	cur.execute(ig)
	
def fillImportTable(cur, conf):
	print("Filling import table...");
	api = ChefAPI(conf["chefURL"],
				  conf["chefKey"],
				  conf["chefUser"],
				  ssl_verify=conf["chefSSLVerify"])
	nodes = api.request("GET", "/organizations/aim/nodes").json()
	for node in nodes:
		r = row(api, node, conf)
		insertRow(cur, r, conf)
	print("Filling import table...Done.")

configFileName = appName() + ".json"
conf = config(configFileName)
conn = connect(conf)
cur = conn.cursor()
dropImportTable(cur, conf)
createImportTable(cur, conf)
fillImportTable(cur, conf)
print("Committing and closing connection...")
conn.commit()
conn.close()
print("Committing and closing connection...Done.")