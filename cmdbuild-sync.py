from chef import ChefAPI, Node, Search, Role
import inspect

api = ChefAPI("https://chef-api.aim.goip.de",
			  "/etc/cmdbuild-sync/cmdbuild-sync.pem",
			  "brunovetter",
			  ssl_verify=False)
nodes = api.request("GET", "/organizations/aim/nodes").json()
for node_id in nodes:
	print(node_id)
	node_info = api.request("GET", "/organizations/aim/nodes/" + node_id).json()
	node_info_table = {}
	node_info_table["NodeName"] = node_id
	node_info_table["ChefEnvironment"] = node_info.get("chef_environment", "")
	automatic = node_info.get("automatic", {})
	node_info_table["CPU0ModelName"] = automatic.get("cpu", {}).get("0", {}).get("model_name", "")
	filesystem = automatic.get("filesystem", {}).get("by_mountpoint", {})
	node_info_table["FSRootPercentUsed"] = filesystem.get("/", {}).get("percent_used", "")
	node_info_table["FSRootInodesPercentUsed"] = filesystem.get("/", {}).get("inodes_percent_used", "")
	node_info_table["FSSDPercentUsed"] = filesystem.get("/media/sd", {}).get("percent_used", "")
	node_info_table["FSSDPercentUsed"] = filesystem.get("/media/sd", {}).get("inodes_percent_used", "")
	node_info_table["KernelRelease"] = automatic.get("kernel", {}).get("release", "")
	node_info_table["OSDescription"] = automatic.get("lsb", {}).get("description", "")
	node_info_table["OhaiTime"] = automatic.get("ohai_time", "")
	node_info_table["FQDN"] = automatic.get("fqdn", "")
	node_info_table["Uptime"] = automatic.get("uptime", "")
	node_info_table["ChefVersion"] = automatic.get("chef_packages", {}).get("chef", {}).get("version", "")
	node_info_table["Timezone"] = automatic.get("time", {}).get("timezone", "")
	node_info_table["RootSSHKey"] = automatic.get("i4i", {}).get("root_ssh_key", "")
	node_info_table["CookbookI4IDeviceVersion"] = automatic.get("cookbooks", {}).get("i4i-device", {}).get("version", "")
	normal = node_info.get("normal", {})
	node_info_table["ReverseTunnelPort"] = normal.get("i4i", {}).get("reverse_tunnel_port", "")
	key = api.request("GET", "/organizations/aim/clients/" + node_id + "/keys/default").json()
	node_info_table["ChefClientPublicKey"] = key.get("public_key", "")
	node_info_table["ChefClientPublicKeyExpDate"] = key.get("expiration_date", "")
	print(node_info_table)