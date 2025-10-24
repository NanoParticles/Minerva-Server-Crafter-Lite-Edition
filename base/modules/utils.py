import psutil
import math
import os
import sqlite3
import socket
from customtkinter import *
import requests
import contextlib
import json
import logging
import traceback
import shutil
import subprocess
import threading
import nbtlib
from base.modules.kernel import MCSCKernelCore
from zipfile import *
outputLog_utils = MCSCKernelCore(module="Utilities")

#Configure Logger
MCSCLogger = logging.getLogger("MCSC Error Logging")
MCSCLogger.setLevel(level=logging.ERROR)
MCSCHandler = logging.StreamHandler()
MCSCFormatting = logging.Formatter("[%(asctime)s] [%(levelname)s]: %(message)s")
MCSCHandler.setFormatter(fmt=MCSCFormatting)
MCSCLogger.addHandler(hdlr=MCSCHandler)

class MCSCInternalError(Exception):
	'Base class for handling any errors'
	def __init__(self,msg,errors=None):
		super().__init__("[Minerva Server Crafter API - Error Reporting]: " + str(msg))
		MCSCLogger.error(msg=str(msg))
		self.errors = errors
		if self.errors is not None:
			trace = ''.join(traceback.format_exception(type(self.errors),self.errors,self.errors.__traceback__))
			MCSCLogger.error("Chained Exception:\n" + trace + f"\n[{self.__class__.__name__}]: {msg}")
			raise self from self.errors
		else:
			trace = traceback.format_exc()
			if trace and "NoneType: None" not in trace:
				MCSCLogger.error("Current Exception context:\n" + trace)
			else:
				MCSCLogger.setLevel(logging.WARNING)
				MCSCLogger.warning("No active exceptions detected.")
				MCSCLogger.setLevel(logging.ERROR)

class SoftwareSpec():
	'Extra Utilities thats handled under Software'

	@contextlib.contextmanager
	def changeDir(path=None):
		'Temporary Change the working directory'
		if path is not None:
			originalDir = os.getcwd()
			os.chdir(path)
			try:
				yield
			finally:
				os.chdir(originalDir)
				return

class HardwareSpec():
	'Extra Utilities for Memory Management'
	def __init__(self):
		from base.modules.kernel import MCSCKernelCore
		self.InstalledMemory = HardwareSpec.getByteSizeInt(psutil.virtual_memory().total)
		self.ScaledMem = self.InstalledMemory[0]
		self.roundedMem = round(self.ScaledMem)
		self.truncatedMem = math.trunc(self.roundedMem)
		self.physicalMem = int(self.truncatedMem)
		self.outputLog_HardwareSpec = MCSCKernelCore(module="Utilities",logic="Hardware Specifications")
		if self.InstalledMemory[1] == "MB":
			#Scale it in Megabytes
			self.MemoryAllocationCap = int(self.truncatedMem) - 5120
			#For a decent server, the minium amount of memory is 2GB(2048)
			self.MiniumMemory = 2048
		if self.InstalledMemory[1] == "GB":
			#Scale it in Gigabytes
			self.MemoryAllocationCap = int(self.truncatedMem) - 5
			self.MiniumMemory = 2

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
	def decodeUUID():
		#We need to fetch the internal data
		from base.modules.config import rootFilepath
		SoftwareSpec.changeDir(rootFilepath)
		MCSCDatabase = sqlite3.connect("mcsc_data.db")
		MCSC_Cursor = MCSCDatabase.cursor()
		MCSC_Cursor.execute("SELECT * FROM mcscInternalData")
		dataDump = MCSC_Cursor.fetchall()
		dataDump = str(dataDump[1][0])
		#decode it from bytes
		hexval = dataDump.split()
		bytestring = bytes(int(h,16) for h in hexval)
		result = bytestring.decode('utf-8')
		return result
	
	def debugInfo(self):
		CurseKey = CurseforgeClass.decodeByteSecret()
		self.outputLog_HardwareSpec.info_print(f"Curseforge API Key: {CurseKey}")
		appid = HardwareSpec.decodeUUID()
		self.outputLog_HardwareSpec.info_print(f"App_ID : {appid}")
		return
	
class InternetHost():
	'Extra Utilities for Internet Connection'
	global Console
	def __init__(self,url:str = None):
		from base.modules.kernel import MCSCKernelCore
		self.url = url
		self.outputLog_internetConnection = MCSCKernelCore(module="Utilities",logic="Internet Connection")
		return

	def connectionCheck(self):
		'Creates a Socket Connection. This is primarily used for checking if the local host is connected to the internet. \n If the socket connection is successfully connected, then it returns true. Otherwise, an exception is raised.'
		try:
			result = socket.create_connection(('8.8.8.8', 53),timeout=8)
			result.close()
			return True
		except (OSError,ExceptionGroup) as e:
			self.outputLog_internetConnection.error_print(e)
			Console.displayException(e)
			return False

	def getIPV4(self):
		'Returns the IP Address of the Local Host Computer'
		try:
			if self.connectionCheck() == True:
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
				self.outputLog_internetConnection.error_print("Unable to connect to the Internet(REASON: No Connection)")
				return
		except socket.error as e:
			self.outputLog_internetConnection.error_print("Unable to connect to the Internet(REASON: socket error)")
			raise MCSCInternalError(msg="Unable to connect to the Internet(REASON: socket error)",errors=e)
		
	def getPublicIP():
		'getPublicIP() -> Public IP Address \n \n Returns the Public IP Address of the Local Host'
		try:
			public_ip = requests.get('https://api.ipify.org',timeout=5)
			if public_ip.status_code == 200:
				return public_ip.text.strip()
		except requests.RequestException as e:
			raise MCSCInternalError(msg="Failed to get Public IP.(REASON: Request Exception raised)")
	
	def isShortenedURL(self,timeout=5):
		try:
			response = requests.head(url=self.url,allow_redirects=False,timeout=timeout)
			return response.status_code in (301,302,303,307,308)
		except requests.ConnectionError and Exception:
			return False

class ModpackIndexClass():
	def getCurseID(modpackName=None):
		outputLog_utils.info_print("Processing Modpack...")
		response_url = f"https://www.modpackindex.com/api/v1/modpacks?limit=3&name={modpackName}"
		response = requests.get(url=response_url)
		if response.status_code == 200:
			outputLog_utils.info_print("Modpack Found.")
			resultsData = response.json()
			results_raw = resultsData['data']
			for item in results_raw:
				name = item['name']
				if name == str(modpackName):
					target_ID = item['curse_info']['curse_id']
					break
				else:
					continue
			
			return target_ID

class CurseforgeClass():
	'Utility for handling the Curseforge API'
	def __init__(self):
		self.profiles = []
		self.clientmods = []
		self.servermods = []
		self.resourcepacks = []
		self.gameversion = None
		self.outputLog_curseforge = MCSCKernelCore(module="Utilities",logic="Curseforge API")
		return
	
	@staticmethod
	def decodeByteSecret() -> str:
		'Decodes the secret to a readable string.'
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/properties.json","r") as jsonFile:
			data_dump = json.load(jsonFile)
			jsonFile.close()
		#Traverse to the curseforge branch
		curseData = data_dump['config']['curseforge']
		byteSecret = curseData['secret']
		if byteSecret is None:
			return None
		else:
			result = bytes.fromhex(byteSecret).decode("ascii")
			return result
	
	def encodeByteSecret(secret=None):
		#Encode the secret
		secret_raw = str(secret)
		result = secret_raw.encode("ascii").hex()
		return result

	def scanForInstances(self):
		from base.modules.config import curseforge_instancePath
		self.outputLog_curseforge.info_print("Scanning Profiles...")
		#We need to scan for the Instances
		for r,d,f in os.walk(curseforge_instancePath):
			for dir_ in d:
				target = os.path.join(r,dir_)
				if os.path.isdir(str(target)):
					curseforge_instanceName = os.path.basename(target)
					self.profiles.append(curseforge_instanceName)
					continue
			break
		return
	
	def getCurseData(self,id=None):
		self.outputLog_curseforge.info_print("Fetching Curse Data by ID...")
		headers = {'Accept': 'application/json', 'x-api-key': str(self.decodeByteSecret())}
		url = f'https://api.curseforge.com/v1/mods/{id}'

		response = requests.get(url=str(url),headers=headers)
		if response.status_code == 200:
			target_data = response.json()
			target = target_data['data']
			self.outputLog_curseforge.info_print("No issues occured while fetching Curse Data.")
			return target
	
	def getdescription(self,id=None):
		#We need the mod description
		key = self.decodeByteSecret()
		headers = {'Accept':'application/json','x-api-key': str(key)}
		outputLog_utils.info_print("Fetching description...")
		url = f'https://api.curseforge.com/v1/mods/{id}/description'
		response = requests.get(url=url,headers=headers)
		if response.status_code == 200:
			jsonData = response.json()
			result = jsonData['data']
			outputLog_utils.info_print("No issues occured while fetching description.")
			return result

	def getModloaderData(self,curseforgeProfile=None):
		from base.modules.config import curseforge_instancePath,ServerType
		from base.modules.server import ServerVersion_Control
		if curseforgeProfile in self.profiles:
			#We need to get the instance data that the curseforge program outputs
			profilePath = os.path.join(str(curseforge_instancePath), str(curseforgeProfile))
			with open(str(profilePath) + "/minecraftinstance.json","r") as curseData:
				dataDump = json.load(curseData)
				curseData.close()
			curse_dataRaw = dataDump['baseModLoader']
			modloaderName = curse_dataRaw['name']
			modloadertype,version1,version2 = str(modloaderName).split("-")
			modloaderData = (modloadertype,version1,version2)
			if str(modloaderData[0]) in ServerType:
				#lets take it a step further
				try:
					if ServerVersion_Control.isVersion(parseVersion=str(modloaderData[1])):
						#Its a minecraft version
						minecraftVersion = str(modloaderData[1])
						servertypeVersion = str(modloaderData[2])
					elif ServerVersion_Control.isVersion(parseVersion=str(modloaderData[2])):
						minecraftVersion = str(modloaderData[2])
						servertypeVersion = str(modloaderData[1])
				finally:
					servertype = str(modloaderData[0])
					#Build the tuple
					targetTuple = (str(servertype),str(minecraftVersion),str(servertypeVersion))
					return targetTuple
			else:
				#Might be a unsupported type. Just return the modloader data
				return modloaderData
	
	def getCurseprofileData(self,curse_profile=None):
		from base.modules.config import curseforge_instancePath
		target = str(curse_profile)
		path = os.path.join(curseforge_instancePath,target,"minecraftinstance.json")
		with open(path,"r",encoding="utf-8") as curseProfileJSON:
			profileData = json.load(curseProfileJSON)
			curseProfileJSON.close()
		return profileData

	def parseID(self,targetType=None,objectID=None):
		'Parses Curseforge API using the given ID\n\nTarget Types: get-object-data,get-description'
		headers = {'Accept':'application/json','x-api-key': self.decodeByteSecret()}
		for target in ['get-object-data','get-description']:
			if targetType in target:
				try:
					if target == 'get-object-data':
						response = requests.get(url=f"https://api.curseforge.com/v1/mods/{objectID}",headers=headers)
					elif target == 'get-description':
						response = requests.get(url=f"https://api.curseforge.com/v1/mods/{objectID}/description",headers=headers)
				except requests.RequestException as e:
					raise MCSCInternalError(msg="Failed to resolve curseforge response type",errors=e)
		if response.status_code == 200:
			resultTarget_raw = response.json()
			resultTarget = resultTarget_raw['data']
			return resultTarget
		else:
			raise MCSCInternalError(msg=f"Unable to parse curseforge api. Request Code: {response.status_code}")
	
	def setListing(self,clientmods=None,servermods=None,resourcepacks=None,mc_version=None):
		if isinstance(clientmods,list):
			if isinstance(mc_version,str):
				self.gameversion = mc_version
				if isinstance(servermods,list):
					self.clientmods = clientmods
					self.servermods = servermods
					if resourcepacks is not None and isinstance(resourcepacks,list):
						self.resourcepacks = resourcepacks
					return
				else:
					raise MCSCInternalError(msg=f"Server Mods parameter expected list, but got {type(servermods)}")
			else:
				raise MCSCInternalError(msg=f"Minecraft Version parameter expected string, but got {type(mc_version)}")
		else:
			raise MCSCInternalError(msg=f"Client Mods parameter expected list, but got {type(clientmods)}")
	
	def getListing(self,modType=None):
		if modType in ["client","server","resource-packs"]:
			if modType == "client":
				return self.clientmods
			elif modType == "server":
				return self.servermods
			elif modType == "resource-packs":
				return self.resourcepacks
		else:
			raise MCSCInternalError(msg=f"modType parameter expected [client, server], but got {modType}")
	
	def clearListing(self):
		self.clientmods = []
		self.servermods = []
		return
			
	def processModpack(self,curseProfile=None):
		#We need to process the profile
		from base.modules.config import curseforge_instancePath,rootFilepath
		instancePath = os.path.join(curseforge_instancePath + "/" + str(curseProfile))
		jsonFile = os.path.join(instancePath,"minecraftinstance.json")
		with open(jsonFile,"r",encoding="utf-8") as profileData:
			profile_data = json.load(profileData)
			profileData.close()
		addon_data = profile_data["installedAddons"]
		gameversion = profile_data["gameVersion"]
		modData = []
		resourcePacks = []
		for item in addon_data:
			#Filter out resource packs
			addonTargetDestinationRaw = item['modFolderPath']
			if addonTargetDestinationRaw is None:
				addonTargetDestinationRaw = str(curseforge_instancePath) + "/mods"
			addonDestination = os.path.basename(addonTargetDestinationRaw)
			if addonDestination == "mods":
				modData.append(item['addonID'])
				continue
			else:
				#Its a resource pack
				resourcepackTuple = (item['name'],item['addonID'])
				resourcePacks.append(resourcepackTuple)
				continue
		#We need to parse the ID
		modObjects = []
		for id in modData:
			modobject = self.parseID(targetType='get-object-data',objectID=id)
			modObjects.append(modobject)
			continue
		#Check for client mods. Lets guess
		clientModCounter = 0
		clientmodListing = []
		for item_ in modObjects:
			#We need to look at the categories
			for category in item_['categories']:
				categoryName = category['name']
				if categoryName in ['Bug Fixes','Cosmetic','Utility & QoL','Map and Information','Twitch Integration']:
					#Its likely a client mod
					clientModCounter += 1
					clientmodTuple = (item_['name'],item_['id'])
					clientmodListing.append(clientmodTuple)
					break
				else:
					continue
		#generate a mod list without the client mods
		clientModNames = set(name for name,_ in clientmodListing)
		servermodListing = []
		for mod in modObjects:
			if mod['name'] not in clientModNames:
				modTuple = (mod['name'],mod['id'])
				servermodListing.append(modTuple)
				continue
			else:
				continue
		if len(resourcePacks)!= 0:
			self.setListing(clientmods=clientmodListing,servermods=servermodListing,resourcepacks=resourcePacks,mc_version=gameversion)
			return
		else:
			self.setListing(clientmods=clientmodListing,servermods=servermodListing,mc_version=gameversion)
			return

class WorldDataClass():
	def __init__(self,worldPath=None):
		self.worldData_metaData = {}
		self.path = worldPath
		self.setMetaData()
		self.seed = self.worldData_metaData['WorldGenSettings']['seed'] or self.worldData_metaData['RandomSeed']
		self.cleanMetaData()
		return
	
	def setMetaData(self) -> dict:
		'Reads the level.dat. Returns the meta data as a dictionary'
		targetPath = str(self.path) + "/level.dat"
		dataRaw = nbtlib.load(targetPath)
		data = dataRaw.get("Data",{})
		for key,val in data.items():
			self.worldData_metaData[str(key)] = val
			continue
		return
	
	def convertSeedToWord(self):
		'Gets the RandomSeed and transforms it to a word as a unsigned 64-bit.'
		seed = self.seed
		#We need to unsign it
		unsignedSeed = seed & 0xFFFFFFFFFFFFFFFF
		word = ""
		while unsignedSeed > 0:
			unsignedSeed,remainder = divmod(unsignedSeed,26)
			word = chr(ord('a') + remainder) + word
		return word or "a"
	
	def convertWordToSeed(self,word=None):
		'Converts the word parameter to a signed 64-bit minecraft seed'
		number = 0
		for char in word:
			if 'a' <= char <= 'z':
				val = ord(char) - ord('a')
			elif 'A' <= char <= 'Z':
				val = ord(char) - ord('A')
			else:
				raise ValueError("Only alphabetic characters allowed")
			
			number = number * 26 + val
		
		number = number & 0xFFFFFFFFFFFFFFFF
		if number >= 2**63:
			number -= 2**64
		return number
	
	def wordVerifier(self,word_=None):
		'Checks the WORD parameter if it outputs the same RandomSeed in the meta data'
		currentSeed = self.seed
		int_seed = self.convertWordToSeed(word=str(word_))
		outputLog_utils.info_print(f"World Seed: {currentSeed}")
		outputLog_utils.info_print(f"Result Seed: {int_seed}")
		if int_seed == currentSeed:
			return True
		else:
			return False
	
	def cleanTimestamp(self):
		'Gets LastPlayed value and returns it into a formatted timestamp'
		from datetime import datetime,timezone
		#The value is in milliseconds
		timestamp_ = self.worldData_metaData['LastPlayed'] / 1000
		resultRaw = datetime.fromtimestamp(timestamp_,tz=timezone.utc)
		result = resultRaw.strftime("%m/%d/%Y - %I:%M:%S %p %Z")
		return result
	
	def cleanDifficulty(self):
		'Gets Difficulty and returns it as a string'
		diffMap = {0:"Peaceful",1:"Easy",2:"Normal",3:"Hard"}
		difficulty_int = self.worldData_metaData['Difficulty']
		global resultDiff
		for key,val in diffMap.items():
			if difficulty_int == key:
				resultDiff = str(val)
				break
			else:
				continue
		return resultDiff
	
	def cleanGameType(self):
		'Gets GameType and returns it as a string'
		typMap = {0:"Survival",1:"Creative",2:"Adventure",3:"Spectator"}
		modeInt = self.worldData_metaData['GameType']
		for key,val in typMap.items():
			if modeInt == key:
				resultTyp = str(val)
				break
			else:
				continue
		return resultTyp
	
	def cleanHardcoreMode(self):
		return "Yes" if self.worldData_metaData['hardcore'] == 1 else "No"
	
	def cleanMetaData(self):
		'Makes what is being used in the world summary more human readable'
		for k1,v1 in self.worldData_metaData.items():
			if "RandomSeed" in k1:
				self.worldData_metaData["RandomSeed"] = self.convertSeedToWord()
			if "WorldGenSettings" in k1:
				self.worldData_metaData["WorldGenSettings"]["seed"] = self.convertSeedToWord()
			if "LastPlayed" in k1:
				self.worldData_metaData["LastPlayed"] = self.cleanTimestamp()
			if "Difficulty" in k1:
				self.worldData_metaData["Difficulty"] = self.cleanDifficulty()
			if "GameType" in k1:
				self.worldData_metaData["GameType"] = self.cleanGameType()
			if "hardcore" in k1:
				self.worldData_metaData["hardcore"] = self.cleanHardcoreMode()
		return

class TopographMapLogic():
	def __init__(self,clientFolder=None,savePath=None,world=None,mc_version=None,moddedWorld=False):
		from base.modules.config import rootFilepath
		self.worldLocation = savePath
		self.world = world
		self.minecraftVersion = mc_version
		self.isModded = moddedWorld
		self.client = clientFolder
		self.genMap = None
		self.mapthread = None
		self.canKill = 0
		self.code = 3
		self.cli_path = str(rootFilepath) + "/base/cli/Topograph Map Rendering/BlueMap"
		return
	
	@staticmethod
	def firstBoot():
		'Generates the configs acting like its the first boot'
		def lineOutput(process):
			for line in process.stdout:
				if line:
					line = line.strip()
					outputLog_utils.info_print(str(line))
					continue
				else:
					break
			return
		processTarget = subprocess.Popen(['java','-jar','bluemap-5.11-cli.jar'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
		processThread = threading.Thread(target=lineOutput,args=(processTarget,))
		processThread.start()
		returncode = processTarget.wait()
		processThread.join()
		if returncode == 0 or returncode != 0:
			outputLog_utils.info_print(f"Process ended with the return code of {returncode}")
			return
	
	def _generateMapConfigDict(self):
		'Creates a dictionary based on the schema'
		from base.modules.config import rootFilepath
		with open(str(rootFilepath) + "/cli-bluemaps-defaults.json", "r") as f:
			schema = json.load(f)

		def recurse(part):
			# Use default if defined
			if "default" in part:
				return part["default"]

			schema_type = part.get("type")

			if schema_type == "object":
				result = {}
				# handle explicit properties
				for key, subschema in part.get("properties", {}).items():
					val = recurse(subschema)
					if val is not None or "default" in subschema:
						result[key] = val
				# handle patternProperties: do NOT create literal keys
				if "patternProperties" in part:
					for pattern, subschema in part["patternProperties"].items():
						# Only create content if default is defined inside
						if "default" in subschema:
							result[pattern] = subschema["default"]
					# Otherwise leave as empty dict
					if not result:
						return {}
				return result

			if schema_type == "array":
				return part.get("default", [])

			# Primitive types with no default → None
			return None

		return recurse(schema)
	
	def generateWorldConfig(self):
		'Writes a conf file for the world that the topographic map handler is bound to'
		from base.modules.config import rootFilepath
		#Create the dictionary
		worldData = self._generateMapConfigDict()
		#Change some things
		worldData['world'] = str(self.world)
		worldData['name'] = str(self.world)
		outputLog_utils.info_print(f"Generating {self.world}.conf ...")
		with open(str(rootFilepath) + f"/base/cli/Topograph Map Rendering/BlueMap/config/maps/{self.world}.conf", "w") as configData:
			for k, v in worldData.items():
				# format strings with quotes
				if isinstance(v, str):
					v = f"\"{v}\""
				# format booleans as lowercase
				elif isinstance(v, bool):
					v = str(v).lower()
				# empty dicts/arrays in BlueMap style
				elif isinstance(v, dict) and not v:
					v = "{}"
				elif isinstance(v, list) and not v:
					v = "[]"
				# write line with space after colon
				line = f"{k}: {v}"
				configData.write(line + "\n")
				continue
		outputLog_utils.info_print(f"Created Configs for world {self.world}")
		return
	
	def cloneWorldSaveData(self):
		'Copies the world data from the save location'
		from base.modules.config import rootFilepath
		target = self.worldLocation + f"/{self.world}"
		destination = str(rootFilepath) + f"/base/cli/Topograph Map Rendering/BlueMap/{self.world}"
		shutil.copytree(str(target),str(destination),dirs_exist_ok=True)
		if self.isModded:
			mods_source = str(self.client) + "/mods"
			mods_destination = str(rootFilepath) + f"/base/cli/Topograph Map Rendering/BlueMap/data/{self.world}/mods"
			shutil.copytree(str(mods_source),str(mods_destination),dirs_exist_ok=True)
		return
	
	def runMapWebGenerator(self):
		'Starts the web map generator with rendering using the configured settings'
		import time
		def lineOutput_(process):
			for line in process.stdout:
				if line:
					line = line.decode('utf-8').strip()
					if "Stopping..." in line:
						self.canKill = 1
					self.currentLine = str(line)
					outputLog_utils.info_print(line)
					time.sleep(0.1)
				else:
					continue
			return
		if not os.path.isfile(str(self.cli_path) + f"/config/maps/{self.world}.conf"):
			#Generate the config
			self.generateWorldConfig()
		if not os.path.isdir(str(self.cli_path) + f"/{self.world}"):
			#Grab the world
			self.cloneWorldSaveData()
		#Run the generator
		cmd = ['java','-jar','bluemap-5.11-cli.jar','-w','-r','--mc-version',str(self.minecraftVersion)]
		if self.isModded == True:
			modSource = str(self.cli_path) + f"/data/{self.world}/mods"
			cmd.extend(['--mods',str(modSource)])
		outputLog_utils.info_print("Using command: " + str(cmd))
		with SoftwareSpec.changeDir(str(self.cli_path)):
			self.genMap = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			self.mapthread = threading.Thread(target=lineOutput_,args=(self.genMap,),name="Topograph Map Generator")
			self.mapthread.start()
			self.code = self.genMap.wait()
			self.mapthread.join()
			return
	
	def runMapGenerator(self):
		'Starts the map rendering generator using the configured settings'
		import time
		def lineOutput(process):
			for line in process.stdout:
				if line:
					line = line.decode('utf-8').strip()
					if "Stopping..." in line:
						self.canKill = 1
					outputLog_utils.info_print(line)
					time.sleep(0.1)
				else:
					continue
			return
		if not os.path.isfile(str(self.cli_path) + f"/config/maps/{self.world}.conf"):
			#Generate the config
			self.generateWorldConfig()
		if not os.path.isdir(str(self.cli_path) + f"/{self.world}"):
			#Grab the world
			self.cloneWorldSaveData()
		#Run the generator
		cmd = ['java','-jar','bluemap-5.11-cli.jar','-r','--mc-version',str(self.minecraftVersion)]
		if self.isModded == True:
			modSource = str(self.cli_path) + f"/data/{self.world}/mods"
			cmd.extend(['--mods',str(modSource)])
		outputLog_utils.info_print("Using command: " + str(cmd))
		with SoftwareSpec.changeDir(str(self.cli_path)):
			self.genMap = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			self.mapthread = threading.Thread(target=lineOutput,args=(self.genMap,),name="Topograph Map Generator")
			self.mapthread.start()
			self.code = self.genMap.wait()
			self.mapthread.join()
			return
	
	def killGenerator(self):
		'Stops the generator'
	
		# Only attempt to kill if it is safe
		if self.canKill != 1:
			outputLog_utils.warning_print("Map generator not ready to be killed yet.")
			return
	
		# Ensure the process exists
		if self.genMap is None:
			outputLog_utils.warning_print("Process handle missing, skipping termination.")
			return
	
		# Attempt to terminate the process
		try:
			self.genMap.terminate()
		except Exception as e:
			outputLog_utils.warning_print(f"Failed to terminate generator: {e}")
	
		# Wait with a timeout to avoid hanging
		try:
			self.genMap.wait(timeout=5)
		except subprocess.TimeoutExpired:
			outputLog_utils.warning_print("Map generator did not stop in time, force killing...")
			try:
				self.genMap.kill()
				self.genMap.wait(timeout=5)
			except Exception as e:
				outputLog_utils.error_print(f"Failed to kill generator: {e}")
	
		# Safely join the thread if it exists
		if self.mapthread is not None:
			try:
				self.mapthread.join(timeout=5)
			except Exception as e:
				outputLog_utils.warning_print(f"Failed to join map thread: {e}")
	
		# Log final state and reset internal variables
		outputLog_utils.info_print(f"Process ended with the return code of {self.genMap.returncode if self.genMap is not None else 'unknown'}")
		self.code = 3
		self.genMap = None
		self.mapthread = None
		self.canKill = 0

	


outputLog_utils.info_print("Loaded Utilities.")
