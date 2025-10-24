import hashlib
import os
import sqlite3
from urllib import response
import requests
from packaging.version import Version
import json
import zipfile
import toml
import time
import datetime
import uuid
from tkinter import filedialog
import subprocess
import threading
from tempfile import NamedTemporaryFile
import shutil
from customtkinter import *
import re
import nbtlib
import urllib
from base.modules.utils import MCSCInternalError,InternetHost,HardwareSpec
from base.modules.kernel import MCSCKernelCore
from jsonschema import validate,ValidationError

outputLog_server = MCSCKernelCore(module="Server")

class ServerVersion_Control():
	'Utility for identifying/managing Minecraft Server Versions'

	outputLog_server.setLogic(logic="Version Control")
	
	def generateSHA1forJarfile(file:str,filepath=None):
		'Returns the SHA1 hash of the given file'
		
		#Hash object
		hash = hashlib.sha1()
		if filepath != None:
			with open(str(filepath) + "/" + str(file) + ".jar", "rb") as jarBinaryRead:
				#loop until the end of the file
				currentChunk = 0
				while currentChunk != b'':
					currentChunk = jarBinaryRead.read(1024)
					hash.update()
			return hash.hexdigest()
	def generateVersionListByServerType(servertype=None,minecraftversion=None) -> list:
		'Returns a list of versions of the server type based on the minecraft version'
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		global ServerType
		SoftwareSpec.changeDir(path=rootFilepath)
		if servertype is not None:
			if servertype in ServerType:
				if servertype == "server":
					#This is the Minecraft Vanilla default filename. We already have that as a seperate command.
					outputLog_server.warning_print("Depreciated usage. Use ServerVersion_Control.getVersionList() for Minecraft Vanilla versions.")
					return
				else:
					#As it stands, only Purpur and forge is case-sensitive by minecraft version
					#["fabric","forge","spigot","server","craftbukkit","purpur"]
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					if servertype == "purpur":
						#Parse the table
						MCSC_Cursor.execute("SELECT BuildID, MinecraftVersion FROM PurpurVersion_Table WHERE MinecraftVersion = ?",(minecraftversion,))
						raw_versionEntries = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
						#Wrap the keys as a list
						versions = list(raw_versionEntries.keys())
					else:
						if servertype == "forge":
							MCSC_Cursor.execute("SELECT forgeversion, minecraftversion FROM forgeVersion_Table WHERE minecraftversion = ?", (minecraftversion,))
							raw_versionEntries = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
							#Wrap the keys as a list\
							versions = list(raw_versionEntries.keys())
			return versions
	def isValidOfficialVanillaHash(hash:str,version:str):
		'Checks if the given hash is a valid SHA1 hash for the given version'
		#We can parse the version manifest
		versionmanifestURL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
		response = requests.get(versionmanifestURL)

		if response.status_code == 200:
			ManifestData = response.json()
			availableVersions = [versions['id'] for versions in ManifestData['versions']]
			if version in availableVersions:
				for versioninfo in ManifestData['versions']:
					versionurl = versioninfo['url']
					versionrequest = requests.get(str(versionurl))
					if versionrequest.status_code == 200:
						versiondata = versionrequest.json()
						serverjarhash = versiondata['downloads']['server']['sha1']
						if str(hash) == str(serverjarhash):
							return True
						else:
							return False

	def isVersion(parseVersion):
		"Checks for specified version in the minecraft version table. Returns True if the version exists. Otherwise, returns false"
		#fetch the version list from the database file
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		with SoftwareSpec.changeDir(path=rootFilepath):
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute("SELECT version FROM minecraftversion_Table")
			rows = MCSC_Cursor.fetchall()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			versions = [v[0] for v in rows]
			selectedVersion = [v for v in versions if parseVersion == v]
			if selectedVersion:
				return True
			else:
				return False

	def downloadvanillaserverfile(version=None):
		'''
		
		Downloads server.jar based on the specified version. The downloaded jar is saved in base/sandbox/build/Minecraft Vanilla/(version number here)

		'''
		from base.modules.config import program_folder
		from base.modules.utils import SoftwareSpec
		with SoftwareSpec.changeDir(path=program_folder):
			if os.path.isdir(str(program_folder) + "/build/Minecraft Vanilla") == False:
				os.mkdir(str(program_folder) + "/build/Minecraft Vanilla")
			if os.path.isdir(str(program_folder) + f"/build/Minecraft Vanilla/{version}") == False:
				os.mkdir(str(program_folder) + f"/build/Minecraft Vanilla/{version}")
			versionManifest = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
			response = requests.get(versionManifest)

			if response.status_code == 200:
				manifestData = response.json()
				availableVersions = {versions['id']:versions['url'] for versions in manifestData['versions']}
				if version in availableVersions.keys():
					for k,v in availableVersions.items():
						versionUrl = availableVersions.get(str(version))
						#Parse the version json file
						versionResponse = requests.get(versionUrl)
						if versionResponse.status_code == 200:
							versionData = versionResponse.json()
							serverjarUrl = versionData['downloads']['server']['url']
							#Fetch the server jar content
							servercontentjarResponse = requests.get(serverjarUrl,stream=True)
							totalSize = int(servercontentjarResponse.headers.get('content-length', 0))
							filesize = HardwareSpec.getByteSize(totalSize)
							outputLog_server.info_print(f"File Size: {filesize}")
							if servercontentjarResponse.status_code == 200:
								#Save to the sandbox directory
								with open(str(program_folder) + f"/build/Minecraft Vanilla/{version}/server.jar","wb") as jarFile:
									jarFile.truncate()
									for chunk in servercontentjarResponse.iter_content(chunk_size=8192):
										jarFile.write(chunk)
								outputLog_server.info_print(f"Server File for Minecraft Version {version} downloaded Successfully.")
								return True
							else:
								outputLog_server.info_print(f"Failed to fetch server.jar for Minecraft Version {version}")
								return False
						else:
							outputLog_server.info_print(f"Failed to fetch the {version}.json for Minecraft Version {version}")
							return False
				else:
					outputLog_server.info_print(f"Version {version} doesn't exist for Minecraft. Check the version number for troubleshooting.")
					return False
			else:
				outputLog_server.info_print("Failed to fetch version manifest json file")
				return False
	
	def getVersionList():
		'Returns a list of Minecraft Vanilla Versions from cache'
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/properties.json","r") as jsonProperties:
			dataDump = json.load(jsonProperties)
			jsonProperties.close()
		result = dataDump['version_cache']['listing']
		return result
		
	def downloadFabricByMinecraftVersion(serverpath,mcVersion=None,loaderversion=None):
		#We need to know what the fabric version the server needs, and we need the loader version
		try:
			if mcVersion == None:
				raise MCSCInternalError("Exception raised. We need the minecraft version is natively running.")
			else:
				if loaderversion == None:
					raise MCSCInternalError("Exception raised. We need the loader version that is being used.")
				else:
					if os.path.isdir(serverpath) == False:
						raise MCSCInternalError("Exception raised. Server path not found.")
					else:
						#All good. We can set the variables
						usingMCVersion = Version(mcVersion)
						usingloaderversion = Version(loaderversion)
		except MCSCInternalError as e:
			outputLog_server.error_print(e)
			return
		finally:
			#We need to parse the installer download url using the parameters
			#Example: https://meta.fabricmc.net/v2/versions/loader/1.20.4/0.15.6/1.0.0/server/jar
			fabricdownloadurl = f"https://meta.fabricmc.net/v2/versions/loader/{usingMCVersion}/{usingloaderversion}/1.0.0/server/jar"
			response = requests.get(fabricdownloadurl)
			if response.status_code == 200:
				with open(str(serverpath) + f"/fabric-installer-{usingMCVersion}-{usingloaderversion}.jar","wb") as downloadingfabric:
					downloadingfabric.write(response.content)
					downloadingfabric.close()
				outputLog_server.info_print("Downloaded fabric installer Successfully.")
				return

class ServerFileIO():
	'ServerFileIO -> File Operation Class \n \n ServerFileIO has Core Components of Minerva Server Crafter. Its primarily File Operations, and Database Queries.'

	class OnModAccess():
		'Utility for reading Internal Mod Data. When this is called, nothing is being change from within the mod itself. Data being fetched is in read-only mode.'
		def __init__(self):
			#We need the last loaded instance
			self.instancedata_raw = ServerFileIO.getLastConfigData()
			self.instanceName = self.instancedata_raw["id"]
			self.category = self.instancedata_raw["category"]
			self.path = self.instancedata_raw["path"]
			outputLog_server.setLogic(logic="File Input/Output")
		
		def readForgeMod(self,modName=None):
			'Constructs Data. Reads the mods.toml file of the given mod. Returns the data as a dictionary'
			from base.modules.config import rootFilepath
			#Check if its using legacy logic
			instanceData = ServerFileIO.getJSONInstanceDatabyName(instanceName=self.instanceName)
			legacyBool = instanceData["legacy-launch"]["forceToDirectory"]
			if legacyBool == True:
				#Get the server directory
				serverdirectory_root = instanceData["legacy-launch"]["serverDirectory"]
			if legacyBool == False:
				#Using the internal server directory structure
				serverdirectory_root = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{str(self.instanceName)}/"
			modsDirectory = os.path.join(str(serverdirectory_root),"/mods")
			with zipfile.ZipFile(str(modsDirectory) + f"/{modName}.jar","r") as modJarArchive:
				with modJarArchive.open("META-INF/mods.toml","r") as modTOML:
					configData = toml.load(modTOML)
					modTOML.close()
				modJarArchive.close()
			resultDict = {}
			#Get the mods section
			modData = configData.get('mods',[])
			for mod in modData:
				modID = mod.get('modId','Unknow-modID')
				version = mod.get('version','Unknown-version')
				displayName = mod.get('displayName','Unknown-name')
				authors = mod.get('authors','Unknown-authors')
				description = mod.get('description','No given description')
				logo = mod.get('logoFile',None)
				license_ = mod.get('license','Unknown-license')

				resultDict[modName] = {'modId': modID, 'version': version, 'displayName': displayName, 'authors': authors, 'description': description, 'logoFile': logo, 'license': license_}
			return resultDict
		
		def readFabricMod(self,modName=None):
			'Constructs Data. Reads the fabric.mod.json from the given mod. Returns the data as a dictionary'
			from base.modules.config import rootFilepath
			#Check if its using legacy logic
			instanceData = ServerFileIO.getJSONInstanceDatabyName(instanceName=self.instanceName)
			legacyBool = instanceData["legacy-launch"]["forceToDirectory"]
			if legacyBool == True:
				#get the server directory
				serverdirectory_root = instanceData["legacy-launch"]["serverDirectory"]
			if legacyBool == False:
				#use the internal sandbox server enviroment
				serverdirectory_root = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{self.instanceName}"
			modsDirectory = os.path.join(str(serverdirectory_root),"/mods")
			with zipfile.ZipFile(str(modsDirectory) + f"{modName}.jar","r") as modJarFile:
				with modJarFile.open("fabric.mod.json","r") as fabricData:
					fabricModData = json.load(fabricData)
					fabricData.close()
				modJarFile.close()
			resultDict = {}
			modID = fabricModData["id"]
			version = fabricModData["version"]
			name = fabricModData["name"]
			description = fabricModData["authors"]
			license_ = fabricModData["license"]
			icon = fabricModData["icon"]
			resultDict[modName] = {'modId': modID, 'version': version, 'name': name, 'description': description, 'license': license_, 'icon': icon}
			return resultDict
		
	def getLastConfigData():
		#Get the last config data
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/properties.json","r") as jsondata:
			data = json.load(jsondata)
			jsondata.close()
		lastconfig = data['Instances']['last-config']
		return lastconfig
	
	class JSONModelUtils:
		'Utilities that involves the properties.json'
		def __init__(self):
			self.currentModel = None
			outputLog_server.setLogic(logic="JSON Model Utils")
		
		def onModelCapture(self):
			'Snapshots the data currently stored in properties.json and sets it as the current model'
			#Ensure we are in the root directory
			from base.modules.config import rootFilepath
			from base.modules.utils import SoftwareSpec
			with SoftwareSpec.changeDir(path=rootFilepath):
				with open(str(rootFilepath) + "/properties.json","r") as jsonData:
					dataDump = json.load(jsonData)
					jsonData.close()
			self.currentModel = dataDump
			return self.currentModel
		
		def getCurrentModel(self):
			return self.currentModel
		
		def rollbackModel(self):
			from base.modules.config import rootFilepath
			from base.modules.utils import SoftwareSpec
			if not self.currentModel:
				raise MCSCInternalError("Take a snapshot of the current JSON Model first")
			else:
				#Ensure we are in the root directory
				with SoftwareSpec.changeDir(path=rootFilepath):
					#Delete the properties.json
					filepath = str(rootFilepath) + "/properties.json"
					os.remove(filepath)
					#Recreate the properties.json
					with open(str(rootFilepath) + "/properties.json","w") as jsonFile:
						json.dump(self.currentModel,jsonFile,indent=4)
					outputLog_server.info_print("Successfully rolled back the JSON Model to its last captured state.")
				return
	
	def onExit_setInstancePointer(instanceName=None,category=None):
		'Handler for setting the last loaded instance'
		from base.modules.config import JSONModel,rootFilepath
		#We need point to an instance
		JSONModel.onModelCapture()
		try:
			instance_path = str(rootFilepath) + f"/base/sandbox/Instances/{category}/{instanceName}"
			with open(str(rootFilepath) + "/properties.json", "r") as jsonPointer:
				datadump = json.load(jsonPointer)
				jsonPointer.close()
			data_payload = {'id': str(instanceName), 'category': str(category), 'path': str(instance_path)}
			datadump['Instances']['last-config'] = data_payload
			with open(str(rootFilepath) + "/properties.json","w") as jsonUpdate:
				json.dump(datadump,jsonUpdate,indent=4)
			return
		except json.JSONDecodeError:
			#Roll it back
			JSONModel.rollbackModel()
			return
		
	def onBoot_firstLoadCheck():
		'Checks if this is a fresh install of the program'
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		with open(str(rootFilepath) + "/properties.json","r") as jsonFile:
			datadump = json.load(jsonFile)
			firstLoadBool = datadump["config"]["first-load"]
			jsonFile.close()
		if firstLoadBool == True:
			#This is called after the version updater populated the version tables with data in the database. SQLite checks are implemented after data population
			SoftwareSpec.changeDir(path=rootFilepath)
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			#Lock down some table data
			MCSC_Cursor.execute("PRAGMA foreign_keys = ON")
			MCSC_Cursor.execute("PRAGMA table_info(forgeVersion_Table)")
			forgeVersion_dataOld = MCSC_Cursor.fetchall()
			MCSC_Cursor.execute("PRAGMA table_info(PurpurVersion_Table)")
			purpurVersion_dataOld = MCSC_Cursor.fetchall()
			#Create Tables
			outputLog_server.info_print("Refactoring Table Data for First Load...")
			MCSC_Cursor.execute("""CREATE TABLE temp_Instances_Table (name TEXT,minecraftVersion TEXT REFERENCES minecraftversion_Table(version) ON DELETE NO ACTION MATCH FULL,serverType TEXT CONSTRAINT "[Minecraft Vanilla, Fabric, Forge, CraftBukkit, PurPur, Spigot]" UNIQUE ON CONFLICT ROLLBACK,targetDirectory TEXT CONSTRAINT [path/to/server/directory] UNIQUE ON CONFLICT ROLLBACK)""")
			MCSC_Cursor.execute("DROP TABLE Instances_Table")
			MCSC_Cursor.execute("ALTER TABLE temp_Instances_Table RENAME TO Instances_Table")
			MCSC_Cursor.execute("CREATE TABLE temp_forgeVersion_Table(forgeversion TEXT,minecraftversion TEXT REFERENCES minecraftversion_Table (version) ON DELETE NO ACTION MATCH [FULL])")
			MCSC_Cursor.execute("INSERT INTO temp_forgeVersion_Table (forgeversion, minecraftversion) SELECT forgeversion, minecraftversion FROM forgeVersion_Table")
			MCSC_Cursor.execute("DROP TABLE forgeVersion_Table")
			MCSC_Cursor.execute("ALTER TABLE temp_forgeVersion_Table RENAME TO forgeVersion_Table")
			MCSC_Cursor.execute("CREATE TABLE temp_PurpurVersion_Table(BuildID NUMERIC,MinecraftVersion TEXT REFERENCES minecraftversion_Table (version) ON DELETE NO ACTION MATCH [FULL])")
			MCSC_Cursor.execute("INSERT INTO temp_PurpurVersion_Table (BuildID, MinecraftVersion) SELECT BuildID, MinecraftVersion FROM PurpurVersion_Table")
			MCSC_Cursor.execute("DROP TABLE PurpurVersion_Table")
			MCSC_Cursor.execute("ALTER TABLE temp_PurpurVersion_Table RENAME TO PurpurVersion_Table")
			MCSCDatabase.commit()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			outputLog_server.info_print("Table Data Rebuilt Successfully.")
			#We need to set the first load bool to false now
			with open(str(rootFilepath) + "/properties.json","r") as jsonfile:
				dataDump = json.load(jsonfile)
				dataDump["config"]["first-load"] = False
				jsonfile.close()
			with open(str(rootFilepath) + "/properties.json","w") as saveJson:
				json.dump(dataDump,saveJson,indent=4)
				jsonfile.close()
			return
		else:
			return		
	
	def loadJSONProperties(instanceName=None,category=None):
		"""Loads json data and updates the MinecraftServerProperties JSON Model in memory for a specific instance

		Parameters:
		instanceName : The name of the instance to be loaded
		category: The category the instance is under
		"""
		#We need to access the data from file
		from base.modules.config import rootFilepath
		#Was there a last config?
		outputLog_server.info_print(f"Loading JSON Model for {instanceName} under {category}...")
		instancePathTarget = str(rootFilepath) + f"/base/sandbox/Instances/{category}/{instanceName}"
		with open(str(instancePathTarget) + "/config.json","r") as jsonAccess:
			jsonDump = json.load(jsonAccess)
			jsonAccess.close()
		#We need to do somethings
		propertiesConfig = jsonDump['minecraft_server_properties']
		outputLog_server.info_print(f"Loaded {instanceName} successfully.")
		return propertiesConfig
	
	def exportPropertiestoJSON(instanceName=None,category=None,alternativeDict=None):
		"""
		Saves the data from memory to properties.json under instanceName

		"""
		from base.modules.config import MinecraftServerProperties
		last_config = ServerFileIO.getLastConfigData()
		targetInstance = last_config["path"]
		instance_name_id = last_config['id']
		if instance_name_id is None:
			return
		else:
			outputLog_server.info_print(f"Saving properties for {instanceName}...")
			with open(str(targetInstance) + "/config.json","r") as jsonData_:
				datadump = json.load(jsonData_)
				jsonData_.close()
			if alternativeDict is not None:
				datadump['minecraft_server_properties'] = alternativeDict
			else:
				datadump['minecraft_server_properties'] = MinecraftServerProperties
			with open(str(targetInstance) + "/config.json","w") as jsonWrite:
				json.dump(datadump,jsonWrite,indent=4)
				jsonWrite.close()
			outputLog_server.info_print("Properties Saved for " + str(instanceName) + ".")
			return
	
	def addPlayerToWhitelist(playerName):
		'addPlayerToWhitelist(playerName) -> Database Query \n \n Logic for adding a player to the Whitelist Table'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		try:
			parseAPI = requests.get("https://api.mojang.com/users/profiles/minecraft/" + str(playerName))
			if parseAPI.status_code == 200:
				playerInfo = parseAPI.json()
				#We need to convert the trimmed uuid to a full uuid
				playerUUID = playerInfo["id"]
				fulluuid = uuid.UUID(str(playerUUID))
				playerInfo["id"] = str(fulluuid)
				playerData = {playerInfo["name"]: playerInfo["id"]}
				#Add to the whitelist_Table
				insertquery = "INSERT OR REPLACE INTO whitelist_Table VALUES (?, ?)"
				for key, value in playerData.items():
					MCSC_Cursor.execute(insertquery,(value,key))
					del playerData
				MCSC_Cursor.close()
				MCSCDatabase.close()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Added " + str(playerInfo["name"]) + " to Whitelist")
				return
			else:
				#Error handling from here on
				if parseAPI.status_code == 204:
					#No Content
					MCSC_Cursor.close()
					MCSCDatabase.close()
					raise Exception("[Minerva Server Crafter]: Mojang API returned 204: No Content Raised")
				else:
					if parseAPI.status_code == 400:
						#Bad Request
						errorInformation = parseAPI.json()
						MCSC_Cursor.close()
						MCSCDatabase.close()
						raise Exception("[Minerva Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
					else:
						if parseAPI.status_code == 405:
							#Method Not Allowed
							errorInformation = parseAPI.json()
							MCSC_Cursor.close()
							MCSCDatabase.close()
							raise Exception("[Minerva Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
						else:
							if parseAPI.status_code == 429:
								#Too many requests
								errorInformation = parseAPI.json()
								MCSC_Cursor.close()
								MCSCDatabase.close()
								raise Exception("[Minerva Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
		except Exception as e:
			ConsoleWindow.displayException(e)
			if errorInformation:
				ConsoleWindow.updateConsole(END,"Mojang API Error - Additional Information\n =================== \n" + str(errorInformation))
			return

	def removePlayerfromWhitelist(playerName):
		'removePlayerfromWhitelist(playerName) -> Database Query \n \n Logic for removing a player from the whitelist table'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		try:
			deleteQuery = "DELETE FROM whitelist_Table WHERE name = ?"
			MCSC_Cursor.execute(deleteQuery,(playerName,))
			MCSCDatabase.commit()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			ConsoleWindow.updateConsole(END, "[Minerva Server Crafter]: Removed " + str(playerName) + " from Whitelist")
			return
		except sqlite3.Error as e:
			#Undo Changes
			ConsoleWindow.displayException(e)
			MCSCDatabase.rollback()
			return
	
	def importWhitelistfromJSON(filepath=None):
		'importWhitelistfromJSON() -> JSON Query \n \n Logic for importing the whitelist.json to the whitelist_Table in the Database file'
		#We need to get the whitelist from json
		global ServerJarSelection
		global ConsoleWindow
		global root_tabs
		from base.modules.config import whitelist

		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		root_tabs.set("Console Shell")
		#We need the server directory in order to get the whitelist.json
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Importing whitelist JSON...")
		whitelistFileDirectory = filepath
		with open(str(whitelistFileDirectory) + "/whitelist.json","r") as whitelistJson:
			datadump = json.load(whitelistJson)
			if datadump:
				for item in datadump:
					whitelist[item["name"]] = item["uuid"]
				if whitelist:
					#We need to put it in the whitelist table
					insertQuery = "INSERT OR REPLACE INTO whitelist_Table VALUES (?, ?)"
					for key,value in list(whitelist.items()):
						MCSC_Cursor.execute(insertQuery, (value,key))
						del whitelist[key]
						continue
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Whitelist.json loaded.")
				else:
					MCSC_Cursor.close()
					MCSCDatabase.close()
					return
			else:
				#Nothing is in the json file. Its a empty list
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return
			whitelistJson.close()
		return
	
#	def writemcEULA(instanceName=None):
#		'Generates the eula.txt file, and sets it to true'
#		from base.modules.config import rootFilepath
#		if instanceName is not None:
#			# We need to lookup the instance to see if there is a profile made
#			with open(os.path.join(rootFilepath, "properties.json"), 'r') as instanceLookup:
#				jsonDump = json.load(instanceLookup)
#				instanceLookup.close()
#			
#			folderPath = None
#			for category in ['Vanilla', 'Modded']:
#				for instance in jsonDump['Instances'][category]:
#					if instanceName in instance:
#						# Are we using legacy behavior?
#						if instance[instanceName]['legacy-launch']['forceToDirectory'] == True:
#							folderPath = instance[instanceName]['legacy-launch']['serverDirectory']
#						else:
#							# There's a profile, so it's got its folder
#							if category == "Vanilla":
#								folderPath = os.path.join(rootFilepath, f"base/sandbox/Instances/{instanceName}")
#							elif category == "Modded":
#								folderPath = os.path.join(rootFilepath, f"base/sandbox/Instances/Modpacks/{instanceName}")
#						break
#				if folderPath:
#					break
#			if folderPath and os.path.isdir(folderPath):
#				with open(os.path.join(folderPath, "eula.txt"), "w") as eulafile:
#					eulafile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Jun 12 07:54:40 EDT 2024\neula=true")
#					eulafile.close()
#				return 200
#			else:
#				return 404
#		else:
#			raise ValueError("Instance name must be provided")
	
	def exportWhitelistfromDatabase(serverdir=None):
		'exportWhitelistfromDatabase() -> Database Query \n \n Logic for exporting the whitelist_Table in the Database file to whitelist.json'
		global ConsoleWindow
		from base.modules.config import whitelist

		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		#We need to parse the whitelist table
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Exporting Whitelist Table...")
		MCSC_Cursor.execute("SELECT uuid, name FROM whitelist_Table")
		rows = MCSC_Cursor.fetchall()
		for row in rows:
			uuid, name = row
			whitelist[str(name)] = str(uuid)
		#We need to then turn it into a list
		formattedwhitelist = [{"uuid": uuid, "name": name} for name, uuid in whitelist.items()]
		serverdirectory = serverdir
		with open(str(serverdirectory) + "/whitelist.json","w") as whitelistWrite:
			json.dump(formattedwhitelist,whitelistWrite,ensure_ascii=False,indent=4)
			whitelistWrite.close()
		MCSC_Cursor.close()
		MCSCDatabase.close()
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Whitelist Table has been successfully saved to JSON")
		return

	
	#Banning Logic

	def issueBanbyName(PlayerName,banReason):
		'issueBanbyName(PlayerName,banReason) -> Database Query \n \n Issues a ban with the given PlayerName and includes the reason of the ban'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		try:
			parseAPIQuery = requests.get("https://api.mojang.com/users/profiles/minecraft/" + str(PlayerName))
			if parseAPIQuery.status_code == 200:
				PlayerInfo = parseAPIQuery.json()
				#turn the id as a UUID object
				playeruuid = PlayerInfo["id"]
				uuidFull = uuid.UUID(str(playeruuid))
				PlayerInfo["id"] = str(uuidFull)
				#Get a timestamp
				currentTime = datetime.datetime.now()
				timeOffset = time.strftime('%z', time.gmtime())
				Timestamp = currentTime.strftime("%Y-%m-%d %H:%M:%S") + ' ' + timeOffset
				#And then finally
				BanInfo = [{"uuid": str(PlayerInfo["id"]),"name": str(PlayerInfo["name"]),"created": str(Timestamp),"source": "Minerva Server Crafter","expires": "forever","reason": str(banReason)}]
				#Add to Table
				for item in BanInfo:
					MCSC_Cursor.execute("INSERT OR REPLACE INTO bannedPlayers_Table VALUES (?,?,?,?,?,?)",(item['uuid'],item['name'],item['created'],item['source'],item['expires'],item['reason']))
					MCSCDatabase.commit()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Ban Hammer was dropped on " + str(PlayerName) + ". REASON: " + str(banReason))
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return
			else:
				if parseAPIQuery.status_code == 204:
					#No Content
					raise Exception("[Minerva Server Crafter]: Mojang API returned 204: No Content Raised")
				else:
					if parseAPIQuery.status_code == 400:
						#Bad Request
						errorInformation = parseAPIQuery.json()
						raise Exception("[Minerva Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
					else:
						if parseAPIQuery.status_code == 405:
							#Method Not Allowed
							errorInformation = parseAPIQuery.json()
							raise Exception("[Minerva Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
						else:
							if parseAPIQuery.status_code == 429:
								#Too many requests
								errorInformation = parseAPIQuery.json()
								raise Exception("[Minerva Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))

		except Exception as e:
			ConsoleWindow.displayException(e)
			if errorInformation:
				ConsoleWindow.updateConsole(END,"Mojang API Error - Additional Information\n =================== \n" + str(errorInformation))
			return
		
	def importplayerBansFromJSON(filepath=None):
		'importplayerBansFromJSON() -> JSON Query \n \n Logic for importing banned-players json file to bannedPlayers_Table in the database file.'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		#We need the server directory
		serverDir = filepath
		with open(str(serverDir) + "/banned-players.json","r") as bannedPlayersJSON:
			payloadData = json.load(bannedPlayersJSON)
			if payloadData:
				#Add to table
				insertQuery = "INSERT OR REPLACE INTO bannedPlayers_Table (uuid,name,created,source,expires,reason)"
				for item in payloadData:
					uuid = item['uuid']
					name = item['name']
					created = item['created']
					source = item['source']
					expires = item['expires']
					reason = item['reason']

					MCSC_Cursor.execute(insertQuery, (uuid,name,created,source,expires,reason))
					MCSCDatabase.commit()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Player Bans JSON successfully imported.")
			else:
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: The Player Bans JSON is empty so we don't need to do anything")
			bannedPlayersJSON.close()
		MCSC_Cursor.close()
		MCSCDatabase.close()
		return
	
	def exportplayerBansToJSON(serverpath=None):
		'exportplayerBansToJSON() -> Database Query \n \nLogic for exporting the bannedPlayers_Table to banned-players JSON file'
		#Get the player bans table from database
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		serverDir = serverpath
		bannedPlayers = []
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Exporting player bans table...")
		MCSC_Cursor.execute("SELECT uuid, name, created, source, expires, reason FROM bannedPlayers_Table")
		bannedPlayersData = MCSC_Cursor.fetchall()
		for row in bannedPlayersData:
			playerData = {"uuid": row["uuid"],"name": row["name"],"created": row["created"],"source": row["source"],"expires": row["expires"],"reason": row["reason"]}
			bannedPlayers.append(playerData)
		with open(str(serverDir) + "/banned-players.json","w") as bannedPlayersWrite:
			json.dump(bannedPlayers,bannedPlayersWrite, indent=2)
			bannedPlayersWrite.close()
		MCSC_Cursor.close()
		MCSCDatabase.close()
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Player Bans Table has been successfully exported to JSON")
		return
	
	def pardonbyName(PlayerName):
		'pardonbyName(PlayerName) -> Database Query \n \n Logic for pardoning a player by removing them from the bannedPlayers_Table in the database file'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		#Delete the player name from the database table
		selectQuery = "SELECT COUNT(*) FROM bannedPlayers_Table WHERE name = ?"
		MCSC_Cursor.execute(selectQuery,(PlayerName,))
		result = MCSC_Cursor.fetchone()
		if result[0] == 1:
			deleteQuery = "DELETE FROM bannedPlayers_Table WHERE name = ?"
			MCSC_Cursor.execute(deleteQuery, (PlayerName,))
			MCSCDatabase.commit()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Pardoned " + str(PlayerName))
			return
		else:
			MCSC_Cursor.close()
			MCSCDatabase.close()
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: " + str(PlayerName) + " isn't found in the Ban Table.")
			return
	
	def importIPBansFromJSON(serverpath=None):
		'importIPBansFromJSON() -> JSON Query \n \n Logic for importing banned-ips JSON file to bannedIPs_Table in the database file'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Importting IP bans from JSON...")
		serverDirectory = serverpath
		with open(str(serverDirectory) + "/banned-ips.json","r") as bannedipsRead:
			banned_ips = json.load(bannedipsRead)
			if banned_ips:
				insertQuery = "INSERT OR REPLACE INTO bannedIPs_Table (ip,created,source,expires,reason)"
				for entry in banned_ips:
					ip = entry['ip']
					created = entry['created']
					source = entry['source']
					expires = entry['expires']
					reason = entry['reason']
				MCSC_Cursor.execute(insertQuery, (ip,created,source,expires,reason))
				MCSCDatabase.commit()
				MCSC_Cursor.close()
				MCSCDatabase.close()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: IP Bans has been imported from JSON file.")
			else:
				MCSC_Cursor.close()
				MCSCDatabase.close()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: The IP Bans JSON is empty, so we don't need to do anything")
			bannedipsRead.close()
		return
	
	def exportIPBansToJSON(serverpath=None):
		'exportIPBansToJSON() -> Database Query \n \n Logic for exporting bannedIPs_Table in the database file to banned-ips JSON file.'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Exportting IP Bans Table...")
		serverdirectory = serverpath
		selectQuery = "SELECT ip, created, source, expires, reason FROM bannedIPs_Table"
		MCSC_Cursor.execute(selectQuery)
		data = MCSC_Cursor.fetchall()
		#Transform the data into the desired format
		banned_ips = []
		for entry in data:
			ip, created, source, expires, reason = entry
			banned_ips.append({'ip': ip,'created': created, 'source': source, 'expires': expires, 'reason': reason})
		with open(str(serverdirectory) + "/banned-ips.json","w") as banIPWrite:
			json.dump(banned_ips,banIPWrite,indent=2)
		MCSC_Cursor.close()
		MCSCDatabase.close()
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: IP Bans Table successfully exported, and saved to JSON file.")
		return
	
	def issueIPBan(ipAddress,reason):
		'issueIPBan(ipAddress,reason) -> Database Query \n \n Logic for banning an specific IP Address with the given ban reason'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		
		try:
			ip = str(ipAddress)
			#Get a timestamp
			currentTime = datetime.datetime.now()
			timeOffset = time.strftime('%z', time.gmtime())
			Timestamp = currentTime.strftime("%Y-%m-%d %H:%M:%S") + ' ' + timeOffset
			#And then finally
			BanInfo = [{"ip": str(ip),"created": str(Timestamp),"source": "Minerva Server Crafter","expires": "forever","reason": str(reason)}]
			#Add to Table
			for item in BanInfo:
				MCSC_Cursor.execute("INSERT OR REPLACE INTO bannedIPs_Table VALUES (?,?,?,?,?)",(item['ip'],item['created'],item['source'],item['expires'],item['reason']))
				MCSCDatabase.commit()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Ban Hammer was dropped on " + str(ip) + ". REASON: " + str(reason))
			return

		except ValueError as e:
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: An exception was raised. Heres a detailed walkthrough:")
			ConsoleWindow.displayException(e)
			MCSCDatabase.rollback()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return
	
	def pardonbyIP(ipAddress):
		'pardonbyIP(ipAddress) -> Database Query \n \n Pardons an IP Address by removing them from the bannedIPs_Table'
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		#Delete the player name from the database table
		selectQuery = "SELECT COUNT(*) FROM bannedIPs_Table WHERE ip = ?"
		MCSC_Cursor.execute(selectQuery,(ipAddress,))
		result = MCSC_Cursor.fetchone()
		if result[0] == 1:
			deleteQuery = "DELETE FROM bannedIPs_Table WHERE ip = ?"
			MCSC_Cursor.execute(deleteQuery, (ipAddress,))
			MCSCDatabase.commit()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Pardoned " + str(ipAddress))
			return
		else:
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: " + str(ipAddress) + " isn't found in the Ban Table.")
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return

	def newServerInstance(name,version=None, servertype=None,serverDirectory=None):
		'Creates an Server instance in Minerva Server Crafter. You must provide a name of the instance, minecraft version, a server type, and a server directory. When any of the given values can\'t find them in their respective list, a ValueError Exception is raised. When all of the values are in the lists, it adds the values to the database table.'
		global ConsoleWindow
		from base.modules.config import minecraftVersions

		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		try:
			#We need to check if the instance is already created in the database
			MCSC_Cursor.execute('SELECT name FROM Instances_Table')
			availableInstances = MCSC_Cursor.fetchall()
			isInstance = name in availableInstances
			if isInstance == True:
				raise ValueError(f"Error: {name} is already an instance.")
			else:
				#Check the version
				if version not in minecraftVersions:
					raise ValueError(f"Invalid Minecraft Version. {version} was given, but its not in the list of available Minecraft Versions")
				else:
					#Check the server type
					if servertype not in ServerType:
						raise ValueError(f"Invalid Server Type. {servertype} was given, but its not in the list of known Minecraft Server Types.")
					else:
						#Check if the server directory is a directory
						if not os.path.isdir(serverDirectory):
							raise ValueError()
						else:
							#All good! We can add it to the table
							MCSC_Cursor.execute('INSERT INTO Instances_Table VALUES (?,?,?,?)',(str(name),str(version),str(servertype),str(serverDirectory)))
							MCSCDatabase.commit()
							MCSC_Cursor.close()
							MCSCDatabase.close()
							ConsoleWindow.updateConsole(END,f"[Minerva Server Crafter API - ServerFileIO]: Added {name} as a instance! =D")
							return

		except Exception as e:
			ConsoleWindow.displayException(e)
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return
	
	def removeInstance(name):
		global ConsoleWindow
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		SoftwareSpec.changeDir(path=rootFilepath)
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		try:
			deleteQuery = "DELETE FROM Instances_Table WHERE name = ?"
			MCSC_Cursor.execute(deleteQuery,(name,))
			MCSCDatabase.commit()
			MCSC_Cursor.close()
			MCSCDatabase.close()
			ConsoleWindow.updateConsole(END,f"[Minerva Server Crafter API - ServerFileIO]: Removed {name} Instance")
			return
		except sqlite3.Error as e:
			ConsoleWindow.displayException(e)
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return
	
	def getVersionInfoFromLastConfig():
		#We need to get the version info based off of the last known config
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/properties.json","r") as propertiesJSONFile:
			datadump = json.load(propertiesJSONFile)
			instances = datadump["Instances"]
			instanceName = datadump["Instances"]["last-config"]["id"]
			for category in ["Vanilla","Modded"]:
				for instance in instances[category]:
					if instanceName in instance:
						versionTarget = instance[str(instanceName)]["minecraftVersion"]
			propertiesJSONFile.close()
		return versionTarget
	
	def InstanceisModded(instanceName=None):
		#We need to check if the instance is modded or not
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/properties.json","r") as jsonFile:
			datadump = json.load(jsonFile)
			instances = datadump["Instances"]
			ModdedInstances = instances["Modded"]
			VanillaInstances = instances["Vanilla"]
			if instanceName in VanillaInstances:
				return False
			elif instanceName in ModdedInstances:
				return True

	def importPropertiesfromFile(Parent,instanceName=None):
		'importPropertiesfromFile() -> File Operation \n \n Prompts the User to select the server directory for importing a server.properties file to JSON Model'
		global ConsoleWindow
		global root_tabs
		from base.modules.config import rootFilepath

		try:
			askPropertiesFile = filedialog.askdirectory(parent=Parent,initialdir=str(rootFilepath),title="Select Server Directory with the server.properties File")
			if os.path.isfile(str(askPropertiesFile) + "/server.properties") == False:
				raise FileNotFoundError("[Minerva Server Crafter]: [Error-32] Server.properties does not exist. This usually means either its a new server, or user did not give the correct path")
			else:
				if os.path.isdir(str(askPropertiesFile) + "/libraries/net/minecraftforge") == True:
					ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Loading server.properties to JSON Model...")
					ServerFileIO.importpropertiestojson(instanceName=str(instanceName),serverjarpath=str(askPropertiesFile),create_data_ok=False)
					ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName),category="Modded")
					ServerFileIO.loadJSONProperties(instanceName=ServerFileIO.getLastConfig())
					ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: JSON Model has been updated, and values has been updated.")
					return
				else:
					ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Loading server.properties to JSON Model...")
					ServerFileIO.importpropertiestojson(instanceName=str(instanceName),serverjarpath=str(askPropertiesFile),create_data_ok=False)
					ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName),category="Vanilla")
					ServerFileIO.loadJSONProperties(instanceName=ServerFileIO.getLastConfig())
					ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: JSON Model has been updated, and values has been updated.")
					return
		except FileNotFoundError as e:
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Exception raised. Here's a detailed walkthrough below")
			ConsoleWindow.displayException(e)
			return
	
	def updatePropertiesbyKey(key,value):
		"updatePropertiesbyKey(key,value) -> Update Dict \n \n Statically sets the value to the given key. This is mostly for setting server.properties values before the saving process begins transferring from memory. If the given key exists in the properties json model, then it updates the key and returns true. Otherwise, it raises an exception and returns false"
		global ConsoleWindow
		from base.modules.config import MinecraftServerProperties
		#We need to see if the key is in the properties json model
		keyCheck = key in MinecraftServerProperties.keys()
		try:
			if keyCheck == True:
				#The key is in the json model! Update the value
				MinecraftServerProperties[str(key)] = value
				MinecraftServerProperties.update()
				return True
			if keyCheck == False:
				raise Exception("[Minerva Server Crafter - Error reporting]: Key doesn't exist in JSON Model. Will not proceed")
		except Exception as e:
			ConsoleWindow.displayException(e)
			return False
	
	def usePropertiesByMinecraftVersion(instanceName=None,minecraftVersion=None):
		'Generates the server.properties file using a specific version of minecraft. While an instanceName is given, the server.properties file will be saved in the instance folder'
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		def printOutput(process):
			for line in process.stdout:
				currentLine = line.decode("utf-8").strip("\n")
				outputLog_server.info_print(currentLine)
				if "Done" in currentLine:
					# Kill the Server
					process.stdin.write(b'/stop\n')
					process.stdin.flush()
					continue
				else:
					continue
			returnCode = process.wait()
			outputLog_server.info_print(f"Command exited with the return code of {returnCode}\n")
			return
		
		currentVersionList = ServerVersion_Control.getVersionList()
		try:
			if minecraftVersion in currentVersionList and minecraftVersion is not None:
				#Detect if the instance name is given
				if instanceName is not None:
					hasInstanceName = True
					if minecraftVersion is not None:
						#We have detected a minecraft version was given and its in the list of known versions
						versionCheck = True
					else:
						raise MCSCInternalError("Minecraft Version came back as a NoneType Value")
				else:
					#An instance name wasnt given
					hasInstanceName = False
					if minecraftVersion is not None:
						#We have detected a minecraft version was given and its in the list of known versions
						versionCheck = True
					else:
						raise MCSCInternalError("Minecraft Version came back as a NoneType Value")
		finally:
			#Create temporary directory to simulate a basic minecraft server
			os.makedirs(os.path.join(str(rootFilepath),f"base/sandbox/build/Minecraft Vanilla/{minecraftVersion}"),exist_ok=True)
			#prep for the destination folder
			try:
				if hasInstanceName == True:
					#Search for the instance
					SoftwareSpec.changeDir(path=rootFilepath)
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					MCSC_Cursor.execute("SELECT name FROM Instances_Table")
					currentInstances = [row[0] for row in MCSC_Cursor.fetchall()]
					if instanceName in currentInstances:
						#Get the instance data folder
						MCSC_Cursor.execute("SELECT targetDirectory FROM Instances_Table WHERE name = ?", (str(instanceName),))
						row = MCSC_Cursor.fetchone()
						instanceData = row[0]
						MCSC_Cursor.close()
						MCSCDatabase.close()
					else:
						MCSC_Cursor.close()
						MCSCDatabase.close()
						raise MCSCInternalError("Instance not found")
				else:
					#An instance was not given. Default to the temporary folder
					instanceData = os.path.join(str(rootFilepath),f"base/sandbox/build/Minecraft Vanilla/{minecraftVersion}")
			finally:
				#Shift to the temporary server directory
				tempServerDir = os.path.join(str(rootFilepath),f"base/sandbox/build/Minecraft Vanilla/{minecraftVersion}")
				SoftwareSpec.changeDir(path=tempServerDir)
				#Get the server jar file
				ServerVersion_Control.downloadvanillaserverfile(version=str(minecraftVersion))
				#Generate eula
				with open(os.path.join(tempServerDir, "eula.txt"), "w") as eulafile:
					eulafile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Jun 12 07:54:40 EDT 2024\neula=true")
					eulafile.close()
				#Run the server
				cmd = ['java','-jar','server.jar','-nogui']
				temp_serverProcess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)
				tempThreadedProcess = threading.Thread(target=printOutput,args=(temp_serverProcess,),name="Server.properties File Generation")
				tempThreadedProcess.start()
				temp_serverProcess_returnCode = temp_serverProcess.wait()
				tempThreadedProcess.join()
				if temp_serverProcess_returnCode == 0:
					#The server files was generated. Clean up the temporary server directory
					for root,dirs,files in os.walk(tempServerDir):
						for dir in dirs:
							dirpath = os.path.join(tempServerDir,dir)
							shutil.rmtree(dirpath)
							continue
						for file in files:
							filepath = os.path.join(tempServerDir,file)
							if file == "server.properties":
								continue
							else:
								os.remove(filepath)
								continue
					#All thats left should be the server.properties file
					#Was an instance given?
					if hasInstanceName == True:
						#Copy to the instance folder
						shutil.copy(os.path.join(tempServerDir,"server.properties"),str(instanceData))
						return
					else:
						#Do nothing. The requirement has already been fulfilled
						return


	def convertInstancePropertiestoPropertiesFile(Parent_,instanceName=None,filepath=None,bypassSaveLocation=False):
		'Converts the instance properties from properties.json and writes it to server.properties. \nIf bypassSaveLocation is True, the server.properties \n file is written to filepath of the server directory without asking for an save location'
		global ConsoleWindow
		global root_tabs
		global instanceView
		from base.modules.config import rootFilepath

		lastConfigData = ServerFileIO.getLastConfigData()
		category = lastConfigData['category']
		ServerFileIO.exportPropertiestoJSON(instanceName=str(instanceName),category=str(category))
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Converting JSON Model...")
		#First we get the Json file data
		with open(str(rootFilepath) + "/properties.json", "r") as jsonPayload:
			raw_data = json.load(jsonPayload)
			jsonPayload.close()
		payload_dict = {}
		payload_dict = raw_data
		#del payload_dict['debug'] #Weird inclusion in the json. This inclusion is on Mojangs end. This option was added back in beta 1.9, but then was later removed from the properties file
		#We need to use the variable ServerJarSelection
		if bypassSaveLocation == False:
			askSaveLocation = filedialog.askdirectory(initialdir=filepath,parent=Parent_,title="Select Server Directory")
			if askSaveLocation == None:
				return
			if os.path.isfile(str(askSaveLocation) + "/server.properties") != True:
				#Lets make one with the header
				with open(str(askSaveLocation) + "/server.properties","w") as generatePropertiesFile:
					#A cheaty way of doing this, but ¯\_(ツ)_/¯
					generatePropertiesFile.write("#Minecraft server properties\n#Sun Jun 16 11:20:03 EDT 2024\n")
					generatePropertiesFile.close()
				with open(str(askSaveLocation) + "/server.properties","a") as propertiesfile:
					for key,value in payload_dict.items():
						if value == None:
							value = ""
						propertiesfile.write(f"{key}={value}\n")
					propertiesfile.close()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Note from Dev - If you are running an earlier version of Minecraft that has settings under a different name within the server.properties, they are not carried over. The backwards compatiblity is in a work-in-progress state. This will definitely change later when its being revisited")
				return
			else:
				if os.path.isfile(str(askSaveLocation) + "/server.properties") == True:
					with open(str(askSaveLocation) + "/server.properties","w") as propertiesFile:
						#A cheaty way of doing this but ¯\_(ツ)_/¯
						propertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
						for Key,val in payload_dict.items():
							if val == None:
								val = ""
							propertiesFile.write(f"{Key}={val}\n")
					#Merge the properties
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Note from Dev - If you are running an earlier version of Minecraft that has settings under a different name within the server.properties, they are not carried over. The backwards compatiblity is in a work-in-progress state. This will definitely change later when its being revisited")
				return
		else:
			#We need to save the file in the given directory
			if os.path.isfile(str(filepath) + "/server.properties") != True:
				#Lets make one with the header
				with open(str(filepath) + "/server.properties","w") as generatePropertiesFile:
					#A cheaty way of doing this, but ¯\_(ツ)_/¯
					generatePropertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
					generatePropertiesFile.close()
				with open(str(filepath) + "/server.properties","a") as propertiesfile:
					for key,value in payload_dict.items():
						if value == None:
							value = ""
						propertiesfile.write(f"{key}={value}\n")
					propertiesfile.close()
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				return
			else:
				if os.path.isfile(str(filepath) + "/server.properties") == True:
					with open(str(filepath) + "/server.properties","w") as propertiesFile:
						#A cheaty way of doing this but ¯\_(ツ)_/¯
						propertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
						for Key,val in payload_dict.items():
							if val == None:
								val = ""
							propertiesFile.write(f"{Key}={val}\n")
					#Merge the properties
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				return
		
	def ResourcePackCall_generateSHA1(url=None):
		'ResourcePackCall_generateSHA1(url) -> Tuple List \n \nDownloads the Resource Pack from the direct download url, hashes the file and file contents and stored into a list object into its index value.\n \nTuple List Index Reference\n========================\n \nIndex value 0 - 1st Zipfile hash \n \nIndex Value 1 - 1st Zipfile Contents Hash \n \nIndex value 2 - 2nd Zipfile hash \n \nIndex Value 3 - 2nd Zipfile Contents Hash \n \nIndex Value 4 - Verification Bool'
		#We need to download the zipfile and generate a sha1 from url
		global ConsoleWindow
		global root_tabs

		root_tabs.set("Console Shell")

		ConsoleWindow.updateConsole(END, "[Minerva Server Crafter]: Downloading Resource Pack from: " + str(url))
		try:
			# Create two temporary files
			with NamedTemporaryFile(delete=False) as temp_file1, NamedTemporaryFile(delete=False) as temp_file2:
				# Download the file twice into the temporary files
				response1 = requests.get(url, stream=True)
				response2 = requests.get(url, stream=True)
				if response1.status_code != 200 or response2.status_code != 200:
					raise ValueError(f"Failed to download file from URL: {url}")

				for chunk1, chunk2 in zip(response1.iter_content(chunk_size=65536), response2.iter_content(chunk_size=65536)):
					temp_file1.write(chunk1)
					temp_file2.write(chunk2)

				# Calculate hashes from both downloads
				sha1_hash1 = hashlib.sha1()
				sha1_hash2 = hashlib.sha1()

				with open(temp_file1.name, "rb") as file1, open(temp_file2.name, "rb") as file2:
					while True:
						data1 = file1.read(65536)
						data2 = file2.read(65536)
						if not data1 or not data2:
							break
						sha1_hash1.update(data1)
						sha1_hash2.update(data2)

				# Get the final hash values
				hash1 = sha1_hash1.hexdigest()
				hash2 = sha1_hash2.hexdigest()

				# Verify the hashes
				verification_result = hash1 == hash2
				
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: File has been downloaded and verified.")
				return [hash1, {"contents_hash": sha1_hash1.hexdigest()}, hash2, {"contents_hash": sha1_hash2.hexdigest()}, verification_result]

		except ValueError as e:
			# Error handling code
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Exception Raised. Heres a detailed walkthrough: ")
			ConsoleWindow.displayException(e)
			return (None, None, None, None, False)
	
	def askAddWhitelistPlayer():
		'askAddWhitelistPlayer() -> User Input Operation \n \n Prompts the user to input a player name to add to the whitelist'
		global ConsoleWindow
		#Push a input dialog
		challengeDialog = CTkInputDialog(text="What is the player's name you want to add?",title="Minerva Server Crafter - Add Whitelist Player Challenge")
		challengeDialog_playername = challengeDialog.get_input()
		if challengeDialog_playername == None:
			return
		#Add to whitelist table
		ServerFileIO.addPlayerToWhitelist(str(challengeDialog_playername))
		#Update the listbox
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Whitelist updated.")
		return
	
	def askBanPlayerName():
		'askBanPlayerName() -> User Input Operation \n \n Prompts the user to input a player name to ban the given name. When a name is provided, it then prompts the user to give a reason of the ban.'
		global ConsoleWindow
		challengedialog_player = CTkInputDialog(title="Minerva Server Crafter - Issue Player Ban",text="What's the Player Name that you want to ban?")
		banName = challengedialog_player.get_input()
		if banName == None:
			return
		challengedialog_Banreason = CTkInputDialog(title="Minerva Server Crafter - Issue Player Ban - Ban Reason",text="Why do want to ban " + str(banName) + "?")
		BanReason = challengedialog_Banreason.get_input()
		ServerFileIO.issueBanbyName(str(banName),str(BanReason))
		ServerFileIO.populateBannedPlayers_Listbox()
		return
	
	def askIPBan():
		'askBanPlayerName() -> User Input Operation \n \n Prompts the user to input an IP Address to ban the given IP. When a IP Address is provided, it then prompts the user to give a reason of the ban.'
		global ConsoleWindow
		challengedialog_ip = CTkInputDialog(title="Minerva Server Crafter - Issue IP Ban",text="What's the IP Address that you want to ban?")
		banIP = challengedialog_ip.get_input()
		if banIP == None:
			return
		challengedialog_banreason = CTkInputDialog(title="Minerva Server Crafter - Issue IP Ban - Ban Reason",text="Why do want to ban " + str(banIP) + "?")
		banreason = challengedialog_banreason.get_input()
		ServerFileIO.issueIPBan(banIP,str(banreason))
		return

	def getLastConfig():
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/properties.json","r") as jsonRead:
			datadump = json.load(jsonRead)
			name = datadump["Instances"]["last-config"]["id"]
			jsonRead.close()
		return name

class ServerTypeInstaller():
	def __init__(self,dst:str | None = None):
		from base.modules.config import rootFilepath
		self.server_type_path = dst
		self.outputLog_ServerTypeInstaller = MCSCKernelCore(module="Server",logic="Server Type Installer")
		return
	
	def installServerType(self,server_type:str | None = None,serverTypeVersion:str | None = None, minecraft_version:str | None = None):
		from base.modules.config import rootFilepath, ServerType
		from base.modules.utils import SoftwareSpec
		from base.modules.updater import MCSCUpdater
		from urllib.parse import urlparse
		def printInstallerOutput(process):
			for line in process.stdout:
				currentLine = line.decode("utf-8").strip()
				self.outputLog_ServerTypeInstaller.info_print(currentLine)
				continue
			returnCode = process.wait()
			self.outputLog_ServerTypeInstaller.info_print(f"Command exited with the return code of {returnCode}\n")
			return
		if server_type is not None and server_type in ServerType:
			is_usingBuildtools = False
			if server_type == "forge":
				#Retrieve the forge installer
				url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/1.21.10-60.0.5/forge-{minecraft_version}-{serverTypeVersion}-installer.jar"
			elif server_type == "fabric":
				#Get the latest fabric installer version
				installerVersions = MCSCUpdater.FabricBaseClass.getInstallerListingfromTable()
				installerVersion = installerVersions[0]
				url = f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{str(installerVersion)}/fabric-installer-{str(installerVersion)}.jar"
			elif server_type == "purpur":
				#Get the purpur server jar from the api
				buildVersionListing = MCSCUpdater.PurpurBaseClass.getBuildsbyVersion(version=minecraft_version)
				if serverTypeVersion in buildVersionListing:
					url = f"https://api.purpurmc.org/v2/purpur/{minecraft_version}/{serverTypeVersion}/download"
			elif server_type == "spigot" or server_type == "craftbukkit":
				#Get buildtools
				url = "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar"
				is_usingBuildtools = True
			response = requests.get(url)
			if response.status_code == 200:
				if is_usingBuildtools == False:
					#Get the filename from the url
					header = response.headers.get('Content-Disposition')
					outputLog_server.debug_print(f"Content-Disposition Header: {header}")
					if header is None:
						filename = os.path.basename(urlparse(response.url).path)
						outputLog_server.debug_print(f"Filename derived from URL: {filename}")
					else:
						filename = re.findall('filename="(.+)"', header)[0]
					#Create the installer
					with open(str(self.server_type_path) + str(filename),"wb") as installerFile:
						installerFile.write(response.content)
						installerFile.close()
				else:
					with open(str(self.server_type_path) + "/BuildTools.jar","wb") as buildtoolsFile:
						buildtoolsFile.write(response.content)
						buildtoolsFile.close()
			#Build the command to run the installer
			if is_usingBuildtools == True:
				if minecraft_version == "1.21.5":
					#Version not stable
					raise MCSCInternalError("Spigot for Minecraft 1.21.5 was deemed as unstable for production servers. Use a different version of Minecraft.")
				else:
					if server_type == "craftbukkit":
						cmd = ['java','-jar','BuildTools.jar','--rev',str(minecraft_version),'output-dir',str(self.server_type_path),'--compile craftbukkit']
					else:
						cmd = ['java','-jar','BuildTools.jar','--rev',str(minecraft_version),'output-dir',str(self.server_type_path)]
			else:
				if server_type == "forge":
					cmd = ['java','-jar',str(filename),'--installServer']
				else:
					if server_type == "fabric":
						cmd = ['java','-jar',str(filename),'server','-downloadMinecraft','-mcversion',str(minecraft_version),'-loader',str(serverTypeVersion),'-noprofile','-dir',str(self.server_type_path)]
			#Run the installer
			outputLog_server.info_print(f"Using command: {cmd}")
			installerProcess = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			#Thread the output
			installerThread = threading.Thread(target=printInstallerOutput,args=(installerProcess,),name="Server Type Installer Process")
			installerThread.start()
			installerProcess_returnCode = installerProcess.wait()
			installerThread.join()
			if installerProcess_returnCode == 0:
				self.outputLog_ServerTypeInstaller.info_print(f"{server_type.capitalize()} Server Type Installation Successful.")
				return
			else:
				self.outputLog_ServerTypeInstaller.error_print(f"{server_type.capitalize()} Server Type Installation Failed with return code {installerProcess_returnCode}.")
				raise MCSCInternalError(f"{server_type.capitalize()} Server Type Installation Failed with return code {installerProcess_returnCode}.")

class InstanceFramework():
	def __init__(self):
		self.vanillaInstances = []
		self.moddedInstances = []
		self.customInstances = []
		self.instance_path = None
		self.outputLog_Instancing = MCSCKernelCore(module="Server",logic="Instance Framework")
		return
	
	def pollCustom(self):
		'Scans the custom folder for current instances'
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		#Navigate to the Vanilla Instances
		customInstances = str(rootFilepath) + "/base/sandbox/Instances/Custom"
		with SoftwareSpec.changeDir(customInstances):
			for __r,_d,f in os.walk(customInstances):
				for server_type in _d:
					servertype_Path = os.path.join(__r,server_type)
					if os.path.isdir(servertype_Path):
						self.customInstances.append(os.path.basename(servertype_Path))
						continue
				break
		return
	
	def pollVanilla(self):
		'Scans the vanilla folder for current instances'
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		#Navigate to the Vanilla Instances
		vanillaInstances = str(rootFilepath) + "/base/sandbox/Instances/Vanilla"
		with SoftwareSpec.changeDir(path=vanillaInstances):
			for r,d,f in os.walk(vanillaInstances):
				for servertype in d:
					servertypePath = os.path.join(r,servertype)
					if os.path.isdir(servertypePath):
						self.vanillaInstances.append(os.path.basename(servertypePath))
						continue
				break
		return
	
	def pollModded(self):
		'Scans the modded folder for current instances'
		from base.modules.config import rootFilepath
		from base.modules.utils import SoftwareSpec
		#Navigate to the Vanilla Instances
		moddedInstances = str(rootFilepath) + "/base/sandbox/Instances/Modded"
		with SoftwareSpec.changeDir(moddedInstances):
			for r,d_,f in os.walk(moddedInstances):
				for Servertype in d_:
					ServertypePath = os.path.join(r,Servertype)
					for Instance in os.listdir(ServertypePath):
						if Instance == "downloads":
							continue
						else:
							if os.path.isdir(ServertypePath):
								self.moddedInstances.append(os.path.basename(ServertypePath))
								continue
							break
		return
	
	def attachInstance(self,instance_path=None):
		#Parse the path
		from base.modules.config import rootFilepath
		if instance_path is not None:
			self.instance_path = os.path.join(rootFilepath,str(instance_path))
			#Load the Minecraft server properties

	def generateInstanceSchema(self,is_curseforge: bool | None = None,is_imported:bool | None = None, instance_name: str | None = None,server_type: str | None = None,minecraft_version_: str | None = None):
		from base.modules.config import rootFilepath,MinecraftPropertiesSchema
		if minecraft_version_ is not None:
			if ServerVersion_Control.isVersion(parseVersion=minecraft_version_):
				version_minecraft = minecraft_version_
		#Check if the schema for the properties file is already generated
		try:
			if not os.path.isdir(str(rootFilepath) + f"/base/config/versions/{version_minecraft}"):
				#Generate the Schema
				self.outputLog_Instancing.warning_print(f"Schema for Minecraft {version_minecraft} Server is missing. Creating...")
				schema_propertiesInstance = MinecraftPropertiesSchema()
				schema_propertiesInstance.serverPropertiesToSchema(minecraft_version=str(version_minecraft))
				self.outputLog_Instancing.info_print("Server.properties Schema Generation Successful.")
		finally:
			#We have everything needed to output a schema for the instance
			self.outputLog_Instancing.info_print(f"Generating Schema for {instance_name} Config...")
			instanceSchema = str(rootFilepath) + "/schema.json"
			propertiesSchema = str(rootFilepath) + f"/base/assets/config/versions/{version_minecraft}/schema.json"
			if not os.path.isfile(propertiesSchema):
				schemaConstructor = MinecraftPropertiesSchema()
				schemaConstructor.serverPropertiesToSchema(minecraft_version=version_minecraft)
			with open(instanceSchema,'r') as instance_schema:
				jsonDataRaw_instance = json.load(instance_schema)
				instance_schema.close()
			with open(propertiesSchema,'r') as properties_schema:
				jsonDataRaw_properties = json.load(properties_schema)
				properties_schema.close()
			jsonData_instance = jsonDataRaw_instance['properties']['minecraft_server_properties']['properties'] #Should result as an empty dictionary
			jsonData_properties = jsonDataRaw_properties['properties']
			#We need to make a list of each setting
			requiredSettings = []
			for key in jsonData_properties.keys():
				requiredSettings.append(key)
			#Set the defaults
			defaultsSchema = str(rootFilepath) + "/defaults.json"
			with open(defaultsSchema,'r') as propertiesDefaults:
				jsonDataRaw_defaults = json.load(propertiesDefaults)
				propertiesDefaults.close()
			jsonData_propertiesDefaults = jsonDataRaw_defaults['properties']
			#Iterate through the dictionary
			for k1,v1 in jsonData_propertiesDefaults.items():
				for item in requiredSettings:
					if str(k1) == item:
						jsonData_instance[str(k1)] = v1
					else:
						continue
			jsonDataRaw_instance['properties']['minecraft_server_properties']['required'] = requiredSettings
			#Save the schema
			try:
				if server_type in ['forge','fabric']:
					if is_curseforge == True:
						if is_imported == True:
							targetInstance = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{instance_name}"
						else:
							targetInstance = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/Modpacks/{instance_name}"
					else:
						targetInstance = str(rootFilepath) + f"/base/sandbox/Instances/Modded/{instance_name}"
				else:
					if server_type == "custom":
						targetInstance = str(rootFilepath) + f"/base/sandbox/Instances/Custom/{instance_name}"
					else:
						targetInstance = str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_name}"
			finally:
				if os.path.isdir(targetInstance):
					with open(str(targetInstance) + "/schema_instance.json",'w') as schemaInstance:
						json.dump(jsonDataRaw_instance,schemaInstance,indent=4)
					self.outputLog_Instancing.info_print(f"Schema Generation for {instance_name} Config has been Generated Successfully.")
					return
				else:
					os.mkdir(targetInstance,exist_ok=True)
					with open(str(targetInstance) + "/schema_instance.json",'w') as schemaInstance:
						json.dump(jsonDataRaw_instance,schemaInstance,indent=4)
					self.outputLog_Instancing.info_print(f"Schema Generation for {instance_name} Config has been Generated Successfully.")
					return
	
	def createInstanceConfig(self,is_imported: bool | None = None, is_curseforge: bool | None = None, instance_name: str | None = None,mod_list:list | None = None,serverType: str | None = None,server_type_version: str | None = None,minecraft_version: str | None = None,custom_data: dict | None = None):
		from base.modules.config import program_folder,rootFilepath,ServerType
		from base.modules.utils import SoftwareSpec
		global properties_signal
		def line_output(process):
			for line in process.stdout:
				currentLine = line.decode('utf-8').strip("\n")
				self.outputLog_Instancing.info_print(currentLine)
				if "Done" in currentLine:
					# Kill the Server
					process.stdin.write(b'/stop\n')
					process.stdin.flush()
					continue
				time.sleep(0.1)
			returnCode = process.wait()
			self.outputLog_Instancing.info_print("Command exited with the return code " + str(returnCode))
			return
		if instance_name is not None:
			self.outputLog_Instancing.info_print("Creating Instance Config...")
			try:
				if serverType == "custom":
					customData = custom_data
			finally:
				if serverType in ServerType:
					if ServerVersion_Control.isVersion(parseVersion=str(minecraft_version)):
						versionMinecraft = str(minecraft_version)
						#We can compile the data effectively
						servertypeVersion = str(server_type_version)
						try:
							if mod_list is not None:
								if isinstance(mod_list,list):
									modListing = mod_list
								else:
									raise TypeError(f"Not a vaild object. Expected list, but got {type(mod_list)}")
							else:
								modListing = []
						finally:
							servertype = str(serverType)
							if serverType == "custom":
								configData = [{'Instance Name': str(instance_name), 'addon_listing': modListing, 'server_type': servertype,'custom_jar_data': customData,'server_type_version': servertypeVersion, 'minecraft_version': versionMinecraft}]
							else:
								configData = [{'Instance Name': str(instance_name), 'addon_listing': modListing, 'server_type': servertype,'server_type_version': servertypeVersion, 'minecraft_version': versionMinecraft}]
							configData = configData[0]
							#Instance Profile generated. We need one other thing
							try:
								if not os.path.isfile(str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}/server.properties"):
									self.outputLog_Instancing.warning_print("Properties File Missing. Generating...")
									ServerVersion_Control.downloadvanillaserverfile(version=str(minecraft_version))
									with open(str(program_folder) + f"/base/sandbox/build/Minecraft Vanilla/{minecraft_version}/eula.txt",'w') as eulaFile:
										eulaFile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Thu Jun 20 22:35:39 EDT 2024\neula=true")
										eulaFile.close()
									with SoftwareSpec.changeDir(path=str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}"):
										propertiesProcess = subprocess.Popen(['java','-jar','server.jar','-nogui'],shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.PIPE)
										propertiesThread = threading.Thread(target=line_output,args=(propertiesProcess,),name="Instance Framework - properties file Generator")
										propertiesThread.start()
										processCode = propertiesProcess.wait()
										propertiesThread.join()
										if processCode == 0:
											self.outputLog_Instancing.info_print("Done.")
											properties_signal = 200
								else:
									self.outputLog_Instancing.info_print("Properties File Detected. Skipping Generation...")
									properties_signal = 200
							finally:
								result = {}
								if properties_signal == 200:
									with open(str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}/server.properties",'r') as propertiesData:
										fileContent = propertiesData.readlines()
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
												self.outputLog_Instancing.error_print(f"Failed to parse key: {key} | value: {value} | Error: {e}")
												raise MCSCInternalError(msg=f"Failed to parse key: {key} | value: {value} | Error: {e}")
									#Put the properties data into the config
									configData['minecraft_server_properties'] = result
									self.outputLog_Instancing.info_print("Config Data has been compiled successfully.")
									for r_,d_,f_ in os.walk(str(program_folder) + f"/build/Minecraft Vanilla/{minecraft_version}"):
										for __file in f_:
											targetFile = os.path.join(r_,__file)
											if __file == "server.properties":
												continue
											else:
												os.remove(targetFile)
										for __dir in d_:
											directoryTarget = os.path.join(r_,__dir)
											shutil.rmtree(directoryTarget)
									#Save the config
									try:
										if serverType in ['forge','fabric']:
											if is_curseforge == True:
												if is_imported == True:
													instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{instance_name}"
												else:
													instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/Modpacks/{instance_name}"
											else:
												instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Modded/{instance_name}"
										else:
											if serverType == "custom":
												instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Custom/{instance_name}"
											else:
												instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_name}"
									finally:
										self.outputLog_Instancing.info_print("Saving...")
										with open(str(instancePath) + "/config.json",'w') as instanceConfig:
											json.dump(configData,instanceConfig,indent=4)
											instanceConfig.close()
										self.outputLog_Instancing.info_print("Saved. Validating Config...")
										#Validate the dump
										with open(str(instancePath) + "/schema_instance.json","r") as instance_data:
											instance_schema = json.load(instance_data)
											instance_data.close()
										with open(str(instancePath) + "/config.json","r") as instance_config:
											config_dump = json.load(instance_config)
											instance_config.close()
										try:
											validate(instance=config_dump,schema=instance_schema)
										except ValidationError as e:
											self.outputLog_Instancing.error_print("Invalid Instance Config.")
											raise MCSCInternalError(msg="Invalid Instance Config",errors=e)
										finally:
											self.outputLog_Instancing.info_print("Instance Config has no issues, and is conformed to the JSON Schema.")
											return
					else:
						self.outputLog_Instancing.error_print("Invalid Minecraft Version")
						raise MCSCInternalError(msg="Not a vaild Minecraft version")
				else:
					self.outputLog_Instancing.error_print("Invalid Server Type")
					raise MCSCInternalError(msg="Not a vaild Server Type")

outputLog_server.setLogic(logic=None)
outputLog_server.info_print("Loaded Internal Minecraft Server Logic.")
