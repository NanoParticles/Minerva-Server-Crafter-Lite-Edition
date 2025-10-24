import queue
import shutil
import time
import os
import sys
import threading
import requests
import sqlite3
from packaging.version import Version
import feedparser
import subprocess
import xmltodict
import json
from typing import Union,Tuple
from base.modules.config import MinecraftPropertiesSchema, rootFilepath, program_folder
from base.modules.utils import MCSCInternalError, CurseforgeClass, SoftwareSpec, TopographMapLogic
from base.modules.server import ServerFileIO
from base.modules.kernel import MCSCKernelCore
outputLog_updater = MCSCKernelCore(module="Updater")

class MCSCUpdater():
	'Version Updater for Minerva Server Crafter'
	q = queue.Queue()

	@classmethod
	def getUpdates(self):
		try:
			PurpurLogic = self.PurpurBaseClass()
			getPurpurUpdate = PurpurLogic.updatePurpurTable()
			#We need the tuple values
			totalPurpurUpdates = getPurpurUpdate[0]
			purpurUpdateBool = getPurpurUpdate[1]
			SpigotLogic = self.SpigotBaseClass()
			getBuildToolsUpdate = SpigotLogic.updateBuildToolsTable()
			totalBuildToolsUpdates = getBuildToolsUpdate[0]
			buildtoolUpdateBool = getBuildToolsUpdate[1]
			ForgeLogic = self.ForgeBaseClass()
			getForgeUpdates = ForgeLogic.updateForgeVersionTable()
			totalForgeUpdates = getForgeUpdates[0]
			forgeUpdateBool = getForgeUpdates[1]
			VanillaMCLogic = self.MinecraftVanillaBaseClass()
			getMinecraftVanillaUpdates = VanillaMCLogic.updateMinecraftVersions()
			totalMinecraftVanillaUpdates = getMinecraftVanillaUpdates[0]
			minecraftVanillaUpdateBool = getMinecraftVanillaUpdates[1]
			FabricLogic = self.FabricBaseClass()
			getFabricInstallerUpdates = FabricLogic.updateFabricInstallerTable()
			totalFabricInstallerUpdates = getFabricInstallerUpdates[0]
			fabricInstallerUpdateBool = getFabricInstallerUpdates[1]
			getFabricVersionUpdates = FabricLogic.updateFabricVersions()
			totalFabricVersionUpdates = getFabricVersionUpdates[0]
			fabricVersionUpdateBool = getFabricVersionUpdates[1]
			versionUpdateDefinitions = int(totalPurpurUpdates) + int(totalBuildToolsUpdates) + int(totalForgeUpdates) + int(totalMinecraftVanillaUpdates) + int(totalFabricInstallerUpdates) + int(totalFabricVersionUpdates)
			if versionUpdateDefinitions > 0:
				#What was updated?
				updateList = []
				if purpurUpdateBool == True:
					updateList.append("Purpur Build(s)")
				if buildtoolUpdateBool == True:
					updateList.append("BuildTools Version(s)")
				if forgeUpdateBool == True:
					updateList.append("Forge Version(s)")
				if minecraftVanillaUpdateBool == True:
					updateList.append("Minecraft Vanilla Version(s)")
				if fabricInstallerUpdateBool == True:
					updateList.append("Fabric Installer Version(s)")
				if fabricVersionUpdateBool == True:
					updateList.append("Fabric Version(s)")
				totalUpdates = len(updateList)
				#We generated the list. Notify the user
				outputLog_updater.info_print(f"There was {totalUpdates} update(s) made to table(s). Total number of changes: {versionUpdateDefinitions}. Rebooting...")
				if minecraftVanillaUpdateBool == True:
					outputLog_updater.info_print("Vanilla Update detected. Halting Reboot and Generating Schema...")
					postUpdate_schemaGen = MinecraftPropertiesSchema()
					postUpdate_schemaGenVersion = str(self.MinecraftVanillaBaseClass.getLatest())
					postUpdate_schemaGen.serverPropertiesToSchema(minecraft_version=postUpdate_schemaGenVersion,include_defaults=True)
					#Moving Schema to the latest config
					shutil.move(str(rootFilepath) + f"/base/assets/config/versions/{postUpdate_schemaGenVersion}/schema.json",str(rootFilepath) + "/base/assets/config/versions/latest/schema.json")
					time.sleep(2.0)
					outputLog_updater.info_print("Schema Generated. Rebooting...")
				os.execl(sys.executable,sys.executable,*sys.argv)
			else:
				outputLog_updater.info_print("No updates detected.")
				return
			
		except MCSCInternalError as e:
			outputLog_updater.error_print(f"Internal Error has occured: {e}")
			return
	
	class VersionCacheObject():
		def __init__():
			raise RuntimeError("Direct calling detected. Avoid doing this.")
		class onVersion():
			def __init__():
				raise RuntimeError("Direct calling detected. Avoid doing this.")
			
			@staticmethod
			def generateListPopulation(versionList=None | list):
				if isinstance(versionList,list):
					result = []
					for version in versionList:
						version_check = MCSCUpdater.VersionCacheObject.onVersion.lookupVersion(version=str(version))
						if isinstance(version_check,bool):
							if version_check:
								result.append(version)
								continue
							else:
								continue
						else:
							continue
				return result
			@staticmethod
			def lookupVersion(version=None | str or None) -> Union[bool,Tuple[bool,str]]:
				'Looks up if version is in the cache and in the database. Returns True if they are in both in the cache and in the database table. Otherwise, returns False if and only if they are not in either the database table or the cache. However, if its missing while its present somewhere else, it returns as a tuple with False, and where it failed'
				from base.modules.config import rootFilepath
				#We need to check if the version is part of the cache
				with open(str(rootFilepath) + "/properties.json","r") as jsonObject:
					data_dump = json.load(jsonObject)
				currentCache = data_dump["version_cache"] #Cache object
				listingPopulation = currentCache["listing"]
				#Check if its in the database
				MCSCDatabase = sqlite3.connect("mcsc_data.db")
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT version FROM minecraftversion_Table")
				dbVersions = [v[0] for v in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
				cacheLookUp = version in listingPopulation
				dbLookUp = version in dbVersions
				if cacheLookUp and dbLookUp:
					return True
				if not cacheLookUp and not dbLookUp:
					return False
				return (False, "cache" if not cacheLookUp else "database")
			def addToCache(version=None | str):
				'Adds version to cache as a known good version'
				from base.modules.config import rootFilepath
				if isinstance(version,str):
					with open(str(rootFilepath) + "/properties.json","r") as jsonFile_:
						data_obj = json.load(jsonFile_)
					cache = data_obj['version_cache']
					version_listing = cache['listing']
					newVersionListing = []
					if version not in version_listing:
						newVersionListing.append(version)
						for item in version_listing:
							newVersionListing.append(item)
						data_obj['version_cache']['listing'] = newVersionListing
					with open(str(rootFilepath) + "/properties.json","w") as newJsonFile:
						json.dump(data_obj,newJsonFile,indent=4)
					return
			def addVersionCacheEntriesToTables():
				'Adds the cached database entries from cache to the table data'
				from base.modules.config import rootFilepath
				with open(str(rootFilepath) + "/properties.json","r") as data_json:
					json_dataobj = json.load(data_json)
				cache_OBJ = json_dataobj['version_cache']
				dbEntries = cache_OBJ['db_entries']
				MCSCDatabase = sqlite3.connect("mcsc_data.db")
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute('DELETE FROM minecraftversion_Table')
				MCSCDatabase.commit()
				MCSC_Cursor.execute("VACUUM;")
				MCSCDatabase.commit()
				for item in dbEntries:
					MCSC_Cursor.execute('INSERT INTO minecraftversion_Table (version, timestampRelease) VALUES (?, ?) ', (item['version'],item['timestamp']))
				MCSCDatabase.commit()
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return


	@classmethod
	def updater(cls):
		try:
			cls.getUpdates()
			cls.q.put(True)
		except MCSCInternalError as e:
			outputLog_updater.error_print(e)
			cls.q.put(False)

	@classmethod
	def runUpdates(cls):
		#Thread the updates
		updaterThread = threading.Thread(target=cls.updater,name="Minerva Server Crafter - Updater",daemon=True)
		updaterThread.start()
		threadresult = cls.q.get()
		if threadresult == True:
			updaterThread.join()
			outputLog_updater.info_print("Database Table Updates completed.")
			ServerFileIO.onBoot_firstLoadCheck()
			outputLog_updater.info_print("Launching...")
			return
		else:
			raise MCSCInternalError("Failed to run Updates. Internal Exception")

	class MinecraftVanillaBaseClass():
		'Utility for handling Minecaft Vanilla Updates'
		def __init__(self):
			self.outputLog_vanillaupdates = MCSCKernelCore(module="Updater",logic="Vanilla Updates")
			return

		def rebuildCache(self):
			'Rebuilds the version cache'
			self.outputLog_vanillaupdates.info_print("Rebuilding Cache...")
			with open(str(rootFilepath) + "/properties.json","r") as jsonCache:
				dataDump = json.load(jsonCache)
				jsonCache.close()
			new_cache = []
			versionswithServer = []
			versionmanifestResponse = requests.get(url="https://launchermeta.mojang.com/mc/game/version_manifest.json")
			if versionmanifestResponse.status_code == 200:
				manifestData = versionmanifestResponse.json()
				versionlisting = manifestData['versions']
				versionDict = {v['id']: v['url'] for v in versionlisting}

				for item in versionDict.keys():
					#Get the url
					versionURL = versionDict[item]
					versionResponse = requests.get(url=str(versionURL))
					if versionResponse.status_code == 200:
						versiondata = versionResponse.json()
						versionDownloadSection = versiondata['downloads']
						if "server" in versionDownloadSection:
							#Server jar found
							self.outputLog_vanillaupdates.info_print(f"Found version {item} with a server.jar. Adding to good version listing...")
							versionswithServer.append(item)
							continue
						else:
							break
				for version_ in versionlisting:
					versionID = version_['id']
					timestamp = version_['releaseTime']
					if versionID in versionswithServer:
						new_cache.append({'version':str(versionID),'timestamp':str(timestamp)})
					else:
						break
				dataDump['version_cache']['listing'] = versionswithServer
				dataDump['version_cache']['db_entries'] = new_cache
				with open(str(rootFilepath) + "/properties.json","w") as _jsonUpdate:
					json.dump(dataDump,_jsonUpdate,indent=4)
			return
		
		def getLatest():
			'Returns the id of the first entry in version manifest'
			response = requests.get(url="https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
			if response.status_code == 200:
				datadump = response.json()
				#Get the version of the first entry
				result = datadump['versions'][0]['id']
			return result
	
		def omitedVersions(self):
			'Returns a list of versions that does not have server.jar. This is best for historical versions that do not have server jars(Cave game, infdev , alpha , and beta)'
			with SoftwareSpec.changeDir(path=str(rootFilepath)):
				MCSCDatabase = sqlite3.connect('mcsc_data.db')
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT * FROM minecraftVersionBlacklist")
				blacklist = [str(row[0]) for row in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
			return blacklist
		
		def validServerVersions(self, versionList:list=None):
			'Returns a list of versions that does have a server jar distribution. This is best for earlier versions after beta'
			if isinstance(versionList,list):
				#Its a list of versions. Make the requests
				self.outputLog_vanillaupdates.info_print("Compiling server version list...")
				listing = versionList
				currentCache = MCSCUpdater.VersionCacheObject.onVersion.generateListPopulation(versionList=listing)
				versionswithServer = currentCache
				self.outputLog_vanillaupdates.info_print(versionswithServer)
				
				result = []
				for item_ in versionList:
					#Its a database entry. Grab the version
					versionResult = item_['version']
					if versionResult in versionswithServer:
						self.outputLog_vanillaupdates.info_print(f"Found version {versionResult} in the known good list of version. Allowing...")
						result.append(item_)
						continue
					else:
						self.outputLog_vanillaupdates.info_print(f"Version {versionResult} is a bad version. Disallowing...")
						continue
				#build the tuple
				self.outputLog_vanillaupdates.info_print("Done processing version list.")
				return result


		def updateMinecraftVersions(self):
			'Checks for Minecraft Version updates. When there is an update, it gets added to the table, and Minerva Server Crafter reboots'

			# Fetch the latest available Minecraft versions from Mojang
			versionManifestURL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
			response = requests.get(versionManifestURL)

			if response.status_code == 200:
				manifestData = response.json()
				#Store versions with the time of release
				versionswithTime = [{'version': version['id'],'timestamp': version['releaseTime']} for version in manifestData['versions']]
				#Sort the version based on the time of release in decending order
				sortedVersions = sorted(versionswithTime,key=lambda x: x['timestamp'],reverse=True)
				versionListing = []
				for item in sortedVersions:
					versionListing.append(item['version'])
				with SoftwareSpec.changeDir(path=str(rootFilepath)):
					# Retrieve existing versions from the database
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					MCSC_Cursor.execute('SELECT version, timestampRelease FROM minecraftversion_Table')
					existing_versions = {row[0]: row[1] for row in MCSC_Cursor.fetchall()}
					# Insert only the new versions into the database while considering blacklisted versions
					versionBlackList = self.omitedVersions()
					new_versions = [version for version in sortedVersions if version['version'] not in existing_versions and version['version'] not in versionBlackList]
					for item_ in new_versions:
						if item_ in versionBlackList:
							new_versions.remove(item_)
					totalupdates = len(new_versions)
					hadUpdate = False
					if new_versions:
						#Set the flag to true
						hadUpdate = True
						self.outputLog_vanillaupdates.info_print(f"There are {totalupdates} new Minecraft Version(s) updates. Updating...")
						self.rebuildCache()
						versionCheck = self.validServerVersions(versionList=new_versions)
						new_versions = versionCheck
						MCSCUpdater.VersionCacheObject.onVersion.addVersionCacheEntriesToTables()
						#MCSC_Cursor.execute('DELETE FROM minecraftversion_Table')
						#MCSCDatabase.commit()
						#MCSC_Cursor.execute("VACUUM;")
						#MCSCDatabase.commit()
						#for item in new_versions:
						#	MCSC_Cursor.execute('INSERT INTO minecraftversion_Table (version, timestampRelease) VALUES (?, ?) ', (item['version'],item['timestamp']))
						#for key,val in existing_versions.items():
						#	MCSC_Cursor.execute('INSERT INTO minecraftversion_Table (version, timestampRelease) VALUES (?, ?)', (key,val))
						# Commit the changes
						#MCSCDatabase.commit()
						#MCSC_Cursor.close()
						#MCSCDatabase.close()
						if hadUpdate == True:
							result = tuple((int(totalupdates),hadUpdate))
						self.outputLog_vanillaupdates.info_print('Version Table has been updated successfully.')
						return result
					else:
						MCSC_Cursor.close()
						MCSCDatabase.close()
						result = tuple((0,False))
						self.outputLog_vanillaupdates.info_print("No new Vanilla Minecraft Versions detected")
						return result
			else:
				outputLog_updater.info_print("Failed to get version manifest")
				return

	class PurpurBaseClass():
		'Utility that handles the compatibilities for Purpur'

		def __init__(self):
			self.outputLog_purpurupdates = MCSCKernelCore(module="Updater",logic="Purpur Updates")
			return

		def getCompatibleVersions() -> list:
			#Parse the JSON
			response = requests.get("https://api.purpurmc.org/v2/purpur")
			if response.status_code == 200:
				purpurRawData = response.json()
				compatibleVersions = [s for s in purpurRawData["versions"]]
				return compatibleVersions

		def updatePurpurTable(self):
			'Checks for updates from the Purpur API. When there is a new build is found, the table gets updated(Newest to oldest). When the purpur table is updated, Minerva Server Crafter reboots'
			#We need to check for any purpur updates

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
				with SoftwareSpec.changeDir(path=str(rootFilepath)):
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					MCSC_Cursor.execute("SELECT Build_ID, Minecraft_Version FROM PurpurVersion_Table")
					# Always cast both build ID and version to the same types
					MCSC_Cursor.execute("SELECT Build_ID, Minecraft_Version FROM PurpurVersion_Table")
					existingBuilds = set((int(row[0]), str(row[1])) for row in MCSC_Cursor.fetchall())
					# Prepare the list of new builds
					newBuilds = []
					for mcversion, buildList in currentBuilds.items():
						for build in buildList:
							buildPair = (int(build), str(mcversion))
							if buildPair not in existingBuilds:
								newBuilds.append(buildPair)

					totalNewBuilds = len(newBuilds)
					hadupdate = False
					if newBuilds:
						#Set the flag
						hadupdate = True
						MCSC_Cursor.execute("DELETE FROM PurpurVersion_Table")
						MCSCDatabase.commit()
						MCSC_Cursor.execute("VACUUM;")
						MCSCDatabase.commit()
						self.outputLog_purpurupdates.info_print(f"There are {totalNewBuilds} new build(s). Updating Table...")
						for mcversion,purpurBuildList in currentBuilds.items():
							for purpurBuildID in purpurBuildList:
								MCSC_Cursor.execute("INSERT INTO PurpurVersion_Table VALUES (?,?)", (purpurBuildID,mcversion))
						MCSCDatabase.commit()
						MCSC_Cursor.close()
						MCSCDatabase.close()
						if hadupdate == True:
							result = tuple((int(totalNewBuilds),hadupdate))
						self.outputLog_purpurupdates.info_print("Build Table has been updated successfully.")
						return result

					else:
						result = tuple((0,False))
						self.outputLog_purpurupdates.info_print("No new Purpur builds detected")
						return result
				
		def getBuildsbyVersion(version) -> list:
			'Returns a list of Purpur Versions thats compatiable with the given Minecraft Version'
			#We need to parse the database table
			with SoftwareSpec.changeDir(path=str(rootFilepath)):
				MCSCDatabase = sqlite3.connect("mcsc_data.db")
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT Build_ID FROM PurpurVersion_Table WHERE Minecraft_Version = ?", (str(version),))
				builds = [row[0] for row in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return builds

	class SpigotBaseClass():
		'Utility that handles the compatiblities thats tied to Spigot and its forks'

		def __init__(self):
			self.outputLog_spigot = MCSCKernelCore(module="Updater",logic="BuildTools Updates")
			return

		def getVersionListing() -> list:
			'Returns a list of minecraft versions tailored to spigot/craftbukkit'
			url = "https://hub.spigotmc.org/nexus/repository/snapshots/org/spigotmc/spigot-api/maven-metadata.xml"
			response = requests.get(url=str(url))
			if response.status_code == 200:
				data = xmltodict.parse(response.content)
				versions = data['metadata']['versioning']['versions']
				currentVersions = [str(v) for v in versions['version']]
				versionListing = []
				for item in currentVersions:
					mcversion = item.split("-")[0]
					if item not in versionListing:
						versionListing.append(mcversion)
						continue
					else:
						continue
				return versionListing

		def updateBuildToolsTable(self):
			'Checks for successful builds of BuildTools in the jenkins repository. Failed builds are exempt from the result. When there is successful builds thats not in the database table, the table gets updated(newest builds to oldest). When the table gets updated, Minerva Server Crafter reboots.'
			
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
				
				with SoftwareSpec.changeDir(path=str(rootFilepath)):
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					MCSC_Cursor.execute("SELECT BuildID, Url FROM BuildTools_SuccessfulBuildVerified_Table")
					databaseData = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
					#Now that we have a dictionary with all of the successful builds, we need to know if its missing in the database
					missingEntries = {a: b for a, b in SuccessfulBuilds.items() if a not in databaseData}
					TotalEntriesMissing = len(missingEntries)
					hadupdate = False
					if missingEntries:
						MCSC_Cursor.execute("DELETE FROM BuildTools_SuccessfulBuildVerified_Table")
						MCSCDatabase.commit()
						MCSC_Cursor.execute("VACUUM;")
						MCSCDatabase.commit()
						#Set Flag
						hadupdate = True
						self.outputLog_spigot.info_print(f"There are {TotalEntriesMissing} new successful build(s). Updating Table...")
						for BuildID,url in missingEntries.items():
							MCSC_Cursor.execute("INSERT INTO BuildTools_SuccessfulBuildVerified_Table (BuildID, Url) VALUES (?,?)", (BuildID, url))
						for k,v in databaseData.items():
							MCSC_Cursor.execute("INSERT INTO BuildTools_SuccessfulBuildVerified_Table (BuildID, Url) VALUES (?,?)", (k, str(v)))
						MCSCDatabase.commit()
						MCSC_Cursor.close()
						MCSCDatabase.close()
						if hadupdate == True:
							result = tuple((int(TotalEntriesMissing),hadupdate))
						self.outputLog_spigot.info_print("Build Table has been updated successfully.")
						return result
					else:
						result = tuple((0,False))
						self.outputLog_spigot.info_print("No new successful builds for BuildTools detected")
						return result


		def getBuildTools(url=None):
			'Obtains by downloading the last successful build from the jenkins'
			if url == None:
				#We need to parse the jenkins archive and get the last successful build of BuildTools jar file
				response = requests.get("https://hub.spigotmc.org/jenkins/view/Public/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar")
			else:
				#We need to parse the jenkins archive and get the BuildTools jar file using the given url
				response = requests.get(str(url))
				if response.status_code == 200:
					if os.path.isdir(str(program_folder) + "/build/BuildTools") == False:
						os.makedirs(str(program_folder) + "/build/BuildTools")
					with open(str(program_folder) + "/build/BuildTools/BuildTools.jar","wb") as buildtoolsjar:
						buildtoolsjar.write(response.content)
						buildtoolsjar.close()
					return
		def runBuildTools(self,parameter=None):
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
			
			with SoftwareSpec.changeDir(path=str(program_folder) + "/build/BuildTools/"):
				BuildToolsThread = threading.Thread(target=session,name="BuildToolsInstance")
				BuildToolsThread.start()
				BuildToolsThread.join()
				BuildToolsThreadresult = x.get()
				if BuildToolsThreadresult == 0:
					self.outputLog_spigot.info_print(f"Command exited with the return code of {BuildToolsThreadresult}")
					return

		def getCraftbukkit(self,version=None,instance_name=None):
			'Installs the most current Spigot Version by passing the given Minecraft Version'
			# Check for BuildTools
			try:
				if version is not None:
					if instance_name is not None:
						if os.path.isfile(str(program_folder) + "/build/BuildTools/BuildTools.jar") == True:
							# Put Spigot in its Instance folder
							outputdirectory = str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_name}/"
							if not os.path.isdir(outputdirectory):
								os.makedirs(outputdirectory, exist_ok=True)  # <-- fix here
							# Run BuildTools with parameters
							parameterCmd = "--o", outputdirectory, "--rev", str(version), "--compile craftbukkit"
							MCSCUpdater.SpigotBaseClass.runBuildTools(parameter=parameterCmd)
							return
						else:
							# Get BuildTools
							MCSCUpdater.SpigotBaseClass.getBuildTools()
							# Re-run the command
							MCSCUpdater.SpigotBaseClass.getCraftbukkit(version=str(version),instance_name=str(instance_name))
							return
					else:
						raise MCSCInternalError(msg="Instance Name was expected, but got a NoneType value.")
				else:
					raise MCSCInternalError(msg="Version was expected, but got a NoneType value.")
			except MCSCInternalError as e:
				self.outputLog_spigot.error_print(e)
				return

		def getSpigot(self,version=None,instance_name=None):
			'Installs the most current Spigot Version by passing the given Minecraft Version'
			# Check for BuildTools
			try:
				if version is not None:
					if instance_name is not None:
						if os.path.isfile(str(program_folder) + "/build/BuildTools/BuildTools.jar") == True:
							# Put Spigot in its Instance folder
							outputdirectory = str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_name}/"
							if not os.path.isdir(outputdirectory):
								os.makedirs(outputdirectory, exist_ok=True)  # <-- fix here
							# Run BuildTools with parameters
							parameterCmd = "--o", outputdirectory, "--rev", str(version)
							MCSCUpdater.SpigotBaseClass.runBuildTools(parameter=parameterCmd)
							return
						else:
							# Get BuildTools
							MCSCUpdater.SpigotBaseClass.getBuildTools()
							# Re-run the command
							MCSCUpdater.SpigotBaseClass.getSpigot(version=str(version),instance_name=str(instance_name))
							return
					else:
						raise MCSCInternalError(msg="Instance Name was expected, but got a NoneType value.")
				else:
					raise MCSCInternalError(msg="Version was expected, but got a NoneType value.")
			except MCSCInternalError as e:
				self.outputLog_spigot.error_print(e)
				return

	class ForgeBaseClass():
		'Utility for handling Forge Updates'
		#Forge doesnt have a web-based API. Theres so little I can do in this dev stage
		def __init__(self):
			self.outputLog_forgeupdates = MCSCKernelCore(module="Updater",logic="Forge Updates")
			return
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

		def updateForgeVersionTable(self):
			'Checks for Forge Updates from Curseforge. When a new forge version is detected, the table is updated. When the table is updated, Minerva Server Crafter reboots.'
			
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
				with SoftwareSpec.changeDir(path=str(rootFilepath)):
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					MCSC_Cursor.execute("SELECT forgeversion, minecraftversion FROM forgeVersion_Table")
					existingVersions = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
					newVersions = [(forgeVersion, minecraftVersion) for minecraftVersion, forgeVersions in currentforgeversions.items() for forgeVersion in forgeVersions if forgeVersion not in existingVersions]
					totalNewVersions = len(newVersions)
					hadupdate = False
					if newVersions:
						#Set Flag
						hadupdate = True
						MCSC_Cursor.execute("DELETE FROM forgeVersion_Table")
						MCSCDatabase.commit()
						MCSC_Cursor.execute("VACUUM;")
						MCSCDatabase.commit()
						self.outputLog_forgeupdates.info_print(f"There are {totalNewVersions} total new version(s). Updating Table...")
						for minecraft_version, forge_version_list in sorted(currentforgeversions.items(), key=lambda x: Version(x[0]), reverse=True):
							for forge_version in forge_version_list:
								MCSC_Cursor.execute("INSERT INTO forgeVersion_Table VALUES (?, ?)", (forge_version, minecraft_version))
						for Key,Val in existingVersions.items():
							MCSC_Cursor.execute("INSERT INTO forgeVersion_Table VALUES (?, ?)",(Key,Val))
						MCSCDatabase.commit()
						MCSC_Cursor.close()
						MCSCDatabase.close()
						if hadupdate == True:
							result = tuple((int(totalNewVersions),hadupdate))
						self.outputLog_forgeupdates.info_print("Version Table Updated.")
						return result
					else:
						result = tuple((0,False))
						self.outputLog_forgeupdates.info_print("No new Forge Versions detected")
						return result
				
		def getForgeVersionsbyVersion(version) -> list:
			'Returns a list of Forge Versions thats compatiable with the given Minecraft Version'
			#We need to get the forge versions based off of the given minecraft version
			with SoftwareSpec.changeDir(path=str(rootFilepath)):
				MCSCDatabase = sqlite3.connect("mcsc_data.db")
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute("SELECT forgeversion FROM forgeVersion_Table WHERE minecraftversion = ?",(str(version),))
				forgeversionlist = [row[0] for row in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return forgeversionlist
		
	class FabricBaseClass():
		'Utility for handling Fabric Updates'
		#We need to do some things
		def __init__(self):
			self.outputLog_fabricupdates = MCSCKernelCore(module="Updater",logic="Fabric Updates")
			return

		def updateFabricInstallerTable(self):
			'Checks for Fabric Installer updates'
			
			MCSCDatabase = sqlite3.connect('mcsc_data.db')
			MCSC_Cursor = MCSCDatabase.cursor()

			response = requests.get("https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml")

			if response.status_code == 200:
				xmlData = xmltodict.parse(response.content)
				installerversionList = xmlData["metadata"]['versioning']['versions']['version']

				fabricinstallerURLS = {str(item): f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{item}/" for item in installerversionList}

				# Get versions already in the table
				MCSC_Cursor.execute("SELECT version FROM FabricInstallerVersion_Table")
				currentVersions = set(row[0] for row in MCSC_Cursor.fetchall())

				# Filter new versions not already in the table
				newVersions = [(installerversion, fabricinstallerURLS[installerversion]) for installerversion in installerversionList if installerversion not in currentVersions]
				totalUpdates = len(newVersions)
				hadupdate = False

				if newVersions:
					#Set the flag
					hadupdate = True
					outputLog_updater.info_print(f"There are {totalUpdates} total update(s). Updating Table...")
					MCSC_Cursor.execute("DELETE FROM FabricInstallerVersion_Table")
					MCSCDatabase.commit()
					MCSC_Cursor.execute("VACUUM;")
					MCSCDatabase.commit()
					for v, u in sorted(newVersions, key=lambda x: Version(x[0]), reverse=True):
						MCSC_Cursor.execute("INSERT INTO FabricInstallerVersion_Table (version,url) VALUES (?,?)",(v,u))
					MCSCDatabase.commit()
					MCSC_Cursor.close()
					MCSCDatabase.close()
					if hadupdate == True:
						result = tuple((int(totalUpdates),hadupdate))
					self.outputLog_fabricupdates.info_print("Version Table has been successfully updated.")
					return result

				else:
					result = tuple((0,False))
					self.outputLog_fabricupdates.info_print("No new Fabric Installer versions detected")
					MCSC_Cursor.close()
					MCSCDatabase.close()
					return result

		@staticmethod
		def getInstallerListingfromTable() -> list:
			'Returns a complete list of applicable installer versions from the version Table'
			#connect to the database
			with SoftwareSpec.changeDir(path=str(rootFilepath)):
				MCSCDatabase = sqlite3.connect('mcsc_data.db')
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute('SELECT version FROM FabricInstallerVersion_Table')
				loaderListing = [loaderVersion[0] for loaderVersion in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return loaderListing
		
		def getInstallerURLPrefixListing() -> list:
			'Returns a complete list of applicable installer urls from the version Table. This does not provide the full url, just the pointer of base url'
			#Connect to the database
			with SoftwareSpec.changeDir(path=str(rootFilepath)):
				MCSCDatabase = sqlite3.connect('mcsc_data.db')
				MCSC_Cursor = MCSCDatabase.cursor()
				MCSC_Cursor.execute('SELECT url FROM FabricInstallerVersion_Table')
				loaderListing = [loaderVersion[0] for loaderVersion in MCSC_Cursor.fetchall()]
				MCSC_Cursor.close()
				MCSCDatabase.close()
				return loaderListing
		
		def updateFabricVersions(self):
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
				with SoftwareSpec.changeDir(path=str(rootFilepath)):
					MCSCDatabase = sqlite3.connect("mcsc_data.db")
					MCSC_Cursor = MCSCDatabase.cursor()
					MCSC_Cursor.execute("SELECT version, compatiableMinecraftVersions FROM fabricVersion_Table")
					versionTableData = {row[0]: row[1] for row in MCSC_Cursor.fetchall()}
					newversions = [version for version in currentfabricVersions.keys() if version not in versionTableData.keys()]
					totalupdates = len(newversions)
					hadupdate = False
					if newversions:
						#We have updates
						hadupdate = True
						self.outputLog_fabricupdates.info_print(f"There are {totalupdates} new version update(s). Updating Table...")
						MCSC_Cursor.execute("DELETE FROM fabricVersion_Table")
						MCSCDatabase.commit()
						MCSC_Cursor.execute("VACUUM;")
						MCSCDatabase.commit()
						for k1,v1 in currentfabricVersions.items():
							MCSC_Cursor.execute("INSERT INTO fabricVersion_Table (version,compatiableMinecraftVersions) VALUES (?,?)", (k1,str(v1)))
						#Insert what used to be in the table
						for k2,v2 in versionTableData.items():
							MCSC_Cursor.execute("INSERT INTO fabricVersion_Table (version,compatiableMinecraftVersions) VALUES (?,?)", (k2,str(v2)))
						self.outputLog_fabricupdates.info_print("Version Table has been successfully updated.")
						MCSCDatabase.commit()
						MCSC_Cursor.close()
						MCSCDatabase.close()
						if hadupdate == True:
							result = tuple((int(totalupdates),hadupdate))
						return result
					else:
						result = tuple((0,False))
						self.outputLog_fabricupdates.info_print("No new Fabric Versions detected")
						return result

if not os.path.isfile(str(program_folder) + "/build/BuildTools/BuildTools.jar"):
	if not os.path.isdir(str(program_folder) + "/build"):
		os.makedirs(str(program_folder) + "/build",exist_ok=True)
		os.makedirs(str(program_folder) + "/build/BuildTools",exist_ok=True)
	MCSCDatabase = sqlite3.connect("mcsc_data.db")
	MCSC_Cursor = MCSCDatabase.cursor()
	outputLog_updater.info_print("BuildTools is missing! Obtaining...")
	#We need to fetch the last successful build from the database table
	MCSC_Cursor.execute("SELECT Url FROM BuildTools_SuccessfulBuildVerified_Table ORDER BY CAST(BuildID AS INTEGER) DESC LIMIT 1")
	latestBuild = MCSC_Cursor.fetchone()[0]
	if latestBuild:
		latestBuild_url = latestBuild + "artifact/target/BuildTools.jar"
		MCSCUpdater.SpigotBaseClass.getBuildTools(url=str(latestBuild_url))
		MCSC_Cursor.close()
		MCSCDatabase.close()
if not os.path.isdir(str(rootFilepath) + "/base/sandbox/Instances"):
	#Generate them
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Vanilla")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Modded")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Custom")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Curseforge")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Curseforge/Modpacks")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Curseforge/imported")
	os.mkdir(str(rootFilepath) + "/base/sandbox/Instances/Curseforge/downloads")

outputLog_updater.info_print("Loaded Updater Logic.")
