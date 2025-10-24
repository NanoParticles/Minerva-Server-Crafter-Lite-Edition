#main.py
from base.modules.kernel import *
outputLog = MCSCKernelCore()
outputLog.info_print("Minerva Server Crafter - A Minecraft Server Hosting Application")
outputLog.info_print("Minerva Server Crafter - v0.3.16 - Console Kernel")
outputLog.info_print("Minerva Server Crafter is not an official Minecraft Product. Minerva Server Crafter is not approved by or associated with Mojang or Microsoft.")
outputLog.info_print("Minerva Server Crafter is under the MIT License.")
outputLog.info_print("This release includes BlueMaps, which is licensed under MIT License. For more information, visit the repo: https://github.com/BlueMap-Minecraft/BlueMap")

from customtkinter import *
import os
import sys
from CTkToolTip import *
from CTkListbox import *
from CTkMenuBar import *
from CTkTable import *
from github import Github
from base.modules.updater import *
from base.modules.config import *
from base.modules.framework import *
from base.modules.gui.ui import *
from base.modules.server import *
from base.modules.utils import *
from base.modules.msc_zipfile import *

#We are going to make a github object
MCSC_API_githubObj = Github()

blocksize = 1024**2
#Notifications
#Initialize the json config stuff
onLoadConfig = False

os.chdir(str(rootFilepath))
whitelist = {}
playerBans = {}
difficultyStrings = ['Peaceful','Easy','Normal','Hard']
gamemodeStrings = ['Survival','Hardcore','Creative']
difficultyInt = [0,1,2,3]
gamemodeInt = [0,1,2]

minecraftVersions = ServerVersion_Control.getVersionList()

currentMemoryMinimum = int(4)
currentMemoryMax = int(4)
JSONModel = ServerFileIO.JSONModelUtils()

root = CTk()

root.title("Minerva Server Crafter" + str(releaseVersion))
root.protocol('WM_DELETE_WINDOW', MCSC_Framework.onMainWindow_onExit)
root.resizable(False,False)

#Check the Operating System for the main window icon

#We need to put in a tab view
rootMenubar = CTkMenuBar(master=root)
fileCascade = rootMenubar.add_cascade("File")
curseCascade = rootMenubar.add_cascade("Curseforge")
serverInstancesCascade = rootMenubar.add_cascade("Server Instances")
settingsCascade = rootMenubar.add_cascade("Settings")
rootMenubar_File = CustomDropdownMenu(widget=fileCascade,bg_color="transparent")
#File
logOption = rootMenubar_File.add_option(option="Save Console to Log File",command=lambda:Console.SaveConsoleToFile(start=1.0,end=END))
loadInstance = rootMenubar_File.add_option(option="Load Instance from File",command=MCSC_Framework.onMainWindow_import)
saveInstance = rootMenubar_File.add_option(option="Save Instance to File",command=lambda:MCSC_Framework.onMainWindow_export(category=lastConfigCategory,id=lastConfigID))
launchServerOption = rootMenubar_File.add_option(option="Launch Server Instance")
rootMenubar_File.add_separator()
aboutoption = rootMenubar_File.add_option(option="About",command=lambda:AboutDialogWindowClass(root))
exitOption = rootMenubar_File.add_option(option="Exit",command=lambda:MCSC_Framework.onMainWindow_onExit(root))
with open(str(rootFilepath) + "/properties.json","r") as properties:
	lastConfigData = json.load(properties)
	properties.close()
lastConfig = lastConfigData['Instances']['last-config']
lastConfigCategory = lastConfig["category"]
lastConfigID = lastConfig['id']

#Curseforge
rootMenubar_curse = CustomDropdownMenu(widget=curseCascade)
if curseforge_localization == True:
	importcurseProfile = rootMenubar_curse.add_option(option="New Instance from Local Profile",command=lambda:curseforgeUI.NewInstanceFromLocal())
importModpack = rootMenubar_curse.add_option(option="Add Modpack from Curseforge",command=lambda:MCSC_Framework.onMainWindow_remoteModpack())

#Instances
rootMenubar_serverinstances = CustomDropdownMenu(widget=serverInstancesCascade,bg_color="transparent")
serverInstances_bindInstance = rootMenubar_serverinstances.add_option(option="Load Instance",command=lambda: LoadInstanceDialog())
rootMenubar_serverinstances.add_separator()
serverInstances_newVanillaInstance = rootMenubar_serverinstances.add_option(option="New Vanilla Instance",command=lambda:NewVanillaInstance())
serverInstances_newModdedInstance = rootMenubar_serverinstances.add_option(option="New Modded Instance",command=lambda:NewModdedInstance())
serverInstances_newPurpurInstance = rootMenubar_serverinstances.add_option(option="New Purpur Instance",command=lambda:NewPurPurInstance())
serverInstances_newCustomJarInstance = rootMenubar_serverinstances.add_option(option="New Custom Jar Instance",command=lambda:NewCustomJarInstance())
serverInstances_configureInstance = rootMenubar_serverinstances.add_submenu(submenu_name="Configure")
serverInstances_configureInstance_Server = serverInstances_configureInstance.add_option(option="Server Settings")
serverInstances_configureInstance.add_separator()
serverInstances_configureInstance_Instance = serverInstances_configureInstance.add_option(option="Instance Settings")
serverInstances_InstanceViewer = rootMenubar_serverinstances.add_option(option="View Instance Details")
#Settings
rootMenubar_settings = CustomDropdownMenu(widget=settingsCascade,bg_color="transparent")
mcscSettings = rootMenubar_settings.add_option(option="Minerva Server Crafter Config")
minecraftdefaults = rootMenubar_settings.add_option(option="Minecraft Server Default Settings")

root.geometry("610x270")
root.title("Minerva Server Crafter - Lite Edition")
if sys.platform.startswith("win32"):
	root.after(200,lambda:root.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
if sys.platform.startswith("linux"):
	root.after(200,lambda:root.iconbitmap("@" + str(rootFilepath) + "/base/assets/icons/minecraftservercrafter-icon.xbm"))
if sys.platform.startswith("darwin"):
	#Unsure if this will work, will pay close attention to Mac Users
	root.after(200,lambda:root.iconbitmap(str(rootFilepath) + "/base/assets/icons/Mac_icon-minecraftservercrafter.icns"))
root.protocol("WM_DELETE_WINDOW",lambda:MCSC_Framework.onMainWindow_onExit(root))
root.resizable(width=False,height=False)
root.after(10,lambda:root.withdraw())
ConsoleFrame = CTkFrame(root)
ConsoleFrame.pack(after=rootMenubar)
Console = ConsoleShell(ConsoleFrame,includeInput=True)
shellVersion = "Version: " + str(VersionNumber) + "\n"

Console.updateConsole(END,"Minerva Server Crafter Lite - Release Build \n" + str(shellVersion))
Console.updateConsole(END,"Written in Python v3.12.4\n\n")


if lastConfigID is not None and lastConfigCategory is not None:
	loadedConfig = ServerFileIO.loadJSONProperties(instanceName=str(lastConfigID),category=str(lastConfigCategory))

	host = InternetHost()

	for key,val in loadedConfig.items():
		if "server-ip" in key:
			val = str(host.getIPV4())
		MinecraftServerProperties[str(key)] = val

MCSCUpdater.getUpdates()	

outputLog.info_print("Launching...")

#test workspace

splash = splashUI()
root.after(4300,lambda:root.deiconify())
root.after(4400,lambda:root.attributes("-topmost",True))
root.after(4500,lambda:root.attributes('-topmost',False))


#Mainloop
with briefRestore():
	root.mainloop()
