#main.py

from customtkinter import *
import subprocess
import time
import threading, queue
import traceback
from tkinter import filedialog
import json
import socket
import os
import sys
import requests
import math
import psutil
import zipfile
from PIL import Image,ImageTk
from CTkToolTip import *
import hashlib
from tempfile import NamedTemporaryFile
from CTkListbox import *
import sqlite3
import uuid
import datetime
import feedparser
from tkinter import ttk
import shutil
import platform
import stat
from github import Github
from packaging.version import Version
import xmltodict
import logging
import ast

#We are going to make a github object
MCSC_API_githubObj = Github()
print("Minerva Server Crafter is not an official Minecraft Product. Minerva Server Crafter is not approved by or associated with Mojang or Microsoft.")

operatingSystem = platform.system()
if operatingSystem == "Windows":
	import ctypes
versionType="release-lite"
version_="0.2.15"
MinecraftServerCrafter_versionData = {}
MinecraftServerProperties = {}
MinecraftServerType = {}
MinecraftServerType["name"] = ""
possibleJarNames = ["fabric-","forge-","spigot-","server","craftbukkit-","purpur-"]
ServerType = ["fabric","forge","spigot","server","craftbukkit","purpur"]
blocksize = 1024**2
#Set the absolute path, so we are going to cheese it
pathreferenceTemp = os.path.dirname(os.path.abspath(__file__))
#Random file reference
propertiesJSONFilepath = os.path.join(pathreferenceTemp,"properties.json")
rootFilepath = os.path.split(propertiesJSONFilepath)[0]
os.chdir(str(rootFilepath))
whitelist = {}
playerBans = {}
difficultyStrings = ['Peaceful','Easy','Normal','Hard']
gamemodeStrings = ['Survival','Hardcore','Creative']
difficultyInt = [0,1,2,3]
gamemodeInt = [0,1,2]

class ModpackIndexClass():
	'Utility for handling Modpack Index API'
	def searchModpack(modpackName=None | str):
		'Searches for modpack'
		if modpackName is not None:
			response = requests.get(f"https://www.modpackindex.com/api/v1/modpacks?name={modpackName}")
			if response.status_code == 200:
				rawModpackData = response.json()
				ModpackData = rawModpackData['data']
				return ModpackData

class CurseforgeClass():
	'Utility for handling the Curseforge API'
	def decodeByteSecret() -> str:
		'Decodes the secret to a readable string. \n \n Note: This function only works with what is left by the devolper, and is intended for a secondary function within the CurseforgeClass. This is a developer function.'
		os.chdir(str(rootFilepath))
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		MCSC_Cursor.execute("SELECT specialSecret FROM mcscInternalData")
		raw_secret = [row[0] for row in MCSC_Cursor.fetchall()]
		MCSC_Cursor.close()
		MCSCDatabase.close()
		byteString = ''.join(raw_secret[0])
		byteOffset = str(byteString[-1]) + str(byteString[-2])
		raw_byteData = byteString[:-1]
		raw_byteData = raw_byteData[:-1]
		raw_byteData = raw_byteData + byteOffset
		raw_byteData = str(raw_byteData)
		#hex values
		hexVals = raw_byteData.split()
		bytesString = bytes(int(h,16) for h in hexVals)
		value = bytesString.decode('utf-8')
		return value
	
	def outputLines(process,modloader):
		for line in process.stdout:
			print("<" + str(modloader).capitalize() + "-Installer-Output>: " + line.decode('ascii').strip("\n"))
			time.sleep(0.1)
		returnCode = process.wait()
		print(f"Command exited with the return code {returnCode}")
		return

	def parsefileIDByModID(modID=None | int, fileID=None | int):
		headers = {'Accept': 'application/json', 'x-api-key': str(CurseforgeClass.decodeByteSecret())}

		response = requests.get(f"https://api.curseforge.com/v1/mods/{modID}/files/{fileID}",headers=headers)
		if response.status_code == 200:
			rawFileDetails = response.json()
			modFileDetails = rawFileDetails['data']
		return modFileDetails
	
	def ManifestJSON_getModFiles(filepath=None | str):
		'Parses the manifest.json in a modpack, and returns the list of mod data(more specifically, the mod files list). Call this second'
		with open(str(filepath) + "/manifest.json","r") as rawModFilesList:
			rawData = json.load(rawModFilesList)
			#We need to point to the files entry
			ModDataList = rawData['files']
			rawModFilesList.close()
		return ModDataList
	
	def ManifestJSON_getModloaderInfo(filepath=None | str):
		'Parses the manifest.json in a modpack, and returns the modloader information'
		with open(str(filepath) + "/manifest.json","r") as rawModloaderInfo:
			rawData = json.load(rawModloaderInfo)
			ModLoaderData = rawData['minecraft']['modLoaders'][0]['id']
			rawModloaderInfo.close()
		return ModLoaderData
	
	def ManifestJSON_getMinecraftVersion(filepath=None | str):
		'Parses the manifest.json in a modpack and returns the minecraft version'
		with open(str(filepath) + "/manifest.json","r") as rawMinecraftVersionInfo:
			rawData = json.load(rawMinecraftVersionInfo)
			minecraftversionData = rawData['minecraft']['version']
			rawMinecraftVersionInfo.close()
		return minecraftversionData
	
	def extractModpackZIP(filepath=None | str):
		'Imports modpack to Minerva Server Crafter from its zipfile. Initial file creation. Call this first. Returns 200 if the file directories and the zip file was extracted successfully'
		
		filename = os.path.splitext(os.path.basename(str(filepath)))[0]
		os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/importdata")
		os.mkdir(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{filename}")
		os.mkdir(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}")
		os.mkdir(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}/mods")
		os.chdir(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{filename}")
		print("[Minerva Server Crafter - Modpack Importing]: Unpacking Modpack from file...")
		try:
			with zipfile.ZipFile(str(filepath),"r") as modpackZipData:
				modpackZipData.extractall()
				modpackZipData.close()
		except zipfile.BadZipFile as e:
			print("[Minerva Server Crafter - Error Reporting]: Failed to extract. Raising exception.")
			raise zipfile.BadZipFile(e)

		print("[Minerva Server Crafter - Modpack Importing]: Import Stage 1 | 8 - File Creation - OK")
		return 200
	
	def getModFileDownloadURL(projectID=None | int,fileID=None | int) -> requests.Response:
		'Obtains the downloadURL for fileID in projectID. If the status code of the GET request came back as 200, then the download URL is returned as its value. Call this 3rd'

		headers = {'Accept': 'application/json','x-api-key': str(CurseforgeClass.decodeByteSecret())}

		response = requests.get(f"https://api.curseforge.com/v1/mods/{projectID}/files/{fileID}/download-url",headers=headers)
		if response.status_code == 200:
			rawURLData = response.json()
			downloadURL = rawURLData['data']
			return downloadURL
		else:
			print(f"[Minerva Server Crafter - Curseforge API Wrapper]: Status Code was {response.status_code}. Raising exception.")
			raise requests.ConnectionError(response=response.status_code,request=response)

	def parsefileID(modID=None,fileID=None):
		headers = {'Accept': 'application/json','x-api-key': str(CurseforgeClass.decodeByteSecret())}

		response = requests.get(f"https://api.curseforge.com/v1/mods/{modID}/files/{fileID}",headers=headers)
		if response.status_code == 200:
			rawfileID_data = response.json()
			fileID_data = rawfileID_data['data']
			return fileID_data

	def parseModID(modID=None):
		'Parses the modID json data from the Curseforge API'

		headers = {'Accept': 'application/json','x-api-key': str(CurseforgeClass.decodeByteSecret())}

		response = requests.get(f"https://api.curseforge.com/v1/mods/{modID}",headers=headers)
		if response.status_code == 200:
			rawjsondata = response.json()
			jsondata = rawjsondata['data']
			return jsondata
	def hascategory(modjsonData=None,categoryQuery=None | str or list) -> bool:
		'Checks in the modjsonData under categories for the categoryQuery as a single string or a list of strings'
		if isinstance(categoryQuery,str):
			category_list = [categoryQuery]
		else:
			category_list = categoryQuery
		
		category_jsonData = modjsonData.get('categories',[])
		modCategories = [category['name'] for category in category_jsonData]
		for category in category_list:
			if category in modCategories:
				result = 1
				break
			else:
				result = 0
				continue
		if result == 1:
			return True
		if result == 0:
			return False
		
	def getModpackServerPack(modpackName=None):
		'Downloads the server pack of a modpack from Curseforge'
		# Begin Search
		global indexVal
		modpackname = str(modpackName)
		#We can use modpack index to search for it
		modpackSearchData = ModpackIndexClass.searchModpack(modpackName=str(modpackname))
		startingIndex = 0
		for result in enumerate(modpackSearchData):
			if modpackSearchData[startingIndex]['name'] == str(modpackName):
				indexVal = startingIndex
				break
			else:
				startingIndex += 1
				continue
		modpackSearchData = modpackSearchData[indexVal]
		#We need curseforge ID of the modpack
		modpackID = modpackSearchData['curse_info']['curse_id']
		modpackData = CurseforgeClass.parseModID(modID=modpackID)
		#We need to get the server pack download url
		mainFileID = modpackData['mainFileId']
		modpack_fileID_data = CurseforgeClass.parsefileID(modID=modpackID,fileID=mainFileID)
		serverPackID = modpack_fileID_data['serverPackFileId']
		serverpackfilename = modpack_fileID_data['fileName']
		serverPackURL = CurseforgeClass.getModFileDownloadURL(projectID=modpackID,fileID=serverPackID)
		serverpackResponse = requests.get(str(serverPackURL))
		if serverpackResponse.status_code == 200:
			with open(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{serverpackfilename}","wb") as serverpackZIP:
				serverpackZIP.write(serverpackResponse.content)
				serverpackZIP.close()
			print(f"[Minerva Server Crafter]: Modpack {modpackName} Server Pack Archive Downloaded Successfully")
			return
	def parseModloaderData(modloaderName=None):
		'Parses the modloader information using modloaderName'
		headers = {'Accept': 'application/json','x-api-key': str(CurseforgeClass.decodeByteSecret())}
		response = requests.get(f"https://api.curseforge.com/v1/minecraft/modloader/{modloaderName}",headers=headers)
		if response.status_code == 200:
			rawModloaderData = response.json()
			ModloaderData = rawModloaderData['data']
			return ModloaderData
	
	def getModpackfromModpackID(modpackID=None):
		'Downloads the modpack data and imports it to Minerva Server Crafter'
		if modpackID is not None:
			modpack_data = CurseforgeClass.parseModID(modID=str(modpackID))
			#We can refine this further
			fileID = modpack_data['mainFileId']
			filedata = CurseforgeClass.parsefileIDByModID(modID=str(modpackID),fileID=fileID)
			filename = filedata['fileName']
			modpack_data = CurseforgeClass.getModFileDownloadURL(projectID=str(modpackID),fileID=fileID)
			modpackResponse = requests.get(str(modpack_data))
			if modpackResponse.status_code == 200:
				with open(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{filename}","wb") as modpackfile:
					modpackfile.write(modpackResponse.content)
					modpackfile.close()
			#lets extract the zip file
			zipPath = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{filename}"
			modpackName = os.path.splitext(os.path.basename(zipPath))[0]
			modpackCode = CurseforgeClass.extractModpackZIP(filepath=str(zipPath))
			if modpackCode == 200:
				#Clean up the downloads folder
				os.remove(str(zipPath))
				#Parse the manifest json to get version data
				minecraftversion = CurseforgeClass.ManifestJSON_getMinecraftVersion(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{modpackName}")
				modloaderType = CurseforgeClass.ManifestJSON_getModloaderInfo(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{modpackName}")
				result = tuple([minecraftversion,modloaderType])
				return result


	@classmethod
	def loadModpack(self,filepath=None | zipfile.Path,modpackName=None,isLegacy=False):
		'Loads a modpack to Minerva Server Crafter. While a filepath is given, the modpackName must be set to None. While a modpackName is given, the filepath must be set to None. For the filepath parmeter, it must be a Curseforge Modpack that was exported to a zip archive. While under the logic of the filepath, Minerva Server Crafter will handle retrieving the mods, and the server type installation. Also while under this logic, Minerva Server Crafter will attempt to skip client-only mods. While under the logic of the modpackName, Minerva Server Crafter will handle retrieving and extracting the server pack from the offical curseforge modpack, and server type installation'
		global finalCode
		global modpackData
		'Imports the Curseforge Modpack ZIP Archive to Minerva Server Crafter using filepath. This process uses data from the manifest.json, and from the overrides folder. The mods are downloaded from curseforge into the downloads folder, given from Minerva Server Crafter. During this process, it can take a bit depending on how many mods there are. Once the mods are finished downloading, they are then transferred over to the Modpack root folder, and emptying the downloads folder. Checks what modloader the modpack is using by the list of known compatible server types. When an unsupported modloader is detected, it raises an internal error, and stops the import process. Otherwise, the importing process proceeds to obtaining the modloaders installer, installing the server distribution of the modloader, grabbing the modpack overrides, then cleaning up the leftover importdata in the Modpacks directory. Once all that is done, the Modpack gets added to the Modpack Instance table.'
		finalCode = 0
		filename = os.path.splitext(os.path.basename(str(filepath)))[0]
		downloadsfolder = str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads"
		print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 1 | 8 - File Creation...")
		if modpackName is not None and filepath is None:
			#We need change up the logic slightly. Since this is an official Modpack on curseforge, we can just lookup the modpack
			print(f"[Minerva Server Crafter - Modpack Importing - Curseforge Modpack]: Searching for Modpack \'{modpackName}\'...")
			searchData = ModpackIndexClass.searchModpack(modpackName=str(modpackName))
			startingIndex = 0
			for result in enumerate(searchData):
				if searchData[startingIndex]['name'] == str(modpackName):
					print("[Minerva Server Crafter - Modpack Importing - Curseforge Modpack]: Modpack Found! :D")
					indexVal = startingIndex
					break
				else:
					startingIndex += 1
					continue
			searchData = searchData[indexVal]
			#Get the curseforge data
			modpackID = searchData['curse_info']['curse_id']
			#Now we can hand it of to the Curseforge API
			modpack_data = CurseforgeClass.parseModID(modID=modpackID)
			fileID = modpack_data['mainFileId']
			filedata = CurseforgeClass.parsefileIDByModID(modID=modpackID,fileID=fileID)
			filename = filedata['fileName']
			modpackResult = CurseforgeClass.getModpackfromModpackID(modpackID=modpackID)
			minecraftVersion = modpackResult[0]
			servertypeVersion = modpackResult[1]
			print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 2 | 8 - Server Pack Download(this can take awhile, depending on file size)...")
			CurseforgeClass.getModpackServerPack(modpackName=str(modpackName))
			print("[Minerva Server Crafter - Modpack Importing]: Stage 2 | 8 - Server Pack Download - OK")
			time.sleep(1.5)
			print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 3 | 8 - Server Pack Extracting...")
			#Extract to the mods folder
			targetedPack = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{filename}"
			modpackname = os.path.splitext(os.path.basename(targetedPack))[0]
			modsfolder = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackname}/mods"
			with zipfile.ZipFile(str(targetedPack),"r") as serverpackZip:
				serverpackZip.extractall(path=modsfolder)
				serverpackZip.close()
			print("[Minerva Server Crafter - Modpack Importing]: Stage 3 | 8 - Server Pack Extracting - OK")
			os.remove(str(targetedPack))
			#Generate modlist
			modlist = []
			for root,Dirs,Files in os.walk(modsfolder):
				for f in Files:
					if f.endswith(".jar"):
						name = os.path.splitext(os.path.basename(f))
						modlist.append(name)
						continue
			time.sleep(1.5)
			print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 4 | 8 - Server Type Downloading...")
			#We need to build the data
			modpackData = {}
			modloaderversion = str(servertypeVersion).split("-")
			modloaderversion = tuple(modloaderversion)
			modpackData["modloader-version"] = str(modloaderversion[1])
			if modloaderversion[0] in ServerType:
				if modloaderversion[0] == "forge":
					#Build the full name of the file
					modpackData["modloader-type"] = modloaderversion[0]
					serverTypeInstaller_filename = str(modloaderversion[0]) + "-" + str(minecraftVersion) + "-" + str(modloaderversion[1]) + "-installer.jar"
					modpackData["modloader-realname"] = str(minecraftVersion) + "-" + str(modloaderversion[1])
					#We need to build the maven direct download url
					url = "https://maven.minecraftforge.net/net/minecraftforge/" + str(modloaderversion[0]) + "/" + str(minecraftVersion) + "-" + str(modloaderversion[1]) + "/" + str(serverTypeInstaller_filename)
					#We need to run a specific command to run the installer
					command = ['java','-jar',str(serverTypeInstaller_filename),'--installServer']
				if modloaderversion[0] == "fabric":
					#We can just use the current installer version
					installerList = MCSCUpdater.FabricBaseClass.getInstallerListingfromTable()
					installerURLlisting = MCSCUpdater.FabricBaseClass.getInstallerURLPrefixListing()
					modpackData["modloader-type"] = modloaderversion[1]
					keyCheck = "modloader-realname" in modpackData.keys()
					if keyCheck == True:
						del modpackData["modloader-realname"]
					serverTypeInstaller_filename = str(modloaderversion[0]) + "-installer-" + str(installerList[0]) + ".jar"
					url = f"{installerURLlisting[0]}/{serverTypeInstaller_filename}"
					#We need to run a specific command to run the installer
					command = ['java','-jar',str(serverTypeInstaller_filename),'server', '-mcversion',str(minecraftversion),'-loader',str(modloaderversion[1]),'-dir',str(downloadsfolder)]
				#Get the installer
				response = requests.get(str(url))
				if response.status_code == 200:
					with open(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{serverTypeInstaller_filename}","wb") as forgeinstallerFile:
						forgeinstallerFile.write(response.content)
						forgeinstallerFile.close()
					#Obtain a minecraft vanilla server, just to be sure
					ServerVersion_Control.downloadvanillaserverfile(version=str(minecraftVersion))
					shutil.copytree(src=str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{minecraftVersion}",dst=str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads",dirs_exist_ok=True)
					os.chdir(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads")
					print("[Minerva Server Crafter - Importing Modpack]: Stage 4 | 8 - Server Type Downloading - OK")
					print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 5 | 8 - Server Type Installation...")
					installerProcess = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
					threadedProcess = threading.Thread(target=CurseforgeClass.outputLines,args=(installerProcess,modloaderversion[0]),name="Server Type Installer Thread")
					threadedProcess.start()
					ReturnCode = installerProcess.wait()
					if ReturnCode == 0:
						threadCompleted = threadedProcess.join()
						print("[Minerva Server Crafter - Importing Modpack]: Stage 5 | 8 - Server Type Installation - OK")
						print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 6 | 8 - Server Type File Operations...")
						#We can safely delete the installer
						os.remove(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{serverTypeInstaller_filename}")
						#We can now copy the file tree now
						shutil.copytree(src=str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackname}",dirs_exist_ok=True)
						#We can clear the downloads folder
						for File_name in os.listdir(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads"):
							file_path = os.path.join(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads", File_name)
							try:
								if os.path.isfile(file_path) or os.path.islink(file_path):
									os.unlink(file_path)
								elif os.path.isdir(file_path):
									shutil.rmtree(file_path)
							except Exception as e:
								raise MCSCInternalError(f"Failed to delete {file_path}.",e)
						print("[Minerva Server Crafter - Importing Modpack]: Stage 6 | 8 - Server Type File Operations - OK")
						print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 7 | 8 - Modpack Overrides...")
						#We can grab the overrides
						shutil.copytree(src=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{modpackname}/overrides",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackname}",dirs_exist_ok=True)
						print("[Minerva Server Crafter - Importing Modpack]: Stage 7 | 8 - Modpack Overrides - OK")
						time.sleep(10)
						print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 8 | 8 - Importing Cleanup...")
						#We can safely delete the import data
						shutil.rmtree(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/importdata")
						print("[Minerva Server Crafter - Importing Modpack]: Stage 8 | 8 - Importing Cleanup - OK")
						print(f"[Minerva Server Crafter]: {modpackName} Curseforge Modpack has been successfully imported. Adding to Modpack Table...")
						#Connect to database
						os.chdir(str(rootFilepath))
						MCSCDatabase = sqlite3.connect('mcsc_data.db')
						MCSC_Cursor = MCSCDatabase.cursor()
						MCSC_Cursor.execute("INSERT INTO CurseforgeModpackInstances_Table (ModpackName,ModpackType,ModpackTypeVersion,Modpack_modlist) VALUES (?,?,?,?)",(modpackName,modloaderversion[0],modloaderversion[1],str(modlist)))
						MCSCDatabase.commit()
						MCSC_Cursor.close()
						MCSCDatabase.close()
						print("[Minerva Server Crafter]: Modpack has been added to the Modpack Table.")
						filename = os.path.splitext(os.path.basename(filename))[0]
						ServerFileIO.addInstancetoJSON(name=str(modpackName),serverType=str(modpackData["modloader-type"]),isModded=True,modlist=modlist,modloaderversion=modpackData["modloader-version"],minecraftversion=minecraftVersion)
						os.rename(src=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
						ServerFileIO.onExit_setInstancePointer(instanceName=str(modpackName))
						ServerFileIO.writemcEULA(instanceName=str(modpackName))
						properties = ServerFileIO.usePropertiesByMinecraftVersion(minecraftVersion=str(minecraftVersion))
						time.sleep(3)
						shutil.copy(src=str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{minecraftVersion}/server.properties",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
						ServerFileIO.exportPropertiestoJSON(instanceName=str(modpackName),alternativeDict=properties)
						return 200
		elif modpackName is None and filepath is not None:
			zipResult = CurseforgeClass.extractModpackZIP(filepath=str(filepath))
			if zipResult == 200:
				print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 2 | 8 - Mod Downloading(This can take awhile, depending on how many mods)...")
				#By this point, we created the directory instance, and extracted the modpack. We need to obtain the mods
				os.chdir(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}/mods/")
				rawModList = CurseforgeClass.ManifestJSON_getModFiles(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{filename}")
				modTotal = len(rawModList)
				currentIndex = 0
				urls = []
				Filenames = []
				modlist = []
				modpackData = {}

				for item in range(int(modTotal)):
					modID = int(rawModList[int(currentIndex)]['projectID'])
					fileID = int(rawModList[int(currentIndex)]['fileID'])
					# Parse mod details
					FileDetails = CurseforgeClass.parsefileIDByModID(modID=modID, fileID=fileID)
					modData = CurseforgeClass.parseModID(modID=modID)
					categoryFilter = ["Addons","Applied Energistics 2", "Blood Magic", "Buildcraft", "CraftTweaker", "Create", "Forestry", "Galacticraft", "Industrial Craft", "Integrated Dynamics", "KubeJS", "Skyblock", "Thaumcraft", "Thermal Expansion", "Tinker's Construct", "Adventure and RPG", "API and Library", "Armor, Tools, and Weapons", "Food", "Magic", "Performance", "Server Utility", "Storage", "Technology", "Automation", "Energy", "Energy, Fluid, and Item Transport", "Farming", "Genetics", "Processing", "Player Transport", "World Gen", "Biomes", "Dimensions", "Mobs", "Ores and Resources", "Structures"]
					# Check if the mod belongs to any of the desired categories
					if CurseforgeClass.hascategory(modjsonData=modData, categoryQuery=categoryFilter):
						modname = FileDetails['displayName']
						File = FileDetails['fileName']
						item_url = CurseforgeClass.getModFileDownloadURL(projectID=int(modID), fileID=int(fileID))
						urls.append(str(item_url))
						Filenames.append(str(File))
						modlist.append(modname)
						# Increase the index for the next iteration
						currentIndex += 1
						continue
					else:
						currentIndex += 1
						continue

				#We now turned the projectID and fileID to direct download URLs links
				totalURLs = len(urls)
				url_startingIndex = 0

				for i in range(int(totalURLs)):
					downloadUrl = str(urls[int(url_startingIndex)])
					Filename = str(Filenames[int(url_startingIndex)])
					finalCode = 0
					#We need the filename
					response = requests.get(str(downloadUrl))
					with open(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{Filename}","wb") as jarfiledwload:
						jarfiledwload.write(response.content)
						jarfiledwload.close()
					url_startingIndex += 1
					if url_startingIndex == int(totalURLs):
						finalCode = 200
						break
					else:
						continue
				if finalCode == 200:
					print("[Minerva Server Crafter - Modpack Importing]: Stage 2 | 8 - Mod Downloading - OK")
					print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 3 | 8 - Mod File Operations...")
					#We have the mods. We can move them to the modpack instance folder
					ModpackDirectory = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}"
					shutil.copytree(src=str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads",dst=str(ModpackDirectory) + "/mods",dirs_exist_ok=True)
					files = os.listdir(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads")
					totalFiles = len(files)
					for file in files:
						Filepath = str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads/" + file
						if os.path.isfile(str(Filepath)) == True:
							os.remove(Filepath)
							totalFiles -= 1
							if totalFiles == 0:
								break
							else:
								continue
					print("[Minerva Server Crafter - Modpack Importing]: Stage 3 | 8 - Mod File Operations - OK")
					print("[Minerva Server Crafter - Modpack Importing]: Beginning Stage 4 | 8 - Server Type Downloading...")
					time.sleep(15)
					#We need to do somethings
					minecraftversion = CurseforgeClass.ManifestJSON_getMinecraftVersion(filepath=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{filename}")
					print(minecraftversion)
					modloaderversion = CurseforgeClass.ManifestJSON_getModloaderInfo(filepath=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{filename}")
					modpackData['minecraft-version'] = str(minecraftversion)
					#We need to build the data 
					modloaderversion = str(modloaderversion).split("-")
					modloaderversion = tuple(modloaderversion)
					modpackData["modloader-version"] = str(modloaderversion[1])
					if modloaderversion[0] in ServerType:
						if modloaderversion[0] == "forge":
							#Build the full name of the file
							modpackData["modloader-type"] = modloaderversion[0]
							serverTypeInstaller_filename = str(modloaderversion[0]) + "-" + str(minecraftversion) + "-" + str(modloaderversion[1]) + "-installer.jar"
							modpackData["modloader-realname"] = str(minecraftversion) + "-" + str(modloaderversion[1])
							#We need to build the maven direct download url
							url = "https://maven.minecraftforge.net/net/minecraftforge/" + str(modloaderversion[0]) + "/" + str(minecraftversion) + "-" + str(modloaderversion[1]) + "/" + str(serverTypeInstaller_filename)
							#We need to run a specific command to run the installer
							command = ['java','-jar',str(serverTypeInstaller_filename),'--installServer']
						if modloaderversion[0] == "fabric":
							#We can just use the current installer version
							installerList = MCSCUpdater.FabricBaseClass.getInstallerListingfromTable()
							installerURLlisting = MCSCUpdater.FabricBaseClass.getInstallerURLPrefixListing()
							modpackData["modloader-type"] = modloaderversion[1]
							keyCheck = "modloader-realname" in modpackData.keys()
							if keyCheck == True:
								del modpackData["modloader-realname"]
							serverTypeInstaller_filename = str(modloaderversion[0]) + "-installer-" + str(installerList[0]) + ".jar"
							url = f"{installerURLlisting[0]}/{serverTypeInstaller_filename}"
							#We need to run a specific command to run the installer
							command = ['java','-jar',str(serverTypeInstaller_filename),'server', '-mcversion',str(minecraftversion),'-loader',str(modloaderversion[1]),'-dir',str(downloadsfolder)]
					else:
						print(f"[Minerva Server Crafter - Error Reporting]: Unsupported Modpack. {filename} is using Modloader {modloaderversion[0]}. This Modloader hasn't been developed in this version of Minerva Server Crafter. Feel free to leave it as a suggestion in the Github.")
						#Remove the two folders
						shutil.rmtree(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/importdata")
						shutil.rmtree(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}")
						raise MCSCInternalError("Unsupported Modpack. Modloader is not in the list of supported Server Types.")
					#Get the installer
					response = requests.get(str(url))
					if response.status_code == 200:
						with open(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{serverTypeInstaller_filename}","wb") as forgeinstallerFile:
							forgeinstallerFile.write(response.content)
							forgeinstallerFile.close()
						#Obtain a minecraft vanilla server, just to be sure
						ServerVersion_Control.downloadvanillaserverfile(version=str(minecraftversion))
						shutil.copytree(src=str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{minecraftversion}",dst=str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads",dirs_exist_ok=True)
						os.chdir(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads")
						print("[Minerva Server Crafter - Importing Modpack]: Stage 4 | 8 - Server Type Downloading - OK")
						print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 5 | 8 - Server Type Installation...")
						installerProcess = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
						threadedProcess = threading.Thread(target=CurseforgeClass.outputLines,args=(installerProcess,modloaderversion[0]),name="Server Type Installer Thread")
						threadedProcess.start()
						ReturnCode = installerProcess.wait()
						if ReturnCode == 0:
							threadCompleted = threadedProcess.join()
							print("[Minerva Server Crafter - Importing Modpack]: Stage 5 | 8 - Server Type Installation - OK")
							print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 6 | 8 - Server Type File Operations...")
							#We can safely delete the installer
							os.remove(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/downloads/{serverTypeInstaller_filename}")
							#We can now copy the file tree now
							shutil.copytree(src=str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}",dirs_exist_ok=True)
							#We can clear the downloads folder
							for File_name in os.listdir(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads"):
								file_path = os.path.join(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/downloads", File_name)
								try:
									if os.path.isfile(file_path) or os.path.islink(file_path):
										os.unlink(file_path)
									elif os.path.isdir(file_path):
										shutil.rmtree(file_path)
								except Exception as e:
									raise MCSCInternalError(f"Failed to delete {file_path}.",e)
							print("[Minerva Server Crafter - Importing Modpack]: Stage 6 | 8 - Server Type File Operations - OK")
							print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 7 | 8 - Modpack Overrides...")
							#We can grab the overrides
							shutil.copytree(src=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/importdata/{filename}/overrides",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}",dirs_exist_ok=True)
							print("[Minerva Server Crafter - Importing Modpack]: Stage 7 | 8 - Modpack Overrides - OK")
							time.sleep(10)
							print("[Minerva Server Crafter - Importing Modpack]: Beginning Stage 8 | 8 - Importing Cleanup...")
							#We can safely delete the import data
							shutil.rmtree(str(rootFilepath) + "/base/sandbox/Instances/Modpacks/importdata")
							print("[Minerva Server Crafter - Importing Modpack]: Stage 8 | 8 - Importing Cleanup - OK")
							print(f"[Minerva Server Crafter]: {filename} Curseforge Modpack has been successfully imported. Adding to Modpack Table...")
							#Connect to database
							os.chdir(str(rootFilepath))
							MCSCDatabase = sqlite3.connect('mcsc_data.db')
							MCSC_Cursor = MCSCDatabase.cursor()
							MCSC_Cursor.execute("INSERT INTO CurseforgeModpackInstances_Table (ModpackName,ModpackType,ModpackTypeVersion,Modpack_modlist) VALUES (?,?,?,?)",(modpackName,modloaderversion[0],modloaderversion[1],str(modlist)))
							MCSCDatabase.commit()
							MCSC_Cursor.close()
							MCSCDatabase.close()
							print("[Minerva Server Crafter]: Modpack has been added to the Modpack Table.")
							filename = os.path.splitext(os.path.basename(filename))[0]
							if isLegacy == True:
								legacybool = isLegacy
								ServerFileIO.addInstancetoJSON(name=str(modpackName),serverType=str(modpackData["modloader-type"]),isModded=True,modlist=modlist,modloaderversion=modpackData["modloader-version"],enforcelegacy=legacybool,serverpath_legacy=str(filepath),minecraftversion=minecraftVersion)
								os.rename(src=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
								ServerFileIO.onExit_setInstancePointer(instanceName=str(modpackName))
								ServerFileIO.writemcEULA(instanceName=str(modpackName))
								properties = ServerFileIO.usePropertiesByMinecraftVersion(minecraftVersion=str(minecraftVersion))
								shutil.copyfile(src=str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{minecraftVersion}/server.properties",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
								ServerFileIO.exportPropertiestoJSON(instanceName=str(modpackName),alternativeDict=properties)
								
							else:
								ServerFileIO.addInstancetoJSON(name=str(modpackName),serverType=str(modpackData["modloader-type"]),isModded=True,modlist=modlist,modloaderversion=modpackData["modloader-version"],minecraftversion=minecraftVersion)
								os.rename(src=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{filename}",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
								ServerFileIO.onExit_setInstancePointer(instanceName=str(modpackName))
								ServerFileIO.writemcEULA(instanceName=str(modpackName))
								properties = ServerFileIO.usePropertiesByMinecraftVersion(minecraftVersion=str(minecraftVersion))
								shutil.copyfile(src=str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{minecraftVersion}/server.properties",dst=str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
								ServerFileIO.exportPropertiestoJSON(instanceName=str(modpackName),alternativeDict=properties)
							return 200

class MCSCUpdater():
	'Version Updater for Minerva Server Crafter'
	q = queue.Queue()

	@classmethod
	def getUpdates(self):
		try:
			self.PurpurBaseClass.updatePurpurTable()
			self.SpigotBaseClass.updateBuildToolsTable()
			self.ForgeBaseClass.updateForgeVersionTable()
			self.MinecraftVanillaBaseClass.updateMinecraftVersions()
			self.FabricBaseClass.updateFabricInstallerTable()
			self.FabricBaseClass.updateFabricVersions()
			return
		except MCSCInternalError as e:
			print(f"Internal Error has occured: {e}")
			return
	
	@classmethod
	def updater(cls):
		try:
			cls.getUpdates()
			cls.q.put(True)
		except MCSCInternalError as e:
			print(e)
			cls.q.put(False)

	@classmethod
	def runUpdates(cls):
		#Thread the updates
		updaterThread = threading.Thread(target=cls.updater,name="Minerva Server Crafter - Updater")
		updaterThread.start()
		threadresult = cls.q.get()
		if threadresult == True:
			print("[Minerva Server Crafter - Updater]: Database Table Updates completed. Launching...")
			return
		else:
			raise MCSCInternalError("Failed to run Updates. Internal Exception")

	class MinecraftVanillaBaseClass():
		def updateMinecraftVersions():
			'Checks for Minecraft Version updates. When there is an update, it gets added to the table, and Minerva Server Crafter reboots'
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()

		    # Fetch the latest available Minecraft versions from Mojang
			versionManifestURL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
			response = requests.get(versionManifestURL)

			if response.status_code == 200:
				manifestData = response.json()

				#Store versions with the time of release
				versionswithTime = [{'version': version['id'],'timestamp': version['releaseTime']} for version in manifestData['versions']]

				#Sort the version based on the time of release in decending order
				sortedVersions = sorted(versionswithTime,key=lambda x: x['timestamp'],reverse=True)

		        # Retrieve existing versions from the database
				MCSC_Cursor.execute('SELECT version, timestampRelease FROM minecraftversion_Table')
				existing_versions = {row[0]: row[1] for row in MCSC_Cursor.fetchall()}

				# Insert only the new versions into the database
				new_versions = [version for version in sortedVersions if version['version'] not in existing_versions]
				totalupdates = len(new_versions)

				if new_versions:
					print(f"[Minerva Server Crafter - Updater - Minecraft Version Check]: There are {totalupdates} new Minecraft Version(s) updates. Updating...")
					MCSC_Cursor.execute('DELETE FROM minecraftversion_Table')
					MCSCDatabase.commit()
					for version in new_versions:
						MCSC_Cursor.execute('INSERT INTO minecraftversion_Table (version, timestampRelease) VALUES (?, ?) ', (version['version'],version['timestamp']))
					for key,val in existing_versions.items():
						MCSC_Cursor.execute('INSERT INTO minecraftversion_Table (version, timestampRelease) VALUES (?, ?)', (key,val))

				# Commit the changes
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					print('[Minerva Server Crafter - Updater - Minecraft Version Check]: Version Table has been updated successfully. Rebooting Program...')
					os.execl(sys.executable,sys.executable,*sys.argv)
				else:
					print("[Minerva Server Crafter - Updater - Minecraft Version Check]: No new Minecraft Versions detected")
					return
			else:
				print("[Minerva Server Crafter - Updater]: Failed to get version manifest")
				return

	class PurpurBaseClass():
		'Utility that handles the compatibilities for Purpur'
		def getCompatibleVersions() -> list:
			#Parse the JSON
			response = requests.get("https://api.purpurmc.org/v2/purpur")
			if response.status_code == 200:
				purpurRawData = response.json()
				compatibleVersions = [s for s in purpurRawData["versions"]]
				return compatibleVersions

		def updatePurpurTable():
			'Checks for updates from the Purpur API. When there is a new build is found, the table gets updated(Newest to oldest). When the purpur table is updated, Minerva Server Crafter reboots'
			#We need to check for any purpur updates
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			baseurl = "https://api.purpurmc.org/v2/purpur/"
			response = requests.get(baseurl)
			if response.status_code == 200:
				rawpurpur = response.json()
				currentversionData = [str(Version(v)) for v in rawpurpur["versions"]]
				currentBuilds = {}
				for version in currentversionData:
					buildURL = f"{baseurl}{version}"
					mcVersion = Version(version)
					buildresponse = requests.get(buildURL)
					if buildresponse.status_code == 200:
						rawbuildData = buildresponse.json()
						currentbuilds = rawbuildData["builds"]["all"]
						buildDataIntegrityCheck = [int(i) for i in currentbuilds]
						sortedBuilds = sorted(buildDataIntegrityCheck,reverse=True)
						currentBuilds[str(mcVersion)] = sortedBuilds
				sortedCurrentBuilds = sorted(currentBuilds.items(),reverse=True)
				del currentBuilds
				currentBuilds = dict(sortedCurrentBuilds)
				MCSC_Cursor.execute("SELECT BuildID, MinecraftVersion FROM PurpurVersion_Table")
				existingBuilds = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
				newBuilds = [(PurpurBuild,minecraftversion) for minecraftversion, PurpurBuild in currentBuilds.items() for PurpurBuild in PurpurBuild if PurpurBuild not in existingBuilds]
				totalNewBuilds = len(newBuilds)
				if newBuilds:
					MCSC_Cursor.execute("DELETE FROM PurpurVersion_Table")
					print(f"[Minerva Server Crafter - Updater - Purpur Builds Check]: There are {totalNewBuilds} new build(s). Updating...")
					for mcversion,purpurBuildList in currentBuilds.items():
						for purpurBuildID in purpurBuildList:
							MCSC_Cursor.execute("INSERT INTO PurpurVersion_Table VALUES (?,?)", (purpurBuildID,mcversion))
						for key,val in existingBuilds.items():
							MCSC_Cursor.execute("INSERT INTO PurpurVersion_Table VALUES (?,?)", (key,val))
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					print("[Minerva Server Crafter - Updater - Purpur Builds Check]: Version Table has been updated successfully. Rebooting...")
					os.execl(sys.executable,sys.executable,*sys.argv)
				else:
					print("[Minerva Server Crafter - Updater - Purpur Builds Check]: No new Purpur builds detected")
					return
		def getBuildsbyVersion(version) -> list:
			'Returns a list of Purpur Versions thats compatiable with the given Minecraft Version'
			#We need to parse the database table
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute("SELECT BuildID FROM PurpurVersion_Table WHERE MinecraftVersion = ?", (str(version),))
			builds = [row[0] for row in MCSC_Cursor.fetchall()]
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return builds

	class SpigotBaseClass():
		'Utility that handles the compatiblities thats tied to Spigot and its forks'
		def updateBuildToolsTable():
			'Checks for successful builds of BuildTools in the jenkins repository. Failed builds are exempt as a result. When there is successful builds thats not in the database table, the table gets updated(newest builds to oldest). When the table gets updated, Minerva Server Crafter reboots.'
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute("SELECT BuildID, Url FROM BuildTools_SuccessfulBuildVerified_Table")
			databaseData = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
			# Parse the JSON
			response = requests.get("https://hub.spigotmc.org/jenkins/job/BuildTools/api/json")
			if response.status_code == 200:
				buildtoolsjson = response.json()
				availableBuilds = [i for i in buildtoolsjson['builds']]
				SuccessfulBuilds = {}
				for item in availableBuilds:
					Key = item.get('number')
					Value = item.get('url')
					SuccessfulBuilds[Key] = Value

				# We need to omit failed builds. We can use the RSS Feed that houses the failed builds
				rssfeed_failedBuilds = feedparser.parse("https://hub.spigotmc.org/jenkins/job/BuildTools/rssFailed")
				failedBuilds = {}
				failedBuildsEntries = rssfeed_failedBuilds['entries']
				for entry in failedBuildsEntries:
					# We can base the dictionary using the title and its link
					key = entry.get('title')
					value = entry.get('link')
					failedBuilds[key] = value

				# Create a list of keys to delete
				keys_to_delete = []
				for x, y in SuccessfulBuilds.items():
					# Check for failed builds
					resultQuery = y in failedBuilds.values()
					if resultQuery:
						# Add the key to the list of keys to delete
						keys_to_delete.append(x)

				# Delete the keys outside the loop
				for key in keys_to_delete:
					del SuccessfulBuilds[key]

				#Now that we have a dictionary with all of the successful builds, we need to know if its missing in the database
				missingEntries = {a: b for a, b in SuccessfulBuilds.items() if a not in databaseData}
				TotalEntriesMissing = len(missingEntries)
				if missingEntries:
					MCSC_Cursor.execute("DELETE FROM BuildTools_SuccessfulBuildVerified_Table")
					MCSCDatabase.commit()
					print(f"[Minerva Server Crafter - Updater - BuildTools Build Check]: There are {TotalEntriesMissing} new successful builds. Updating database...")
					for BuildID,url in missingEntries.items():
						MCSC_Cursor.execute("INSERT INTO BuildTools_SuccessfulBuildVerified_Table (BuildID, Url) VALUES (?,?)", (BuildID, url))
					for k,v in databaseData.items():
						MCSC_Cursor.execute("INSERT INTO BuildTools_SuccessfulBuildVerified_Table (BuildID, Url) VALUES (?,?)", (k, str(v)))
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					print("[Minerva Server Crafter - Updater - BuildTools Build Check]: Version Table has been updated successfully. Rebooting Program...")
					os.execl(sys.executable,sys.executable,*sys.argv)
				else:
					print("[Minerva Server Crafter - Updater - BuildTools Build Check]: No new BuildTools Versions detected")
					return


		def getBuildTools(url=None):
			'Obtains by downloading the last successful build from the jenkins'
			if url == None:
				#We need to parse the jenkins archive and get the last successful build of BuildTools jar file
				response = requests.get("https://hub.spigotmc.org/jenkins/view/Public/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar")
			else:
				#We need to parse the jenkins archive and get the BuildTools jar file using the given url
				response = requests.get(str(url))
			if response.status_code == 200:
				if os.path.isdir(str(rootFilepath) + "/base/sandbox/build/BuildTools") == False:
					os.makedirs(str(rootFilepath) + "/base/sandbox/build/BuildTools")
				with open(str(rootFilepath) + "/base/sandbox/build/BuildTools/BuildTools.jar","wb") as buildtoolsjar:
					buildtoolsjar.write(response.content)
					buildtoolsjar.close()
				return
		def runBuildTools(parameter=None):
			'Runs Buildtools. If a parameter is given, Buildtools will run with the parameter'
			x = queue.Queue()
			def session():
				if parameter == None:
					#Run BuildTools with no parameters. This retrieves the latest version of spigot
					process = subprocess.Popen(['java','-jar','BuildTools.jar'])
				else:
					process = subprocess.Popen(['java','-jar','BuildTools.jar',str(parameter)])
				returnCode = process.wait()
				if returnCode == 0:
					x.put(returnCode)
					return
			os.chdir(str(rootFilepath) + "/base/sandbox/build/BuildTools/")
			BuildToolsThread = threading.Thread(target=session,name="BuildToolsInstance")
			BuildToolsThread.start()
			BuildToolsThread.join()
			BuildToolsThreadresult = x.get()
			if BuildToolsThreadresult == 0:
				print(f"Command exited with the return code of {BuildToolsThreadresult}")
				return

		def getCraftBukkit(version):
			'Installs the most current Craftbukkit Version by passing the given Minecraft Version'
			#We need to see if we have buildtools first
			if os.path.isfile(str(rootFilepath) + "/base/sandbox/build/BuildTools/BuildTools.jar") == True:
				#We have the last successful build of BuildTools
				#We want to save the craftbukkit jar in its instance within the version folder
				outputDirectory = str(rootFilepath) + f"/base/sandbox/Instances/CraftBukkit/{version}/"
				if os.path.isdir(outputDirectory) == False:
					os.mkdir(outputDirectory)
				parametercmd = "--o", outputDirectory, "--rev", str(version), "--compile craftbukkit"
				MCSCUpdater.SpigotBaseClass.runBuildTools(parameter=str(parametercmd))
				return
			else:
				#Get buildtools
				MCSCUpdater.SpigotBaseClass.getBuildTools()
				#Re-run the command
				MCSCUpdater.SpigotBaseClass.getCraftBukkit(version)
				return

		def getSpigot(version):
			'Installs the most current Spigot Version by passing the given Minecraft Version'
			#Check for BuildTools
			if os.path.isfile(str(rootFilepath) + "/base/sandbox/build/BuildTools/BuildTools.jar") == True:
				#Put Spigot in its Instance folder in the version folder
				outputdirectory = str(rootFilepath) + f"/base/sandbox/Instances/Spigot/{version}"
				outputdirectory = str(outputdirectory)
				if os.path.isdir(outputdirectory) == False:
					os.mkdir(outputdirectory)
				#Run BuildTools with parameters
				parameterCmd = "--o",outputdirectory,"--rev",str(version)
				MCSCUpdater.SpigotBaseClass.runBuildTools(parameter=parameterCmd)
				return
			else:
				#Get BuildTools
				MCSCUpdater.SpigotBaseClass.getBuildTools()
				#Re-run the command
				MCSCUpdater.SpigotBaseClass.getSpigot(version)
				return

	class ForgeBaseClass():
		#Forge doesnt have a web-based API. Theres so little I can do in this dev stage
		def getmcVersionListing() -> list:
			'Returns a sorted list of compatible Minecraft Versions that forge works with using Curseforge\'s API'
			#Parse the database table
			response = requests.get("https://api.curseforge.com/v1/minecraft/modloader",headers={"Accept": "application/json"})
			if response.status_code == 200:
				ForgeRawData = response.json()
				forgeData = ForgeRawData["data"]
				compatibleMCVersions = []

				for version in forgeData:
					MCVersion = version["gameVersion"]
					if MCVersion not in compatibleMCVersions:
						compatibleMCVersions.append(MCVersion)
					else:
						continue
				
				#Sort the versions
				sortedMCVersions = sorted(compatibleMCVersions,key=lambda x: Version(x),reverse=True)
				return sortedMCVersions

		def updateForgeVersionTable():
			'Checks for Forge Updates from Curseforge. When a new forge version is detected, the table is updated. When the table is updated, Minerva Server Crafter reboots.'
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			response = requests.get("https://api.curseforge.com/v1/minecraft/modloader",headers={"Accept": "application/json",'x-api-key': str(CurseforgeClass.decodeByteSecret())})
			if response.status_code == 200:
				forgeRawData = response.json()
				forgedata = forgeRawData["data"]
				#We need to strip off the forge- tag on it while retain the minecraft version attached to it
				currentforgeversions = {}
				for v in forgedata:
					forgeVersion = v["name"].split("forge-")[1]
					minecraftVersion = v["gameVersion"]
					if minecraftVersion in currentforgeversions:
						currentforgeversions[minecraftVersion].append(forgeVersion)
					else:
						currentforgeversions[minecraftVersion] = [forgeVersion]

				#We need to take a snapshot of whats in the database table
				MCSC_Cursor.execute("SELECT forgeversion, minecraftversion FROM forgeVersion_Table")
				existingVersions = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
				newVersions = [(forgeVersion, minecraftVersion) for minecraftVersion, forgeVersions in currentforgeversions.items() for forgeVersion in forgeVersions if forgeVersion not in existingVersions]
				totalNewVersions = len(newVersions)
				if newVersions:
					MCSC_Cursor.execute("DELETE FROM forgeVersion_Table")
					print(f"[Minerva Server Crafter - Updater - Forge Version Check]: There are {totalNewVersions} total new version(s). Updating...")
					for minecraft_version, forge_version_list in sorted(currentforgeversions.items(), key=lambda x: Version(x[0]), reverse=True):
						for forge_version in forge_version_list:
							MCSC_Cursor.execute("INSERT INTO forgeVersion_Table VALUES (?, ?)", (forge_version, minecraft_version))

					for Key,Val in existingVersions.items():
						MCSC_Cursor.execute("INSERT INTO forgeVersion_Table VALUES (?, ?)",(Key,Val))
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					print("[Minerva Server Crafter - Updater - Forge Version Check]: Version Table Updated. Rebooting...")
					os.execl(sys.executable,sys.executable,*sys.argv)
				else:
					print("[Minerva Server Crafter - Updater - Forge Version Check]: No new Forge Versions detected")
					return
		def getForgeVersionsbyVersion(version) -> list:
			'Returns a list of Forge Versions thats compatiable with the given Minecraft Version'
			#We need to get the forge versions based off of the given minecraft version
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute("SELECT forgeversion FROM forgeVersion_Table WHERE minecraftversion = ?",(str(version),))
			forgeversionlist = [row[0] for row in MCSC_Cursor.fetchall()]
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return forgeversionlist
	class FabricBaseClass():
    #We need to do some things
		def updateFabricInstallerTable():
			'Checks for Fabric Installer updates'
			MCSCDatabase = sqlite3.connect('mcsc_data.db')
			MCSC_Cursor = MCSCDatabase.cursor()

			response = requests.get("https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml")

			if response.status_code == 200:
				xmlData = xmltodict.parse(response.content)
				loaderversionList = xmlData["metadata"]['versioning']['versions']['version']

				fabricloaderURLS = {str(item): f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{item}/" for item in loaderversionList}

				# Get versions already in the table
				MCSC_Cursor.execute("SELECT version FROM FabricInstallerVersion_Table")
				currentVersions = set(row[0] for row in MCSC_Cursor.fetchall())

				# Filter new versions not already in the table
				newVersions = [(loaderversion, fabricloaderURLS[loaderversion]) for loaderversion in loaderversionList if loaderversion not in currentVersions]
				totalUpdates = len(newVersions)

				if newVersions:
					print(f"[Minerva Server Crafter - Updater - Fabric Installer Check]: There are {totalUpdates} total update(s). Updating Table...")
					MCSC_Cursor.execute("DELETE FROM FabricInstallerVersion_Table")
					for v, u in sorted(newVersions, key=lambda x: Version(x[0]), reverse=True):
						MCSC_Cursor.execute("INSERT INTO FabricInstallerVersion_Table (version,url) VALUES (?,?)",(v,u))
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					print("[Minerva Server Crafter - Updater - Fabric Installer Check]: Version Table has been successfully updated. Rebooting...")
					os.execl(sys.executable,sys.executable,*sys.argv)

				else:
					print("[Minerva Server Crafter - Updater - Fabric Installer Check]: No new Fabric Installer versions detected")
					MCSC_Cursor.close()
					MCSCDatabase.close()
					return
		
		def getInstallerListingfromTable() -> list:
			'Returns a complete list of applicable installer versions from the version Table'
			#connect to the database
			MCSCDatabase = sqlite3.connect('mcsc_data.db')
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute('SELECT version FROM FabricLoaderVersionTable')
			loaderListing = [loaderVersion[0] for loaderVersion in MCSC_Cursor.fetchall()]
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return loaderListing
		
		def getInstallerURLPrefixListing() -> list:
			'Returns a complete list of applicable installer urls from the version Table. This does not provide the full url, just the pointer of base url'
			#Connect to the database
			MCSCDatabase = sqlite3.connect('mcsc_data.db')
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute('SELECT url FROM FabricLoaderVersionTable')
			loaderListing = [loaderVersion[0] for loaderVersion in MCSC_Cursor.fetchall()]
			MCSC_Cursor.close()
			MCSCDatabase.close()
			return loaderListing
		
		def updateFabricVersions():
			'Checks for version updates for fabric using the Curseforge API'
			headers = {"Accept": "application/json",'x-api-key': str(CurseforgeClass.decodeByteSecret())}

			response = requests.get("https://api.curseforge.com/v1/minecraft/modloader",headers=headers,params={'includeAll': True})
			if response.status_code == 200:
				rawFabricVersionData = response.json()
				#We need to clean up the data a little cuz its got all of the versions that curseforge offers
				FabricVersionData = rawFabricVersionData['data']
				currentfabricVersions = {}
				for v in FabricVersionData:
					name = v['name']
					if name.startswith('fabric-') == True:
						fabricversiondata = name.split('-')
						fabricVersion = fabricversiondata[1]
						minecraftVersion = fabricversiondata[2]
						if fabricVersion not in currentfabricVersions.keys():
							currentfabricVersions[str(fabricVersion)] = []
							currentfabricVersions[str(fabricVersion)].append(minecraftVersion)
							continue
						else:
							currentfabricVersions[str(fabricVersion)].append(minecraftVersion)
							continue
				#We need to see if table needs any updates
				os.chdir(str(rootFilepath))
				MCSCDatabase = sqlite3.connect("mcsc_data.db")
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT version, compatiableMinecraftVersions FROM fabricVersion_Table")
				versionTableData = {row[0]: row[1] for row in MCSC_Cursor.fetchall()}
				newversions = [version for version in currentfabricVersions.keys() if version not in versionTableData.keys()]
				totalupdates = len(newversions)
				if newversions:
					#We have updates
					print(f"[Minerva Server Crafter - Updater - Fabric Version Check]: There are {totalupdates} updates. Updating Table...")
					MCSC_Cursor.execute("DELETE FROM fabricVersion_Table")
					for k1,v1 in currentfabricVersions.items():
						MCSC_Cursor.execute("INSERT INTO fabricVersion_Table (version,compatiableMinecraftVersions) VALUES (?,?)", (k1,str(v1)))
					#Insert what used to be in the table
					for k2,v2 in versionTableData.items():
						MCSC_Cursor.execute("INSERT INTO fabricVersion_Table (version,compatiableMinecraftVersions) VALUES (?,?)", (k2,str(v2)))
					
					print("[Minerva Server Crafter - Updater - Fabric Version Check]: Version Table has been successfully updated. Rebooting...")
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					os.execl(sys.executable,sys.executable,*sys.argv)
				else:
					print("[Minerva Server Crafter - Updater - Fabric Version Check]: No new Fabric Versions detected")
					return

class ServerVersion_Control():
	'Utility for identifying/managing Minecraft Server Versions'
	
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
		global ServerType
		if servertype is not None:
			if servertype in ServerType:
				if servertype == "server":
					#This is the Minecraft Vanilla default filename. We already have that as a seperate command.
					print("[Minerva Server Crafter - Server Version Control API]: Depreciated usage. Use ServerVersion_Control.getVersionList() for Minecraft Vanilla versions.")
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
		
		Downloads server.jar based on the specified version. The downloaded jar is saved in base/build/Minecraft Vanilla/(version number here)

		'''
		if os.path.isdir(str(rootFilepath) + "/base/sandbox/build/Minecraft Vanilla") == False:
			os.mkdir(str(rootFilepath) + "/base/sandbox/build/Minecraft Vanilla")
		if os.path.isdir(str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{version}") == False:
			os.mkdir(str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{version}")
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
						print(f"File Size: {totalSize / (1024 * 1024):.2f}MB")
						if servercontentjarResponse.status_code == 200:
							#Save to the sandbox directory
							with open(str(rootFilepath) + f"/base/sandbox/build/Minecraft Vanilla/{version}/server.jar","wb") as jarFile:
								jarFile.truncate()
								for chunk in servercontentjarResponse.iter_content(chunk_size=8192):
									jarFile.write(chunk)
									downloadedSize = len(chunk)
							print(f"[Minerva Server Crafter - Version Control]: Server File for Minecraft Version {version} downloaded Successfully.")
							return True
						else:
							print(f"[Minerva Server Crafter - Version Control]: Failed to fetch server.jar for Minecraft Version {version}")
							return False
					else:
						print(f"[Minerva Server Crafter - Version Control]: Failed to fetch the {version}.json for Minecraft Version {version}")
						return False
			else:
				print(f"[Minerva Server Crafter - Version Control]: Version {version} doesn't exist for Minecraft. Check the version number for troubleshooting.")
				return False
		else:
			print("[Minerva Server Crafter - Version Control]: Failed to fetch version manifest json file")
			return False
	
	def getVersionList():
		'Returns a list of Minecraft Vanilla Versions'
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		MCSC_Cursor.execute('SELECT version FROM minecraftversion_Table ORDER BY timestampRelease DESC')
		returnVal = [row[0] for row in MCSC_Cursor.fetchall()]
		MCSC_Cursor.close()
		MCSCDatabase.close()
		return returnVal
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
			print(e)
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
				print("[Minerva Server Crafter]: Downloaded fabric installer Successfully.")
				return

class HardwareSpec():
	'HardwareSpec() -> Memory Management \n \n Extra Utilities for Memory Management '
	def getByteSize(bytes, suffix="B"):
		'getByteSize(bytes) -> String \n \n Returns the total measurement of bytes either in Megabytes, or Gigabytes as a string'
		totalBytes = int(bytes)
		if totalBytes >= int(1048576) and totalBytes < int(1073741824):
			unit = "M"
			TotalMB = int(totalBytes) / (int(1024) * int(1024))
			return str(f"{TotalMB:.2f}{unit}{suffix}")
		if totalBytes >= int(1073741824) and totalBytes < int(1099511627775):
			unit = "G"
			TotalGB = int(totalBytes) / (int(1024) * int(1024) * int(1024))
			return str(f"{TotalGB:.2f}{unit}{suffix}")
	def getByteSizeInt(bytes):
		'getByteSizeInt(bytes) -> Integer \n \n Returns the total measurement of bytes either in Megabytes, or Gigabytes as a tuple. \n \n Tuple Reference \n ================= \n index 0: Integer value \n index 1: Measurement Scale'
		totalbytes = int(bytes)
		if totalbytes >= int(1048576) and totalbytes < int(1073741824):
			TotalMB = int(totalbytes) / (int(1024) * int(1024))
			return (float(f"{TotalMB:.2f}"),"MB")
		if totalbytes >= int(1073741824) and totalbytes < int(1099511627775):
			TotalGB = int(totalbytes) / (int(1024) * int(1024) * int(1024))
			return (float(f"{TotalGB:.2f}"),"GB")
	def getPhysicalMemory(suffix="B"):
		'getPhysicalMemory() -> Hardware Scale \n \n Returns the amount of physical memory installed'
		TotalBytes = int(psutil.virtual_memory().total)
		if TotalBytes >= int(1048576) and TotalBytes < int(1073741824):
			unit = "M"
			TotalMB = int(TotalBytes) / (int(1024) * int(1024))
			RoundedMB = round(TotalMB)
			PhysicalMemMB = math.trunc(int(RoundedMB))
			return f'{PhysicalMemMB}{unit}{suffix}'
		if TotalBytes >= int(1073741824) and TotalBytes < int(1099511627775):
			unit = "G"
			TotalGB = int(TotalBytes) / (int(1024) * int(1024) * int(1024))
			RoundedGB = round(TotalGB)
			PhysicalMemGB = math.trunc(int(RoundedGB))
			return f'{PhysicalMemGB}{unit}{suffix}'
		return
	def ServerQuery_onServerStart_MemoryAllocate(ScaledMemInt=0,ScaledMemSize=None,MemoryScaleSize=None):
		#We need to properly measure the amount of ScaledMemInt into MemoryScaleSize(i.e. 32GB in Megabytes)
		#Simple Math time xD
		ScaledMemByteSize = str(ScaledMemSize)
		if ScaledMemByteSize == "GB":
			#We need the total amount of scaled memory in bytes
			ScaledMemIntinbytes = int(ScaledMemInt) * int(1**9)
			#We need to scale the bytes in the value of MemoryScaleSize
			ExpectedScaleSize = str(MemoryScaleSize)
			if ExpectedScaleSize == "MB":
				#Scale the bytes in megabytes
				TotalScaledMemMB = int(ScaledMemIntinbytes) / (int(1024) * int(1024))
				#We need it as a whole number
				RoundedScaledMemMB = round(TotalScaledMemMB)
				ScaledMeminMB = math.trunc(int(RoundedScaledMemMB))
				return (float(ScaledMemInt),str(ScaledMemSize),float(f'{ScaledMeminMB}'))
	
class InternetHost():
	'InternetHost() -> Internet Connection \n \n Extra Utilities for Internet Connection'
	global ConsoleWindow
	def connectionCheck():
		'connectionCheck() -> Socket Connection \n \n Creates a Socket Connection. This is primarily used for checking if the local host is connected to the internet. \n If the socket connection is successfully connected, then it returns true. Otherwise, an exception is raised.'
		try:
			result = socket.create_connection(('8.8.8.8', 53),timeout=8)
			result.close()
			return True
		except (OSError,ExceptionGroup) as e:
			print(e)
			ConsoleWindow.displayException(e)
			return False
	def getIPV4():
		'getIPV4() -> Local IP Address \n \n Returns the IP Address of the Local Host Computer'
		try:
			if InternetHost.connectionCheck() == True:
				Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				try:
					Socket.connect(('10.255.255.255',1))
					IP = Socket.getsockname()[0]
				except Exception:
					IP = '127.0.0.1'
				finally:
					Socket.close()
				return IP
			else:
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter API - Internet Host]: Unable to connect to the Internet(REASON: No Connection)")
				return
		except socket.error as e:
			ConsoleWindow.updateConsole(END,"[Minerva Server Crafter API - Internet Host]: Unable to connect to the Internet(REASON: Exception raised, detailed walkthrough below)")
			ConsoleWindow.displayException(e)
			return
	def getPublicIP():
		'getPublicIP() -> Public IP Address \n \n Returns the Public IP Address of the Local Host'
		try:
			public_ip = requests.get('https://api.ipify.org',timeout=5)
			if public_ip.status_code == 200:
				return public_ip.text.strip()
		except requests.RequestException as e:
			ConsoleWindow.displayException(e)
			return
minecraftVersions = ServerVersion_Control.getVersionList()

class ServerFileIO():
	'ServerFileIO -> File Operation Class \n \n ServerFileIO has Core Components of Minerva Server Crafter. Its primarily File Operations, and Database Queries.'
	def __init__(self):
		PropertiesFileSearchThread = None
		BannedPlayers_SearchThread = None
		BannedIPs_SearchThread = None
		ServerJarSelection = None
		WhitelistPlayers_SearchThread = None
	
	def getInstanceMinecraftVersion(instanceName=None):
		'Returns the Minecraft Version that the given instance is using'
		if instanceName is not None:
			with open(str(rootFilepath) + "/properties.json","r") as rawJSONData:
				dataDump = json.load(rawJSONData)
				instances = dataDump["Instances"]
				for category in ["Vanilla","Modded"]:
					for instance in instances[category]:
						if instanceName in instance:
							minecraftversion = str(instance[str(instanceName)]["minecraftVersion"])
							break
						else:
							continue
				rawJSONData.close()
		return minecraftversion

	def onExit_setInstancePointer(instanceName=None):
		'Handler for setting the last loaded instance when Minerva Server Crafter closes'
		#We need point to an instance
		with open(str(rootFilepath) + "/properties.json", "r+") as jsonPointer:
			datadump = json.load(jsonPointer)
			instances = datadump["Instances"]
			for category in ["Vanilla","Modded"]:
				for instance in instances[category]:
					if instanceName in instance:
						instances["last-config"]["id"] = str(instanceName)
						jsonPointer.seek(0)
						json.dump(datadump,jsonPointer,indent=4)
						jsonPointer.close()
						return

	def onBoot_loadInstance():
		'Handler for loading the last loaded instance properties at startup'
		#We need to get the name of the instance from the last loaded instances
		with open(str(rootFilepath) + "/properties.json", "r+") as jsonPoint:
			datadump = json.load(jsonPoint)
			instances = datadump["Instances"]
			instanceName = datadump["Instances"]["last-config"]["id"]
			#We can now load from the json
			for category in ["Vanilla","Modded"]:
				for instance in instances[category]:
					if instanceName in instance:
						jsonBranch = instance[instanceName]["properties"]

			for key,val in jsonBranch.items():
				MinecraftServerProperties[key] = val if val else None
			jsonPoint.close()
		return
	
	def loadJSONProperties(instanceName=None):
		"""Loads properties.json data and updates the MinecraftServerProperties JSON Model in memory for a specific instance
		
		Parameters:

		instanceName : The name of the instance to be loaded
		"""
		#Load the json file
		with open(str(rootFilepath) + "/properties.json","r") as readJSON:
			dataDump = json.load(readJSON)
			#Search for the instance
			instances = dataDump["Instances"]
			for category in ["Vanilla","Modded"]:
				for instance in instances[category]:
					if instanceName in instance:
						for key,val in instance[instanceName]["properties"].items():
							MinecraftServerProperties[key] = val if val else None
						print(f"[Minerva Server Crafter]: Properties for {instanceName} loaded. Rebuilding...")
						#Statically set the IP
						MinecraftServerProperties["server-ip"] = str(InternetHost.getIPV4())
						#Apply update
						MinecraftServerProperties.update()
						print("[Minerva Server Crafter]: Structure Rebuilt Successfully")
						ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
						return
					else:
						continue
				return
	
	def exportPropertiestoJSON(instanceName=None,alternativeDict=None):
		"""
		Saves the data from memory to properties.json under instanceName

		"""
		print(f"[Minerva Server Crafter]: Saving properties for {instanceName}...")
		with open(str(rootFilepath) + "/properties.json","r+") as jsonWrite:
			datadump = json.load(jsonWrite)
			vanillaInstances = datadump["Instances"]["Vanilla"]
			moddedInstances = datadump["Instances"]["Modded"]
			for instanceVanillaCheck in vanillaInstances:
				if instanceName in vanillaInstances:
					if alternativeDict is not None:
						instanceVanillaCheck[instanceName]["properties"] = alternativeDict
						break
					else:
						instanceVanillaCheck[instanceName]["properties"] = MinecraftServerProperties
						break
				else:
					break

			for instanceModdedCheck in moddedInstances:
				if instanceName in moddedInstances:
					if alternativeDict is not None:
						instanceModdedCheck[instanceName]["properties"] = alternativeDict
						break
					else:
						instanceModdedCheck[instanceName]["properties"] = MinecraftServerProperties
						break
				else:
					break
			
			jsonWrite.seek(0)
			json.dump(datadump,jsonWrite,indent=4)
			jsonWrite.truncate()
			jsonWrite.close()
		print("[Minerva Server Crafter]: Properties Saved for " + str(instanceName) + ".")
		return
	
	def importpropertiestojson(serverjarpath=None, instanceName=None, isModded=None, minecraftVersion = None, create_data_ok=True, legacyBehavior = False, modloader_version=None,modloaderType=None):
		"""
		Imports server.properties to json model in memory.

		Parameters
		==========

		serverjarpath : filepath to the server directory

		instanceName : name of the instance

		isModded : Tells whether or not if the instanceName is Vanilla Minecraft or Modded Minecraft. This must be called when creating the instance in the json file

		minecraftVersion : minecraft version of the instanceName. This must be called for when creating the instance in the json file

		create_data_ok : Tells whether or not to treat the calling of the function like if the instanceName wasn't in the json file and makes the profile within the json. This must be called for the data processing when the instance is being created while the flag is set to true. Otherwise, it will pass the instanceName to exportPropertiestoJSON() 	

		legacyBehavior : Tells whether or not to enforce launching the server from the server directory instead from an instance folder. This must be false while create_data_ok is True. Otherwise, an exception is raised

		modloader_Version: Tells what the modloader version is. This must be given when isModded is true. Otherwise, an MCSCInternalError exception is raised

		modloaderType: Tells what the modloader is. This must be given when isModded is set to true. Otherwise an MCSCInternalError is raised.

		"""
		if os.path.isfile(str(serverjarpath) + "/server.properties") == True:
			with open(f"{serverjarpath}/server.properties","r") as propertiesfile:
				properties = {}
				for line in propertiesfile:
					if line.strip() and not line.startswith("#"):
						key,val = line.strip().split('=',1)
						properties[key] = val if val else None
				propertiesfile.close()
			for Key,Val in properties.items():
				MinecraftServerProperties[Key] = Val
			if isModded == True and modloader_version is None or modloaderType is None:
				try:
					if modloader_version is None:
						raise MCSCInternalError("Modloader Version was not given. You must provide the version.")
					else:
						if modloaderType is None:
							raise MCSCInternalError("Modloader Type was not given. You must provide the modloader type.")
				except MCSCInternalError as e:
					print(e)
					return
				finally:
					if isModded == True:
						if modloader_version is not None and modloaderType is not None:
							if create_data_ok == True and legacyBehavior == False:
								if serverjarpath == None:
									modloaderID = str(modloaderType).lower()
									with open(str(rootFilepath) + "/properties.json","r+") as jsonWriting:
										datadump = json.load(jsonWriting)
										jsonBranch = datadump["Instances"]["Modded"]
										for instance in jsonBranch:
											instance[instanceName]["minecraftVersion"] = str(minecraftVersion)
											instance[instanceName]["modloader"]["id"] = modloaderID
											instance[instanceName]["modloader"]["version"] = str(modloader_version)
											if modloaderID == "forge":
												instance[instanceName]["modloader"]["isForge"] = True
												serverjarpathForge = str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{instanceName}/libraries/net/minecraftforge/forge/{minecraftVersion}-{modloader_version}"
												instance[instanceName]["modloader"]["serverjar_filepath"] = str(serverjarpathForge)
											else:
												instance[instanceName]["modloader"]["isForge"] = False
												instance[instanceName]["modloader"]["serverjar_filepath"] = None
											instance[instanceName]["legacy-launch"]["forceToDirectory"] = False
											instance[instanceName]["legacy-launch"]["serverDirectory"] = None
											instance[instanceName]["properties"] = MinecraftServerProperties
										jsonWriting.seek(0)
										json.dump(datadump,jsonWriting,indent=4)
										jsonWriting.truncate()
										jsonWriting.close()
									print(f"[Minerva Server Crafter]: Import successful to JSON Model and created entry for {instanceName} to file.")
									ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
									return
							else:
								if create_data_ok == False and legacyBehavior == True:
									if serverjarpath is not None:
										#Skipping the file creation
										with open(str(rootFilepath) + "/properties.json","r+") as jsonWriting:
											datadump = json.load(jsonWriting)
											jsonBranch = datadump["Instances"]["Modded"]
											for instance in jsonBranch:
												instance[instanceName]["minecraftVersion"] = str(minecraftVersion)
												instance[instanceName]["modloader"]["id"] = modloaderID
												instance[instanceName]["modloader"]["version"] = str(modloader_version)
												if modloaderID == "forge":
													instance[instanceName]["modloader"]["isForge"] = True
													serverjarpathforge = str(serverjarpath) + f"/libraries/net/minecraftforge/forge/{minecraftVersion}-{modloader_version}"
													instance[instanceName]["modloader"]["serverjar_filepath"] = str(serverjarpathforge)
												else:
													instance[instanceName]["modloader"]["isForge"] = False
													instance[instanceName]["modloader"]["serverjar_filepath"] = None
												instance[instanceName]["legacy-launch"]["forceToDirectory"] = True
												instance[instanceName]["legacy-launch"]["serverDirectory"] = str(serverjarpath)
												instance[instanceName]["properties"] = MinecraftServerProperties
											jsonWriting.seek(0)
											json.dump(datadump,jsonWriting,indent=4)
											jsonWriting.truncate()
											jsonWriting.close()
										print(f"[Minerva Server Crafter]: Import successful to JSON Model and created entry for {instanceName} to file.")
										ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
										return
				
								else:
									ServerFileIO.exportPropertiestoJSON(instanceName=str(instanceName))
									ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
									return
					else:
						if create_data_ok == True and legacyBehavior == False:
							if serverjarpath == None:
								with open(str(rootFilepath) + "/properties.json","r+") as jsonWriting:
									datadump = json.load(jsonWriting)
									jsonBranch = datadump["Instances"]["Vanilla"]
									for instance in jsonBranch:
										instance[instanceName]["minecraftVersion"] = str(minecraftVersion)
										instance[instanceName]["legacy-launch"]["forceToDirectory"] = False
										instance[instanceName]["legacy-launch"]["serverDirectory"] = None
										instance[instanceName]["properties"] = MinecraftServerProperties
									jsonWriting.seek(0)
									json.dump(datadump,jsonWriting,indent=4)
									jsonWriting.truncate()
									jsonWriting.close()
								print(f"[Minerva Server Crafter]: Import successful to JSON Model and created entry for {instanceName} to file.")
								ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
								return
						else:
							if create_data_ok == False and legacyBehavior == True:
								if serverjarpath is not None:
									#Skipping the file creation
									with open(str(rootFilepath) + "/properties.json","r+") as jsonWriting:
										datadump = json.load(jsonWriting)
										jsonBranch = datadump["Instances"]["Vanilla"]
										for instance in jsonBranch:
											instance[instanceName]["minecraftVersion"] = str(minecraftVersion)
											instance[instanceName]["legacy-launch"]["forceToDirectory"] = True
											instance[instanceName]["legacy-launch"]["serverDirectory"] = str(serverjarpath)
											instance[instanceName]["properties"] = MinecraftServerProperties
										jsonWriting.seek(0)
										json.dump(datadump,jsonWriting,indent=4)
										jsonWriting.truncate()
										jsonWriting.close()
									print(f"[Minerva Server Crafter]: Import successful to JSON Model and created entry for {instanceName} to file.")
									ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
									return

							else:
								ServerFileIO.exportPropertiestoJSON(instanceName=str(instanceName))
								ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
								return

	def scanJarForServerType():
		'scanJarForServerType() -> Search Query \n \n Searches the current jar file for the type of server it is'
		global ServerJarSelection
		data_set = {}
		with zipfile.ZipFile(str(ServerJarSelection.getFilepathString()),"r") as currentWorkingJar:
			#We need to read a manifest file
			with currentWorkingJar.open("META-INF/MANIFEST.MF","r") as ManifestFile_raw:
				for line in ManifestFile_raw.readlines():
					line = line.decode("utf-8").strip()
					if line:
						try:
							key,val = line.split(":",1)
							data_set[key] = val.strip()
						except ValueError:
							pass
				ManifestFile_raw.close()
			currentWorkingJar.close()
		#Whats the main class called?
		mainClassQuery = data_set.get("Main-Class")
		while True:
			if mainClassQuery.startswith("net.minecraft"):
				serverType = "Minecraft Vanilla"
				MinecraftServerType["name"] = "Minecraft Vanilla"
				MinecraftServerType.update()
				break
			else:
				if mainClassQuery.startswith("net.fabricmc"):
					serverType = "Fabric"
					MinecraftServerType["name"] = "Fabric"
					MinecraftServerType.update()
					break
				else:
					if mainClassQuery.startswith("org.bukkit.craftbukkit"):
						serverType = "CraftBukkit"
						MinecraftServerType["name"] = "CraftBukkit"
						MinecraftServerType.update()
						break
					else:
						break
		return serverType
	
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
	
	def importWhitelistfromJSON():
		'importWhitelistfromJSON() -> JSON Query \n \n Logic for importing the whitelist.json to the whitelist_Table in the Database file'
		#We need to get the whitelist from json
		global ServerJarSelection
		global ConsoleWindow

		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		#We need the server directory in order to get the whitelist.json
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Importing whitelist JSON...")
		whitelistFileDirectory = ServerJarSelection.getcurrentpath()
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
	
	def writemcEULA(instanceName=None):
		'Generates the eula.txt file, and sets it to true'
		if instanceName is not None:
			# We need to lookup the instance to see if there is a profile made
			with open(os.path.join(rootFilepath, "properties.json"), 'r') as instanceLookup:
				jsonDump = json.load(instanceLookup)
			
			folderPath = None
			for category in ['Vanilla', 'Modded']:
				for instance in jsonDump[category]:
					if instanceName in instance:
						# Are we using legacy behavior?
						if instance[instanceName]['legacy-launch']['forceToDirectory'] == True:
							folderPath = instance[instanceName]['legacy-launch']['serverDirectory']
						else:
							# There's a profile, so it's got its folder
							if category == "Vanilla":
								folderPath = os.path.join(rootFilepath, f"base/sandbox/Instances/{instanceName}")
							elif category == "Modded":
								folderPath = os.path.join(rootFilepath, f"base/sandbox/Instances/Modpacks/{instanceName}")
						break
				if folderPath:
					break
				
			if folderPath and os.path.isdir(folderPath):
				with open(os.path.join(folderPath, "eula.txt"), "w") as eulafile:
					eulafile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Jun 12 07:54:40 EDT 2024\neula=true")
				return 200
			else:
				return 404
		else:
			raise ValueError("Instance name must be provided")
	
	def exportWhitelistfromDatabase():
		'exportWhitelistfromDatabase() -> Database Query \n \n Logic for exporting the whitelist_Table in the Database file to whitelist.json'
		global ConsoleWindow

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
		serverdirectory = ServerJarSelection.getcurrentpath()
		with open(str(serverdirectory) + "/whitelist.json","w") as whitelistWrite:
			json.dump(formattedwhitelist,whitelistWrite,ensure_ascii=False,indent=4)
			whitelistWrite.close()
		MCSC_Cursor.close()
		MCSCDatabase.close()
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Whitelist Table has been successfully saved to JSON")
		return
	
	def populateWhitelist_Listbox():
		'populateWhitelist_Listbox() -> Database Query \n \n Logic for displaying the whitelisted players thats in the whitelist_Table in the Listbox widget'
		global WhitelistListbox

		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		#Is the listbox already populated?
		challengeWhitelistInt = WhitelistListbox.size()
		if challengeWhitelistInt < 0:
			for i in enumerate(challengeWhitelistInt):
				WhitelistListbox.delete(i)
		#Get all of the player names in the whitelist table
		MCSC_Cursor.execute("SELECT name FROM whitelist_Table")
		WhitelistedPlayers = MCSC_Cursor.fetchall()
		WhitelistedPlayers = [name[0] for name in WhitelistedPlayers]
		for item in WhitelistedPlayers:
			WhitelistListbox.insert(END,str(item))
		MCSC_Cursor.close()
		MCSCDatabase.close()
		return
	
	def removeFromWhitelist():
		'removeFromWhitelist() -> Listbox Elements \n \n Updates the listbox elements. This function removes players from both the whitelist_Table in the database file and the Listbox'
		#Remove player from whitelist listbox
		global WhitelistListbox
		global ConsoleWindow
		whitelistChoice = WhitelistListbox.get()
		ServerFileIO.removePlayerfromWhitelist(str(whitelistChoice))
		WhitelistListbox.delete(WhitelistListbox.curselection())
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Whitelist updated.")
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
		
	def importplayerBansFromJSON():
		'importplayerBansFromJSON() -> JSON Query \n \n Logic for importing banned-players json file to bannedPlayers_Table in the database file.'
		global ServerJarSelection
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		#We need the server directory
		serverDir = ServerJarSelection.getcurrentpath()
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
	
	def exportplayerBansToJSON():
		'exportplayerBansToJSON() -> Database Query \n \nLogic for exporting the bannedPlayers_Table to banned-players JSON file'
		#Get the player bans table from database
		global ServerJarSelection
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		serverDir = ServerJarSelection.getcurrentpath()
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
	
	def importIPBansFromJSON():
		'importIPBansFromJSON() -> JSON Query \n \n Logic for importing banned-ips JSON file to bannedIPs_Table in the database file'
		global ServerJarSelection
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Importting IP bans from JSON...")
		serverDirectory = ServerJarSelection.getcurrentpath()
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
	
	def exportIPBansToJSON():
		'exportIPBansToJSON() -> Database Query \n \n Logic for exporting bannedIPs_Table in the database file to banned-ips JSON file.'
		global ServerJarSelection
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Exportting IP Bans Table...")
		serverdirectory = ServerJarSelection.getcurrentpath()
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
		
	def populateBannedPlayers_Listbox():
		'populateBannedPlayers_Listbox -> Database Query \n \n Logic for displaying the Banned Players in the Listbox.'
		global BannedPlayerNamesListbox
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		#Is the player bans populated already?
		challengePlayerbansInt = BannedPlayerNamesListbox.size()
		if challengePlayerbansInt < 0:
			for i in enumerate(challengePlayerbansInt):
				BannedPlayerNamesListbox.delete(i)
		#Get all of the player names in the banned Players table
		MCSC_Cursor.execute("SELECT name FROM bannedPlayers_Table")
		bannedPlayersNames = MCSC_Cursor.fetchall()
		bannedPlayersNames = [name[0] for name in bannedPlayersNames]
		for item in bannedPlayersNames:
			BannedPlayerNamesListbox.insert(END,str(item))
		MCSC_Cursor.close()
		MCSCDatabase.close()
		return
	
	def populateBannedIPs_Listbox():
		'populateBannedIPs_Listbox() -> Database Query \n \n Logic for displaying the Banned IPs in the Listbox.'
		global BannedIPsListbox
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()

		#Is the IP Bans already populated?
		challengeIPBansInt = BannedIPsListbox.size()
		if challengeIPBansInt < 0:
			for i in enumerate(challengeIPBansInt):
				BannedIPsListbox.delete(i)
		#Get all of the ips in the banned ips table
		MCSC_Cursor.execute("SELECT ip FROM bannedIPs_Table")
		bannedIPs = MCSC_Cursor.fetchall()
		bannedIPs = [name[0] for name in bannedIPs]
		for item in bannedIPs:
			BannedIPsListbox.insert(END,str(item))
		MCSC_Cursor.close()
		MCSCDatabase.close()
		return
	
	def newServerInstance(name,version:str=minecraftVersions[0], servertype:str=ServerType[0],serverDirectory:str=None):
		'Creates an Server instance in Minerva Server Crafter. You must provide a name of the instance, minecraft version, a server type, and a server directory. When any of the given values can\'t find them in their respective list, a ValueError Exception is raised. When all of the values are in the lists, it adds the values to the database table.'
		global ConsoleWindow
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
	
	def addInstancetoJSON(name=None, serverType=None, isModded=False, modlist=[], modloaderversion=None, enforcelegacy=False, serverpath_legacy=None, minecraftversion=None):
		'Adds instance to properties.json'
		if name is not None and minecraftversion is not None and serverType is not None:
			instance_name = str(name)
			mcversion = str(minecraftversion)
			if isModded == False:
				# It's a vanilla server
				category = "Vanilla"
				if serverType in ["spigot", "craftbukkit", "purpur"]:
					servertype = str(serverType)
				if enforcelegacy == False:
					# We don't need to fill out the server directory
					legacyBool = False
					serverpath = None
				else:
					if enforcelegacy == True:
						legacyBool = True
						serverpath = str(serverpath_legacy)
			else:
				if isModded == True:
					if serverType == "vanilla":
						raise ValueError("Parameter Conflict. Must set isModded to False")
					else:
						category = "Modded"
						if serverType in ["fabric", "forge"]:
							servertype = str(serverType)
							if serverType == "forge":
								forgeBool = True
								modloader_version = str(modloaderversion)
								serverjarpathing = f"base/sandbox/Instances/Modpacks/{instance_name}/libraries/net/minecraftforge/forge/{mcversion}-{modloader_version}"
							else:
								forgeBool = False
								modloader_version = str(modloaderversion)
								serverjarpathing = None
							# Remove extensions from modlist
							modlisting = [mod[0] for mod in modlist]
							if enforcelegacy == False:
							    # We don't need to fill out the server directory
								legacyBool = False
								serverpath = None
							else:
								if enforcelegacy == True:
									legacyBool = True
									serverpath = str(serverpath_legacy)
		# Now we can hand the data off to the properties.json
		file_path = os.path.join(str(rootFilepath), "properties.json")
		if os.path.exists(file_path):
			with open(file_path, "r") as newEntry:
				try:
					jsondump = json.load(newEntry)
				except json.JSONDecodeError:
					jsondump = {"Instances": {"Vanilla": [], "Modded": []}}
		else:
			jsondump = {"Instances": {"Vanilla": [], "Modded": []}}

		if isModded == False:
			# Insert new data
			legacyData = {'forceToDirectory': legacyBool, 'serverDirectory': str(serverpath)}
			propertiesData = {}
			entryData_raw = {'minecraftVersion': str(mcversion), 'legacy-launch': legacyData, 'properties': propertiesData}
			# Attach the name to this entry data
			jsondump['Instances'][category].append({str(instance_name): entryData_raw})
		else:
			if isModded == True:
				modloaderData = {'id': servertype, 'version': modloader_version, 'serverjar_filepath': serverjarpathing, 'isForge': forgeBool, 'modlisting': modlisting}
				legacyData = {'forceToDirectory': legacyBool, 'serverDirectory': serverpath}
				propertiesData = {}
				entryData_raw = {'minecraftVersion': mcversion, 'modloader': modloaderData, 'legacy-launch': legacyData, 'properties': propertiesData}
				jsondump['Instances'][category].append({str(instance_name): entryData_raw})
		
		print(jsondump)

		with open(file_path, "w") as newEntry:
			json.dump(jsondump, newEntry, indent=4)
		return

	
	def removeInstance(name):
		global ConsoleWindow
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
		with open(str(rootFilepath) + "/properties.json","r") as jsonFile:
			datadump = json.load(jsonFile)
			instances = datadump["Instances"]
			ModdedInstances = instances["Modded"]
			VanillaInstances = instances["Vanilla"]
			if instanceName in VanillaInstances:
				return False
			elif instanceName in ModdedInstances:
				return True

	def importPropertiesfromFile(instanceName=None):
		'importPropertiesfromFile() -> File Operation \n \n Prompts the User to select the server directory for importing a server.properties file to JSON Model'
		global ConsoleWindow
		global root_tabs
		root_tabs.set("Console Shell")
		try:
			askPropertiesFile = filedialog.askdirectory(parent=root,initialdir=str(rootFilepath),title="Select Server Directory with the server.properties File")
			if os.path.isfile(str(askPropertiesFile) + "/server.properties") == False:
				raise FileNotFoundError("[Minerva Server Crafter]: [Error-32] Server.properties does not exist. This usually means either its a new server, or user did not give the correct path")
			else:
				ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Loading server.properties to JSON Model...")
				ServerFileIO.importpropertiestojson(instanceName=str(instanceName),serverjarpath=str(askPropertiesFile),create_data_ok=False)
				ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
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
	
	def usePropertiesByMinecraftVersion(minecraftVersion=None):
		'Generates the server.properties file using a specific version of minecraft'
		def printOutput(process):
			for line in process.stdout:
				currentLine = line.decode("utf-8").strip("\n")
				print(currentLine)
				if "Done" in currentLine:
					# Kill the Server
					process.stdin.write(b'/stop\n')
					process.stdin.flush()
					continue
				else:
					continue
			returnCode = process.wait()
			print(f"Command exited with the return code of {returnCode}\n")
			return

		# We need to check if the minecraft version exists
		availableVersions = ServerVersion_Control.getVersionList()
		if minecraftVersion in availableVersions:
			dir_path = os.path.join(rootFilepath, f"base/sandbox/build/Minecraft Vanilla/{minecraftVersion}")
			properties_file = os.path.join(dir_path, "server.properties")

			if os.path.isdir(dir_path) and os.path.exists(properties_file):
				# Directory and properties file both exist
				targetedProperties = {}
				with open(properties_file, "r") as readingProperties:
					for line in readingProperties.readlines():
						if line.strip() and not line.startswith("#"):
							key, val = line.split("=")
							val = val.strip()
							if val == "":
								val = None
							targetedProperties[key] = val
				return targetedProperties
			else:
				# Directory doesn't exist or properties file is missing, create directory and generate properties file
				print(f"[Minerva Server Crafter]: Directory or properties file not found, creating...")
				os.makedirs(dir_path, exist_ok=True)
				result = ServerVersion_Control.downloadvanillaserverfile(version=str(minecraftVersion))

				with open(os.path.join(dir_path, "eula.txt"), "w") as eulafile:
					eulafile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Jun 12 07:54:40 EDT 2024\neula=true")
					eulafile.close()

				if result:
					# Run the jar
					os.chdir(dir_path)
					cmd = ['java', '-jar', 'server.jar', '--nogui']
					process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
					threadedProcess = threading.Thread(target=printOutput, args=(process,), name="Properties File Generation Thread")
					threadedProcess.start()
					threadedProcess.join()  # Wait for the thread to finish

					if os.path.exists(properties_file):
						# We have the properties file
						workspace = dir_path
						for root, dirs, files in os.walk(workspace):
							for dir in dirs:
								dirpath = os.path.join(workspace, dir)
								shutil.rmtree(dirpath)
							for file in files:
								filepath = os.path.join(workspace, file)
								if os.path.basename(filepath) == "server.properties":
									continue
								else:
									os.remove(filepath)

						targetedProperties = {}
						with open(properties_file, "r") as readingProperties:
							for line in readingProperties.readlines():
								if line.strip() and not line.startswith("#"):
									key, val = line.split("=")
									val = val.strip()
									if val == "":
										val = None
									targetedProperties[key] = val
						return targetedProperties
					else:
						print("[Minerva Server Crafter]: Properties file not created")
						raise MCSCInternalError("Failed to generate server.properties")
				else:
					print("[Minerva Server Crafter]: Failed to download server.jar")
					raise MCSCInternalError("Failed to download server.jar")

		return None


	def convertInstancePropertiestoPropertiesFile(instanceName=None,filepath=None,bypassSaveLocation=False):
		'Converts the instance properties from properties.json and writes it to server.properties. \nIf bypassSaveLocation is True, the server.properties \n file is written to filepath of the server directory without asking for an save location'
		global ConsoleWindow
		global root_tabs
		global instanceView

		ServerFileIO.exportPropertiestoJSON(instanceName=str(instanceName))
		ConsoleWindow.updateConsole(END,"[Minerva Server Crafter]: Converting JSON Model...")
		#First we get the Json file data
		with open(str(rootFilepath) + "/properties.json", "r") as jsonPayload:
			raw_data = json.load(jsonPayload)
			jsonPayload.close()
		payload_dict = {}
		payload_dict = raw_data
		del payload_dict['debug'] #Weird inclusion in the json. This inclusion is on Mojangs end. This option was added back in beta 1.9, but then was later removed from the properties file
		#We need to use the variable ServerJarSelection
		if bypassSaveLocation == False:
			askSaveLocation = filedialog.askdirectory(initialdir=filepath,parent=root,title="Select Server Directory")
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
		global WhitelistListbox
		global ConsoleWindow
		#Push a input dialog
		challengeDialog = CTkInputDialog(text="What is the player's name you want to add?",title="Minerva Server Crafter - Add Whitelist Player Challenge")
		challengeDialog_playername = challengeDialog.get_input()
		if challengeDialog_playername == None:
			return
		#Add to whitelist table
		ServerFileIO.addPlayerToWhitelist(str(challengeDialog_playername))
		#Update the listbox
		WhitelistListbox.delete(0,END)
		ServerFileIO.populateWhitelist_Listbox()
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
		ServerFileIO.populateBannedIPs_Listbox()
		return
	
	def PardonName():
		'PardonName() -> Listbox Element \n \n Updates the listbox. When the user pardons a player, it both updates the listbox and the table in the database file'
		#We need to get the player's name from the listbox that we are pardoning
		selectedName = BannedPlayerNamesListbox.get()
		ServerFileIO.pardonbyName(str(selectedName))
		BannedPlayerNamesListbox.delete(BannedPlayerNamesListbox.curselection())
		ServerFileIO.populateBannedPlayers_Listbox()
		return
	
	def PardonIP():
		'PardonName() -> Listbox Element \n \n Updates the listbox. When the user pardons a ip address, it both updates the listbox and the table in the database file'
		selectedIP = BannedIPsListbox.get()
		ServerFileIO.pardonbyIP(str(selectedIP))
		BannedIPsListbox.delete(BannedIPsListbox.curselection())
		ServerFileIO.populateBannedIPs_Listbox()
		return
	
	def getLastConfig():
		with open(str(rootFilepath) + "/properties.json","r") as jsonRead:
			datadump = json.load(jsonRead)
			name = datadump["Instances"]["last-config"]["id"]
			jsonRead.close()
		return name



VersionRelease = str(versionType)
VersionNumber = str(version_)
releaseVersion = " - Version: " + str(VersionRelease) + "-" + str(VersionNumber)
InstalledMemory = HardwareSpec.getByteSizeInt(psutil.virtual_memory().total)
ScaledMem = InstalledMemory[0]
roundedMem = round(ScaledMem)
truncatedMem = math.trunc(roundedMem)
physicalMem = int(truncatedMem)
if InstalledMemory[1] == "MB":
	#Scale it in Megabytes
	MemoryAllocationCap = int(truncatedMem) - 5120
	#For a decent server, the minium amount of memory is 2GB(2048)
	MiniumMemory = 2048
if InstalledMemory[1] == "GB":
	#Scale it in Gigabytes
	MemoryAllocationCap = int(truncatedMem) - 5
	MiniumMemory = 2
currentMemoryMinimum = int(4)
currentMemoryMax = int(4)


class MCSC_Framework():
	def onMainWindow_openAbout():
		aboutdlg = AboutDialogWindowClass(root)
		return
	def onMainWindow_setTabState(widget,tabName,state):
		selectedWidget = widget
		selectedWidget._segmented_button._buttons_dict[str(tabName)].configure(state=str(state))
		return
	def onMainWindow_onExit():
		#We need to handle the autosaving to prevent data loss
		currentInstance = ServerFileIO.getLastConfig()
		ServerFileIO.exportPropertiestoJSON(instanceName=str(currentInstance))
		ServerFileIO.onExit_setInstancePointer(instanceName=str(currentInstance))
		root.destroy()
		sys.exit(0)
	def onMainWindow_openInstanceSelect():
		global instanceView
		instanceView = NewInstanceWindowClass(root)
		return
	def onMainWindow_openResourcePackConfig():
		resourcePackConfig = ResourcePackWindow(root)
		return
	def onMainWindow_openMOTDConfig():
		motdConfig = MOTDWindow(root)
		return
	def isAdmin():
		if operatingSystem == "Windows":
			return ctypes.windll.shell32.IsUserAnAdmin()
	def runasAdminUser():
		if operatingSystem == "Windows":
			ctypes.windll.shell32.ShellExecuteW(None,"runas",sys.executable, " ".join(sys.argv),None, 1)
			return
	def dropToNormalUser():
		script = sys.argv[0]
		parms = " ".join(sys.argv[1:])
		os.system(f"pythonw.exe {script} {parms}")
		return

class MCSCInternalError(Exception):
	def __init__(self,msg,errors=None):
		super().__init__("[Minerva Server Crafter API - Error Reporting]: " + str(msg))
		self.errors = errors
		if self.errors != None:
			raise self.errors
		else:
			return

root = CTk()
root.title("Minerva Server Crafter" + str(releaseVersion))
root.geometry("620x279")
root.protocol('WM_DELETE_WINDOW', MCSC_Framework.onMainWindow_onExit)
root.resizable(False,False)
#Check the Operating System for the main window icon
if sys.platform.startswith("win32"):
	root.iconbitmap(str(rootFilepath) + "/base/ui/minecraftservercrafter.ico")
if sys.platform.startswith("linux"):
	root.iconbitmap("@" + str(rootFilepath) + "/base/ui/minecraftservercrafter-icon.xbm")
if sys.platform.startswith("darwin"):
	#Unsure if this will work, will pay close attention to Mac Users
	root.iconbitmap(str(rootFilepath) + "/base/ui/Mac_icon-minecraftservercrafter.icns")
#We need to put in a tab view

root_tabs = CTkTabview(root,width=250)
root.rowconfigure(0,weight=1)
root.columnconfigure(2,weight=1)
root_tabs.grid(row=0,column=2,sticky="nsew")
root_tabs.add("Console Shell")
root_tabs.add("Whitelisting")
root_tabs.add("Banned Players")
root_tabs.add("Minerva Server Crafter Settings")

#Statically let the appearance mode to Dark Mode
set_appearance_mode("dark")

#CustomTkinter classes
class AboutDialogWindowClass():
	def __init__(self,parent):
		self.root = CTkToplevel(parent)
		parent.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/ui/minecraftservercrafter.ico"))
		self.root.geometry("800x630")
		self.root.title("Minerva Server Crafter" + str(releaseVersion) + " - About")
		#Create Widgets
		self.aboutFrame = CTkFrame(self.root)
		self.aboutFrame.grid(row=0,column=0,sticky=NS)
		self.aboutTreeview = ttk.Treeview(self.root)
		self.aboutTreeview.grid(row=0,column=0,sticky=NS)
		self.aboutTreeview.rowconfigure(index=0,weight=1)
		itemRoot = self.aboutTreeview.insert("",END,text="Licenses",open=True) #Parent element
		self.aboutTreeview.insert(itemRoot,END,text="Curseforge API",iid=120)
		self.aboutTreeview.insert(itemRoot,END,text="Fabric API",iid=121)
		self.aboutTreeview.insert(itemRoot,END,text="Purpur API",iid=122)
		self.aboutTreeview.insert(itemRoot,END,text="BuildTools",iid=123)
		self.aboutTreeview.insert(itemRoot,END,text="Mojang API",iid=126)
		self.aboutTreeview.insert(itemRoot,END,text="Minerva Server Crafter",open=False,iid=127)
		self.aboutTreeview.insert(127,END,text="Custom Tkinter",open=False,iid=1200)
		self.aboutTreeview.insert(127,END,text="Python",iid=1202)
		self.aboutTreeview.insert(1200,END,text="CTkToolTip",iid=2300)
		self.aboutTreeview.insert(1200,END,text="CTkListbox",iid=2301)
		self.licenseView = CTkFrame(self.root)
		self.licenseView.grid(row=0,column=1,columnspan=2,sticky=NSEW)
		self.licenseView.columnconfigure(index=1,weight=1)
		self.licenseText = CTkTextbox(self.licenseView,text_color="white",width=600,height=600)
		self.licenseText.pack(fill=BOTH,side=LEFT,expand=True)
		self.licenseText.insert(END,"Select what license you want to see from the treeview")
		self.licenseText.configure(state=DISABLED)
		self.aboutTreeview.bind("<<TreeviewSelect>>",self.viewLicense)
		self.closebtn = CTkButton(self.root,text="Close",command=self.root.destroy)
		self.closebtn.grid(row=1,column=1,sticky=E)
	def viewLicense(self,event):
		#We need to get whats selected from the treeview
		currentItem = self.aboutTreeview.focus()
		selectedItem = str(self.aboutTreeview.item(currentItem)["text"])
		if selectedItem == "Licenses":
			self.licenseText.configure(state=NORMAL)
			self.licenseText.delete(1.0,END)
			self.licenseText.insert(END,"Select what license you want to see from the treeview")
			self.licenseText.configure(state=DISABLED)
			return
		licenseDirectory = str(rootFilepath) + f"/base/licensing/{selectedItem}/"
		with open(str(licenseDirectory) + f"{selectedItem} License.txt","r") as licenseTXT:
			self.licenseText.configure(state=NORMAL)
			self.licenseText.delete(1.0,END)
			self.licenseText.insert(END,licenseTXT.read())
			self.licenseText.configure(state=DISABLED)
			licenseTXT.close()
		return

class NewInstanceWindowClass():
	def __init__(self,parent,**kwargs):
		self.parent = parent
		self.mcversions = ServerVersion_Control.getVersionList()
		self.vanillaservertypes = ["Spigot","Minecraft Vanilla","CraftBukkit","Purpur","Custom"]
		self.moddedservertypes = ["Select a modloader","Forge","Fabric","Custom"]
		self.moddedservertypesversions = []
		self.instancesFolder = str(rootFilepath) + "/base/sandbox/Instances"
		self.modpacksFolder = str(rootFilepath) + "/base/sandbox/Instances/Modpacks"

		#Create the widget
		self.root = CTkToplevel(self.parent)
		self.rootTabs = CTkTabview(self.root)
		self.rootTabs.grid(row=0,column=0,sticky="nsew")
		self.rootTabs.add("Vanilla Server Instances")
		self.rootTabs.add("Modded Server Instances")
		self.parent.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/ui/minecraftservercrafter.ico"))
		self.root.title("Minerva Server Crafter - Lite Edition - Server Instances")
		self.root.geometry("880x650")
		#Treeview of the available vanilla instances
		self.vanillatreeviewFrame = CTkFrame(self.rootTabs.tab("Vanilla Server Instances"))
		self.vanillatreeviewFrame.grid(row=0,column=1,ipadx=10,ipady=10)
		#Treeview widget
		self.vanillainstanceView = ttk.Treeview(self.vanillatreeviewFrame)
		self.vanillainstanceView.grid(row=1,column=0,ipadx=100,ipady=200)
		self.vanillainstanceSelectbtn = CTkButton(self.vanillatreeviewFrame,text="Use Selected Instance",command=lambda:self.attachInstance(widget=self.vanillainstanceView))
		self.vanillainstanceSelectbtn.grid(row=2,column=0,padx=3,pady=3)
		self.vanillainstanceView.column("#0",width=200)
		self.vanillainstanceView.heading("#0",text="Instances")
		#Details of the instance
		self.vanillainstanceDetailsFrame = CTkFrame(self.rootTabs.tab("Vanilla Server Instances"))
		self.vanillainstanceDetailsFrame.grid(row=0,column=0,ipadx=10,padx=10)
		self.vanillainstanceImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/default.png"),size=(150,150))
		self.vanillainstanceImage = CTkLabel(self.vanillainstanceDetailsFrame,text="",image=self.vanillainstanceImageData)
		self.vanillainstanceImage.grid(row=0,column=0,sticky=EW,columnspan=2,pady=10)
		self.vanillainstanceName = CTkLabel(self.vanillainstanceDetailsFrame,text="To Begin, Select or create a new instance")
		self.vanillainstanceName.grid(row=1,column=0,columnspan=2)
		self.vanillainstancetargetedDirectory = CTkLabel(self.vanillainstanceDetailsFrame,text=" ")
		self.vanillainstancetargetedDirectory.grid(row=2,column=0)
		self.vanillainstanceservertype = CTkLabel(self.vanillainstanceDetailsFrame,text=" ")
		self.vanillainstanceservertype.grid(row=3,column=0)
		self.vanillainstanceminecraftVersion = CTkLabel(self.vanillainstanceDetailsFrame,text=" ")
		self.vanillainstanceminecraftVersion.grid(row=4,column=0)
		#Vanilla Instance creation area
		self.creationTabsvanilla = CTkTabview(self.vanillainstanceDetailsFrame)
		self.creationTabsvanilla.grid(row=5,column=0,columnspan=2)
		self.creationTabsvanilla.add("Create Instance")
		self.creationTabsvanilla.add("Instance Server Properties")
		MCSC_Framework.onMainWindow_setTabState(self.creationTabsvanilla,"Instance Server Properties","disabled")
		self.create_vanillainstanceFrame = CTkFrame(self.creationTabsvanilla.tab("Create Instance"))
		self.create_vanillainstanceFrame.grid(row=5,column=0,padx=10,pady=10)
		self.create_vanillainstance_instanceNameLabel = CTkLabel(self.create_vanillainstanceFrame,text="Instance Name: ")
		self.create_vanillainstance_instanceNameLabel.grid(row=0,column=0,padx=10,pady=10)
		self.create_vanillainstance_instanceNameEntry = CTkEntry(self.create_vanillainstanceFrame,placeholder_text="HINT: This is what your calling this instance")
		self.create_vanillainstance_instanceNameEntry.grid(row=0,column=1,ipadx=100,columnspan=2)
		self.create_vanillainstance_minecraftVersionLabel = CTkLabel(self.create_vanillainstanceFrame,text="Minecraft Server Version: ")
		self.create_vanillainstance_minecraftVersionLabel.grid(row=1,column=0,padx=10,pady=10)
		self.create_vanillainstance_minecraftVersionCombo = CTkComboBox(self.create_vanillainstanceFrame,values=self.mcversions)
		self.create_vanillainstance_minecraftVersionCombo.grid(row=1,column=1,ipadx=100,columnspan=2)
		self.create_vanillainstance_serverTypeLabel = CTkLabel(self.create_vanillainstanceFrame,text="Server Type: ")
		self.create_vanillainstance_serverTypeLabel.grid(row=2,column=0,padx=10,pady=10)
		self.create_vanillainstance_serverTypeCombo = CTkComboBox(self.create_vanillainstanceFrame,values=self.vanillaservertypes)
		self.create_vanillainstance_serverTypeCombo.grid(row=2,column=1,ipadx=100,columnspan=2)
		self.create_vanillainstance_serverDirectoryLabel = CTkLabel(self.create_vanillainstanceFrame,text="Server Directory: ")
		self.create_vanillainstance_serverDirectoryLabel.grid(row=3,column=0,padx=10,pady=10)
		self.create_vanillainstance_serverDirectoryLabel_directory = CTkLabel(self.create_vanillainstanceFrame,text=" ")
		self.create_vanillainstance_serverDirectoryLabel_directory.grid(row=3,column=1)
		self.create_vanillainstance_browseForServerDirectoryBtn = CTkButton(self.create_vanillainstanceFrame,text="Browse")
		self.create_vanillainstance_browseForServerDirectoryBtn.grid(row=3,column=2,padx=1)
		self.create_vanillainstance_generateInstanceBtn = CTkButton(self.create_vanillainstanceFrame,text="Generate Instance",command=self.buttonActionVanilla_onClickSubmit)
		self.create_vanillainstance_generateInstanceBtn.grid(row=4,column=0)
		self.create_vanillainstance_enforceserverDirectory = CTkCheckBox(self.create_vanillainstanceFrame,text="Strict Server Directory",onvalue=True,offvalue=False)
		self.create_vanillainstance_enforceserverDirectory.grid(row=4,column=1)
		#Vanilla Instance Server Properties tab
		self.vanillaserverPropertiesFrame = CTkFrame(self.creationTabsvanilla.tab("Instance Server Properties"))
		self.vanillaserverPropertiesFrame.pack(fill=BOTH,expand=True,anchor=W,ipadx=100)
		self.vanillaserverPropertiesFrame_tabs = CTkTabview(self.vanillaserverPropertiesFrame)
		self.vanillaserverPropertiesFrame_tabs.pack(fill=BOTH,expand=True,side=RIGHT,)
		self.vanillaserverPropertiesFrame_tabs.add("World Settings")
		self.vanillaserverPropertiesFrame_tabs.add("Network & Security")
		#Action Panel
		self.vanillaActionPanel = CTkFrame(self.vanillaserverPropertiesFrame)
		self.vanillaActionPanel.pack(fill=Y,expand=True,side=LEFT)
		#Server Type Image
		self.vanillaServerTypeImage = CTkLabel(self.vanillaActionPanel, text="\n\n\n\nSettings Panel\n")
		self.vanillaServerTypeImage.grid(row=0,column=0,pady=10)
		self.vanillaImportPropertiesFileBtn = CTkButton(self.vanillaActionPanel,text="Import Settings from File",command=ServerFileIO.importPropertiesfromFile)
		self.vanillaImportPropertiesFileBtn.grid(row=1,column=0)
		self.vanillaImportPropertiesFile_tip = CTkToolTip(self.vanillaImportPropertiesFileBtn,"Imports server.properties Settings to JSON Model")
		self.vanillaSavetoJSONFile = CTkButton(self.vanillaActionPanel,text="Apply Settings to JSON",command=lambda: self.exportToJSONModel(instanceName=str(ServerFileIO.getLastConfig()),useVersion=str(ServerFileIO.getVersionInfoFromLastConfig())))
		self.vanillaSavetoJSONFile.grid(row=2,column=0)
		self.vanillaSavetoJSONFile_tip = CTkToolTip(self.vanillaSavetoJSONFile,"Saves the JSON Model to properties.json")
		self.vanillaConvertJSONData = CTkButton(self.vanillaActionPanel,text="Convert Settings to File",command=lambda:ServerFileIO.convertJSONPropertiestoPropertiesFile(rootFilepath))
		self.vanillaConvertJSONData.grid(row=3,column=0)
		self.vanillaConvertJSONData_tip = CTkToolTip(self.vanillaConvertJSONData,"Converts properties.json to server.properties, and saves it into the server directory")
		#World Settings Tab
		self.vanilla_WorldSettingsFrame = CTkScrollableFrame(self.vanillaserverPropertiesFrame_tabs.tab("World Settings"))
		self.vanilla_WorldSettingsFrame.pack(fill=BOTH,expand=True,anchor=W)
		self.vanilla_WorldNameLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="World Name: ")
		self.vanilla_WorldNameLabel.grid(row=0,column=0,sticky=E)
		self.vanilla_WorldNameStringVar = StringVar(value=MinecraftServerProperties.get("level-name"))
		self.vanilla_WorldNameEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_WorldNameStringVar)
		self.vanilla_WorldNameEntry.grid(row=0,column=1,sticky=W)
		self.vanilla_WorldNameEntry_tip = CTkToolTip(self.vanilla_WorldNameLabel,"server.properties setting: 'level-name'")
		self.vanilla_levelSeedLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="World Seed: ")
		self.vanilla_levelSeedLabel.grid(row=1,column=0,sticky=E)
		self.vanilla_levelSeedStringVar = StringVar(value=MinecraftServerProperties.get("level-seed"))
		self.vanilla_levelSeedEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_levelSeedStringVar)
		self.vanilla_levelSeedEntry.grid(row=1,column=1,sticky=W)
		self.vanilla_levelSeedEntry_tip = CTkToolTip(self.vanilla_levelSeedLabel,"server.properties setting: 'level-seed'")
		self.vanilla_gamemodeList = ["survival","creative","adventure","spectator"]
		self.vanilla_gamemodeStringVar = StringVar(value=MinecraftServerProperties.get("gamemode"))
		self.vanilla_gamemodeListLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Gamemode: ")
		self.vanilla_gamemodeListLabel.grid(row=2,column=0,sticky=E)
		self.vanilla_gamemodeListComboBox = CTkComboBox(self.vanilla_WorldSettingsFrame,values=self.vanilla_gamemodeList,variable=self.vanilla_gamemodeStringVar)
		self.vanilla_gamemodeListComboBox.grid(row=2,column=1,sticky=W)
		self.vanilla_gamemodeList_tip = CTkToolTip(self.vanilla_gamemodeListLabel,"server.properties setting: 'gamemode'")
		self.vanilla_spawnprotectionRadiusInt = IntVar(value=MinecraftServerProperties.get('spawn-protection'))
		self.vanilla_spawnprotectionradiusLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Spawn Protection Radius: ")
		self.vanilla_spawnprotectionradiusLabel.grid(row=3,column=0,sticky=E)
		self.vanilla_spawnprotectionradiusEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_spawnprotectionRadiusInt)
		self.vanilla_spawnprotectionradiusEntry.grid(row=3,column=1,sticky=W)
		self.vanilla_spawnprotection_tip = CTkToolTip(self.vanilla_spawnprotectionradiusLabel,"server.properties setting: 'spawn-protection'")
		self.vanilla_worldsizeInt = IntVar(value=MinecraftServerProperties.get('max-world-size'))
		self.vanilla_worldsizeLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="World Size: ")
		self.vanilla_worldsizeLabel.grid(row=4,column=0,sticky=E)
		self.vanilla_worldsizeEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_worldsizeInt)
		self.vanilla_worldsizeEntry.grid(row=4,column=1,sticky=W)
		self.vanilla_worldsize_tip = CTkToolTip(self.vanilla_worldsizeLabel,"server.properties settings: 'max-world-size'")
		self.vanilla_worldtypeLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="World Type: ")
		self.vanilla_worldtypeLabel.grid(row=5,column=0,sticky=E)
		self.vanilla_worldtypeOptions = ["default","minecraft:normal","minecraft:flat","minecraft:large_biomes","minecraft:amplified","minecraft:single_biome_surface"]
		self.vanilla_worldtypeStringVar = StringVar(value=MinecraftServerProperties.get("level-type"))
		self.vanilla_worldtypeComboBox = CTkComboBox(self.vanilla_WorldSettingsFrame,values=self.vanilla_worldtypeOptions,variable=self.vanilla_worldtypeStringVar)
		self.vanilla_worldtypeComboBox.grid(row=5,column=1,sticky=W)
		self.vanilla_worldtype_tip = CTkToolTip(self.vanilla_worldtypeLabel,"server.properties setting: 'level-type'")
		self.vanilla_worldDifficultyVar = StringVar(value=MinecraftServerProperties.get('difficulty'))
		self.vanilla_worldDifficultyList = ['peaceful','easy','normal','hard']
		self.vanilla_worldDifficultyComboBox = CTkComboBox(self.vanilla_WorldSettingsFrame,values=self.vanilla_worldDifficultyList,variable=self.vanilla_worldDifficultyVar)
		self.vanilla_worldDifficultyComboBox.grid(row=6,column=1,sticky=W)
		self.vanilla_worldDifficultyLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Server Difficulty: ")
		self.vanilla_worldDifficultyLabel.grid(row=6,column=0,sticky=E)
		self.vanilla_worldDifficulty_tip = CTkToolTip(self.vanilla_worldDifficultyLabel,"server.properties setting: 'difficulty'")
		self.vanilla_playercountIntVar = IntVar(value=MinecraftServerProperties.get('max-players'))
		self.vanilla_playercountLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Player Count: ")
		self.vanilla_playercountLabel.grid(row=7,column=0,sticky=E)
		self.vanilla_playercountEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_playercountIntVar)
		self.vanilla_playercountEntry.grid(row=7,column=1,sticky=W)
		self.vanilla_playercount_tip = CTkToolTip(self.vanilla_playercountLabel,"server.properties setting: 'max-players'")
		self.vanilla_resourcePackPromptLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Resource Pack Prompt: ")
		self.vanilla_resourcePackPromptLabel.grid(row=8,column=0,sticky=E)
		self.vanilla_resourcePackPromptStringVar = StringVar(value=MinecraftServerProperties.get('resource-pack-prompt'))
		self.vanilla_resourcePackPromptEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_resourcePackPromptStringVar)
		self.vanilla_resourcePackPromptEntry.grid(row=8,column=1,sticky=W)
		self.vanilla_resourcePackPromptLabel_tip = CTkToolTip(self.vanilla_resourcePackPromptLabel,"server.properties setting: 'resource-pack-prompt'")
		self.vanilla_generatorsettingsvar = StringVar(value=MinecraftServerProperties.get('generator-settings'))
		self.vanilla_generatorSettingsLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Generator Settings: ")
		self.vanilla_generatorSettingsLabel.grid(row=9,column=0,sticky=E)
		self.vanilla_generatorSettingsEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_generatorsettingsvar)
		self.vanilla_generatorSettingsEntry.grid(row=9,column=1,sticky=W)
		self.vanilla_generatorsettings_tip = CTkToolTip(self.vanilla_generatorSettingsLabel,"server.properties setting: 'generator-settings'")
		self.vanilla_viewDistanceIntVar = IntVar(value=MinecraftServerProperties.get('view-distance'))
		self.vanilla_viewDistanceLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="View Distance: ")
		self.vanilla_viewDistanceLabel.grid(row=10,column=0,sticky=E)
		self.vanilla_viewDistanceEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_viewDistanceIntVar)
		self.vanilla_viewDistanceEntry.grid(row=10,column=1,sticky=W)
		self.vanilla_viewDistance_tip = CTkToolTip(self.vanilla_viewDistanceLabel,"server.properties settings: 'view-distance'")
		self.vanilla_simulationDistanceIntVar = IntVar(value=MinecraftServerProperties.get('simulation-distance'))
		self.vanilla_simulationDistanceLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Simulation Distance: ")
		self.vanilla_simulationDistanceLabel.grid(row=11,column=0,sticky=E)
		self.vanilla_simulationDistanceEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_simulationDistanceIntVar)
		self.vanilla_simulationDistanceEntry.grid(row=11,column=1,sticky=W)
		self.vanilla_simulationDistance_tip = CTkToolTip(self.vanilla_simulationDistanceLabel,"server.properties setting: 'simulation-distance'")
		self.vanilla_neighborupdatesIntVar = IntVar(value=MinecraftServerProperties.get('max-chained-neighbor-updates'))
		self.vanilla_neighborupdatesLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Max Chained Updates: ")
		self.vanilla_neighborupdatesLabel.grid(row=12,column=0,sticky=E)
		self.vanilla_neighborupdatesEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_neighborupdatesIntVar)
		self.vanilla_neighborupdatesEntry.grid(row=12,column=1,sticky=W)
		self.vanilla_neighborupdates_tip = CTkToolTip(self.vanilla_neighborupdatesLabel,"server.properties setting: 'max-chained-neighbor-updates'")
		self.vanilla_disableddataPackStringVar = StringVar(value=MinecraftServerProperties.get('initial-disabled-packs'))
		self.vanilla_disableddataPackLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Disabled Datapacks: ")
		self.vanilla_disableddataPackLabel.grid(row=13,column=0,sticky=E)
		self.vanilla_disableddataPackEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_disableddataPackStringVar)
		self.vanilla_disableddataPackEntry.grid(row=13,column=1,sticky=W)
		self.vanilla_enableddatapacksStringVar = StringVar(value=MinecraftServerProperties.get('initial-enabled-packs'))
		self.vanilla_enableddatapacksLabel = CTkLabel(self.vanilla_WorldSettingsFrame,text="Enabled Datapacks: ")
		self.vanilla_enableddatapacksLabel.grid(row=14,column=0,sticky=E)
		self.vanilla_enableddatapacksEntry = CTkEntry(self.vanilla_WorldSettingsFrame,textvariable=self.vanilla_enableddatapacksStringVar)
		self.vanilla_enableddatapacksEntry.grid(row=14,column=1,sticky=W)
		self.vanilla_resourcePackConfigurationBtn = CTkButton(self.vanilla_WorldSettingsFrame,text="Configure Resource Pack",command=MCSC_Framework.onMainWindow_openResourcePackConfig)
		self.vanilla_resourcePackConfigurationBtn.grid(row=15,column=0,sticky=W,pady=3)
		self.vanilla_MOTDConfigBtn = CTkButton(self.vanilla_WorldSettingsFrame,text="Configure MOTD",command=MCSC_Framework.onMainWindow_openMOTDConfig)
		self.vanilla_MOTDConfigBtn.grid(row=15,column=1,sticky=W,pady=3)
		#World Settings booleans
		self.vanilla_WorldSettingsBools = CTkFrame(self.vanilla_WorldSettingsFrame)
		self.vanilla_WorldSettingsBools.grid(row=16,column=0,columnspan=2)
		self.vanilla_usecmdBlocksBoolVar = BooleanVar(value=MinecraftServerProperties.get("enable-command-block"))
		self.vanilla_commandBlockUsage = CTkCheckBox(self.vanilla_WorldSettingsBools,onvalue=True,offvalue=False,text="Allow Command Blocks",variable=self.vanilla_usecmdBlocksBoolVar)
		self.vanilla_commandBlockUsage.grid(row=0,column=0,sticky=W,padx=3)
		self.vanilla_cmdBlock_tip = CTkToolTip(self.vanilla_commandBlockUsage,"server.properties setting: 'enable-command-block'")
		self.vanilla_isPVPBool = BooleanVar(value=MinecraftServerProperties.get('pvp'))
		self.vanilla_isPVP = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Allow PVP",variable=self.vanilla_isPVPBool,onvalue=True,offvalue=False)
		self.vanilla_isPVP.grid(row=0,column=1,padx=3)
		self.vanilla_pvp_tip = CTkToolTip(self.vanilla_isPVP,"server.properties setting: 'pvp'")
		self.vanilla_strictGamemodeBool = BooleanVar(value=MinecraftServerProperties.get('force-gamemode'))
		self.vanilla_strictGamemode = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Enforce Gamemode",variable=self.vanilla_strictGamemodeBool,onvalue=True,offvalue=False)
		self.vanilla_strictGamemode.grid(row=1,column=0,padx=3,pady=3,sticky=W)
		self.vanilla_strictGamemode_tip = CTkToolTip(self.vanilla_strictGamemode,"server.properties setting: 'force-gamemode'")
		self.vanilla_resourcePackRequirementBool = BooleanVar(value=MinecraftServerProperties.get('require-resource-pack'))
		self.vanilla_resourcePackRequirement = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Requires Resource Pack",variable=self.vanilla_resourcePackRequirementBool,onvalue=True,offvalue=False)
		self.vanilla_resourcePackRequirement.grid(row=2,column=0,padx=3,sticky=NW)
		self.vanilla_resourcePackRequirement_tip = CTkToolTip(self.vanilla_resourcePackRequirement,"server.properties setting: 'require-resource-pack'")
		self.vanilla_netherDimension = BooleanVar(value=MinecraftServerProperties.get('allow-nether'))
		self.vanilla_netherTravel = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Allow Nether",variable=self.vanilla_netherDimension,onvalue=True,offvalue=False)
		self.vanilla_netherTravel.grid(row=1,column=1)
		self.vanilla_canFly = BooleanVar(value=MinecraftServerProperties.get('allow-flight'))
		self.vanilla_hasFlight = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Allow Flying",variable=self.vanilla_canFly,onvalue=True,offvalue=False)
		self.vanilla_hasFlight.grid(row=2,column=1,padx=3,pady=3)
		self.vanilla_flying_tip = CTkToolTip(self.vanilla_hasFlight, "server.properties setting: 'allow-flight'")
		self.vanilla_netherTravel_tip = CTkToolTip(self.vanilla_netherTravel,"server.properties setting:'allow-nether'")
		self.vanilla_isHardcoreWorldBool = BooleanVar(value=MinecraftServerProperties.get("hardcore"))
		self.vanilla_isHardcore = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Hardcore World",variable=self.vanilla_isHardcoreWorldBool,onvalue=True,offvalue=False)
		self.vanilla_isHardcore.grid(row=3,column=0,sticky=NW,padx=3)
		self.vanilla_hardcore_tip = CTkToolTip(self.vanilla_isHardcore,"server.properties setting:'hardcore'")
		self.vanilla_onlinePlayersHiddenBool = BooleanVar(value=MinecraftServerProperties.get('hide-online-players'))
		self.vanilla_showOnlinePlayers = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Hide Online Players",variable=self.vanilla_onlinePlayersHiddenBool,onvalue=True,offvalue=False)
		self.vanilla_showOnlinePlayers.grid(row=3,column=1,padx=3,sticky=W)
		self.vanilla_visibeOnlinePlayers = CTkToolTip(self.vanilla_showOnlinePlayers,"server.properties setting: 'hide-online-players'")
		self.vanilla_statusBool = BooleanVar(value=MinecraftServerProperties.get('enable-status'))
		self.vanilla_toggleStatus = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Toggle Status",variable=self.vanilla_statusBool,onvalue=True,offvalue=False)
		self.vanilla_toggleStatus.grid(row=4,column=0,padx=3,pady=3,sticky=W)
		self.vanilla_strictProfileBool = BooleanVar(value=MinecraftServerProperties.get('enforce-secure-profile'))
		self.vanilla_strictProfile = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Stricted Profiling",variable=self.vanilla_strictProfileBool,onvalue=True,offvalue=False)
		self.vanilla_strictProfile.grid(row=5,column=0,sticky=W,padx=3)
		self.vanilla_strictProfile_tip = CTkToolTip(self.vanilla_strictProfile,"server.properties setting: 'enforce-secure-profile'")
		self.vanilla_nativeTransport = BooleanVar(value=MinecraftServerProperties.get('use-native-transport'))
		self.vanilla_useNativeTransport = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Native Transport",variable=self.vanilla_nativeTransport,onvalue=True,offvalue=False)
		self.vanilla_useNativeTransport.grid(row=6,column=0,sticky=W,padx=3,pady=3)
		self.vanilla_nativeTransport_tip = CTkToolTip(self.vanilla_useNativeTransport,"server.properties setting: 'use-native-transport'")
		self.vanilla_structureGeneration = BooleanVar(value=MinecraftServerProperties.get('generate-structures'))
		self.vanilla_structureWillGenerate = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Structure Generation",variable=self.vanilla_structureGeneration,onvalue=True,offvalue=False)
		self.vanilla_structureWillGenerate.grid(row=4,column=1,sticky=W,padx=3)
		self.vanilla_structure_tip = CTkToolTip(self.vanilla_structureWillGenerate,"server.properties setting:'generate-structures'")
		self.vanilla_npcSpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-npcs'))
		self.vanilla_NPCspawning = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Spawn NPCs",variable=self.vanilla_npcSpawning,onvalue=True,offvalue=False)
		self.vanilla_NPCspawning.grid(row=5,column=1,sticky=W,padx=3)
		self.vanilla_npcSpawning_tip = CTkToolTip(self.vanilla_NPCspawning,"server.properties setting: 'spawn-npcs'")
		self.vanilla_animalSpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-animals'))
		self.vanilla_Animalspawning = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Spawn Animals",variable=self.vanilla_animalSpawning,onvalue=True,offvalue=False)
		self.vanilla_Animalspawning.grid(row=6,column=1,sticky=W,padx=3)
		self.vanilla_animalspawning_tip = CTkToolTip(self.vanilla_Animalspawning,"server.properties setting: 'spawn-animals'")
		self.vanilla_enemySpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-monsters'))
		self.vanilla_Enemyspawning = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Spawn Enemies",variable=self.vanilla_enemySpawning,onvalue=True,offvalue=False)
		self.vanilla_Enemyspawning.grid(row=7,column=1,sticky=W,padx=3)
		self.vanilla_enemyspawning_tip = CTkToolTip(self.vanilla_Enemyspawning,"server.properties setting: 'spawn-monsters'")
		self.vanilla_broadcastConsoleBool = BooleanVar(value=MinecraftServerProperties.get('broadcast-console-to-ops'))
		self.vanilla_broadcastConsole = CTkCheckBox(self.vanilla_WorldSettingsBools,text="Broadcast System Console",variable=self.vanilla_broadcastConsoleBool,onvalue=True,offvalue=False)
		self.vanilla_broadcastConsole.grid(row=7,column=0,sticky=W,padx=3)
		self.vanilla_broadcastconsole_tip = CTkToolTip(self.vanilla_broadcastConsole,"server.properties setting: 'broadcast-console-to-ops'")
		#Network & Security Tab
		self.vanilla_NetworkSecurityTab = CTkScrollableFrame(self.vanillaserverPropertiesFrame_tabs.tab("Network & Security"))
		self.vanilla_NetworkSecurityTab.pack(fill=BOTH,expand=True,anchor=W)
		self.vanilla_MinecraftServerIPStringVar = StringVar(value=MinecraftServerProperties.get('server-ip'))
		self.vanilla_IPAddressLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Server IP: ")
		self.vanilla_IPAddressLabel.grid(row=0,column=0,sticky=E)
		self.vanilla_IPAddressEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_MinecraftServerIPStringVar)
		self.vanilla_IPAddressEntry.grid(row=0,column=1,sticky=W)
		self.vanilla_IPAddress_tip = CTkToolTip(self.vanilla_IPAddressLabel,"server.properties setting: 'server-ip'")
		self.vanilla_NetworkCompressionIntVar = IntVar(value=MinecraftServerProperties.get('network-compression-threshold'))
		self.vanilla_networkcompressionLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Network Compression: ")
		self.vanilla_networkcompressionLabel.grid(row=1,column=0,sticky=E)
		self.vanilla_networkCompressionEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_NetworkCompressionIntVar)
		self.vanilla_networkCompressionEntry.grid(row=1,column=1,sticky=W)
		self.vanilla_networkCompression_tip = CTkToolTip(self.vanilla_networkcompressionLabel,"server.properties setting: 'network-compression-threshold'")
		self.vanilla_ticktimeIntVar = IntVar(value=MinecraftServerProperties.get('max-tick-time'))
		self.vanilla_ticktimeLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Max Tick Rate: ")
		self.vanilla_ticktimeLabel.grid(row=2,column=0,sticky=E)
		self.vanilla_ticktimeEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_ticktimeIntVar)
		self.vanilla_ticktimeEntry.grid(row=2,column=1,sticky=W)
		self.vanilla_ticktime_tip = CTkToolTip(self.vanilla_ticktimeLabel,"server.properties setting: 'max-tick-time'")
		self.vanilla_maxplayersIntVar = IntVar(value=MinecraftServerProperties.get('max-players'))
		self.vanilla_maxplayersLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Max Players: ")
		self.vanilla_maxplayersLabel.grid(row=3,column=0,sticky=E)
		self.vanilla_maxplayersEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_maxplayersIntVar)
		self.vanilla_maxplayersEntry.grid(row=3,column=1,sticky=W)
		self.vanilla_maxplayers_tip = CTkToolTip(self.vanilla_maxplayersLabel,"server.properties setting: 'max-players'")
		self.vanilla_serverportIntVar = IntVar(value=MinecraftServerProperties.get('server-port'))
		self.vanilla_serverportLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Server Port: ")
		self.vanilla_serverportLabel.grid(row=4,column=0,sticky=E)
		self.vanilla_serverportEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_serverportIntVar)
		self.vanilla_serverportEntry.grid(row=4,column=1,sticky=W)
		self.vanilla_serverport_tip = CTkToolTip(self.vanilla_serverportLabel,"server.properties setting: 'server-port'")
		self.vanilla_opPermissionlvlList = ["0","1","2","3","4"]
		self.vanilla_opPermissionlvlIntVar = IntVar(value=MinecraftServerProperties.get('op-permission-level'))
		self.vanilla_opPermissionlvlLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Op Permission Level: ")
		self.vanilla_opPermissionlvlLabel.grid(row=5,column=0,sticky=E)
		self.vanilla_opPermissionlvlComboBox = CTkComboBox(self.vanilla_NetworkSecurityTab,values=self.vanilla_opPermissionlvlList,variable=self.vanilla_opPermissionlvlIntVar)
		self.vanilla_opPermissionlvlComboBox.grid(row=5,column=1,sticky=W)
		self.vanilla_opPermissionlvl_tip = CTkToolTip(self.vanilla_opPermissionlvlLabel,"server.properties setting: 'op-permission-level'")
		self.vanilla_entitybroadcastRangeList = [str(i) for i in range(10,1000)] #Best way of generating numbers from its set range
		self.vanilla_entitybroadcastRangeIntVar = IntVar(value=MinecraftServerProperties.get('entity-broadcast-range-percentage'))
		self.vanilla_entitybroadcastRangeLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Entity Broadcasting: ")
		self.vanilla_entitybroadcastRangeLabel.grid(row=6,column=0,sticky=E)
		self.vanilla_entitybroadcastRangeCombobox = CTkComboBox(self.vanilla_NetworkSecurityTab,values=self.vanilla_entitybroadcastRangeList,variable=self.vanilla_entitybroadcastRangeIntVar)
		self.vanilla_entitybroadcastRangeCombobox.grid(row=6,column=1,sticky=W)
		self.vanilla_entitybroadcastRange_tip = CTkToolTip(self.vanilla_entitybroadcastRangeLabel,"server.properties setting: 'entity-broadcast-range-percentage")
		self.vanilla_playertimeoutIntVar = IntVar(value=MinecraftServerProperties.get('player-idle-timeout'))
		self.vanilla_playertimeoutLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Idle Player Timeout: ")
		self.vanilla_playertimeoutLabel.grid(row=7,column=0,sticky=E)
		self.vanilla_playertimeoutEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_playercountIntVar)
		self.vanilla_playertimeoutEntry.grid(row=7,column=1,sticky=W)
		self.vanilla_playertimeout_tip = CTkToolTip(self.vanilla_playertimeoutLabel,"server.properties setting: 'player-idle-timeout'")
		self.vanilla_ratelimitIntvar = IntVar(value=MinecraftServerProperties.get('rate-limit'))
		self.vanilla_ratelimitLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Rate Limit: ")
		self.vanilla_ratelimitLabel.grid(row=8,column=0,sticky=E)
		self.vanilla_ratelimitEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_ratelimitIntvar)
		self.vanilla_ratelimitEntry.grid(row=8,column=1,sticky=W)
		self.vanilla_ratelimit_tip = CTkToolTip(self.vanilla_ratelimitLabel,"server.properties setting: 'rate-limit'")
		self.vanilla_functionPermissionlvlList = [str(x) for x in range(1,4)]
		self.vanilla_functionPermissionlvlIntvar = IntVar(value=MinecraftServerProperties.get('function-permission-level'))
		self.vanilla_functionPermissionlvlLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Fuction Permission Level: ")
		self.vanilla_functionPermissionlvlLabel.grid(row=9,column=0,sticky=E)
		self.vanilla_functionPermissionlvlComboBox = CTkComboBox(self.vanilla_NetworkSecurityTab,values=self.vanilla_functionPermissionlvlList,variable=self.vanilla_functionPermissionlvlIntvar)
		self.vanilla_functionPermissionlvlComboBox.grid(row=9,column=1,sticky=W)
		self.vanilla_functionPermissionlvl_tip = CTkToolTip(self.vanilla_functionPermissionlvlLabel,"server.properties setting: 'function-permission-level'")
		self.vanilla_rconPasswordStringVar = StringVar(value=MinecraftServerProperties.get('rcon.password'))
		self.vanilla_rconPasswordLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="RCON Password: ")
		self.vanilla_rconPasswordLabel.grid(row=10,column=0,sticky=E)
		self.vanilla_rconPasswordEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_rconPasswordStringVar)
		self.vanilla_rconPasswordEntry.grid(row=10,column=1,sticky=W)
		self.vanilla_rconPassword_tip = CTkToolTip(self.vanilla_rconPasswordLabel,"server.properties setting: 'rcon.password'")
		self.vanilla_rconportIntVar = IntVar(value=MinecraftServerProperties.get('rcon.port'))
		self.vanilla_rconportLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="RCON Port: ")
		self.vanilla_rconportLabel.grid(row=11,column=0,sticky=E)
		self.vanilla_rconportEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_rconportIntVar)
		self.vanilla_rconportEntry.grid(row=11,column=1,sticky=W)
		self.vanilla_rconport_tip = CTkToolTip(self.vanilla_rconportLabel,"server.properties setting: 'rcon.port'")
		self.vanilla_queryportIntVar = IntVar(value=MinecraftServerProperties.get('query.port'))
		self.vanilla_queryportLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Query Port: ")
		self.vanilla_queryportLabel.grid(row=12,column=0,sticky=E)
		self.vanilla_queryportEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_queryportIntVar)
		self.vanilla_queryportEntry.grid(row=12,column=1,sticky=W)
		self.vanilla_queryport_tip = CTkToolTip(self.vanilla_queryportLabel,"server.properties setting: 'query.port'")
		self.vanilla_bugreportingStringVar = StringVar(value=MinecraftServerProperties.get('bug-report-link'))
		self.vanilla_bugreportingLabel = CTkLabel(self.vanilla_NetworkSecurityTab,text="Bug Report Link: ")
		self.vanilla_bugreportingLabel.grid(row=13,column=0,sticky=E)
		self.vanilla_bugreportingEntry = CTkEntry(self.vanilla_NetworkSecurityTab,textvariable=self.vanilla_bugreportingStringVar)
		self.vanilla_bugreportingEntry.grid(row=13,column=1,sticky=W)
		self.vanilla_bugreporting_tip = CTkToolTip(self.vanilla_bugreportingLabel,"server.properties setting: 'bug-report-link'")
		#Networking Tab Bools
		self.vanilla_NetworkSecurityTabBools = CTkFrame(self.vanilla_NetworkSecurityTab)
		self.vanilla_NetworkSecurityTabBools.grid(row=13,column=0,columnspan=2,sticky=E)
		self.vanilla_togglequery = BooleanVar(value=MinecraftServerProperties.get('enable-query'))
		self.vanilla_canQueryCheck = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Enable Query",variable=self.vanilla_togglequery,onvalue=True,offvalue=False)
		self.vanilla_canQueryCheck.grid(row=0,column=1,padx=3,pady=3,sticky=W)
		self.vanilla_canquery_tip = CTkToolTip(self.vanilla_canQueryCheck,"server.properties setting: 'enable-query'")
		self.vanilla_chunkwriteSyncingBool = BooleanVar(value=MinecraftServerProperties.get('sync-chunk-writes'))
		self.vanilla_chunkwriteSyncingCheck = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Synchronized Chunk Writing",variable=self.vanilla_chunkwriteSyncingBool,onvalue=True,offvalue=False)
		self.vanilla_chunkwriteSyncingCheck.grid(row=1,column=0,padx=3,pady=3,sticky=W)
		self.vanilla_chunkwriteSyncing_tip = CTkToolTip(self.vanilla_chunkwriteSyncingCheck,"server.properties setting: 'sync-chunk-writes'")
		self.vanilla_proxyBlockingBool = BooleanVar(value=MinecraftServerProperties.get('prevent-proxy-connections'))
		self.vanilla_proxyBlockingCheck = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Block Proxy Connections",variable=self.vanilla_proxyBlockingBool,onvalue=True,offvalue=False)
		self.vanilla_proxyBlockingCheck.grid(row=0,column=0,padx=3,pady=3,sticky=W)
		self.vanilla_proxyblocking_tip = CTkToolTip(self.vanilla_proxyBlockingCheck,"server.properties setting: 'prevent-proxy-connections'")
		self.vanilla_toggleOnlineMode = BooleanVar(value=MinecraftServerProperties.get('online-mode'))
		self.vanilla_isOnline = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Online Mode",variable=self.vanilla_toggleOnlineMode,onvalue=True,offvalue=False)
		self.vanilla_isOnline.grid(row=1,column=1,sticky=W,padx=3,pady=3)
		self.vanilla_isonline_tip = CTkToolTip(self.vanilla_isOnline,"server.properties setting: 'online-mode'")
		self.vanilla_jmxMonitoringBool = BooleanVar(value=MinecraftServerProperties.get('enable-jmx-monitoring'))
		self.vanilla_jmxMonitoringCheck = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Toggle JMX Monitoring",variable=self.vanilla_jmxMonitoringBool,onvalue=True,offvalue=False)
		self.vanilla_jmxMonitoringCheck.grid(row=2,column=0,sticky=W,pady=3,padx=3)
		self.vanilla_jmxMonitoring_tip = CTkToolTip(self.vanilla_jmxMonitoringCheck,"server.properties setting: 'enable-jmx-monitoring'")
		self.vanilla_isIPLogging = BooleanVar(value=MinecraftServerProperties.get('log-ips'))
		self.vanilla_IPLogBool = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Log IPs",onvalue=True,offvalue=False,variable=self.vanilla_isIPLogging)
		self.vanilla_IPLogBool.grid(row=2,column=1,padx=3,pady=3,sticky=W)
		self.vanilla_togglerconBool = BooleanVar(value=MinecraftServerProperties.get('enable-rcon'))
		self.vanilla_rconToggler = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Enable RCON",variable=self.vanilla_togglerconBool,onvalue=True,offvalue=False)
		self.vanilla_rconToggler.grid(row=3,column=1,padx=3,pady=3,sticky=W)
		self.vanilla_broadcastrconBool = BooleanVar(value=MinecraftServerProperties.get('broadcast-rcon-to-ops'))
		self.vanilla_rconBroadcast = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Broadcast RCON",variable=self.vanilla_broadcastrconBool,onvalue=True,offvalue=False)
		self.vanilla_rconBroadcast.grid(row=3,column=0,sticky=W,padx=3,pady=3)
		self.vanilla_acceptTransfersBool = BooleanVar(value=MinecraftServerProperties.get('accept-transfers'))
		self.vanilla_acceptTransfers = CTkCheckBox(self.vanilla_NetworkSecurityTabBools,text="Accept Transfers from Another Server",variable=self.vanilla_acceptTransfersBool,onvalue=True,offvalue=False)
		self.vanilla_acceptTransfers.grid(row=4,column=0,padx=3,pady=3,sticky=W)
		self.populateInstanceView(self.vanillainstanceView,"",self.instancesFolder,"Modpacks")
		self.vanillainstanceView.bind("<<TreeviewSelect>>",self.displayInstanceDetails)
		#Treeview
		self.moddedinstancesViewFrame = CTkFrame(self.rootTabs.tab("Modded Server Instances"))
		self.moddedinstancesViewFrame.grid(row=0,column=1,ipadx=10,ipady=10)
		self.moddedinstanceView = ttk.Treeview(self.moddedinstancesViewFrame)
		self.moddedinstanceView.grid(row=0,column=0,ipadx=100,ipady=200)
		self.moddedinstanceSelectbtn = CTkButton(self.moddedinstancesViewFrame,text="Use Selected Instance",command=lambda:self.attachInstance(widget=self.moddedinstanceView))
		self.moddedinstanceSelectbtn.grid(row=1,column=0,padx=3,pady=3)
		self.moddedinstanceView.column("#0",width=200)
		self.moddedinstanceView.heading("#0",text="Modded Instances")
		#Modded Instances Details
		self.moddedinstanceDetailsFrame = CTkFrame(self.rootTabs.tab("Modded Server Instances"))
		self.moddedinstanceDetailsFrame.grid(row=0,column=0,ipadx=10,padx=10)
		self.moddedinstanceImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/default.png"),size=(150,150))
		self.moddedinstanceImage = CTkLabel(self.moddedinstanceDetailsFrame,text="",image=self.moddedinstanceImageData)
		self.moddedinstanceImage.grid(row=0,column=0,sticky=EW,columnspan=2,pady=10)
		self.moddedinstanceName = CTkLabel(self.moddedinstanceDetailsFrame,text="To Begin, Select or create a new modded instance")
		self.moddedinstanceName.grid(row=1,column=0,columnspan=2)
		self.moddedinstancetargetedDirectory = CTkLabel(self.moddedinstanceDetailsFrame,text=" ")
		self.moddedinstancetargetedDirectory.grid(row=2,column=0)
		self.moddedinstanceservertype = CTkLabel(self.moddedinstanceDetailsFrame,text=" ")
		self.moddedinstanceservertype.grid(row=3,column=0)
		self.moddedinstanceminecraftVersion = CTkLabel(self.moddedinstanceDetailsFrame,text=" ")
		self.moddedinstanceminecraftVersion.grid(row=4,column=0)
		self.moddedinstancemodloaderversion = CTkLabel(self.moddedinstanceDetailsFrame,text=" ")
		self.moddedinstancemodloaderversion.grid(row=5,column=0)
		self.moddedInstance_importModpackbtn = CTkButton(self.moddedinstanceDetailsFrame,text="Import Curseforge Modpack",command=self.onModpackLoad_LoadModpack)
		self.moddedInstance_importModpackbtn.grid(row=6,column=0,pady=3,columnspan=2)
		self.moddedInstance_importModpack_tooltip = CTkToolTip(self.moddedInstance_importModpackbtn, "NOTE: Do not use Server Pack. Minerva Server Crafter automatically .")
		#Modded Instance creation area
		self.creationTabsmodded = CTkTabview(self.moddedinstanceDetailsFrame)
		self.creationTabsmodded.grid(row=7,column=0,columnspan=2)
		self.creationTabsmodded.add("Create Instance")
		self.creationTabsmodded.add("Instance Server Properties")
		MCSC_Framework.onMainWindow_setTabState(self.creationTabsmodded,"Instance Server Properties","disabled")
		self.create_moddedinstanceFrame = CTkFrame(self.creationTabsmodded.tab("Create Instance"))
		self.create_moddedinstanceFrame.grid(row=5,column=0,padx=10,pady=10)
		self.create_moddedinstance_instanceNameLabel = CTkLabel(self.create_moddedinstanceFrame,text="Instance Name: ")
		self.create_moddedinstance_instanceNameLabel.grid(row=0,column=0,padx=10,pady=10)
		self.create_moddedinstance_instanceNameEntry = CTkEntry(self.create_moddedinstanceFrame,placeholder_text="HINT: This is what your calling this instance")
		self.create_moddedinstance_instanceNameEntry.grid(row=0,column=1,ipadx=100,columnspan=2)
		self.create_moddedinstance_serverTypeLabel = CTkLabel(self.create_moddedinstanceFrame,text="Server Type: ")
		self.create_moddedinstance_serverTypeLabel.grid(row=1,column=0,padx=10,pady=10)
		self.create_moddedinstance_serverTypeCombo = CTkComboBox(self.create_moddedinstanceFrame,values=self.moddedservertypes,command=self.setMCVersions)
		self.create_moddedinstance_serverTypeCombo.grid(row=1,column=1,ipadx=100,columnspan=2)
		self.create_moddedinstance_minecraftVersionLabel = CTkLabel(self.create_moddedinstanceFrame,text="Minecraft Server Version: ")
		self.create_moddedinstance_minecraftVersionLabel.grid(row=2,column=0,padx=10,pady=10)
		self.create_moddedinstance_minecraftVersionStringVar = StringVar()
		self.create_moddedinstance_minecraftVersionCombo = CTkComboBox(self.create_moddedinstanceFrame,values=[],variable=self.create_moddedinstance_minecraftVersionStringVar,command=self.setServerTypeVersions)
		self.create_moddedinstance_minecraftVersionCombo.grid(row=2,column=1,ipadx=100,columnspan=2)
		self.create_moddedinstance_serverTypeVersionLabel = CTkLabel(self.create_moddedinstanceFrame,text="Server Type Version: ")
		self.create_moddedinstance_serverTypeVersionLabel.grid(row=3,column=0,padx=10,pady=10)
		self.create_moddedinstance_serverTypeVersionStringVar = StringVar()
		self.create_moddedinstance_serverTypeVersionCombo = CTkComboBox(self.create_moddedinstanceFrame,values=[],variable=self.create_moddedinstance_serverTypeVersionStringVar)
		self.create_moddedinstance_serverTypeVersionCombo.grid(row=3,column=1,columnspan=2,ipadx=100)
		self.create_moddedinstance_serverDirectoryLabel = CTkLabel(self.create_moddedinstanceFrame,text="Server Directory: ")
		self.create_moddedinstance_serverDirectoryLabel.grid(row=4,column=0,padx=10,pady=10)
		self.create_moddedinstance_serverDirectoryLabel_directory = CTkLabel(self.create_moddedinstanceFrame,text=" ")
		self.create_moddedinstance_serverDirectoryLabel_directory.grid(row=4,column=1)
		self.create_moddedinstance_browseForServerDirectoryBtn = CTkButton(self.create_moddedinstanceFrame,text="Browse")
		self.create_moddedinstance_browseForServerDirectoryBtn.grid(row=4,column=2,padx=1)
		self.create_moddedinstance_generateInstanceBtn = CTkButton(self.create_moddedinstanceFrame,text="Generate Instance",command=self.buttonActionModded_onClickSubmit)
		self.create_moddedinstance_generateInstanceBtn.grid(row=5,column=0)
		self.create_moddedinstance_enforceserverDirectory = CTkCheckBox(self.create_moddedinstanceFrame,text="Strict Server Directory",onvalue=True,offvalue=False)
		self.create_moddedinstance_enforceserverDirectory.grid(row=5,column=1)
		#Modded Instance Server Properties tab
		self.moddedserverPropertiesFrame = CTkFrame(self.creationTabsmodded.tab("Instance Server Properties"))
		self.moddedserverPropertiesFrame.pack(fill=BOTH,expand=True,anchor=W,ipadx=100)
		self.moddedserverPropertiesFrame_tabs = CTkTabview(self.moddedserverPropertiesFrame)
		self.moddedserverPropertiesFrame_tabs.pack(fill=BOTH,expand=True,side=RIGHT,)
		self.moddedserverPropertiesFrame_tabs.add("World Settings")
		self.moddedserverPropertiesFrame_tabs.add("Network & Security")
		#Action Panel
		self.moddedActionPanel = CTkFrame(self.moddedserverPropertiesFrame)
		self.moddedActionPanel.pack(fill=Y,expand=True,side=LEFT)
		#Server Type Image
		self.moddedServerTypeImage = CTkLabel(self.moddedActionPanel, text="\n\n\n\nSettings Panel\n")
		self.moddedServerTypeImage.grid(row=0,column=0,pady=10)
		self.moddedImportPropertiesFileBtn = CTkButton(self.moddedActionPanel,text="Import Settings from File",command=ServerFileIO.importPropertiesfromFile)
		self.moddedImportPropertiesFileBtn.grid(row=1,column=0)
		self.moddedImportPropertiesFile_tip = CTkToolTip(self.moddedImportPropertiesFileBtn,"Imports server.properties Settings to JSON Model")
		self.moddedSavetoJSONFile = CTkButton(self.moddedActionPanel,text="Apply Settings to JSON",command=lambda: self.exportToJSONModel(instanceName=str(ServerFileIO.getLastConfig()),useVersion=str(ServerFileIO.getVersionInfoFromLastConfig())))
		self.moddedSavetoJSONFile.grid(row=2,column=0)
		self.moddedSavetoJSONFile_tip = CTkToolTip(self.moddedSavetoJSONFile,"Saves the JSON Model to properties.json")
		self.moddedConvertJSONData = CTkButton(self.moddedActionPanel,text="Convert Settings to File",command=lambda:ServerFileIO.convertJSONPropertiestoPropertiesFile(rootFilepath))
		self.moddedConvertJSONData.grid(row=3,column=0)
		self.moddedConvertJSONData_tip = CTkToolTip(self.moddedConvertJSONData,"Converts properties.json to server.properties, and saves it into the server directory")
		#World Settings Tab
		self.modded_WorldSettingsFrame = CTkScrollableFrame(self.moddedserverPropertiesFrame_tabs.tab("World Settings"))
		self.modded_WorldSettingsFrame.pack(fill=BOTH,expand=True,anchor=W)
		self.modded_WorldNameLabel = CTkLabel(self.modded_WorldSettingsFrame,text="World Name: ")
		self.modded_WorldNameLabel.grid(row=0,column=0,sticky=E)
		self.modded_WorldNameStringVar = StringVar(value=MinecraftServerProperties.get("level-name"))
		self.modded_WorldNameEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_WorldNameStringVar)
		self.modded_WorldNameEntry.grid(row=0,column=1,sticky=W)
		self.modded_WorldNameEntry_tip = CTkToolTip(self.modded_WorldNameLabel,"server.properties setting: 'level-name'")
		self.modded_levelSeedLabel = CTkLabel(self.modded_WorldSettingsFrame,text="World Seed: ")
		self.modded_levelSeedLabel.grid(row=1,column=0,sticky=E)
		self.modded_levelSeedStringVar = StringVar(value=MinecraftServerProperties.get("level-seed"))
		self.modded_levelSeedEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_levelSeedStringVar)
		self.modded_levelSeedEntry.grid(row=1,column=1,sticky=W)
		self.modded_levelSeedEntry_tip = CTkToolTip(self.modded_levelSeedLabel,"server.properties setting: 'level-seed'")
		self.modded_gamemodeList = ["survival","creative","adventure","spectator"]
		self.modded_gamemodeStringVar = StringVar(value=MinecraftServerProperties.get("gamemode"))
		self.modded_gamemodeListLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Gamemode: ")
		self.modded_gamemodeListLabel.grid(row=2,column=0,sticky=E)
		self.modded_gamemodeListComboBox = CTkComboBox(self.modded_WorldSettingsFrame,values=self.modded_gamemodeList,variable=self.modded_gamemodeStringVar)
		self.modded_gamemodeListComboBox.grid(row=2,column=1,sticky=W)
		self.modded_gamemodeList_tip = CTkToolTip(self.modded_gamemodeListLabel,"server.properties setting: 'gamemode'")
		self.modded_spawnprotectionRadiusInt = IntVar(value=MinecraftServerProperties.get('spawn-protection'))
		self.modded_spawnprotectionradiusLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Spawn Protection Radius: ")
		self.modded_spawnprotectionradiusLabel.grid(row=3,column=0,sticky=E)
		self.modded_spawnprotectionradiusEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_spawnprotectionRadiusInt)
		self.modded_spawnprotectionradiusEntry.grid(row=3,column=1,sticky=W)
		self.modded_spawnprotection_tip = CTkToolTip(self.modded_spawnprotectionradiusLabel,"server.properties setting: 'spawn-protection'")
		self.modded_worldsizeInt = IntVar(value=MinecraftServerProperties.get('max-world-size'))
		self.modded_worldsizeLabel = CTkLabel(self.modded_WorldSettingsFrame,text="World Size: ")
		self.modded_worldsizeLabel.grid(row=4,column=0,sticky=E)
		self.modded_worldsizeEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_worldsizeInt)
		self.modded_worldsizeEntry.grid(row=4,column=1,sticky=W)
		self.modded_worldsize_tip = CTkToolTip(self.modded_worldsizeLabel,"server.properties settings: 'max-world-size'")
		self.modded_worldtypeLabel = CTkLabel(self.modded_WorldSettingsFrame,text="World Type: ")
		self.modded_worldtypeLabel.grid(row=5,column=0,sticky=E)
		self.modded_worldtypeOptions = ["default","minecraft:normal","minecraft:flat","minecraft:large_biomes","minecraft:amplified","minecraft:single_biome_surface"]
		self.modded_worldtypeStringVar = StringVar(value=MinecraftServerProperties.get("level-type"))
		self.modded_worldtypeComboBox = CTkComboBox(self.modded_WorldSettingsFrame,values=self.modded_worldtypeOptions,variable=self.modded_worldtypeStringVar)
		self.modded_worldtypeComboBox.grid(row=5,column=1,sticky=W)
		self.modded_worldtype_tip = CTkToolTip(self.modded_worldtypeLabel,"server.properties setting: 'level-type'")
		self.modded_worldDifficultyVar = StringVar(value=MinecraftServerProperties.get('difficulty'))
		self.modded_worldDifficultyList = ['peaceful','easy','normal','hard']
		self.modded_worldDifficultyComboBox = CTkComboBox(self.modded_WorldSettingsFrame,values=self.modded_worldDifficultyList,variable=self.modded_worldDifficultyVar)
		self.modded_worldDifficultyComboBox.grid(row=6,column=1,sticky=W)
		self.modded_worldDifficultyLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Server Difficulty: ")
		self.modded_worldDifficultyLabel.grid(row=6,column=0,sticky=E)
		self.modded_worldDifficulty_tip = CTkToolTip(self.modded_worldDifficultyLabel,"server.properties setting: 'difficulty'")
		self.modded_playercountIntVar = IntVar(value=MinecraftServerProperties.get('max-players'))
		self.modded_playercountLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Player Count: ")
		self.modded_playercountLabel.grid(row=7,column=0,sticky=E)
		self.modded_playercountEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_playercountIntVar)
		self.modded_playercountEntry.grid(row=7,column=1,sticky=W)
		self.modded_playercount_tip = CTkToolTip(self.modded_playercountLabel,"server.properties setting: 'max-players'")
		self.modded_resourcePackPromptLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Resource Pack Prompt: ")
		self.modded_resourcePackPromptLabel.grid(row=8,column=0,sticky=E)
		self.modded_resourcePackPromptStringVar = StringVar(value=MinecraftServerProperties.get('resource-pack-prompt'))
		self.modded_resourcePackPromptEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_resourcePackPromptStringVar)
		self.modded_resourcePackPromptEntry.grid(row=8,column=1,sticky=W)
		self.modded_resourcePackPromptLabel_tip = CTkToolTip(self.modded_resourcePackPromptLabel,"server.properties setting: 'resource-pack-prompt'")
		self.modded_generatorsettingsvar = StringVar(value=MinecraftServerProperties.get('generator-settings'))
		self.modded_generatorSettingsLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Generator Settings: ")
		self.modded_generatorSettingsLabel.grid(row=9,column=0,sticky=E)
		self.modded_generatorSettingsEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_generatorsettingsvar)
		self.modded_generatorSettingsEntry.grid(row=9,column=1,sticky=W)
		self.modded_generatorsettings_tip = CTkToolTip(self.modded_generatorSettingsLabel,"server.properties setting: 'generator-settings'")
		self.modded_viewDistanceIntVar = IntVar(value=MinecraftServerProperties.get('view-distance'))
		self.modded_viewDistanceLabel = CTkLabel(self.modded_WorldSettingsFrame,text="View Distance: ")
		self.modded_viewDistanceLabel.grid(row=10,column=0,sticky=E)
		self.modded_viewDistanceEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_viewDistanceIntVar)
		self.modded_viewDistanceEntry.grid(row=10,column=1,sticky=W)
		self.modded_viewDistance_tip = CTkToolTip(self.modded_viewDistanceLabel,"server.properties settings: 'view-distance'")
		self.modded_simulationDistanceIntVar = IntVar(value=MinecraftServerProperties.get('simulation-distance'))
		self.modded_simulationDistanceLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Simulation Distance: ")
		self.modded_simulationDistanceLabel.grid(row=11,column=0,sticky=E)
		self.modded_simulationDistanceEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_simulationDistanceIntVar)
		self.modded_simulationDistanceEntry.grid(row=11,column=1,sticky=W)
		self.modded_simulationDistance_tip = CTkToolTip(self.modded_simulationDistanceLabel,"server.properties setting: 'simulation-distance'")
		self.modded_neighborupdatesIntVar = IntVar(value=MinecraftServerProperties.get('max-chained-neighbor-updates'))
		self.modded_neighborupdatesLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Max Chained Updates: ")
		self.modded_neighborupdatesLabel.grid(row=12,column=0,sticky=E)
		self.modded_neighborupdatesEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_neighborupdatesIntVar)
		self.modded_neighborupdatesEntry.grid(row=12,column=1,sticky=W)
		self.modded_neighborupdates_tip = CTkToolTip(self.modded_neighborupdatesLabel,"server.properties setting: 'max-chained-neighbor-updates'")
		self.modded_disableddataPackStringVar = StringVar(value=MinecraftServerProperties.get('initial-disabled-packs'))
		self.modded_disableddataPackLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Disabled Datapacks: ")
		self.modded_disableddataPackLabel.grid(row=13,column=0,sticky=E)
		self.modded_disableddataPackEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_disableddataPackStringVar)
		self.modded_disableddataPackEntry.grid(row=13,column=1,sticky=W)
		self.modded_enableddatapacksStringVar = StringVar(value=MinecraftServerProperties.get('initial-enabled-packs'))
		self.modded_enableddatapacksLabel = CTkLabel(self.modded_WorldSettingsFrame,text="Enabled Datapacks: ")
		self.modded_enableddatapacksLabel.grid(row=14,column=0,sticky=E)
		self.modded_enableddatapacksEntry = CTkEntry(self.modded_WorldSettingsFrame,textvariable=self.modded_enableddatapacksStringVar)
		self.modded_enableddatapacksEntry.grid(row=14,column=1,sticky=W)
		self.modded_resourcePackConfigurationBtn = CTkButton(self.modded_WorldSettingsFrame,text="Configure Resource Pack",command=MCSC_Framework.onMainWindow_openResourcePackConfig)
		self.modded_resourcePackConfigurationBtn.grid(row=15,column=0,sticky=W,pady=3)
		self.modded_MOTDConfigBtn = CTkButton(self.modded_WorldSettingsFrame,text="Configure MOTD",command=MCSC_Framework.onMainWindow_openMOTDConfig)
		self.modded_MOTDConfigBtn.grid(row=15,column=1,sticky=W,pady=3)
		#World Settings booleans
		self.modded_WorldSettingsBools = CTkFrame(self.modded_WorldSettingsFrame)
		self.modded_WorldSettingsBools.grid(row=16,column=0,columnspan=2)
		self.modded_usecmdBlocksBoolVar = BooleanVar(value=MinecraftServerProperties.get("enable-command-block"))
		self.modded_commandBlockUsage = CTkCheckBox(self.modded_WorldSettingsBools,onvalue=True,offvalue=False,text="Allow Command Blocks",variable=self.modded_usecmdBlocksBoolVar)
		self.modded_commandBlockUsage.grid(row=0,column=0,sticky=W,padx=3)
		self.modded_cmdBlock_tip = CTkToolTip(self.modded_commandBlockUsage,"server.properties setting: 'enable-command-block'")
		self.modded_isPVPBool = BooleanVar(value=MinecraftServerProperties.get('pvp'))
		self.modded_isPVP = CTkCheckBox(self.modded_WorldSettingsBools,text="Allow PVP",variable=self.modded_isPVPBool,onvalue=True,offvalue=False)
		self.modded_isPVP.grid(row=0,column=1,padx=3)
		self.modded_pvp_tip = CTkToolTip(self.modded_isPVP,"server.properties setting: 'pvp'")
		self.modded_strictGamemodeBool = BooleanVar(value=MinecraftServerProperties.get('force-gamemode'))
		self.modded_strictGamemode = CTkCheckBox(self.modded_WorldSettingsBools,text="Enforce Gamemode",variable=self.modded_strictGamemodeBool,onvalue=True,offvalue=False)
		self.modded_strictGamemode.grid(row=1,column=0,padx=3,pady=3,sticky=W)
		self.modded_strictGamemode_tip = CTkToolTip(self.modded_strictGamemode,"server.properties setting: 'force-gamemode'")
		self.modded_resourcePackRequirementBool = BooleanVar(value=MinecraftServerProperties.get('require-resource-pack'))
		self.modded_resourcePackRequirement = CTkCheckBox(self.modded_WorldSettingsBools,text="Requires Resource Pack",variable=self.modded_resourcePackRequirementBool,onvalue=True,offvalue=False)
		self.modded_resourcePackRequirement.grid(row=2,column=0,padx=3,sticky=NW)
		self.modded_resourcePackRequirement_tip = CTkToolTip(self.modded_resourcePackRequirement,"server.properties setting: 'require-resource-pack'")
		self.modded_netherDimension = BooleanVar(value=MinecraftServerProperties.get('allow-nether'))
		self.modded_netherTravel = CTkCheckBox(self.modded_WorldSettingsBools,text="Allow Nether",variable=self.modded_netherDimension,onvalue=True,offvalue=False)
		self.modded_netherTravel.grid(row=1,column=1)
		self.modded_canFly = BooleanVar(value=MinecraftServerProperties.get('allow-flight'))
		self.modded_hasFlight = CTkCheckBox(self.modded_WorldSettingsBools,text="Allow Flying",variable=self.modded_canFly,onvalue=True,offvalue=False)
		self.modded_hasFlight.grid(row=2,column=1,padx=3,pady=3)
		self.modded_flying_tip = CTkToolTip(self.modded_hasFlight, "server.properties setting: 'allow-flight'")
		self.modded_netherTravel_tip = CTkToolTip(self.modded_netherTravel,"server.properties setting:'allow-nether'")
		self.modded_isHardcoreWorldBool = BooleanVar(value=MinecraftServerProperties.get("hardcore"))
		self.modded_isHardcore = CTkCheckBox(self.modded_WorldSettingsBools,text="Hardcore World",variable=self.modded_isHardcoreWorldBool,onvalue=True,offvalue=False)
		self.modded_isHardcore.grid(row=3,column=0,sticky=NW,padx=3)
		self.modded_hardcore_tip = CTkToolTip(self.modded_isHardcore,"server.properties setting:'hardcore'")
		self.modded_onlinePlayersHiddenBool = BooleanVar(value=MinecraftServerProperties.get('hide-online-players'))
		self.modded_showOnlinePlayers = CTkCheckBox(self.modded_WorldSettingsBools,text="Hide Online Players",variable=self.modded_onlinePlayersHiddenBool,onvalue=True,offvalue=False)
		self.modded_showOnlinePlayers.grid(row=3,column=1,padx=3,sticky=W)
		self.modded_visibeOnlinePlayers = CTkToolTip(self.modded_showOnlinePlayers,"server.properties setting: 'hide-online-players'")
		self.modded_statusBool = BooleanVar(value=MinecraftServerProperties.get('enable-status'))
		self.modded_toggleStatus = CTkCheckBox(self.modded_WorldSettingsBools,text="Toggle Status",variable=self.modded_statusBool,onvalue=True,offvalue=False)
		self.modded_toggleStatus.grid(row=4,column=0,padx=3,pady=3,sticky=W)
		self.modded_strictProfileBool = BooleanVar(value=MinecraftServerProperties.get('enforce-secure-profile'))
		self.modded_strictProfile = CTkCheckBox(self.modded_WorldSettingsBools,text="Stricted Profiling",variable=self.modded_strictProfileBool,onvalue=True,offvalue=False)
		self.modded_strictProfile.grid(row=5,column=0,sticky=W,padx=3)
		self.modded_strictProfile_tip = CTkToolTip(self.modded_strictProfile,"server.properties setting: 'enforce-secure-profile'")
		self.modded_nativeTransport = BooleanVar(value=MinecraftServerProperties.get('use-native-transport'))
		self.modded_useNativeTransport = CTkCheckBox(self.modded_WorldSettingsBools,text="Native Transport",variable=self.modded_nativeTransport,onvalue=True,offvalue=False)
		self.modded_useNativeTransport.grid(row=6,column=0,sticky=W,padx=3,pady=3)
		self.modded_nativeTransport_tip = CTkToolTip(self.modded_useNativeTransport,"server.properties setting: 'use-native-transport'")
		self.modded_structureGeneration = BooleanVar(value=MinecraftServerProperties.get('generate-structures'))
		self.modded_structureWillGenerate = CTkCheckBox(self.modded_WorldSettingsBools,text="Structure Generation",variable=self.modded_structureGeneration,onvalue=True,offvalue=False)
		self.modded_structureWillGenerate.grid(row=4,column=1,sticky=W,padx=3)
		self.modded_structure_tip = CTkToolTip(self.modded_structureWillGenerate,"server.properties setting:'generate-structures'")
		self.modded_npcSpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-npcs'))
		self.modded_NPCspawning = CTkCheckBox(self.modded_WorldSettingsBools,text="Spawn NPCs",variable=self.modded_npcSpawning,onvalue=True,offvalue=False)
		self.modded_NPCspawning.grid(row=5,column=1,sticky=W,padx=3)
		self.modded_npcSpawning_tip = CTkToolTip(self.modded_NPCspawning,"server.properties setting: 'spawn-npcs'")
		self.modded_animalSpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-animals'))
		self.modded_Animalspawning = CTkCheckBox(self.modded_WorldSettingsBools,text="Spawn Animals",variable=self.modded_animalSpawning,onvalue=True,offvalue=False)
		self.modded_Animalspawning.grid(row=6,column=1,sticky=W,padx=3)
		self.modded_animalspawning_tip = CTkToolTip(self.modded_Animalspawning,"server.properties setting: 'spawn-animals'")
		self.modded_enemySpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-monsters'))
		self.modded_Enemyspawning = CTkCheckBox(self.modded_WorldSettingsBools,text="Spawn Enemies",variable=self.modded_enemySpawning,onvalue=True,offvalue=False)
		self.modded_Enemyspawning.grid(row=7,column=1,sticky=W,padx=3)
		self.modded_enemyspawning_tip = CTkToolTip(self.modded_Enemyspawning,"server.properties setting: 'spawn-monsters'")
		self.modded_broadcastConsoleBool = BooleanVar(value=MinecraftServerProperties.get('broadcast-console-to-ops'))
		self.modded_broadcastConsole = CTkCheckBox(self.modded_WorldSettingsBools,text="Broadcast System Console",variable=self.modded_broadcastConsoleBool,onvalue=True,offvalue=False)
		self.modded_broadcastConsole.grid(row=7,column=0,sticky=W,padx=3)
		self.modded_broadcastconsole_tip = CTkToolTip(self.modded_broadcastConsole,"server.properties setting: 'broadcast-console-to-ops'")
		#Network & Security Tab
		self.modded_NetworkSecurityTab = CTkScrollableFrame(self.moddedserverPropertiesFrame_tabs.tab("Network & Security"))
		self.modded_NetworkSecurityTab.pack(fill=BOTH,expand=True,anchor=W)
		self.modded_MinecraftServerIPStringVar = StringVar(value=MinecraftServerProperties.get('server-ip'))
		self.modded_IPAddressLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Server IP: ")
		self.modded_IPAddressLabel.grid(row=0,column=0,sticky=E)
		self.modded_IPAddressEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_MinecraftServerIPStringVar)
		self.modded_IPAddressEntry.grid(row=0,column=1,sticky=W)
		self.modded_IPAddress_tip = CTkToolTip(self.modded_IPAddressLabel,"server.properties setting: 'server-ip'")
		self.modded_NetworkCompressionIntVar = IntVar(value=MinecraftServerProperties.get('network-compression-threshold'))
		self.modded_networkcompressionLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Network Compression: ")
		self.modded_networkcompressionLabel.grid(row=1,column=0,sticky=E)
		self.modded_networkCompressionEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_NetworkCompressionIntVar)
		self.modded_networkCompressionEntry.grid(row=1,column=1,sticky=W)
		self.modded_networkCompression_tip = CTkToolTip(self.modded_networkcompressionLabel,"server.properties setting: 'network-compression-threshold'")
		self.modded_ticktimeIntVar = IntVar(value=MinecraftServerProperties.get('max-tick-time'))
		self.modded_ticktimeLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Max Tick Rate: ")
		self.modded_ticktimeLabel.grid(row=2,column=0,sticky=E)
		self.modded_ticktimeEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_ticktimeIntVar)
		self.modded_ticktimeEntry.grid(row=2,column=1,sticky=W)
		self.modded_ticktime_tip = CTkToolTip(self.modded_ticktimeLabel,"server.properties setting: 'max-tick-time'")
		self.modded_maxplayersIntVar = IntVar(value=MinecraftServerProperties.get('max-players'))
		self.modded_maxplayersLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Max Players: ")
		self.modded_maxplayersLabel.grid(row=3,column=0,sticky=E)
		self.modded_maxplayersEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_maxplayersIntVar)
		self.modded_maxplayersEntry.grid(row=3,column=1,sticky=W)
		self.modded_maxplayers_tip = CTkToolTip(self.modded_maxplayersLabel,"server.properties setting: 'max-players'")
		self.modded_serverportIntVar = IntVar(value=MinecraftServerProperties.get('server-port'))
		self.modded_serverportLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Server Port: ")
		self.modded_serverportLabel.grid(row=4,column=0,sticky=E)
		self.modded_serverportEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_serverportIntVar)
		self.modded_serverportEntry.grid(row=4,column=1,sticky=W)
		self.modded_serverport_tip = CTkToolTip(self.modded_serverportLabel,"server.properties setting: 'server-port'")
		self.modded_opPermissionlvlList = ["0","1","2","3","4"]
		self.modded_opPermissionlvlIntVar = IntVar(value=MinecraftServerProperties.get('op-permission-level'))
		self.modded_opPermissionlvlLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Op Permission Level: ")
		self.modded_opPermissionlvlLabel.grid(row=5,column=0,sticky=E)
		self.modded_opPermissionlvlComboBox = CTkComboBox(self.modded_NetworkSecurityTab,values=self.modded_opPermissionlvlList,variable=self.modded_opPermissionlvlIntVar)
		self.modded_opPermissionlvlComboBox.grid(row=5,column=1,sticky=W)
		self.modded_opPermissionlvl_tip = CTkToolTip(self.modded_opPermissionlvlLabel,"server.properties setting: 'op-permission-level'")
		self.modded_entitybroadcastRangeList = [str(i) for i in range(10,1000)] #Best way of generating numbers from its set range
		self.modded_entitybroadcastRangeIntVar = IntVar(value=MinecraftServerProperties.get('entity-broadcast-range-percentage'))
		self.modded_entitybroadcastRangeLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Entity Broadcasting: ")
		self.modded_entitybroadcastRangeLabel.grid(row=6,column=0,sticky=E)
		self.modded_entitybroadcastRangeCombobox = CTkComboBox(self.modded_NetworkSecurityTab,values=self.modded_entitybroadcastRangeList,variable=self.modded_entitybroadcastRangeIntVar)
		self.modded_entitybroadcastRangeCombobox.grid(row=6,column=1,sticky=W)
		self.modded_entitybroadcastRange_tip = CTkToolTip(self.modded_entitybroadcastRangeLabel,"server.properties setting: 'entity-broadcast-range-percentage")
		self.modded_playertimeoutIntVar = IntVar(value=MinecraftServerProperties.get('player-idle-timeout'))
		self.modded_playertimeoutLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Idle Player Timeout: ")
		self.modded_playertimeoutLabel.grid(row=7,column=0,sticky=E)
		self.modded_playertimeoutEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_playercountIntVar)
		self.modded_playertimeoutEntry.grid(row=7,column=1,sticky=W)
		self.modded_playertimeout_tip = CTkToolTip(self.modded_playertimeoutLabel,"server.properties setting: 'player-idle-timeout'")
		self.modded_ratelimitIntvar = IntVar(value=MinecraftServerProperties.get('rate-limit'))
		self.modded_ratelimitLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Rate Limit: ")
		self.modded_ratelimitLabel.grid(row=8,column=0,sticky=E)
		self.modded_ratelimitEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_ratelimitIntvar)
		self.modded_ratelimitEntry.grid(row=8,column=1,sticky=W)
		self.modded_ratelimit_tip = CTkToolTip(self.modded_ratelimitLabel,"server.properties setting: 'rate-limit'")
		self.modded_functionPermissionlvlList = [str(x) for x in range(1,4)]
		self.modded_functionPermissionlvlIntvar = IntVar(value=MinecraftServerProperties.get('function-permission-level'))
		self.modded_functionPermissionlvlLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Fuction Permission Level: ")
		self.modded_functionPermissionlvlLabel.grid(row=9,column=0,sticky=E)
		self.modded_functionPermissionlvlComboBox = CTkComboBox(self.modded_NetworkSecurityTab,values=self.modded_functionPermissionlvlList,variable=self.modded_functionPermissionlvlIntvar)
		self.modded_functionPermissionlvlComboBox.grid(row=9,column=1,sticky=W)
		self.modded_functionPermissionlvl_tip = CTkToolTip(self.vanilla_functionPermissionlvlLabel,"server.properties setting: 'function-permission-level'")
		self.modded_rconPasswordStringVar = StringVar(value=MinecraftServerProperties.get('rcon.password'))
		self.modded_rconPasswordLabel = CTkLabel(self.modded_NetworkSecurityTab,text="RCON Password: ")
		self.modded_rconPasswordLabel.grid(row=10,column=0,sticky=E)
		self.modded_rconPasswordEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_rconPasswordStringVar)
		self.modded_rconPasswordEntry.grid(row=10,column=1,sticky=W)
		self.modded_rconPassword_tip = CTkToolTip(self.modded_rconPasswordLabel,"server.properties setting: 'rcon.password'")
		self.modded_rconportIntVar = IntVar(value=MinecraftServerProperties.get('rcon.port'))
		self.modded_rconportLabel = CTkLabel(self.modded_NetworkSecurityTab,text="RCON Port: ")
		self.modded_rconportLabel.grid(row=11,column=0,sticky=E)
		self.modded_rconportEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_rconportIntVar)
		self.modded_rconportEntry.grid(row=11,column=1,sticky=W)
		self.modded_rconport_tip = CTkToolTip(self.modded_rconportLabel,"server.properties setting: 'rcon.port'")
		self.modded_queryportIntVar = IntVar(value=MinecraftServerProperties.get('query.port'))
		self.modded_queryportLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Query Port: ")
		self.modded_queryportLabel.grid(row=12,column=0,sticky=E)
		self.modded_queryportEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_queryportIntVar)
		self.modded_queryportEntry.grid(row=12,column=1,sticky=W)
		self.modded_queryport_tip = CTkToolTip(self.modded_queryportLabel,"server.properties setting: 'query.port'")
		self.modded_bugreportingStringVar = StringVar(value=MinecraftServerProperties.get('bug-report-link'))
		self.modded_bugreportingLabel = CTkLabel(self.modded_NetworkSecurityTab,text="Bug Report Link: ")
		self.modded_bugreportingLabel.grid(row=13,column=0,sticky=E)
		self.modded_bugreportingEntry = CTkEntry(self.modded_NetworkSecurityTab,textvariable=self.modded_bugreportingStringVar)
		self.modded_bugreportingEntry.grid(row=13,column=1,sticky=W)
		self.modded_bugreporting_tip = CTkToolTip(self.modded_bugreportingLabel,"server.properties setting: 'bug-report-link'")
		#Networking Tab Bools
		self.modded_NetworkSecurityTabBools = CTkFrame(self.modded_NetworkSecurityTab)
		self.modded_NetworkSecurityTabBools.grid(row=13,column=0,columnspan=2,sticky=E)
		self.modded_togglequery = BooleanVar(value=MinecraftServerProperties.get('enable-query'))
		self.modded_canQueryCheck = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Enable Query",variable=self.modded_togglequery,onvalue=True,offvalue=False)
		self.modded_canQueryCheck.grid(row=0,column=1,padx=3,pady=3,sticky=W)
		self.modded_canquery_tip = CTkToolTip(self.modded_canQueryCheck,"server.properties setting: 'enable-query'")
		self.modded_chunkwriteSyncingBool = BooleanVar(value=MinecraftServerProperties.get('sync-chunk-writes'))
		self.modded_chunkwriteSyncingCheck = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Synchronized Chunk Writing",variable=self.modded_chunkwriteSyncingBool,onvalue=True,offvalue=False)
		self.modded_chunkwriteSyncingCheck.grid(row=1,column=0,padx=3,pady=3,sticky=W)
		self.modded_chunkwriteSyncing_tip = CTkToolTip(self.modded_chunkwriteSyncingCheck,"server.properties setting: 'sync-chunk-writes'")
		self.modded_proxyBlockingBool = BooleanVar(value=MinecraftServerProperties.get('prevent-proxy-connections'))
		self.modded_proxyBlockingCheck = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Block Proxy Connections",variable=self.modded_proxyBlockingBool,onvalue=True,offvalue=False)
		self.modded_proxyBlockingCheck.grid(row=0,column=0,padx=3,pady=3,sticky=W)
		self.modded_proxyblocking_tip = CTkToolTip(self.modded_proxyBlockingCheck,"server.properties setting: 'prevent-proxy-connections'")
		self.modded_toggleOnlineMode = BooleanVar(value=MinecraftServerProperties.get('online-mode'))
		self.modded_isOnline = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Online Mode",variable=self.modded_toggleOnlineMode,onvalue=True,offvalue=False)
		self.modded_isOnline.grid(row=1,column=1,sticky=W,padx=3,pady=3)
		self.modded_isonline_tip = CTkToolTip(self.modded_isOnline,"server.properties setting: 'online-mode'")
		self.modded_jmxMonitoringBool = BooleanVar(value=MinecraftServerProperties.get('enable-jmx-monitoring'))
		self.modded_jmxMonitoringCheck = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Toggle JMX Monitoring",variable=self.modded_jmxMonitoringBool,onvalue=True,offvalue=False)
		self.modded_jmxMonitoringCheck.grid(row=2,column=0,sticky=W,pady=3,padx=3)
		self.modded_jmxMonitoring_tip = CTkToolTip(self.modded_jmxMonitoringCheck,"server.properties setting: 'enable-jmx-monitoring'")
		self.modded_isIPLogging = BooleanVar(value=MinecraftServerProperties.get('log-ips'))
		self.modded_IPLogBool = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Log IPs",onvalue=True,offvalue=False,variable=self.modded_isIPLogging)
		self.modded_IPLogBool.grid(row=2,column=1,padx=3,pady=3,sticky=W)
		self.modded_togglerconBool = BooleanVar(value=MinecraftServerProperties.get('enable-rcon'))
		self.modded_rconToggler = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Enable RCON",variable=self.modded_togglerconBool,onvalue=True,offvalue=False)
		self.modded_rconToggler.grid(row=3,column=1,padx=3,pady=3,sticky=W)
		self.modded_broadcastrconBool = BooleanVar(value=MinecraftServerProperties.get('broadcast-rcon-to-ops'))
		self.modded_rconBroadcast = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Broadcast RCON",variable=self.modded_broadcastrconBool,onvalue=True,offvalue=False)
		self.modded_rconBroadcast.grid(row=3,column=0,sticky=W,padx=3,pady=3)
		self.modded_acceptTransfersBool = BooleanVar(value=MinecraftServerProperties.get('accept-transfers'))
		self.modded_acceptTransfers = CTkCheckBox(self.modded_NetworkSecurityTabBools,text="Accept Transfers from Another Server",variable=self.modded_acceptTransfersBool,onvalue=True,offvalue=False)
		self.modded_acceptTransfers.grid(row=4,column=0,padx=3,pady=3,sticky=W)
		self.populateInstanceView(self.moddedinstanceView,"",self.modpacksFolder,"downloads")
				
		self.closebtn = CTkButton(self.root,text="Close",command=lambda:self.root.destroy())
		self.closebtn.grid(row=1,column=0,sticky=E,pady=10)
	
	def setMCVersions(self,event):
		#We need to know what server type is selected
		currentSelection = self.create_moddedinstance_serverTypeCombo.get()
		print(currentSelection)
		if currentSelection == "Forge":
			#We need to update the widget
			versions = MCSCUpdater.ForgeBaseClass.getmcVersionListing()
			self.create_moddedinstance_minecraftVersionCombo.configure(values=versions)
			return
		else:
			if currentSelection == "Fabric":
				#We need to update the widget
				os.chdir(str(rootFilepath))
				MCSCDatabase = sqlite3.connect('mcsc_data.db')
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT compatiableMinecraftVersions FROM fabricVersion_Table")
				versions = [v for v in MCSC_Cursor.fetchone()]
				versions = versions[0]
				versions = ast.literal_eval(versions)
				MCSC_Cursor.close()
				MCSCDatabase.close()
				print(versions)
				self.create_moddedinstance_minecraftVersionCombo.configure(values=versions)
				return
			else:
				if currentSelection == "Custom":
					#We need to update the widget. This might change later
					versions = ServerVersion_Control.getVersionList()
					self.create_moddedinstance_serverTypeVersionCombo.configure(values=versions)
					return
	
	def setServerTypeVersions(self,event):
		currentselection_minecraftVersions = self.create_moddedinstance_minecraftVersionCombo.get()
		currentselection_servertypes = self.create_moddedinstance_serverTypeCombo.get()
		if currentselection_servertypes == "Forge":
			servertypeVersions = MCSCUpdater.ForgeBaseClass.getForgeVersionsbyVersion(str(currentselection_minecraftVersions))
			servertypeVersions = list(set(servertypeVersions))
			servertypeVersions = sorted(servertypeVersions,key=Version,reverse=True)
			self.create_moddedinstance_serverTypeVersionCombo.configure(values=servertypeVersions,state=NORMAL)
			return
		else:
			if currentselection_servertypes == "Fabric":
				os.chdir(str(rootFilepath))
				MCSCDatabase = sqlite3.connect('mcsc_data.db')
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT version FROM fabricVersion_Table")
				servertypeVersions = [v for v in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
				servertypeVersions = [item[0] for item in servertypeVersions]
				servertypeVersions = [Version(v) for v in servertypeVersions]
				servertypeVersions = sorted(servertypeVersions,reverse=True)
				servertypeVersions = [str(Versions) for Versions in servertypeVersions]
				self.create_moddedinstance_serverTypeVersionCombo.configure(values=servertypeVersions,state=NORMAL)
				return
			else:
				if currentselection_servertypes == "Custom":
					self.create_moddedinstance_serverTypeVersionCombo.configure(values=[],state=DISABLED)
					return

	def populateInstanceView(self,treeview, parent, directory, omitFolder):
		items = os.listdir(directory)
		instances = []
		for item in items:
			if item == omitFolder:
				continue
			itemPath = os.path.join(directory, item)
			if os.path.isdir(itemPath):
				instances.append(item)
				continue
			else:
				pass
					
		instances.sort()

		for item in instances:
			itemPath = os.path.join(directory, item)
			if os.path.isdir(itemPath):
				Directory = treeview.insert(parent, END, text=item, values=("Instance"))
			else:
				pass
	
	def createVanillaInstance(self,name,minecraftversion=None,servertype=None,serverDirectory=None):
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		isStrictedServerDirectory = self.create_vanillainstance_enforceserverDirectory.get()

		#We need to do some checks
		try:
			#Parse the instance folder
			currentInstances = os.listdir(self.instancesFolder)
			if os.path.isdir(self.instancesFolder + "/" + str(name)) == False:
				#We need to check the given minecraft version
				MCSC_Cursor.execute("SELECT version FROM minecraftversion_Table ORDER BY version DESC")
				availableMCVersions = MCSC_Cursor.fetchall()
				if minecraftversion in [version[0] for version in availableMCVersions]:
					#We need to check if the server type is valid
					if servertype in self.servertypes:
						#We need to check if the server directory exists
						if os.path.isdir(str(serverDirectory)) == True:
							#create the instance data
							newInstanceFolder = self.instancesFolder + "/" + str(name)
							os.mkdir(str(newInstanceFolder))
							if MCSC_Framework.isAdmin() == 0:
								print("[Minerva Server Crafter]: Higher Privileges required. Prompting UAC...")
								#elevate the privileges
								MCSC_Framework.runasAdminUser()
								if isStrictedServerDirectory == False:
									#Generate the files in the new instance. We will use the server directory as a reference point
									shutil.copytree(str(serverDirectory),str(newInstanceFolder),dirs_exist_ok=True)
									ServerFileIO.importpropertiestojson(serverjarpath=None,instanceName=str(name),minecraftVersion=str(minecraftversion),isModded=False,create_data_ok=True,legacyBehavior=False)
									self.exportToJSONModel(instanceName=str(name))
									for root,dirs,files in os.walk(str(self.instancesFolder)):
										for dir in dirs:
											os.chmod(os.path.join(root,dir),stat.S_IWRITE)
										for file in files:
											os.chmod(os.path.join(root,file),stat.S_IWRITE)
									print("[Minerva Server Crafter - ADMIN MODE]: All server directory files has been generated using user-given directory as a model and saved as a instance. Exiting Admin Mode...")
									MCSC_Framework.dropToNormalUser()
									MCSC_Cursor.execute("INSERT INTO Instances_Table (name, minecraftVersion, serverType) VALUES (?,?,?)",(name,minecraftversion,servertype))
									MCSCDatabase.commit()
									print("[Minerva Server Crafter]: Data has been saved.")
									#Close the database connection
									MCSC_Cursor.close()
									MCSCDatabase.close()
									self.populateInstanceView(self.vanillainstanceView,"",self.instancesFolder)
									return
								else:
									#We dont need to generate the files. The behavior is like the old JSON model
									ServerFileIO.importpropertiestojson(serverjarpath=str(serverDirectory),instanceName=str(name),minecraftVersion=str(minecraftversion),isModded=False,create_data_ok=False,legacyBehavior=True)
									self.exportToJSONModel(instanceName=str(name))
									MCSC_Cursor.execute("INSERT INTO Instances_Table (name, minecraftVersion, serverType, targetDirectory) VALUES (?,?,?,?)",(name,minecraftversion,servertype,serverDirectory))
									MCSCDatabase.commit()
									print("[Minerva Server Crafter]: Data has been saved.")
									#Close the database connection
									MCSC_Cursor.close()
									MCSCDatabase.close()
									self.populateInstanceView(self.vanillainstanceView,"",self.instancesFolder)
									return

						else:
							raise MCSCInternalError("Directory not found.")
					else:
						raise MCSCInternalError("Not a valid Server Type.")
				else:
					raise MCSCInternalError("Not a valid minecraft version.")
			else:
				raise MCSCInternalError(f"{name} is already an existing instance.")

		except MCSCInternalError as e:
			ConsoleWindow.displayException(e)
			MCSC_Cursor.close()
			return
	def attachInstance(self,widget=None):
		global launchServerBtn
		self.Widget = widget
		if self.Widget == None:
			raise MCSCInternalError("Widget parameter was a NoneType value")
		selecteditemdata = self.Widget.focus()
		selecteditem = self.Widget.item(selecteditemdata).get('text')
		if selecteditem:
			#We can load the properties from the json
			instanceName = str(selecteditem)
			ServerFileIO.loadJSONProperties(instanceName=str(instanceName))
			ServerFileIO.onExit_setInstancePointer(instanceName=str(instanceName))
			print(f"[Minerva Server Crafter]: Instance Attached Successfully.")
			MCSC_Framework.onMainWindow_setTabState(self.creationTabsvanilla,"Instance Server Properties","normal")
			MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting","normal")
			MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players","normal")
			launchServerBtn.configure(state="normal")
			return

	def displayInstanceDetails(self,event):
		# We need to get what's selected in the treeview
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		selecteditemData = self.vanillainstanceView.focus()
		selected_item = self.vanillainstanceView.item(selecteditemData).get('text')
		if selected_item:
			instance_name = str(selected_item)

			# Parse the Instance table
			MCSC_Cursor.execute("SELECT name, minecraftVersion, serverType, targetDirectory FROM Instances_Table WHERE name = ?", (instance_name,))
			instance_data = MCSC_Cursor.fetchone()

			if instance_data:
				name, mc_version, server_type, path = instance_data
				self.vanillainstanceName.configure(text=f"Instance Name: {name}")
				self.vanillainstanceminecraftVersion.configure(text=f"Minecraft Server Version: {mc_version}")
				self.vanillainstanceservertype.configure(text=f"Server Type: {server_type}")
				self.vanillainstancetargetedDirectory.configure(text=f"Server Directory:\n{path}")
				#Update the image
				if server_type == "Minecraft Vanilla":
					self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/minecraft_vanilla_source.png"))
					MCSC_Cursor.close()
					MCSCDatabase.close()
					return
				else:
					if server_type == "Fabric":
						self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/fabric_source.png"))
						MCSC_Cursor.close()
						MCSCDatabase.close()
						return
					else:
						if server_type == "Spigot":
							self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/spigot_source.png"))
							MCSC_Cursor.close()
							MCSCDatabase.close()
							return
						else:
							if server_type == "Forge":
								self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/forge_source.png"))
								MCSC_Cursor.close()
								return
							else:
								if server_type == "CraftBukkit":
									self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/craftbukkit_source.png"))
									MCSC_Cursor.close()
									MCSCDatabase.close()
									return
								else:
									if server_type == "Purpur":
										self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/purpur_source.png"))
										MCSC_Cursor.close()
										MCSCDatabase.close()
										return
									else:
										if server_type == "Custom":
											self.vanillainstanceImageData.configure(dark_image=Image.open(str(rootFilepath) + "/base/ui/custom_server_jar.png"))
											MCSC_Cursor.close()
											MCSCDatabase.close()
											return
	def exportToJSONModel(self,instanceName=None,useVersion=None):
		'exportToJSONModel() -> Save operation \n \n Exports the Properties JSON Model to properties.json'
		global ConsoleWindow
		global root_tabs
		root_tabs.set("Console Shell")

		#We need to update values
		ServerFileIO.updatePropertiesbyKey("enable-jmx-monitoring",self.vanilla_jmxMonitoringBool.get())
		ServerFileIO.updatePropertiesbyKey("rcon.port",self.vanilla_rconportIntVar.get())
		ServerFileIO.updatePropertiesbyKey("level-seed",self.vanilla_levelSeedStringVar.get())
		ServerFileIO.updatePropertiesbyKey("gamemode",self.vanilla_gamemodeStringVar.get())
		ServerFileIO.updatePropertiesbyKey("enable-command-block",self.vanilla_usecmdBlocksBoolVar.get())
		ServerFileIO.updatePropertiesbyKey("enable-query",self.vanilla_togglequery.get())
		ServerFileIO.updatePropertiesbyKey("generator-settings",self.vanilla_generatorsettingsvar.get())
		ServerFileIO.updatePropertiesbyKey("level-name",self.vanilla_WorldNameStringVar.get())
		ServerFileIO.updatePropertiesbyKey("query.port",self.vanilla_queryportIntVar.get())
		ServerFileIO.updatePropertiesbyKey("pvp",self.vanilla_isPVPBool.get())
		ServerFileIO.updatePropertiesbyKey("generate-structures",self.vanilla_structureGeneration.get())
		ServerFileIO.updatePropertiesbyKey("difficulty",self.vanilla_worldDifficultyVar.get())
		ServerFileIO.updatePropertiesbyKey("network-compression-threshold",self.vanilla_NetworkCompressionIntVar.get())
		ServerFileIO.updatePropertiesbyKey("max-tick-time",self.vanilla_ticktimeIntVar.get())
		ServerFileIO.updatePropertiesbyKey("require-resource-pack",self.vanilla_resourcePackRequirementBool.get())
		ServerFileIO.updatePropertiesbyKey("max-players",self.vanilla_maxplayersIntVar.get())
		ServerFileIO.updatePropertiesbyKey("use-native-transport",self.vanilla_nativeTransport.get())
		ServerFileIO.updatePropertiesbyKey("online-mode",self.vanilla_toggleOnlineMode.get())
		ServerFileIO.updatePropertiesbyKey("enable-status",self.vanilla_statusBool.get())
		ServerFileIO.updatePropertiesbyKey("allow-flight",self.vanilla_canFly.get())
		ServerFileIO.updatePropertiesbyKey("broadcast-rcon-to-ops",self.vanilla_broadcastrconBool.get())
		ServerFileIO.updatePropertiesbyKey("view-distance",self.vanilla_viewDistanceIntVar.get())
		ServerFileIO.updatePropertiesbyKey("resource-pack-prompt",self.vanilla_resourcePackPromptStringVar.get())
		ServerFileIO.updatePropertiesbyKey("server-ip",self.vanilla_IPAddressEntry.get())
		ServerFileIO.updatePropertiesbyKey("allow-nether",self.vanilla_netherDimension.get())
		ServerFileIO.updatePropertiesbyKey("server-port",self.vanilla_serverportIntVar.get())
		ServerFileIO.updatePropertiesbyKey("enable-rcon",self.vanilla_togglerconBool.get())
		ServerFileIO.updatePropertiesbyKey("sync-chunk-writes",self.vanilla_chunkwriteSyncingBool.get())
		ServerFileIO.updatePropertiesbyKey("op-permission-level",self.vanilla_opPermissionlvlIntVar.get())
		ServerFileIO.updatePropertiesbyKey("prevent-proxy-connections",self.vanilla_proxyBlockingBool.get())
		ServerFileIO.updatePropertiesbyKey("hide-online-players",self.vanilla_onlinePlayersHiddenBool.get())
		ServerFileIO.updatePropertiesbyKey("entity-broadcast-range-percentage",self.vanilla_entitybroadcastRangeIntVar.get())
		ServerFileIO.updatePropertiesbyKey("simulation-distance",self.vanilla_simulationDistanceIntVar.get())
		ServerFileIO.updatePropertiesbyKey("rcon.password",self.vanilla_rconPasswordStringVar.get())
		ServerFileIO.updatePropertiesbyKey("player-idle-timeout",self.vanilla_playertimeoutIntVar.get())
		ServerFileIO.updatePropertiesbyKey("force-gamemode",self.vanilla_strictGamemodeBool.get())
		ServerFileIO.updatePropertiesbyKey("rate-limit",self.vanilla_ratelimitIntvar.get())
		ServerFileIO.updatePropertiesbyKey("hardcore",self.vanilla_isHardcoreWorldBool.get())
		ServerFileIO.updatePropertiesbyKey("white-list",whitelistedBool.get())
		ServerFileIO.updatePropertiesbyKey("broadcast-console-to-ops",self.vanilla_broadcastConsoleBool.get())
		ServerFileIO.updatePropertiesbyKey("spawn-npcs",self.vanilla_npcSpawning.get())
		ServerFileIO.updatePropertiesbyKey("spawn-animals",self.vanilla_animalSpawning.get())
		ServerFileIO.updatePropertiesbyKey("function-permission-level",self.vanilla_functionPermissionlvlIntvar.get())
		ServerFileIO.updatePropertiesbyKey("level-type",self.vanilla_worldtypeStringVar.get())
		ServerFileIO.updatePropertiesbyKey("spawn-monsters",self.vanilla_enemySpawning.get())
		ServerFileIO.updatePropertiesbyKey("enforce-whitelist",strictedWhitelistBool.get())
		ServerFileIO.updatePropertiesbyKey("spawn-protection",self.vanilla_spawnprotectionRadiusInt.get())
		ServerFileIO.updatePropertiesbyKey("max-world-size",self.vanilla_worldsizeInt.get())
		ServerFileIO.updatePropertiesbyKey("enforce-secure-profile",self.vanilla_strictProfileBool.get())
		ServerFileIO.updatePropertiesbyKey("max-chained-neighbor-updates",self.vanilla_neighborupdatesIntVar.get())
		ServerFileIO.updatePropertiesbyKey("initial-disabled-packs",self.vanilla_disableddataPackStringVar.get())
		ServerFileIO.updatePropertiesbyKey("initial-enabled-packs",self.vanilla_enableddatapacksStringVar.get())
		ServerFileIO.updatePropertiesbyKey("log-ips",self.vanilla_isIPLogging.get())
		#Update the dictionary
		MinecraftServerProperties.update()
		print("[Minerva Server Crafter]: Properties Data Updated Successfully. Conducting Save Sequence...")
		#We need to make the properties file backwards compatible
		if useVersion is not None:
			availableVersions = ServerVersion_Control.getVersionList()
			if useVersion in availableVersions:
				print(f"[Minerva Server Crafter]: We are using a Minecraft {useVersion} Server. Porting data to that version...")
				#We need to model the data based on the version of minecraft
				expectedProperties = ServerFileIO.usePropertiesByMinecraftVersion(minecraftVersion=str(useVersion))
				#We need to check keys
				for k1,v1 in MinecraftServerProperties.items():
					for k2 in expectedProperties.keys():
						keyCheck = MinecraftServerProperties.get(k1) in expectedProperties.keys()
						if keyCheck == True:
							expectedProperties[k2] = v1
							continue
						else:
							continue
				del expectedProperties['debug']
				ServerFileIO.exportPropertiestoJSON(instanceName=str(instanceName),alternativeDict=expectedProperties)
				print("[Minerva Server Crafter]: Properties Data Porting Done. :D")
				return
					
	
	def buttonActionVanilla_onClickSubmit(self):
		#Get all of the data that was put in
		name = self.create_vanillainstance_instanceNameEntry.get()
		minecraft_version = self.create_vanillainstance_minecraftVersionCombo.get()
		mcServer_Type = self.create_vanillainstance_serverTypeCombo.get()
		target_directory = self.create_vanillainstance_serverDirectoryLabel_directory.cget("text")
		print(name,minecraft_version,mcServer_Type,target_directory)
		#Begin the data processing for creating the instance
		#Verify if the SHA-1 of the jar file given matches with an official public distribution
		if mcServer_Type == "Minecraft Vanilla":
			ServerVersion_Control.downloadvanillaserverfile(version=str(minecraft_version))
			referenced_hash = ServerVersion_Control.generateSHA1forJarfile("server",filepath=str(target_directory))
			if ServerVersion_Control.isValidOfficialVanillaHash(referenced_hash,str(minecraft_version)) == True:
				#Hash was verified via cross-referencing between a hexdigest, and its own version json file
				self.createVanillaInstance(str(name),str(minecraft_version),str(mcServer_Type),str(target_directory))
				return
			else:
				raise MCSCInternalError("File Hash Mismatch")
		else:
			if mcServer_Type == "Spigot":
				#This has to be obtained by buildtools
				MCSCUpdater.SpigotBaseClass.getSpigot(str(minecraft_version))
				spigotName = "spigot-" + str(minecraft_version)
				spigotName = str(spigotName)
				referenced_directory = str(rootFilepath) + f"/base/sandbox/build/Spigot/{minecraft_version}"
				#Get the SHA1 hash
				reference_hash = ServerVersion_Control.generateSHA1forJarfile(str(spigotName),filepath=str(referenced_directory))
				instance_hash = ServerVersion_Control.generateSHA1forJarfile(str(spigotName),filepath=str(target_directory))
				try:
					if str(reference_hash) == str(instance_hash):
						#The hashes are the same, so they are the same file
						self.createInstance(str(name),str(minecraft_version),str(mcServer_Type),str(target_directory))
						return
					else:
						raise MCSCInternalError("File Hash Mismatch")
				except MCSCInternalError as e:
					print(e)
					return
			else:
				if mcServer_Type == "Craftbukkit":
					#This has to be obtained by buildtools
					MCSCUpdater.SpigotBaseClass.getCraftBukkit(str(minecraft_version))
					craftbukkitName = "craftbukkit-" + str(minecraft_version)
					craftbukkitName = str(craftbukkitName)
					referenced_directory = str(rootFilepath) + f"/base/sandbox/build/Craftbukkit/{minecraft_version}"
					#Get the SHA1 hash
					reference_hash = ServerVersion_Control.generateSHA1forJarfile(str(craftbukkitName),filepath=str(referenced_directory))
					instance_hash = ServerVersion_Control.generateSHA1forJarfile(str(craftbukkitName),filepath=str(target_directory))
					if str(reference_hash) == str(instance_hash):
						#The hashes are the same, so they are the same file
						self.createInstance(str(name),str(minecraft_version),str(mcServer_Type),str(target_directory))
						return
				else:
					if mcServer_Type == "Purpur":
						#Skip file hash check
						self.createInstance(str(name),str(minecraft_version),str(mcServer_Type),str(target_directory))
						return
	def createmoddedInstance(self,name,minecraftversion=None,servertype=None,serverDirectory=None,isModpack=None):
		global ConsoleWindow
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		isStrictedServerDirectory = self.create_moddedinstance_enforceserverDirectory.get()

		#We need to do some checks
		try:
			#Parse the instance folder
			currentInstances = os.listdir(self.modpacksFolder)
			if os.path.isdir(self.modpacksFolder + "/" + str(name)) == False:
				#We need to check the given minecraft version
				MCSC_Cursor.execute("SELECT version FROM minecraftversion_Table ORDER BY version DESC")
				availableMCVersions = MCSC_Cursor.fetchall()
				if minecraftversion in [version[0] for version in availableMCVersions]:
					#We need to check if the server type is valid
					if servertype in self.moddedservertypes:
						#We need to check if the server directory exists
						if os.path.isdir(str(serverDirectory)) == True:
							#create the instance data
							newInstanceFolder = self.modpacksFolder + "/" + str(name)
							os.mkdir(str(newInstanceFolder))
							if MCSC_Framework.isAdmin() == 0:
								print("[Minerva Server Crafter]: Higher Privileges required. Prompting UAC...")
								#elevate the privileges
								MCSC_Framework.runasAdminUser()
								if isStrictedServerDirectory == False:
									#Generate the files in the new instance. We will use the server directory as a reference point
									shutil.copytree(str(serverDirectory),str(newInstanceFolder),dirs_exist_ok=True)
									ServerFileIO.importpropertiestojson(serverjarpath=None,instanceName=str(name),minecraftVersion=str(minecraftversion),isModded=True,create_data_ok=True,legacyBehavior=False)
									self.exportToJSONModel(instanceName=str(name))
									for root,dirs,files in os.walk(str(self.modpacksFolder)):
										for dir in dirs:
											os.chmod(os.path.join(root,dir),stat.S_IWRITE)
										for file in files:
											os.chmod(os.path.join(root,file),stat.S_IWRITE)
									print("[Minerva Server Crafter - ADMIN MODE]: All server directory files has been generated using user-given directory as a model and saved as a instance. Exiting Admin Mode...")
									MCSC_Framework.dropToNormalUser()
									MCSC_Cursor.execute("INSERT INTO Instances_Table (name, minecraftVersion, serverType) VALUES (?,?,?)",(name,minecraftversion,servertype))
									MCSCDatabase.commit()
									print("[Minerva Server Crafter]: Data has been saved.")
									#Close the database connection
									MCSC_Cursor.close()
									MCSCDatabase.close()
									self.populateInstanceView(self.moddedinstanceView,"",self.modpacksFolder)
									return
								else:
									#We dont need to generate the files. The behavior is like the old JSON model
									ServerFileIO.importpropertiestojson(serverjarpath=str(serverDirectory),instanceName=str(name),minecraftVersion=str(minecraftversion),isModded=True,create_data_ok=False,legacyBehavior=True)
									self.exportToJSONModel(instanceName=str(name))
									MCSC_Cursor.execute("INSERT INTO Instances_Table (name, minecraftVersion, serverType, targetDirectory) VALUES (?,?,?,?)",(name,minecraftversion,servertype,serverDirectory))
									MCSCDatabase.commit()
									print("[Minerva Server Crafter]: Data has been saved.")
									#Close the database connection
									MCSC_Cursor.close()
									MCSCDatabase.close()
									self.populateInstanceView(self.moddedinstanceView,"",self.modpacksFolder)
									return
						
						else:
							raise MCSCInternalError("Directory not found.")
					else:
						raise MCSCInternalError("Not a valid Server Type.")
				else:
					raise MCSCInternalError("Not a valid minecraft version.")
			else:
				raise MCSCInternalError(f"{name} is already an existing instance.")

		except MCSCInternalError as e:
			ConsoleWindow.displayException(e)
			MCSC_Cursor.close()
			return
	def onModpackLoad_LoadModpack(self):
		#We need ask for the filepath of the zipfile
		target_modpackZipfile = filedialog.askopenfile(parent=self.root,filetypes=[("Curseforge Modpack(*.zip)","*.zip")],defaultextension=".zip",initialdir=str(rootFilepath),title="Select Curseforge Modpack ZIP")
		if target_modpackZipfile == None:
			return
		else:
			#This technically opens the file. We just need the filepath of the zip. So we can just close it programmibly
			modpackPath = target_modpackZipfile.name
			target_modpackZipfile.flush()
			target_modpackZipfile.close()
			if target_modpackZipfile.closed == True:
				#We can load the modpack
				modpackLoading = CurseforgeClass.loadModpack(filepath=str(modpackPath))
				if modpackLoading == 200:
					#Modpack has been sideloaded. We need the name of the modpack
					modpackName = os.path.basename(str(modpackPath))
					modpackName = os.path.splitext(modpackName)
					modpackName = modpackName[0]
					Modpack_Data = {}
					for k1,v1 in Modpack_Data.items():
						for k2,v2 in modpackData.items():
							k1 = k2
							v1 = v2
							Modpack_Data[str(k1)] = str(v1)
					print(Modpack_Data.items())
					os.chdir(str(rootFilepath) + f"/base/sandbox/Instances/Modpacks/{modpackName}")
					#We need to do the first run
					def printLines(process):
						for line in process.stdout:
							print(line)
							time.sleep(0.1)
						returnCode = process.wait()
						print(f"Command exited with the return code {returnCode}")
						return
					firstruncmd = ['java', '@user_jvm_args.txt', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/win_args.txt','nogui','%*']
					firstRunProcess = subprocess.Popen(firstruncmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True,text=True)
					firstRunThread = threading.Thread(target=printLines,args=(firstRunProcess,),name="Server First Run")
					firstRunThread.start()
					returnCode = firstRunProcess.wait()
					firstRunThread.join()
					if returnCode == 0:
						#We can load the properties now
						self.createmoddedInstance()

						self.populateInstanceView(self.moddedinstanceView,"",self.modpacksFolder,"downloads")
					return
	def buttonActionModded_onClickSubmit(self):
		#Get all of the data that was put in
		name = self.create_vanillainstance_instanceNameEntry.get()
		minecraft_version = self.create_vanillainstance_minecraftVersionCombo.get()
		mcServer_Type = self.create_vanillainstance_serverTypeCombo.get()
		target_directory = self.create_vanillainstance_serverDirectoryLabel_directory.cget("text")
		print(name,minecraft_version,mcServer_Type,target_directory)
		
		if mcServer_Type == "Forge":
			pass
		else:
			if mcServer_Type == "Fabric":
				pass
			else:
				if mcServer_Type == "Custom":
					pass

class ConsoleShell(CTkFrame):
	def __init__(self,parent):
		self.parent = parent
		process2 = None
		outputThread = None
		self.pauseEvent = threading.Event()

		self.root = CTkCanvas(self.parent)
		self.root.grid(row=0,column=0,sticky="nsew")
		self.ConsoleCanvas = CTkCanvas(self.root)
		self.ConsoleCanvas.grid(row=0,column=0,sticky="nsew")
		self.ConsoleOut = CTkTextbox(self.ConsoleCanvas, width=400, corner_radius=0,state="disabled",bg_color="black")
		self.ConsoleOut.pack(fill=BOTH,expand=True,anchor="center")
		self.ConsoleOut.tag_config("stderr",foreground="#b22222")
		self.InputCanvas = CTkCanvas(self.root)
		self.InputCanvas.grid(row=1,column=0,sticky="nsew")
		self.ConsoleIn = CTkEntry(self.InputCanvas,placeholder_text="Input a command",bg_color="black")
		self.ConsoleIn.pack(fill=X,ipadx=200,side=LEFT)
		self.SendBtn = CTkButton(self.InputCanvas,text="Send",bg_color="black",command=lambda:self.ServerProcess_OnTransmitInput())
		self.SendBtn.pack(side=RIGHT)
		self.root.rowconfigure(0,weight=1)
		self.root.rowconfigure(1,weight=2)
		self.root.columnconfigure(0,weight=1)

	def SaveConsoleToFile(self,start,end):
		global root_tabs
		'SaveConsoleToFile(startingIndex,EndingIndex) -> File Operation \n \n Saves the Console Shell Text to a log file.'

		root_tabs.set("Console Shell")
		#Get whats all in the Console
		self.updateConsole(END,"[Minerva Server Crafter]: Saving Console Log...")
		self.ConsoleOut.configure(state="normal")
		data = self.ConsoleOut.get(start,end)
		file = filedialog.asksaveasfile(mode='w',defaultextension='.log',filetypes=[("Log File",".log")],confirmoverwrite=True)
		if file is None:
			return
		file.write(data)
		file.close()
		self.ConsoleOut.configure(state="disabled")
		self.updateConsole(END,"[Minerva Server Crafter]: Console Log saved.")
		return
	
	def displayException(self,exception):
		'displayException(exception) -> Exception Trace \n \n Sends any exceptions given from python to the Console Shell instead.'
		self.exceptionDetailData = traceback.extract_tb(exception.__traceback__)
		self.filepath,self.lineNumber,self.functionName,self.line = self.exceptionDetailData[-1]
		self.exceptionDetails = f"[Minerva Server Crafter - ErrorReporting]: [Error-301]\n \n=====BEGINNING OF WALKTHROUGH===== \n \nException Type: {type(exception).__name__} \nFilepath Location: {self.filepath} \nLine Number: {self.lineNumber} \nFunction Name: {self.functionName} \nLine Contents: {self.line}\nMessage: {str(exception)} \n \n=====END OF WALKTHROUGH===== \n \n"
		self.updateConsole(END,self.exceptionDetails)
		traceback.print_exception(exception)
		return

	def updateConsole(self,index,string):
		'updateConsole(index,string) -> Console Output \n \n Prints the given string to the ConsoleShell'
		self.ConsoleOut.configure(state="normal")
		self.ConsoleOut.insert(index,str(string) + '\n')
		self.ConsoleOut.configure(state="disabled")
		self.ConsoleOut.see(END)
		return
	
	def ServerProcess_OnTransmitInput(self):
		'ServerProcess_OnTransmitInput() -> Server Input \n \nPasses input to stdin of the Minecraft Server on its own Thread. \nIf the server isn\'t running, nothing is sent to the subprocess.'
		def SendInput():
			serverRunning = outputThread.is_alive()
			if process2.returncode is None and serverRunning == True:
				inputQuery = str(self.ConsoleIn.get())
				self.updateConsole(END, "[Minerva Server Crafter]: <User-Input>: " + str(inputQuery))
				process2.stdin.write(str(inputQuery))
				process2.stdin.write('\n')  # Add a newline character to simulate pressing Enter
				process2.stdin.flush()
				self.ConsoleIn.delete(0,END)
				for line in process2.stdout:
					self.updateConsole(END, "[Minerva Server Crafter]: <Server-IO>: " + line.strip())

			else:
				self.updateConsole(END, '[Minerva Server Crafter]: Server is not running. Will not proceed')
				self.ConsoleIn.delete(0, END)
				return

		global process2
		global outputThread

		try:
			inputThread = threading.Thread(target=SendInput)
			inputThread.start()
		except SystemExit:
			inputThread.join()
	
	def beginServerProcess(self, instanceName=None, memoryAllocation=False, initialMemory=0, maxMemory=0, isForge=False):
		'Begins the Minecraft Server. If memoryAllocation is True, then memory allocation(measured in MB) for the Java VM is included in building the java command, otherwise its exempted. \n The initialMemory parameter sets the minimum memory, and the maxMemory sets the maxium memory. \n The isForge parameter tells whether or not if the server is a forge server. This is must return true due to how forge is programmed internally.'
	
		def print_output(process):
			for line in process2.stdout:
				self.updateConsole(END,"[Minerva Server Crafter]: <Server-IO>: " + line.strip())
				time.sleep(0.1)
			returnCode = process.wait()
			self.updateConsole(END,"[Minerva Server Crafter]: Command exited with the return code " + str(returnCode))

		global root_tabs
		global rootFilepath
		global process2
		global outputThread
		global MemoryAllocationCap
		global attachedInstance

		root_tabs.set("Console Shell")
		self.killEvent = False
		#We need to do some magic
		instancesDirectory = os.path.join(str(rootFilepath),"/base/sandbox/Instances")
		#Get the instance details
		with open(str(rootFilepath) + "/properties.json","r") as jsonFile:
			datadump = json.load(jsonFile)
			#We need to know if its using the legacy behavior
			instances = datadump["Instances"]
			for category in ["Vanilla","Modded"]:
				for instance in instances[category]:
					isLegacy = instance[instanceName]["legacy-launch"]["forceToDirectory"]
					serverdirectory = instance[instanceName]["legacy-launch"]["serverDirectory"]
			jsonFile.close()

		if isForge == True:
			if isLegacy == True:
				if memoryAllocation == True:
					currentScaledMemory = str(InstalledMemory[1])
					if currentScaledMemory == "GB":
						if operatingSystem == "Windows":
							os.chdir(str(serverdirectory))
							cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/win_args.txt' , '-nogui', '%*']
						else:
							os.chdir(str(serverdirectory))
							cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/unix_args.txt' , '-nogui', '$@']
						#We need to scale the command so it measures the values in GB
						#cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '-jar', str(selectedJar), '-nogui']
					if currentScaledMemory == "MB":
						#We need to scale the command so it measures the values in MB
						#cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '-jar', str(selectedJar), '-nogui']
						if operatingSystem == "Windows":
							os.chdir(str(serverdirectory))
							cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/win_args.txt' , '-nogui', '%*']
						else:
							os.chdir(str(serverdirectory))
							cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/unix_args.txt' , '-nogui', '$@']
			if isLegacy == False:
				selectedmoddedInstance = os.path.join(str(instancesDirectory),f"/Modpacks/{instanceName}")
				#We need to get some instance information
				if memoryAllocation == True:
					currentScaledMemory = str(InstalledMemory[1])
					if currentScaledMemory == "GB":
						#We need to either point to the run.bat or the run.sh file depending on what the operating system is
						if operatingSystem == "Windows":
							os.chdir(str(selectedmoddedInstance))
							cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/win_args.txt' , '-nogui', '%*']
						else:
							os.chdir(str(selectedmoddedInstance))
							cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/unix_args.txt' , '-nogui', '$@']
						#We need to scale the command so it measures the values in GB
						#cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '-jar', str(selectedJar), '-nogui']
					if currentScaledMemory == "MB":
						#We need to scale the command so it measures the values in MB
						#cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '-jar', str(selectedJar), '-nogui']
						if operatingSystem == "Windows":
							os.chdir(str(selectedmoddedInstance))
							cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/win_args.txt' , '-nogui', '%*']
						else:
							os.chdir(str(selectedmoddedInstance))
							cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '@libraries/net/minecraftforge/forge/1.19.2-43.2.0/unix_args.txt' , '-nogui', '$@']
		else:
			if isLegacy == True:
				os.chdir(serverdirectory)
				if memoryAllocation == True:
					currentScaledMemory = str(InstalledMemory[1])
					if currentScaledMemory == "GB":
						cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '-jar', 'server.jar', '-nogui']
					if currentScaledMemory == "MB":
						cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '-jar', 'server.jar', '-nogui']
				else:
					cmd = ['java', '-jar', 'server.jar', '-nogui']
			if isLegacy == False:
				selectedvanillainstance = os.path.join(str(instancesDirectory),str(instanceName))
				os.chdir(selectedvanillainstance)
				if memoryAllocation == True:
					currentScaledMemory = str(InstalledMemory[1])
					if currentScaledMemory == "GB":
						cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '-jar', 'server.jar', '-nogui']
					if currentScaledMemory == "MB":
						cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '-jar', 'server.jar', '-nogui']
				else:
					cmd = ['java', '-jar', 'server.jar', '-nogui']
		self.updateConsole(END,"[Minerva Server Crafter]: Using java command: " + str(cmd))
		time.sleep(0.1)
		if isLegacy == True:
			self.updateConsole(END,"[Minerva Server Crafter]: Enforcing Server Directory")
		if isLegacy == False:
			self.updateConsole(END, "[Minerva Server Crafter]: Ignoring Server Directory")
		#Update the server.properties file
		self.updateConsole(END,"[Minerva Server Crafter]: Pre-Server Startup Phase: Updating server.properties...")
		time.sleep(5)
		if isForge == True:
			if isLegacy == True:
				ServerFileIO.convertInstancePropertiestoPropertiesFile(instanceName=str(instanceName),filepath=str(serverdirectory),bypassSaveLocation=True)
			if isLegacy == False:
				ServerFileIO.convertInstancePropertiestoPropertiesFile(instanceName=str(instanceName),filepath=str(selectedmoddedInstance),bypassSaveLocation=True)
		if isForge == False:
			if isLegacy == True:
				ServerFileIO.convertInstancePropertiestoPropertiesFile(instanceName=str(instanceName),filepath=str(serverdirectory),bypassSaveLocation=True)
			if isLegacy == False:
				ServerFileIO.convertInstancePropertiestoPropertiesFile(instanceName=str(instanceName),filepath=str(selectedvanillainstance),bypassSaveLocation=True)
		#Update the JSON Bans
		self.updateConsole(END,"[Minerva Server Crafter]: Pre-Server Startup Phase: Updating JSON Bans[1/2]...")
		time.sleep(5)
		ServerFileIO.exportplayerBansToJSON()
		self.updateConsole(END,"[Minerva Server Crafter]: Pre-Server Startup Phase: Updating JSON Bans[2/2]...")
		time.sleep(5)
		ServerFileIO.exportIPBansToJSON()
		#Update Whitelist
		self.updateConsole(END,"[Minerva Server Crafter]: Pre-Server Startup Phase: Update Whitelist...")
		time.sleep(5)
		ServerFileIO.exportWhitelistfromDatabase()
		# All done!
		self.updateConsole(END,"[Minerva Server Crafter]: Starting Server...")
		# Launch the server
		try:
			#Run the command
			process2 = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.PIPE,text=True)
			outputThread = threading.Thread(target=print_output,args=(process2,))
			outputThread.start()

		except Exception as e:
			# Handle exceptions
			self.displayException(e)
		
		
class ResourcePackWindow():
	def closeWindow(self): #original, I know xD
		self.root.grab_release()
		self.root.destroy()
		return
	
	def updateResourcePackValues(self):
		global ConsoleWindow
		global root_tabs

		root_tabs.set("Console Shell")
		#We need to update the values for the resource pack information
		MinecraftServerProperties.update({'resource-pack': str(self.resourcePackEntry.get())})
		MinecraftServerProperties.update({'resource-pack-sha1': str(self.resourcePackSHA1StringVar.get())})
		ConsoleWindow.updateConsole(END,"<Minerva Server Crafter>: Resource Pack Values Updated Successfully.")
		self.closeWindow()
		return
	
	def ResourcePackCalling_VerifyupdateWindow(self,url=None):
		#We need to generate the sha1 and confirm if its valid
		self.Hashes = ServerFileIO.ResourcePackCall_generateSHA1(url=url)
		self.fileHash = self.Hashes[0]
		self.integrityCheck = self.Hashes[4]
		if self.integrityCheck == True:
			#Valid Hash
			self.resourcePackSHA1StringVar.set(self.fileHash)
			self.resourcePackVerifier.configure(text="\u2714\uFE0F",text_color="green")
			self.applybtn.configure(state=NORMAL)
			return
		if self.integrityCheck == False:
			#Invalid Hash
			self.resourcePackVerifier.configure(text="\u274C",text_color="red")
			return
		
	def getHash(self,url=None):
		#We need access of the generateSHA1 tuple in the ServerFileIO class
		self.hash = ServerFileIO.ResourcePackCall_generateSHA1(url=url)
		return self.hash
	def __init__(self,parent):
		self.parent = parent

		#Create widget
		
		self.root = CTkToplevel()
		self.root.title("Resource Pack Configuration")
		self.parent.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/ui/minecraftservercrafter.ico"))
		self.root.geometry("450x90")
		self.root.grid_columnconfigure((0,1,2,3,4,5,6,7,8),weight=1)
		self.root.grid_rowconfigure(0,weight=1)
		self.root.grab_set()
		self.folderHashes = {}
		self.resourcepackStringVar = StringVar(value=MinecraftServerProperties.get('resource-pack'))
		self.resourcePackLabel = CTkLabel(self.root,anchor=W,text="Resource Pack URL: ")
		self.resourcePackLabel.grid(row=0,column=0,sticky=W)
		self.resourcePack_tip = CTkToolTip(self.resourcePackLabel,"server.properties setting: 'resource-pack'")
		self.resourcePackEntry = CTkEntry(self.root,textvariable=self.resourcepackStringVar)
		self.resourcePackEntry.grid(row=0,column=1,columnspan=9,sticky=EW)
		self.resourcePackEntry_tip = CTkToolTip(self.resourcePackEntry,"Usage: You must put in a valid direct download link(Curseforge, Dropbox, Mediafire, etc),\notherwise the SHA-1 Hash for the Resource Pack won't generate, or be invalid.")
		self.resourcePackSHA1Label = CTkLabel(self.root,anchor=W,text="Resource Pack SHA-1: ")
		self.resourcePackSHA1Label.grid(row=1,column=0,sticky=W)
		self.resourcePackLabel_tip = CTkToolTip(self.resourcePackSHA1Label,"server.properties setting: 'resource-pack-sha1'")
		self.resourcePackSHA1StringVar = StringVar(value=MinecraftServerProperties.get('resource-pack-sha1'))
		self.resourcePackSHA1 = CTkLabel(self.root,anchor=W,text=" ",textvariable=self.resourcePackSHA1StringVar)
		self.resourcePackSHA1.grid(row=1,column=1,sticky=W)
		self.resourcePackVerifier = CTkLabel(self.root,anchor=W,text=" ",font=("Times New Roman Bold",24))
		self.resourcePackVerifier.grid(row=2,column=1,columnspan=2,sticky=E)
		self.verifybtn = CTkButton(self.root,text="Generate & Verify SHA-1",command=lambda:self.ResourcePackCalling_VerifyupdateWindow(url=self.resourcePackEntry.get()))
		self.verifybtn.grid(row=2,column=1,sticky=W)
		self.applybtn = CTkButton(self.root,text="Apply Settings & Close",state=DISABLED,command=lambda:self.updateResourcePackValues())
		self.applybtn.grid(row=2,column=0,sticky=W)
		return

class MOTDWindow():
	def updateProperties(self):
		self.CURRENTtext = self.MOTDTextbox.get("1.0",END)
		MinecraftServerProperties['motd'] = str(self.CURRENTtext)
		self.root.grab_release()
		self.root.destroy()
		return
	
	def characterLimit(self):
		self.CharCap = 59
		self.currentText = self.MOTDTextbox.get("1.0","end-1c")
		if len(self.currentText) >= self.CharCap:
			self.sliceVal = int(self.CharCap) - 1
			self.trimmedText = self.currentText[:int(self.sliceVal)]
			self.MOTDTextbox.delete("1.0",END)
			self.MOTDTextbox.insert(END,str(self.trimmedText))
			return

	def characterLimitevent(self,event):
		self.CharCap = 59
		self.currentText = self.MOTDTextbox.get("1.0","end-1c")
		if len(self.currentText) >= self.CharCap:
			self.sliceVal = int(self.CharCap) - 1
			self.trimmedText = self.currentText[:int(self.sliceVal)]
			self.MOTDTextbox.delete("1.0",END)
			self.MOTDTextbox.insert(END,str(self.trimmedText))
			return
	
	def updateCounter_event(self,event):
		self.textCurrent = self.MOTDTextbox.get("1.0","end-1c")
		self.charCounter.configure(text=f"{len(self.textCurrent)}/59 Characters Used")
		return
	
	def updateCounter(self):
		self.currentText = self.MOTDTextbox.get("1.0","end-1c")
		self.charCounter.configure(text=f"{len(self.currentText)}/59 Characters Used")
		return
	
	def newline(self):
		self.CurrentText = self.MOTDTextbox.get("1.0","end-1c")
		self.MOTDTextbox.delete("1.0",END)
		self.MOTDTextbox.insert(END,str(self.CurrentText) + "\\n")
		self.characterLimit()
		self.updateCounter()
		return
	
	def inserttextFormat(self, format):
		# Check for the format and insert the corresponding code
		if format == "Bold":
			self.MOTDTextbox.insert(END, "\\u00A7l")
			self.characterLimit()
			self.updateCounter()
		elif format == "Obfuscated":
			self.MOTDTextbox.insert(END, "\\u00A7k")
			self.characterLimit()
			self.updateCounter()
		elif format == "Strikethrough":
			self.MOTDTextbox.insert(END, "\\u00A7m")
			self.characterLimit()
			self.updateCounter()
		elif format == "Underline":
			self.MOTDTextbox.insert(END, "\\u00A7n")
			self.characterLimit()
			self.updateCounter()
		elif format == "Italics":
			self.MOTDTextbox.insert(END, "\\u00A7o")
			self.characterLimit()
			self.updateCounter()
		elif format == "Reset":
			self.MOTDTextbox.insert(END, "\\u00A7r")
			self.characterLimit()
			self.updateCounter()
		return
	
	def __init__(self,parent):
		self.parent = parent

		#Create Widget
		self.root = CTkToplevel()
		self.root.title("Message of the Day Configuration")
		self.parent.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/ui/minecraftservercrafter.ico"))
		self.root.geometry("545x110")
		self.root.grab_set()
		self.FormatingFrame = CTkFrame(self.root)
		self.FormatingFrame.grid(row=0,column=0,columnspan=6,rowspan=2)
		self.MOTDStringVar = StringVar(value=MinecraftServerProperties.get("motd"))
		self.MOTDTextbox = CTkTextbox(self.FormatingFrame,width=180,height=47,fg_color="#414141")
		self.MOTDTextbox.pack(fill=BOTH,expand=True,side=BOTTOM)
		self.MOTDTextbox.insert(END,self.MOTDStringVar.get())
		self.boldbtn = CTkButton(self.FormatingFrame,text="Bold",width=30,command=lambda:self.inserttextFormat("Bold"))
		self.boldbtn.pack(side=TOP,anchor=W,padx=1)
		self.obfuscatedbtn = CTkButton(self.FormatingFrame,text="Obfuscated",width=70,command=lambda:self.inserttextFormat("Obfuscated"))
		self.obfuscatedbtn.pack(before=self.boldbtn,side=RIGHT,padx=1)
		self.strikethroughbtn = CTkButton(self.FormatingFrame,text="Strikethrough",width=80,command=lambda:self.inserttextFormat("Strikethrough"))
		self.strikethroughbtn.pack(before=self.obfuscatedbtn,side=RIGHT,padx=1)
		self.underlinedbtn = CTkButton(self.FormatingFrame,text="Underlined",width=70,command=lambda:self.inserttextFormat("Underline"))
		self.underlinedbtn.pack(before=self.strikethroughbtn,side=RIGHT,padx=1)
		self.italicsbtn = CTkButton(self.FormatingFrame,text="Italics",width=70,command=lambda:self.inserttextFormat("Italics"))
		self.italicsbtn.pack(before=self.underlinedbtn,side=RIGHT,padx=1)
		self.resetFormattingbtn = CTkButton(self.FormatingFrame,width=90,text="Reset Formatting",command=lambda:self.inserttextFormat("Reset"))
		self.resetFormattingbtn.pack(before=self.italicsbtn,side=RIGHT,padx=1)
		self.newlinebtn = CTkButton(self.FormatingFrame,width=50,text="New Line",command=self.newline)
		self.newlinebtn.pack(before=self.resetFormattingbtn,side=RIGHT,padx=1)
		self.applybtn = CTkButton(self.root,text="Apply & Close",command=self.updateProperties)
		self.applybtn.grid(row=2,column=5,sticky=E,pady=4)
		self.initalCount = self.MOTDTextbox.get("1.0","end-1c")
		self.charCounter = CTkLabel(self.root,text=f"{len(self.initalCount)}/59 Characters Used")
		self.charCounter.grid(row=2,column=0,sticky=W)

		self.MOTDTextbox.bind("<Key>",self.characterLimitevent)
		self.MOTDTextbox.bind("<KeyRelease>",self.updateCounter_event)
		
		return

#Console Shell Tab
ConsoleFrame = CTkFrame(root_tabs.tab("Console Shell"))
ConsoleWindow = ConsoleShell(ConsoleFrame)
ConsoleFrame.grid(row=0,column=0,sticky="nsew")


#Minerva Server Crafter Tab
MinecraftServerCrafterTabFrame = CTkFrame(root_tabs.tab("Minerva Server Crafter Settings"))
MinecraftServerCrafterTabFrame.pack(fill=BOTH,expand=True,anchor=W)
InstanceSelectViewer = CTkButton(MinecraftServerCrafterTabFrame,text="View Instances",command=MCSC_Framework.onMainWindow_openInstanceSelect)
InstanceSelectViewer.grid(row=0,column=0)
launchServerBtn = CTkButton(MinecraftServerCrafterTabFrame,text="Launch Server",command=ConsoleWindow.beginServerProcess,state=DISABLED)
launchServerBtn.grid(row=1,column=0,pady=5)
saveConsoleLogbtn = CTkButton(MinecraftServerCrafterTabFrame,text="Export Console Shell",command=lambda:ConsoleWindow.SaveConsoleToFile(1.0,END))
saveConsoleLogbtn.grid(row=2,column=0,sticky=N)
aboutbtn = CTkButton(MinecraftServerCrafterTabFrame,text="Licenses",command=MCSC_Framework.onMainWindow_openAbout)
aboutbtn.grid(row=3,column=0,sticky=N)
memoryAllocatedBool = BooleanVar(value=False)
MemoryAllocation = CTkCheckBox(MinecraftServerCrafterTabFrame,text="Allocate Server Memory",variable=memoryAllocatedBool,onvalue=True,offvalue=False)
MemoryAllocation.grid(row=0,column=1)
#Memory Allocation Constraints
MemoryAllocationFrame = CTkFrame(MinecraftServerCrafterTabFrame)
MemoryAllocationFrame.grid(row=1,column=1,rowspan=4)
def showValMinimum(value):
	MemoryAllocationMiniumValueToolTip.configure(message=int(value))
#We need to set the intvar
MinimumMemoryInt = IntVar(value=currentMemoryMinimum)
MemoryAllocationMiniumLabel = CTkLabel(MemoryAllocationFrame,text="Minimum Memory Allocated")
MemoryAllocationMiniumLabel.grid(row=0,column=0,pady=4)
MemoryAllocationMiniumSlider = CTkSlider(MemoryAllocationFrame,state=DISABLED,from_= int(MiniumMemory),to= int(MemoryAllocationCap),command=showValMinimum)
MemoryAllocationMiniumSlider.grid(row=1,column=0)
MemoryAllocationMiniumSlider.set(MinimumMemoryInt.get())
#We need to show the value of the Slider
MemoryAllocationMiniumValueToolTip = CTkToolTip(MemoryAllocationMiniumSlider,message=str(MinimumMemoryInt.get()))
def showValMax(value):
	MemoryAllocationMaximumTooltip.configure(message=int(value))
#Set the intvar
MaximumMemoryInt = IntVar(value=currentMemoryMax)
MemoryAllocationMaximumLabel = CTkLabel(MemoryAllocationFrame,text="Maximum Memory Allocation")
MemoryAllocationMaximumLabel.grid(row=2,column=0,pady=4)
MemoryAllocationMaximumSlider = CTkSlider(MemoryAllocationFrame,state=DISABLED,from_= int(MemoryAllocationMiniumSlider.get()),to= int(MemoryAllocationCap),command=showValMax)
MemoryAllocationMaximumSlider.grid(row=3,column=0,pady=4)
MemoryAllocationMaximumSlider.set(MaximumMemoryInt.get())
#We need to show the value of the slider
MemoryAllocationMaximumTooltip = CTkToolTip(MemoryAllocationMaximumSlider,message=str(MaximumMemoryInt.get()))
#We need to toggle widgets when the checkbox is ticked or not
def updateWidgets():
	CheckboxIsTicked = memoryAllocatedBool.get()
	if CheckboxIsTicked == False:
		#Memory isnt getting allocated
		#Disable the sliders
		MemoryAllocationMiniumSlider.configure(state=DISABLED)
		MemoryAllocationMaximumSlider.configure(state=DISABLED)
		#Set the launch server button command
		launchServerBtn.configure(command=ConsoleWindow.beginServerProcess)
		return
	if CheckboxIsTicked == True:
		#Memory is getting allocated
		#Enable the sliders
		MemoryAllocationMiniumSlider.configure(state=NORMAL)
		MemoryAllocationMaximumSlider.configure(state=NORMAL)
		#Set the launch server button command
		launchServerBtn.configure(command=lambda:ConsoleWindow.beginServerProcess(memoryAllocation=True,initialMemory=int(MinimumMemoryInt.get()),maxMemory=int(MaximumMemoryInt.get())))
		return
MemoryAllocation.configure(command=updateWidgets)

#Players List

#Whitelist Tab

whitelistTab = CTkFrame(root_tabs.tab("Whitelisting"))
whitelistTab.grid(row=0,column=0,sticky=N,padx=20)
whitelistedBool = BooleanVar(value=MinecraftServerProperties.get('white-list'))
isWhitelisted = CTkCheckBox(whitelistTab,text="Enable Whitelisting",variable=whitelistedBool,onvalue=True,offvalue=False)
isWhitelisted.grid(row=0,column=0,sticky=W,padx=3)
strictedWhitelistBool = BooleanVar(value=MinecraftServerProperties.get('enforce-whitelist'))
strictedWhitelistCheck = CTkCheckBox(whitelistTab,text="Enforced Whitelisting",variable=strictedWhitelistBool,onvalue=True,offvalue=False)
strictedWhitelistCheck.grid(row=0,column=1,sticky=W,padx=3,pady=3)
WhitelistFrame = CTkFrame(root_tabs.tab("Whitelisting"))
WhitelistFrame.grid(row=0,column=2,rowspan=7,padx=30)
WhitelistListbox = CTkListbox(WhitelistFrame)
WhitelistListbox.pack(fill=BOTH,expand=True,side=BOTTOM)
addPlayerbtn = CTkButton(root_tabs.tab("Whitelisting"),text="Add Player",command=ServerFileIO.askAddWhitelistPlayer)
addPlayerbtn.grid(row=1,column=0,sticky=E)
removePlayerbtn = CTkButton(root_tabs.tab("Whitelisting"),text="Remove Player",command=ServerFileIO.removeFromWhitelist)
removePlayerbtn.grid(row=2,column=0,sticky=E)

#Banning tab

BansTab = CTkScrollableFrame(root_tabs.tab("Banned Players"))
BansTab.pack(fill=BOTH,expand=True,anchor=W)
BannedPlayerNamesFrame = CTkFrame(BansTab)
BannedPlayerNamesFrame.grid(row=0,column=0,rowspan=5,sticky=W)
BannedPlayerNamesListbox = CTkListbox(BannedPlayerNamesFrame)
BannedPlayerNamesListbox.pack(fill=Y,expand=True,side=BOTTOM)
BannedPlayerNamesLabel = CTkLabel(BannedPlayerNamesFrame,text="Banned Players")
BannedPlayerNamesLabel.pack(side=TOP)
BannedIPsFrame = CTkFrame(BansTab)
BannedIPsFrame.grid(row=0,column=2,rowspan=5,sticky=W)
BannedIPsListbox = CTkListbox(BannedIPsFrame)
BannedIPsListbox.pack(fill=Y,expand=True,side=BOTTOM)
BannedIPsLabel = CTkLabel(BannedIPsFrame,text="Banned IPs")
BannedIPsLabel.pack(side=TOP)
BannedTab_ActionPanel = CTkFrame(BansTab)
BannedTab_ActionPanel.grid(row=0,column=1,rowspan=5,sticky=W)
BannedByPlayerNamebtn = CTkButton(BannedTab_ActionPanel,text="Ban by Name",command=ServerFileIO.askBanPlayerName)
BannedByPlayerNamebtn.grid(row=0,column=0)
BanByIPbtn = CTkButton(BannedTab_ActionPanel,text="Ban by IP Address",command=ServerFileIO.askIPBan)
BanByIPbtn.grid(row=1,column=0,sticky=W)
pardonPlayerNamebtn = CTkButton(BannedTab_ActionPanel,text="Pardon by Name",command=ServerFileIO.PardonName)
pardonPlayerNamebtn.grid(row=2,column=0,sticky=W)
pardonIPbtn = CTkButton(BannedTab_ActionPanel,text="Pardon by IP Address",command=ServerFileIO.PardonIP)
pardonIPbtn.grid(row=3,column=0,sticky=W)


shellVersion = "Version: " + str(VersionNumber) + "\n"
lastConfig = ServerFileIO.getLastConfig()

MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting","disabled")
MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players","disabled")

ConsoleWindow.updateConsole(END,"Minerva Server Crafter Lite - Release Build \n" + str(shellVersion))
ConsoleWindow.updateConsole(END,"To begin, go to Minerva Server Crafter Settings > Attach Server Jar \n")

ServerFileIO.loadJSONProperties(instanceName=str(lastConfig))
MCSCUpdater.runUpdates()

#test workspace
#test = CurseforgeClass.loadModpack(filepath=None,modpackName="FXNT Create")
modlist = ['item1','item2','item3']
modlist = tuple(modlist)
test = ServerFileIO.addInstancetoJSON(name="test",serverType="fabric",isModded=True,modlist=modlist,modloaderversion="0.15.3",minecraftversion="1.20.2")

if os.path.isfile(str(rootFilepath) + "/base/sandbox/build/BuildTools/BuildTools.jar") == False:
	MCSCDatabase = sqlite3.connect("mcsc_data.db")
	MCSC_Cursor = MCSCDatabase.cursor()
	print("[Minerva Server Crafter API - SpigotBaseClass]: BuildTools is missing! Obtaining...")
	#We need to fetch the last successful build from the database table
	MCSC_Cursor.execute("SELECT Url FROM BuildTools_SuccessfulBuildVerified_Table ORDER BY CAST(BuildID AS INTEGER) DESC LIMIT 1")
	latestBuild = MCSC_Cursor.fetchone()
	if latestBuild:
		latestBuild_url = latestBuild[0] + "artifact/target/BuildTools.jar"
		MCSCUpdater.SpigotBaseClass.getBuildTools(url=str(latestBuild_url))
		MCSC_Cursor.close()
		MCSCDatabase.close()

#Mainloop
root.mainloop()
