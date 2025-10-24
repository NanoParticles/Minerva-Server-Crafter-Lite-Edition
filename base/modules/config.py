import os
import glob
import subprocess
import threading
import shutil
import re
import json
import genson
import requests
import sqlite3
import time
import platform
from base.modules.server import ServerVersion_Control,ServerFileIO
from base.modules.kernel import MCSCKernelCore

outputLog_config = MCSCKernelCore(module="Config")
#OS checks and architecture
architecture = platform.machine().lower()
if "aarch64" in architecture:
	arch_name = "ARM 64bit"
elif "arm" in architecture:
	arch_name = "ARM 32bit"
elif architecture in ("x86_64","amd64"):
	arch_name = "x86 64bit"
elif architecture in ("i386","i686","x86"):
	arch_name = "x86 32bit"
#Set the absolute path, so we are going to cheese it
pathreferenceTemp = os.path.dirname(os.path.abspath(__file__))
ServerIsRunning = False
InstanceAttached = False
#Random file reference
rootFilepath = os.path.abspath(os.path.join(pathreferenceTemp,"../.."))
onLoadConfig = False
#Builds are stored somewhere else
data = os.getenv('APPDATA')
program_folder = os.path.join(data,"minerva-server-crafter")
if not os.path.exists(str(program_folder)):
	outputLog_config.info_print("Program folder missing. Creating...")
	os.makedirs(program_folder,exist_ok=True)
versionType="release-lite"
version_="0.3.16"
VersionRelease = str(versionType)
VersionNumber = str(version_)
releaseVersion = " - Version: " + str(VersionRelease) + "-" + str(VersionNumber)
operatingSystem = platform.system()
libc = None
if operatingSystem == "Linux":
	#Linux only
	libc = "unknown"
	if glob.glob("/lib/*musl*") or glob.glob("/usr/lib/*musl*"):
		libc = "musl"
	else:
		libc = "glibc"
possibleJarNames = ["fabric-","forge-","spigot-","server","craftbukkit-","purpur-"]
ServerType = ["fabric","forge","spigot","vanilla","craftbukkit","purpur","custom"]
currentMemoryMinimum = int(4)
currentMemoryMax = int(4)
MinecraftServerProperties = {}
currentInstanceConfig = {}
JSONModel = ServerFileIO.JSONModelUtils()
whitelist = {}
playerBans = {}
minecraftVersions = ServerVersion_Control.getVersionList()
curseforge_localization = False


if os.path.isdir(str(os.path.expanduser("~") + "/curseforge")):
	outputLog_config.info_print("Curseforge Application detected. Will consider Local Profiles in logic.")
	curseforge_localization = True
	curseforge_instancePath = str(os.path.expanduser("~")) + "/curseforge/minecraft/Instances"

class MinecraftPropertiesSchema():
	def __init__(self):
		self.defaultConfig = genson.SchemaBuilder(schema_uri=False)
		self.outputLog_schema = MCSCKernelCore(module="Config",logic="Schema Generator")
		return
	
	@staticmethod
	def lookupLatestVersion():
		'Returns the latest minecraft version on the manifest as a tuple'
		versionManifest = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
		response = requests.get(versionManifest)
		if response.status_code == 200:
			manifestDataRaw = response.json()
			result = (manifestDataRaw['latest']['release'],manifestDataRaw['latest']['snapshot'])
			return result
		else:
			return (None,None)

	@staticmethod
	def lastTableUpdateVersion():
		'Returns the last know minecraft version definition in the table data'
		from base.modules.utils import SoftwareSpec
		from base.modules.config import rootFilepath
		SoftwareSpec.changeDir(path=rootFilepath)
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		MCSC_Cursor.execute("SELECT version,timestampRelease FROM minecraftversion_Table LIMIT 1")
		currentVersions = {x[0]:x[1] for x in MCSC_Cursor.fetchall()}
		result = sorted(currentVersions)[0]
		MCSC_Cursor.close()
		MCSCDatabase.close()
		return result

	def serverPropertiesToSchema(self,minecraft_version=None,include_defaults=False):
		from base.modules.utils import MCSCInternalError,SoftwareSpec
		from base.modules.config import program_folder,rootFilepath
		'Generates a schema.json using the server.properties file as a baseline for the specific minecraft version. By default, the default values are omitted from the file generation. When include_defaults is set to true, defaults.json is seen as a schema and is merged with the data set based on what was read from the server.properties for the given minecraft version. The schema.json is saved under base/config/versions/(minecraft version here)'
		def output_lines(process):
			for line in process.stdout:
				currentLine = line.decode('utf-8').strip("\n")
				self.outputLog_schema.info_print(currentLine)
				if "Done" in currentLine:
					# Kill the Server
					process.stdin.write(b'/stop\n')
					process.stdin.flush()
					continue
				time.sleep(0.1)
			returnCode = process.wait()
			self.outputLog_schema.info_print("Command exited with the return code " + str(returnCode))
			return
		if not os.path.isdir(str(rootFilepath) + f"/base/assets/config/versions/{minecraft_version}"):
			os.mkdir(str(rootFilepath) + f"/base/assets/config/versions/{minecraft_version}")
		if minecraft_version is not None:
			self.outputLog_schema.info_print(f"Generating a server.properties Schema under Minecraft Version {minecraft_version}...")
			ServerVersion_Control.downloadvanillaserverfile(version=str(minecraft_version))
			with SoftwareSpec.changeDir(path=str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}"):
				with open(str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}/eula.txt",'w') as eulaFile:
					eulaFile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Thu Jun 20 22:35:39 EDT 2024\neula=true")
					eulaFile.close()
				#Run the Server, then terminate it
				self.outputLog_schema.info_print("Running a sandbox Server...")
				self.generatorProcess = subprocess.Popen(['java','-jar','server.jar','-nogui'],shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.PIPE)
				self.generatorThread = threading.Thread(target=output_lines,args=(self.generatorProcess,),name="Properties Schema Builder")
				self.generatorThread.start()
				self.generatorCode = self.generatorProcess.wait()
				self.generatorThread.join()
				if self.generatorCode == 0:
					self.outputLog_schema.info_print("Cleaning up...")
					#Clear the directory leaving behind the properties file
					for root_,dirs,files in os.walk(str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}"):
						for dir in dirs:
							targetDir = os.path.join(root_,dir)
							if os.path.isdir(targetDir):
								shutil.rmtree(targetDir)
								continue
							else:
								continue
						for file in files:
							filepath = os.path.join(root_,file)
							if file == "server.properties":
								continue
							else:
								os.remove(filepath)
								continue
					#Read the properties file
					result = {}
					self.outputLog_schema.info_print("Compiling Schema Data...")
					with open(str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}/server.properties","r") as propertiesFile:
						fileContent = propertiesFile.readlines()
						for line in fileContent:
							if line.startswith("#"):
								continue
							key,value = line.strip().split("=")
							value = value.strip()
							try:
								# Check for boolean values
								if value.lower() == "true":
									result[str(key)] = True
								elif value.lower() == "false":
									result[str(key)] = False
								# Check for empty values (keep them as empty strings)
								elif value == "":
									result[str(key)] = ""
								# Check for integers
								elif value.isdigit():
									result[str(key)] = int(value)
								# Check for floats using regex to exclude non-numeric values like "survival"
								elif re.fullmatch(r"-?\d+\.\d+", value):  # Matches floats (e.g., "10.5", "-3.14")
									result[str(key)] = float(value)
								# Otherwise, treat as a string
								else:
									result[str(key)] = value
							except Exception as e:
								self.outputLog_schema.error_print(f"Failed to parse key: {key} | value: {value} | Error: {e}")
								raise MCSCInternalError(msg=f"Failed to parse key: {key} | value: {value} | Error: {e}")
					#We have a reference model! Build the Schema.
					if include_defaults is True:
						self.outputLog_schema.info_print("Configuring Defaults...")
						with open(str(rootFilepath) + "/defaults.json","r") as defaultsJSON:
							data_dump = json.load(defaultsJSON)
							defaultsJSON.close()
						self.defaultConfig.add_schema(data_dump)
					self.outputLog_schema.info_print("Building Schema...")
					self.defaultConfig.add_object(result)
					schemaPath = os.path.join(str(rootFilepath) + f"/base/assets/config/versions/{minecraft_version}/schema.json")
					schemaRaw = json.loads(self.defaultConfig.to_json())
					schemaRaw['properties'] = {k:v for k,v in schemaRaw['properties'].items() if str(k) in result}
					#Save the schema
					self.outputLog_schema.info_print("Saving Schema...")
					with open(schemaPath,'w') as schemaFile:
						json.dump(schemaRaw,schemaFile,indent=4)
						schemaFile.close()
					self.outputLog_schema.info_print("Saved.")
					return

outputLog_config.info_print("Loaded Configs.")
