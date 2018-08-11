from chef import ChefAPI, Node, Search, Role
import inspect
import psycopg2

api = ChefAPI("https://chef-api.aim.goip.de",
			  "cmdbuild-sync.pem",
			  "brunovetter",
			  ssl_verify=False)
conn = psycopg2.connect("dbname=cmdbuild-sync user=postgres password=postgres host=localhost")
conn.set_session(autocommit=False)
cur = conn.cursor()
nodes = api.request("GET", "/organizations/aim/nodes").json()
create_string = "CREATE TABLE IF NOT EXISTS ChefImport ("
create_string += "NodeName CHAR(50), "
create_string += "ChefEnvironment CHAR(50), "
create_string += "CPU0ModelName CHAR(50), "
create_string += "FSRootPercentUsed CHAR(5), "
create_string += "FSRootInodesPercentUsed CHAR(5), "
create_string += "FSSDPercentUsed CHAR(5), "
create_string += "FSSDInodesPercentUsed CHAR(5), "
create_string += "KernelRelease CHAR(50), "
create_string += "OSDescription CHAR(100), "
create_string += "OhaiTime CHAR(50), "
create_string += "FQDN CHAR(100), "
create_string += "Uptime CHAR(50), "
create_string += "ChefVersion CHAR(50), "
create_string += "Timezone CHAR(50), "
create_string += "RootSSHKey CHAR(500), "
create_string += "CookbookI4IDeviceVersion CHAR(50), "
create_string += "ReverseTunnelPort CHAR(10), "
create_string += "ChefClientPublicKey CHAR(500), "
create_string += "ChefClientPublicKeyExpDate CHAR(50));"
cur.execute(create_string)
cur.execute("DELETE FROM ChefImport;")
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