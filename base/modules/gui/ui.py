from logging import root
from typing import Callable, final
from numpy import imag
from base.modules.kernel import MCSCKernelCore,briefRestore
outputLog_ui = MCSCKernelCore(module="UI")
import webview
from customtkinter import *
from tkinter.ttk import Treeview
from CTkTable import *
from CTkListbox import *
from PIL import Image
import json
import threading
import traceback
import time
import subprocess
from CTkToolTip import *
from CTkMenuBar import *
from PIL import ImageFilter
import shutil
import sqlite3
import cairosvg
import random
import math
import sys
import io
import nbtlib
import anvil
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
with briefRestore():
	import pygame
outputLog_ui.info_print(f"Pygame {pygame.__version__} with SDL {pygame.version.SDL} Loaded. Hello Pygame. :)")
from base.modules.server import *
from base.modules.config import ServerType,MinecraftServerProperties,releaseVersion,operatingSystem,rootFilepath,InstanceAttached,program_folder
from base.modules.utils import CurseforgeClass, MCSCInternalError,HardwareSpec, SoftwareSpec
from base.modules.updater import MCSCUpdater
from base.modules.msc_zipfile import MSCZipLib

class LoadInstanceDialog():
	def __init__(self):
		self.root = CTkToplevel()
		self.root.resizable(width=False,height=False)
		if sys.platform.startswith("win32"):
			self.root.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
		if sys.platform.startswith("linux"):
			self.root.after(200,lambda:self.root.iconbitmap("@" + str(rootFilepath) + "/base/assets/icons/minecraftservercrafter-icon.xbm"))
		if sys.platform.startswith("darwin"):
			#Unsure if this will work, will pay close attention to Mac Users
			self.root.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/Mac_icon-minecraftservercrafter.icns"))
		self.root.title("Minerva Server Crafter - Load Instance")
		self.root.geometry("467x271")
		self.instances_raw = InstanceFramework()
		self.instances_raw.pollModded()
		self.instances_raw.pollVanilla()
		self.instances_raw.pollCustom()
		self.instances_vanilla_raw = self.instances_raw.vanillaInstances
		self.instances_modded_raw = self.instances_raw.moddedInstances
		self.instances_custom_raw = self.instances_raw.customInstances
		self.instances = []
		for item in self.instances_vanilla_raw:
			self.instances.append(item)
		for Item in self.instances_modded_raw:
			self.instances.append(Item)
		for item_ in self.instances_custom_raw:
			self.instances.append(item_)


		#We need to show all of the instances
		self.treeviewFrame = CTkFrame(self.root)
		self.treeviewFrame.grid(row=0,column=0)
		self.treeview = Treeview(self.treeviewFrame)
		self.treeview.pack(fill=BOTH,expand=True)
		self.treeview.heading("#0",text="Vanilla/Modded Instances")
		#Scrollbar
		self.treeviewScrollbar = CTkScrollbar(self.root,command=self.treeview.yview)
		self.treeviewScrollbar.grid(row=0,column=1,sticky=NS)
		#Instance Details
		self.detailsFrame = CTkFrame(self.root)
		self.detailsFrame.grid(row=0,column=2,padx=5,rowspan=3)
		self.instanceImage = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/default.png"),size=(100,100))
		self.instanceImageLabel = CTkLabel(self.detailsFrame,text=" ",image=self.instanceImage)
		self.instanceImageLabel.grid(row=0,column=0,columnspan=2)
		self.instanceTable = CTkTable(self.detailsFrame,row=5,column=2,values=[])
		self.instanceTable.grid(row=1,column=0)
		self.instanceTable.insert(row=0,column=0,value="Instance Name")
		self.instanceTable.insert(row=1,column=0,value="Curseforge Modpack?")
		self.instanceTable.insert(row=2,column=0,value="Server Type")
		self.instanceTable.insert(row=3,column=0,value="Server Type Version")
		self.instanceTable.insert(row=4,column=0,value="Minecraft Version")
		self.attachSelectedInstancebtn = CTkButton(self.detailsFrame,text="Attach Instance",state="disabled",command=lambda:self.attachInstance())
		self.attachSelectedInstancebtn.grid(row=6,column=0,columnspan=2)
		self.closebtn = CTkButton(self.root,text="Close",command=lambda:self.root.destroy())
		self.closebtn.grid(row=1,column=0)

		self.treeview.configure(yscrollcommand=self.treeviewScrollbar.set)
		self.treeview.bind("<<TreeviewSelect>>",self.onTreeviewSelect_displayConfig)

		self.populateTreeview()
		return
	
	def attachInstance(self):
		global MinecraftServerProperties
		global InstanceAttached
		from main import onLoadConfig
		#We need to do some things
		selectedInstance = self.treeview.focus()
		selectedInstance_text = self.treeview.item(selectedInstance,'text')
		if selectedInstance_text in self.instances_vanilla_raw:
			instance_path = str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{selectedInstance_text}"
			ServerFileIO.onExit_setInstancePointer(instanceName=selectedInstance_text,category="Vanilla")
		elif selectedInstance_text in self.instances_modded_raw:
			instance_path = str(rootFilepath) + f"/base/sandbox/Instances/Modded/{selectedInstance_text}"
			ServerFileIO.onExit_setInstancePointer(instanceName=selectedInstance_text,category="Modded")
		elif selectedInstance_text in self.instances_custom_raw:
			instance_path = str(rootFilepath) + f"/base/sandbox/Instances/Custom/{selectedInstance_text}"
			ServerFileIO.onExit_setInstancePointer(instanceName=selectedInstance_text,category="Custom")
		print(f"[Minerva Server Crafter]: Loading {selectedInstance_text}...")
		#Load the config
		onLoadConfig = True
		InstanceAttached = True
		print("[Minerva Server Crafter]: Instance Attached.")
		return
		

	def populateTreeview(self):
		for x in self.instances:
			self.treeview.insert("",END,text=str(x))
		return

	def onTreeviewSelect_displayConfig(self, event):
		selectedItem = self.treeview.focus()
		if not selectedItem:
			self.root.geometry("467x271")
			return

		selectedItem_text = self.treeview.item(selectedItem,'text')
		# Get the instance path
		if selectedItem_text in self.instances_vanilla_raw:
			instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{selectedItem_text}"
		elif selectedItem_text in self.instances_modded_raw:
			instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Modded/{selectedItem_text}"
		elif selectedItem_text in self.instances_custom_raw:
			instancePath = str(rootFilepath) + f"/base/sandbox/Instances/Custom/{selectedItem_text}"
		else:
			print(f"[WARN] Selected item '{selectedItem}' was not found in any known instance list.")
			return  # Avoid accessing undefined variable

		try:
			with open(str(instancePath) + "/config.json") as instanceConfig:
				config_data = json.load(instanceConfig)
		except FileNotFoundError:
			print(f"[ERROR] config.json not found at {instancePath}")
			return
		except json.JSONDecodeError as e:
			print(f"[ERROR] Failed to parse JSON: {e}")
			return

		# Continue processing if file was successfully read
		instanceName = config_data['Instance Name']
		curseforgeBool = True if os.path.isdir(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/{instanceName}") else False
		curseforge_text = "Yes" if curseforgeBool else "No"
		server_type = config_data['server_type']
		server_type_version = config_data['server_type_version']
		minecraft_version = config_data['minecraft_version']

		# Set the values
		self.instanceTable.insert(row=0, column=1, value=str(instanceName))
		self.instanceTable.insert(row=1, column=1, value=str(curseforge_text))
		self.instanceTable.insert(row=2, column=1, value=str(server_type).capitalize())
		self.instanceTable.insert(row=3, column=1, value=str(server_type_version))
		self.instanceTable.insert(row=4, column=1, value=str(minecraft_version))

		# Enable Attach Instance
		self.attachSelectedInstancebtn.configure(state="normal")
		self.root.geometry("523x271")

		#Update the Image
		for __server_type in ServerType:
			if __server_type == "fabric":
				if __server_type == str(server_type):
					self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/fabric_source.png"))
			else:
				if __server_type == "forge":
					if __server_type == str(server_type):
						self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/forge_source.png"))
				else:
					if __server_type == "spigot":
						if __server_type == str(server_type):
							self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/spigot_source.png"))
					else:
						if __server_type == "vanilla":
							if __server_type == str(server_type):
								self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/minecraft_vanilla_source.png"))
						else:
							if __server_type == "craftbukkit":
								if __server_type == str(server_type):
									self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/craftbukkit_source.png"))
							else:
								if __server_type == "purpur":
									if __server_type == str(server_type):
										self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/purpur_source.png"))
								else:
									if __server_type == "custom":
										if __server_type == str(server_type):
											self.instanceImage.configure(dark_image=Image.open(str(rootFilepath) + "/base/assets/images/custom_server_jar.png"))
		return

class splashUI():
	#Point to the splash logo
	def __init__(self):
		splash_imagePath = str(rootFilepath) + "/base/assets/images/splash_startup.png"

		self.splashRoot = CTkToplevel()
		#Store the parent window
		if sys.platform.startswith("win32"):
			self.splashRoot.after(200,lambda:self.splashRoot.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
		if sys.platform.startswith("linux"):
			self.splashRoot.after(200,lambda:self.splashRoot.iconbitmap("@" + str(rootFilepath) + "/base/assets/icons/minecraftservercrafter-icon.xbm"))
		if sys.platform.startswith("darwin"):
			#Unsure if this will work, will pay close attention to Mac Users
			self.splashRoot.after(200,lambda:self.splashRoot.iconbitmap(str(rootFilepath) + "/base/assets/icons/Mac_icon-minecraftservercrafter.icns"))
		self.splashRoot.overrideredirect(True)
		self.splashRoot.attributes('-topmost',True)
		#Place it at the center
		screen_width = self.splashRoot.winfo_screenwidth()
		screen_height = self.splashRoot.winfo_screenheight()

		x = (screen_width - 620) // 2
		y = (screen_height - 300) // 2

		self.splashRoot.geometry(f"620x300+{x}+{y}")
		self.splashRoot_ImageData = Image.open(splash_imagePath)
		self.splashRoot_Image = CTkImage(dark_image=self.splashRoot_ImageData,size=(620,300))
		self.splashRoot_ImageLabel = CTkLabel(self.splashRoot,text=" ",image=self.splashRoot_Image)
		self.splashRoot_ImageLabel.pack()
		self.splashRoot_Attribution = CTkLabel(self.splashRoot_ImageLabel,text="Binary Wave Image Made by - kjpargeter2018 \nBinary Wave Image Provided by - Veectzy.com")
		self.splashRoot_Attribution.grid(row=0,column=0,sticky=SW)
		self.splashRoot.after(4100,lambda:self.splashRoot.destroy())
		return

class AboutDialogWindowClass():
	def __init__(self,parent):
		self.root = CTkToplevel(parent)
		if sys.platform.startswith("win32"):
			parent.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
		if sys.platform.startswith("linux"):
			parent.after(200,lambda:self.root.iconbitmap("@" + str(rootFilepath) + "/base/assets/icons/minecraftservercrafter-icon.xbm"))
		if sys.platform.startswith("darwin"):
			#Unsure if this will work, will pay close attention to Mac Users
			parent.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/Mac_icon-minecraftservercrafter.icns"))
		self.root.geometry("800x630")
		self.root.title("Minerva Server Crafter" + str(releaseVersion) + " - About")
		#Create Widgets
		self.aboutFrame = CTkFrame(self.root)
		self.aboutFrame.grid(row=0,column=0,sticky=NS)
		self.aboutTreeview = Treeview(self.root)
		self.aboutTreeview.grid(row=0,column=0,sticky=NS)
		self.aboutTreeview.rowconfigure(index=0,weight=1)
		itemRoot = self.aboutTreeview.insert("",END,text="Licenses",open=True) #Parent element
		self.aboutTreeview.insert(itemRoot,END,text="Curseforge API",iid=120)
		self.aboutTreeview.insert(itemRoot,END,text="Fabric API",iid=121)
		self.aboutTreeview.insert(itemRoot,END,text="Purpur API",iid=122)
		self.aboutTreeview.insert(itemRoot,END,text="BuildTools",iid=123)
		self.aboutTreeview.insert(itemRoot,END,text="Mojang API",iid=126)
		self.aboutTreeview.insert(itemRoot,END,text="Modpack Index API",iid=119)
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
		licenseDirectory = str(rootFilepath) + f"/base/assets/licensing/{selectedItem}/"
		with open(str(licenseDirectory) + f"{selectedItem} License.txt","r") as licenseTXT:
			self.licenseText.configure(state=NORMAL)
			self.licenseText.delete(1.0,END)
			self.licenseText.insert(END,licenseTXT.read())
			self.licenseText.configure(state=DISABLED)
			licenseTXT.close()
		return
	
class ConsoleShell(CTkFrame):
	'Creates a console-like widget. While includeInput is set to True, ConsoleShell toggles an user input'
	def __init__(self,parent,includeInput=True):
		self.parent = parent
		super().__init__(self.parent,bg_color="transparent",fg_color="gray")
		self.inputBool = includeInput
		self.process2 = None
		self.outputThread = None
		self.pauseEvent = threading.Event()
		self.ServerIsRunning = False
		self.grid(row=0,column=0,sticky="nsew")
		self.ConsoleCanvas = CTkFrame(self,bg_color="transparent")
		self.ConsoleCanvas.grid(row=0,column=0,sticky="nsew",padx=3,pady=3)
		self.ConsoleOut = CTkTextbox(self.ConsoleCanvas,width=400,state="disabled",bg_color="gray")
		self.ConsoleOut.pack(fill=BOTH,expand=True,anchor="center")
		self.ConsoleOut.tag_config("stderr",foreground="#b22222")
		self.InputCanvas = CTkFrame(self,bg_color="transparent")
		self.InputCanvas.grid(row=1,column=0,sticky="nsew",pady=3,padx=3)
		self.ConsoleIn = CTkEntry(self.InputCanvas,placeholder_text="Input a command",bg_color="gray")
		self.ConsoleIn.pack(fill=X,ipadx=200,side=LEFT)
		self.SendBtn = CTkButton(self.InputCanvas,text="Send",bg_color="gray",command=lambda:self.ServerProcess_OnTransmitInput())
		self.SendBtn.pack(side=RIGHT)
		self.ConsoleIn.bind("<Return>",lambda event:self.ServerProcess_OnTransmitInput(event=event))
		if self.inputBool == False:
			self.InputCanvas.grid_remove()
		self.rowconfigure(0,weight=1)
		self.rowconfigure(1,weight=2)
		self.columnconfigure(0,weight=1)
		return

	def configure(self, cnf=None, **kwargs):
		if "includeInput" in kwargs:
			new_value = kwargs.pop("includeInput")
			if new_value != self.inputBool:
				self.inputBool = new_value
				if self.inputBool:
					self.InputCanvas.grid(row=1, column=0, sticky="nsew", pady=3, padx=3)
				else:
					self.InputCanvas.grid_remove()
		super().configure(cnf, **kwargs)
		return

	def SaveConsoleToFile(self,start,end):
		'SaveConsoleToFile(startingIndex,EndingIndex) -> File Operation \n \n Saves the Console Shell Text to a log file.'

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
		self.currentIndex = self.ConsoleOut.index(index)
		self.ConsoleOut.configure(state="normal")
		self.ConsoleOut.insert(index,str(string) + '\n')
		self.ConsoleOut.configure(state="disabled")
		self.ConsoleOut.see(END)
		return
	
	def ServerProcess_OnTransmitInput(self,event=None):
		'Passes input to stdin of the Minecraft Server on its own Thread. \nIf the server isn\'t running, nothing is sent to the subprocess. Requires includeInput set to True'
		if self.inputBool:
			def SendInput():
				try:
					if 'outputThread' in globals():
						if self.process2.returncode is None and ServerIsRunning == True:
							inputQuery = str(self.ConsoleIn.get())
							self.updateConsole(END, "[Minecraft Server Crafter]: <User-Input>: " + str(inputQuery))
							self.process2.stdin.write(str(inputQuery))
							self.process2.stdin.write('\n')  # Add a newline character to simulate pressing Enter
							self.process2.stdin.flush()
							self.ConsoleIn.delete(0,END)
							for line in self.process2.stdout:
								self.updateConsole(END, "[Minerva Server Crafter]: <Server-IO>: " + line.strip())
								continue
							return

					else:
						self.updateConsole(END, '[Minerva Server Crafter]: Server is not running. Will not proceed')
						self.ConsoleIn.delete(0, END)
						return
				except Exception as e:
					print(f"[Minerva Server Crafter]: Error while sending input: {str(e)}")
					self.ConsoleIn.delete(0,END)
					return

			try:
				inputThread = threading.Thread(target=SendInput,name="Minecraft Server Input Processing",daemon=True)
				inputThread.start()
				return
			except SystemExit:
				inputThread.join()
				return

	def beginServerProcess(self, instanceName=None, memoryAllocation=False, initialMemory=0, maxMemory=0):
		'''
		Begins the Minecraft Server. If memoryAllocation is True, then memory allocation (measured in MB or GB)
		for the Java VM is included in building the java command, otherwise it's exempted.
		The initialMemory parameter sets the minimum memory, and the maxMemory sets the maximum memory.
		'''
		global InstanceAttached
		from base.modules.utils import SoftwareSpec

		def print_output(process):
			global ServerIsRunning
			for line in process.stdout:
				self.updateConsole("end", "[Minerva Server Crafter]: <Server-IO>: " + line.strip())
				time.sleep(0.1)
			returnCode = process.wait()
			self.updateConsole("end", "[Minerva Server Crafter]: Command exited with the return code " + str(returnCode))
			ServerIsRunning = False
			return

		if InstanceAttached:
			# Retrieve the instance data from the JSON model using getJSONInstanceDatabyName
			instanceData = ServerFileIO.getLastConfigData()
			#We need memory
			hardwareData = HardwareSpec()
			instancetype = instanceData['category']
			instancePath = instanceData['path']
			with open(str(instancePath) + "/config.json","r") as instance_config:
				_json_data = json.load(instance_config)
			serverType_text = _json_data['server_type']
			if serverType_text == "forge":
				isForge = True
			else:
				isForge = False

			# Build the Java command based on memory allocation settings
			cmd = ['java']
			if memoryAllocation:
				memoryUnit = 'G' if hardwareData.InstalledMemory[1] == "GB" else 'M'
				cmd.extend([f'-Xms{initialMemory}{memoryUnit}', f'-Xmx{maxMemory}{memoryUnit}'])

			if isForge:
				# Use specific arguments for Forge servers
				argFile = 'win_args.txt' if operatingSystem == "Windows" else 'unix_args.txt'
				cmd.extend(['-XX:+UseG1GC','-XX:MaxGCPauseMillis=50',f'@libraries/net/minecraftforge/forge/1.19.2-43.2.0/{argFile}', '-nogui'])
			else:
				if instancetype == "Modded":
					#We need to check what the modded instance is
					modloaderData = instanceData['modloader']
					modloadername = modloaderData['id']
					if modloadername == "fabric":
						#point to the fabric jar
						cmd.extend(['-XX:+UseG1GC','-XX:MaxGCPauseMillis=50','-jar', 'fabric-server-launch.jar', '-nogui'])
				else:
					# Standard command for Vanilla servers
					cmd.extend(['-XX:+UseG1GC','-XX:MaxGCPauseMillis=50','-jar', 'server.jar', '-nogui'])

			# Update console output
			self.updateConsole("end", "[Minerva Server Crafter]: Using java command: " + ' '.join(cmd))
			time.sleep(0.1)

			# Display server launch details
			self.updateConsole("end", "[Minerva Server Crafter]: Pre-Server Startup Phase: Updating server.properties...")
			time.sleep(5)

			# Update server properties and configuration files
			ServerFileIO.convertInstancePropertiestoPropertiesFile(instanceName=str(instanceName), filepath=instancePath, bypassSaveLocation=True)

			# Update JSON bans and whitelist
			self.updateConsole("end", "[Minerva Server Crafter]: Pre-Server Startup Phase: Updating JSON Bans...")
			time.sleep(5)
			ServerFileIO.exportplayerBansToJSON(serverpath=instancePath)
			ServerFileIO.exportIPBansToJSON(serverpath=instancePath)

			self.updateConsole("end", "[Minerva Server Crafter]: Pre-Server Startup Phase: Update Whitelist...")
			time.sleep(5)
			ServerFileIO.exportWhitelistfromDatabase(serverdir=instancePath)

			# All done, start the server!
			self.updateConsole("end", "[Minerva Server Crafter]: Starting Server...")
			with SoftwareSpec.changeDir(path=str(instancePath)):
				try:
					# Run the server command
					self.ServerIsRunning = True
					self.process2 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True)
					self.outputThread = threading.Thread(target=print_output, args=(self.process2,), name="Minecraft Server Output")
					self.outputThread.start()

				except Exception as e:
					# Handle any exceptions during the server launch
					self.displayException(e)

				finally:
					self.process2 = None
					self.outputThread = None
					self.updateConsole(END,"[Minerva Server Crafter]: Server has been terminated.")
					return
		else:
			self.updateConsole(END,"[Minerva Server Crafter]: Instance has not been loaded yet. Will not proceed.")
			return

class NewPurPurInstance():
	def __init__(self):
		self.buildListing = []
		self.minecraftVersions = MCSCUpdater.PurpurBaseClass.getCompatibleVersions()

		#Create Widget
		self.root = CTkToplevel()
		self.root.title("New Purpur Instance")
		self.frame = CTkFrame(self.root)
		self.frame.grid(row=0,column=0)
		self.instanceNameLabel = CTkLabel(self.frame, text="Instance Name: ")
		self.instanceNameLabel.grid(row=0,column=0)
		self.instanceNameEntry = CTkEntry(self.frame,placeholder_text="This is what we are calling the instance")
		self.instanceNameEntry.grid(row=0,column=1)
		self.minecraftVersionLabel = CTkLabel(self.frame,text="Minecraft Version: ")
		self.minecraftVersionLabel.grid(row=1,column=0)
		self.minecraftVersionListing = CTkComboBox(self.frame,values=self.minecraftVersions,command=lambda v: self.getBuildListing())
		self.minecraftVersionListing.grid(row=1,column=1)
		self.purpurBuildLabel = CTkLabel(self.frame,text="Purpur Build: ")
		self.purpurBuildLabel.grid(row=2,column=0)
		self.purpurBuildListing = CTkComboBox(self.frame,values=" ")
		self.purpurBuildListing.grid(row=2,column=1)
		self.generateBtn = CTkButton(self.frame,text="Generate",command=self.generate)
		self.generateBtn.grid(row=3,column=0)
		self.closeBtn = CTkButton(self.root,text="Close",command=lambda:self.root.destroy())
		self.closeBtn.grid(row=1,column=0,columnspan=2,pady=5)
		return

	def getBuildListing(self):
		mcVersion = self.minecraftVersionListing.get()
		#Parse for buildIDs
		buildListing = MCSCUpdater.PurpurBaseClass.getBuildsbyVersion(version=mcVersion)
		#Is the buildlisting populated?
		currentBuildCount = len(self.buildListing)
		if currentBuildCount >= 1:
			self.buildListing.clear()
		for build_id in buildListing:
			self.buildListing.append(str(build_id))
		self.purpurBuildListing.configure(values=self.buildListing)
		return

	def generate(self):
		from base.modules.utils import SoftwareSpec
		instance_Name = self.instanceNameEntry.get()
		minecraftVersion = self.minecraftVersionListing.get()
		build_id = self.purpurBuildListing.get()
		url = f"https://api.purpurmc.org/v2/purpur/{minecraftVersion}/{build_id}/download"
		instanceData = InstanceFramework()
		instanceData.generateInstanceSchema(instance_name=str(instance_Name),server_type="purpur",minecraft_version_=str(minecraftVersion))
		instanceData.createInstanceConfig(instance_name=str(instance_Name),serverType="purpur",server_type_version=str(build_id),minecraft_version=str(minecraftVersion))
		#Get the server jar
		response = requests.get(url=url)
		if response.status_code == 200:
			#Save it to the instace folder
			with open(str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_Name}/purpur-{minecraftVersion}-{build_id}.jar","wb") as purpurJar:
				purpurJar.write(response.content)
				purpurJar.close()
			#Generate the server
			with SoftwareSpec.changeDir(path=str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_Name}"):
				with open(str(rootFilepath) + f"/base/sandbox/Instances/Vanilla/{instance_Name}/eula.txt",'w') as eulaFile:
					eulaFile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Thu Jun 20 22:35:39 EDT 2024\neula=true")
					eulaFile.close()
			print("[Minerva Server Crafter]: Instance Generated.")
			self.root.destroy()
			return

class ResourcePackWindow():
	def closeWindow(self): #original, I know xD
		self.root.grab_release()
		self.root.destroy()
		return

	def updateResourcePackValues(self):
		global ConsoleWindow

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

class ServerTypeInstallerUI():
	def __init__(self,parent,installerProcess=None,installerThread=None,servertype=None):
		self.parent = parent
		self.installer = installerProcess
		self.thread = installerThread
		if servertype is not None:
			self.servertypeName = [x.capitalize() for x in ServerType if servertype.lower() == x.lower()]
			self.servertypeName = self.servertypeName[0]
			self.process_ThreadisAliveSignalBool = installerThread.is_alive()
			if self.servertypeName == "Server":
				#This is a minecraft vanilla name. This class is meant for servers with installers
				raise MCSCInternalError("Minecraft Vanilla Detected. Will not proceed.")
			self.root = CTkToplevel(self.parent)
			self.root.title(f"{self.servertypeName} Server Installation")
			self.consoledialogFrame = CTkFrame(self.root)
			self.consoledialogFrame.pack(fill=BOTH,expand=True)
			self.progressBarFrame = CTkFrame(self.consoledialogFrame)
			self.progressBarFrame.grid(row=1,column=0,columnspan=3,pady=5,ipadx=15)
			self.progressBar = CTkProgressBar(self.progressBarFrame)
			self.progressBar.pack(fill=BOTH,expand=True,anchor=W,side=RIGHT)
			self.consoleWindow = ConsoleShell(self.consoledialogFrame,includeInput=False)
			self.progressBar.set(0)
			if self.installerSignal(thread=installerThread) == True:
				#The thread is alive
				self.returncode = self.installerOutputLines()
				if self.returncode == 0:
					self.root.destroy()
					installerThread.join()
			return
		else:
			raise MCSCInternalError("Must provide the Server Type")

	def installerOutputLines(self):
		for line in self.installerProcess.stdout:
			self.consoleWindow.updateConsole(END,f"<{self.servertypeName}-Installer-Output>: " + line.decode('ascii').strip("\n"))
			time.sleep(0.1)
		returnCode = self.installer.wait()
		print(f"Command exited with the return code {returnCode}")
		return returnCode

	def installerSignal(self):
		'Returns threading.is_alive() bool'
		self.process_ThreadisAliveSignalBool = self.thread.is_alive()
		return self.process_ThreadisAliveSignalBool

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

class NewVanillaInstance():
	def __init__(self):
		self.root = CTkToplevel()
		self.types = [item for item in ServerType if item not in ["fabric", "forge", "purpur", "custom"]]

		# Set window icon based on platform
		icon_path = {"win32": f"{rootFilepath}/base/assets/icons/minecraftservercrafter.ico","linux": f"@{rootFilepath}/base/assets/icons/minecraftservercrafter-icon.xbm","darwin": f"{rootFilepath}/base/assets/icons/Mac_icon-minecraftservercrafter.icns"}.get(sys.platform, None)
		if icon_path:
			self.root.after(200, lambda: self.root.iconbitmap(icon_path))

		self.root.title("New Vanilla Instance")
		self.instanceFrame = CTkFrame(self.root)
		self.instanceFrame.grid(row=0, column=0)

		# Instance Name
		self.instanceNameLabel = CTkLabel(self.instanceFrame, text="Instance Name: ")
		self.instanceNameLabel.grid(row=0, column=0)
		self.instanceNameEntry = CTkEntry(self.instanceFrame, placeholder_text="This is what you're calling the Instance")
		self.instanceNameEntry.grid(row=0, column=1)

		# Server Type
		self.servertypeLabel = CTkLabel(self.instanceFrame, text="Server Type: ")
		self.servertypeLabel.grid(row=1, column=0)
		self.servertypeDropdown = CTkComboBox(self.instanceFrame, values=self.types)
		self.servertypeDropdown.grid(row=1, column=1)

		# Minecraft Version
		self.minecraftVersionLabel = CTkLabel(self.instanceFrame, text="Minecraft Version: ")
		self.minecraftVersionLabel.grid(row=2, column=0)
		self.minecraftVersionDropdown = CTkComboBox(self.instanceFrame)
		self.minecraftVersionDropdown.grid(row=2, column=1)

		# Buttons
		self.generatebtn = CTkButton(self.instanceFrame, text="Generate Instance", command=self.generateInstance)
		self.generatebtn.grid(row=3, column=0, columnspan=2)
		self.closebtn = CTkButton(self.root, text="Close", command=self.root.destroy)
		self.closebtn.grid(row=1, column=0, pady=5)
		self.populateVersions()
		return

	def populateVersions(self):
		servertype = self.servertypeDropdown.get()
		if servertype in ["spigot", "craftbukkit"]:
			versions = MCSCUpdater.SpigotBaseClass.getVersionListing()
		elif servertype == "vanilla":
			versions = ServerVersion_Control.getVersionList()
		else:
			versions = []

		self.minecraftVersionDropdown.configure(values=versions)
		if versions:
			self.minecraftVersionDropdown.set(versions[0])

	def generateInstance(self):
		instanceName = self.instanceNameEntry.get()
		servertype = self.servertypeDropdown.get()
		mcversion = self.minecraftVersionDropdown.get()
		instance_path = str(rootFilepath) + f"/base/sandbox/Instances/"
		plugins = os.path.join(instance_path,"/plugins")
		pluginListing = []
		if servertype in ["spigot","craftbukkit"]:
			for root,dirs,files in os.walk(str(plugins)):
				for file in files:
					fileTarget = os.path.join(root,file)
					pluginName = os.path.basename(fileTarget)
					pluginListing.append(pluginName)
		instance = InstanceFramework()
		instance.generateInstanceSchema(instance_name=instanceName, server_type=servertype, minecraft_version_=mcversion)
		pluginCount = len(pluginListing)
		if pluginCount <= 1:
			instance.createInstanceConfig(instance_name=instanceName, mod_list=pluginListing, serverType=servertype, server_type_version=mcversion, minecraft_version=mcversion)
		else:
			instance.createInstanceConfig(instance_name=instanceName, mod_list=[], serverType=servertype, server_type_version=mcversion, minecraft_version=mcversion)

		if servertype == "spigot":
			MCSCUpdater.SpigotBaseClass.getSpigot(version=mcversion, instance_name=instanceName)
			for Root,Dirs,Files in os.walk(str(program_folder) + "/build/BuildTools"):
				for f in Files:
					targetFile = os.path.join(Root,f)
					file_ = os.path.basename(targetFile)
					if file_.startswith("spigot-"):
						shutil.move(targetFile,os.path.join(str(rootFilepath),f"/base/sandbox/Instances/{servertype.capitalize()}/{instanceName}/"))
						break
			print("[Minerva Server Crafter - Instance Generator]: Spigot has been successfully generated, and moved to Instance folder.")
		elif servertype == "vanilla":
			ServerVersion_Control.downloadvanillaserverfile(version=mcversion)
			shutil.move(f"{program_folder}/build/Minecraft Vanilla/{mcversion}/server.jar",f"{rootFilepath}/base/sandbox/Instances/{servertype.capitalize()}/{instanceName}")
			print("[Minerva Server Crafter - Instance Generator]: Minecraft Vanilla has been successfully generated and moved to the Instance folder")
		elif servertype == "craftbukkit":
			MCSCUpdater.SpigotBaseClass.getCraftbukkit(version=mcversion, instance_name=instanceName)
			for Root,Dirs,v in os.walk(str(program_folder) + "/build/BuildTools"):
				for f_ in v:
					target_File = os.path.join(Root,f_)
					f_ = os.path.basename(target_File)
					if f_.startswith("craftbukkit-"):
						shutil.move(target_File,os.path.join(rootFilepath,f"/base/sandbox/Instances/{servertype.capitalize()}/{instanceName}/"))
						break
			print("[Minerva Server Crafter - Instance Generator]: Craftbukkit has been successfully generated and moved to the Instance folder")
		#Backup the instance
		with open(str(instance_path) + f"/{servertype.capitalize()}/{instanceName}/config.json","r") as json_config:
			configDump = json.load(json_config)
			json_config.close()
		with open(str(instance_path) + f"/{servertype.capitalize()}/{instanceName}/schema_instance.json","r") as json_schema:
			schemaDump = json.load(json_schema)
			json_schema.close()
		#Create a zip archive
		filepathTarget = str(instance_path) + f"/{servertype.capitalize()}/{instanceName}"
		fileBlacklist = ["config.json","schema_instance.json","instance_data.zip"]
		with zipfile.ZipFile(str(filepathTarget) + "/instance_data.zip","w",zipfile.ZIP_DEFLATED) as instanceArchive_write:
			for root, dirs, files in os.walk(filepathTarget):
				for file in files:
					file_path = os.path.join(root, file)
					# Relative path from the root folder
					rel_path = os.path.relpath(file_path, start=filepathTarget)

					# Exclude files only if they are in the root folder
					if file in fileBlacklist and os.path.dirname(rel_path) == "":
						continue

					instanceArchive_write.write(file_path, arcname=rel_path)
					instanceArchive_write.close()
		archivePath = str(filepathTarget) + "/instance_data.zip"
		instance_archivePath = str(filepathTarget) + "/instance_backup.msczip"
		with zipfile.ZipFile(str(archivePath),"r") as instanceBackup:
			instance_archive = MSCZipLib(schema=schemaDump,instanceData=configDump,zipobj=instanceBackup,disablePrompt=True,destination=str(instance_archivePath))
			instanceBackup.close()
		instance_archive.createMSCArchive()
		return

class NewModdedInstance():
	def __init__(self):
		self.root = CTkToplevel()
		self.root.title("New Modded Instance")
		if sys.platform.startswith("win32"):
			self.root.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
		if sys.platform.startswith("linux"):
			self.root.after(200,lambda:self.root.iconbitmap("@" + str(rootFilepath) + "/base/assets/icons/minecraftservercrafter-icon.xbm"))
		if sys.platform.startswith("darwin"):
			#Unsure if this will work, will pay close attention to Mac Users
			self.root.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/Mac_icon-minecraftservercrafter.icns"))
		self.servertypes = []
		self.mcListing = ServerVersion_Control.getVersionList()
		for _item in ServerType:
			if _item == "spigot" or _item == "vanilla" or _item == "craftbukkit" or _item == "purpur" or _item == "custom":
				continue
			else:
				self.servertypes.append(_item)
				continue
		self.frame = CTkFrame(self.root)
		self.frame.grid(row=0,column=0)
		self.instanceNameLabel = CTkLabel(self.frame,text="Instance Name: ")
		self.instanceNameLabel.grid(row=0,column=0)
		self.instanceNameEntry = CTkEntry(self.frame,placeholder_text="This is what you are calling the Instance")
		self.instanceNameEntry.grid(row=0,column=1)
		#Server Types
		self.mcversionLabel = CTkLabel(self.frame,text="Minecraft Version: ")
		self.mcversionLabel.grid(row=1,column=0)
		self.mcversionCombo = CTkComboBox(self.frame,values=self.mcListing)
		self.mcversionCombo.grid(row=1,column=1)
		self.servertypesLabel = CTkLabel(self.frame,text="Server Type: ")
		self.servertypesLabel.grid(row=2,column=0)
		self.ServerTypeCombo = CTkComboBox(self.frame,values=self.servertypes,command=lambda _:self.setTypeListing())
		self.ServerTypeCombo.grid(row=2,column=1)
		self.serverversionLabel = CTkLabel(self.frame,text="Server Type Version: ")
		self.serverversionLabel.grid(row=3,column=0)
		self.serverversionCombo = CTkComboBox(self.frame,state="disable")
		self.serverversionCombo.grid(row=3,column=1)
		self.generateButton = CTkButton(self.frame,text="Generate")
		self.generateButton.grid(row=4,column=0,columnspan=2)
		self.closeBtn = CTkButton(self.root,text="Close",command=lambda: self.root.destroy())
		self.closeBtn.grid(row=1,column=0,pady=5)

		#Event Binds

		return

	def setTypeListing(self):
		typeSelected = self.ServerTypeCombo.get()
		if typeSelected == "fabric":
			versionListing = []
			#Parse the table
			MCSCDatabase = sqlite3.connect("mcsc_data.db")
			MCSC_Cursor = MCSCDatabase.cursor()
			MCSC_Cursor.execute("SELECT * FROM fabricVersion_Table")
			currentVersions = {row[0]:row[1] for row in MCSC_Cursor.fetchall()}
			for key in currentVersions:
				versionListing.append(key)
			self.serverversionCombo.configure(state="normal",values=versionListing)
			return
		else:
			if typeSelected == "forge":
				mcVersion = self.mcversionCombo.get()
				versionListing = MCSCUpdater.ForgeBaseClass.getForgeVersionsbyVersion(version=str(mcVersion))
				self.serverversionCombo.configure(state="normal",values=versionListing)
				return

class NewCustomJarInstance():
	def __init__(self):
		#Think experimental build
		self.path = ""
		self.mc_versions = ServerVersion_Control.getVersionList()

		self.root = CTkToplevel()
		self.root.title("Minerva Server Crafter - New Custom Jar Instance")

		self.frame = CTkFrame(self.root)
		self.frame.grid(row=0,column=0)
		self.instancenameLabel = CTkLabel(self.frame, text="Instance Name: ")
		self.instancenameLabel.grid(row=0,column=0,sticky=E)
		self.instancenameEntry = CTkEntry(self.frame,placeholder_text="This is what we are calling the instance")
		self.instancenameEntry.grid(row=0,column=1,ipadx=100,sticky=W)
		#We need more info
		self.logicBehaviorFrame = CTkFrame(self.frame)
		self.logicBehaviorFrame.grid(row=1,column=0,columnspan=2)
		self.addonbehaviorFrame = CTkFrame(self.logicBehaviorFrame)
		self.addonbehaviorFrame.grid(row=0,column=0,columnspan=3,pady=4)
		self.isModding = CTkCheckBox(self.addonbehaviorFrame,text="Mods only",onvalue=True,offvalue=False,command=lambda:self.logicFilter_onModdingTicked())
		self.isModding.grid(row=0,column=0,sticky=W,padx=5)
		self.isModding_tip = CTkToolTip(widget=self.isModding,message="Treat the instance as if it has mods only")
		self.isPlugins = CTkCheckBox(self.addonbehaviorFrame,text="Plugins only",onvalue=True,offvalue=False,command=lambda:self.logicFilter_onPluginsTicked())
		self.isPlugins.grid(row=0,column=1,sticky=W,padx=5)
		self.isPlugins_tip = CTkToolTip(widget=self.isPlugins,message="Treat the instance as if its using plugins only")
		self.isHybrid = CTkCheckBox(self.addonbehaviorFrame,text="Mods and Plugins",onvalue=True,offvalue=False,command=lambda:self.logicFilter_onHybridTicked())
		self.isHybrid.grid(row=0,column=2,sticky=W,padx=5)
		self.isHybrid_tip = CTkToolTip(self.isHybrid,message="Treat the instance as if its using both Mods and Plugins")
		self.isVanilla = CTkCheckBox(self.addonbehaviorFrame,text="No Mods / Plugins",command=lambda:self.logicFilter_onVanillaTicked())
		self.isVanilla.grid(row=0,column=3,sticky=W,padx=5)
		self.isVanilla_tip = CTkToolTip(widget=self.isVanilla,message="Treat the instance as if it was Vanilla Minecraft")
		self.serverDirectoryLabel = CTkLabel(self.logicBehaviorFrame,text="Server Directory Path: ")
		self.serverDirectoryLabel.grid(row=2,column=0,sticky=E)
		self.serverDirectoryEntryText = CTkEntry(self.logicBehaviorFrame,state="disabled")
		self.serverDirectoryEntryText.grid(row=2,column=1,ipadx=100)
		self.browsebtn = CTkButton(self.logicBehaviorFrame,text="Browse",command=lambda:self.browseforDirectory())
		self.browsebtn.grid(row=2,column=2)
		self.runInDirectory = CTkCheckBox(self.logicBehaviorFrame,text="Ignore Instance Folder",onvalue=False,offvalue=True)
		self.runInDirectory.grid(row=3,column=0)
		self.runInDirectory_tip = CTkToolTip(self.runInDirectory,message="Uses the given directory as a server directory rather than putting the server data in its own folder")
		self.minecraft_versionLabel = CTkLabel(self.logicBehaviorFrame,text="Minecraft Version: ")
		self.minecraft_versionLabel.grid(row=4,column=0,sticky=E)
		self.minecraftVersionListing = CTkComboBox(self.logicBehaviorFrame,values=self.mc_versions)
		self.minecraftVersionListing.grid(row=4,column=1,columnspan=2,ipadx=100,sticky=W)
		self.applybtn = CTkButton(self.logicBehaviorFrame,text="Apply",command=lambda:self.logicFilter_onApply())
		self.applybtn.grid(row=5,column=0,columnspan=3)
		self.closebtn = CTkButton(self.root,text="Close",command=lambda:self.root.destroy())
		self.closebtn.grid(row=1,column=0,columnspan=2)
		return
	
	def logicFilter_onModdingTicked(self):
		moddingCheck = self.isModding.get()
		if moddingCheck == True:
			#disable the others
			self.isPlugins.configure(state="disabled")
			self.isHybrid.configure(state="disabled")
			self.isVanilla.configure(state="disabled")
			return
		else:
			self.isPlugins.configure(state="normal")
			self.isHybrid.configure(state="normal")
			self.isVanilla.configure(state="normal")
			return
	
	def logicFilter_onPluginsTicked(self):
		pluginsCheck = self.isPlugins.get()
		if pluginsCheck == True:
			#disable the others
			self.isModding.configure(state="disabled")
			self.isHybrid.configure(state="disabled")
			self.isVanilla.configure(state="disabled")
			return
		else:
			self.isModding.configure(state="normal")
			self.isHybrid.configure(state="normal")
			self.isVanilla.configure(state="normal")
			return
	
	def logicFilter_onHybridTicked(self):
		hybridCheck = self.isHybrid.get()
		if hybridCheck == True:
			#disable the others
			self.isPlugins.configure(state="disabled")
			self.isModding.configure(state="disabled")
			self.isVanilla.configure(state="disabled")
			return
		else:
			self.isPlugins.configure(state="normal")
			self.isModding.configure(state="normal")
			self.isVanilla.configure(state="normal")
			return
	
	def logicFilter_onVanillaTicked(self):
		hybridCheck = self.isVanilla.get()
		if hybridCheck == True:
			#disable the others
			self.isPlugins.configure(state="disabled")
			self.isModding.configure(state="disabled")
			self.isHybrid.configure(state="disabled")
			return
		else:
			self.isPlugins.configure(state="normal")
			self.isModding.configure(state="normal")
			self.isHybrid.configure(state="normal")
			return
	
	def browseforDirectory(self):
		targetDirectory = filedialog.askdirectory(title="Select Minecraft Server Directory")
		if targetDirectory == "":
			return
		self.serverDirectoryEntryText.configure(state="normal")
		self.serverDirectoryEntryText.insert(END,str(targetDirectory))
		self.serverDirectoryEntryText.configure(state="disabled")
		return
	
	def logicFilter_onApply(self):
		#Check what checkbox is checked
		instance_name = self.instancenameEntry.get()
		hybridCheck = self.isHybrid.get()
		moddedCheck = self.isModding.get()
		pluginCheck = self.isPlugins.get()
		regularCheck = self.isVanilla.get()
		server_path = self.serverDirectoryEntryText.get()
		parent_pathing = self.runInDirectory.get()
		minecraft_version = self.minecraftVersionListing.get()
		try:
			if hybridCheck == True:
				logicBehavior = "both"
			elif moddedCheck == True:
				logicBehavior = "modding"
			elif pluginCheck == True:
				logicBehavior = "plugins"
			elif regularCheck == True:
				logicBehavior = "neither"
		finally:
			try:
				if parent_pathing == False:
					#We need to put the server directory contents in the Instance Folder
					os.mkdir(str(rootFilepath) + f"/base/sandbox/Instances/Custom/{instance_name}")
					for r, d, f in os.walk(server_path):
						for dir in d:
							source_dir = os.path.join(r, dir)
							rel_path = os.path.relpath(source_dir, server_path)
							dest_dir = os.path.join(rootFilepath, "base", "sandbox", "Instances", "Custom", instance_name, rel_path)
							if not os.path.exists(dest_dir):
								shutil.copytree(source_dir, dest_dir)
						for file in f:
							source_file = os.path.join(r, file)
							rel_path = os.path.relpath(source_file, server_path)
							dest_file = os.path.join(rootFilepath, "base", "sandbox", "Instances", "Custom", instance_name, rel_path)
							dest_dir = os.path.dirname(dest_file)
							if not os.path.exists(dest_dir):
								os.makedirs(dest_dir)
							shutil.copy2(source_file, dest_file)
					#Statically set the folder to the Instance Folder
					server_path = str(rootFilepath) + f"/base/sandbox/Instances/Custom/{instance_name}"
			finally:
				#generate logic
				logic = {'logic_behavior': str(logicBehavior),'ServerHasParentDirectory': parent_pathing, 'server_path': server_path}
				instanceLogicBase = InstanceFramework()
				instanceLogicBase.generateInstanceSchema(instance_name=str(instance_name),server_type="custom",minecraft_version_=str(minecraft_version))
				instanceLogicBase.createInstanceConfig(instance_name=str(instance_name),serverType="custom",custom_data=logic,server_type_version="N/A",minecraft_version=str(minecraft_version))
				return

class ModIsClientWarning:
	def __init__(self, *args, **kwargs):
		raise RuntimeError("Use ModIsClientWarning.ask(modID=...) instead of calling the class directly.")

	@classmethod
	def ask(cls, modID=None):
		# We move actual logic into a hidden inner class
		class _ActualWarningDialog:
			def __init__(self, modID):
				from base.modules.utils import CurseforgeClass
				self.curseforge = CurseforgeClass()
				self.mod_idDataRaw = self.curseforge.parseID(targetType='get-object-data', objectID=modID)
				self.modData = self.mod_idDataRaw['data']
				self.modName = self.modData['name']
				self.choiceResult = None
				#Create Widgets
				self.root = CTkToplevel()
				self.root.title("WARNING‼️ Client mod detected‼️")
				self.root.protocol("WM_DELETE_WINDOW", self.onDecline)
				self.message = CTkLabel(self.root,text=f"{self.modName} is potentially a client mod. Adding client mods to a server will prevent the server from\nstarting. However, some client mods are made to also run on a server(Ex. Distant Horizons, Journey Map, etc.). To see if {self.modName} can run on a server, consult\nwith the mod page or the built-in mod viewer. Do you wish to add {self.modName} to the pending items to import?")
				self.message.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
				self.acceptbtn = CTkButton(self.root, text="Yes", command=self.onAccept)
				self.acceptbtn.grid(row=1, column=0, padx=10, pady=10)
				self.declinebtn = CTkButton(self.root, text="No", command=self.onDecline)
				self.declinebtn.grid(row=1, column=2, padx=10, pady=10)
				return

			def onAccept(self):
				self.choiceResult = True
				self.root.destroy()

			def onDecline(self):
				self.choiceResult = False
				self.root.destroy()

		# Create and run dialog
		dialog = _ActualWarningDialog(modID)
		dialog.root.grab_set()
		dialog.root.wait_window()
		return dialog.choiceResult		

class curseforgeUI():
	class CurseforgeModImporter_ModpackTree():
		def __init__(self,parent,**kwargs):
			self.parent = parent
			self.didSearch = False
			self.entries = []
			self.rowEntry = 0
			#Create view
			self.listview = CTkScrollableFrame(self.parent)
			self.listview.pack(fill=BOTH,expand=True)
			self.listview.grid_columnconfigure(0,weight=1)
			return

		def clearAllEntries(self):
			'Removes all entries safely regardless of index values'
			while self.entries:
				entry = self.entries.pop(0)
				for key, widget in entry.items():
					if key.startswith("card_") and widget is not None:
						widget.destroy()
			self.listview.update_idletasks()
			return

		def add_entry(self,title:str | None = None, subtitle:str | None = None, description:str | None = None,icon:Image.Image | None = None,footnotes:str | None = None, objectID:int | None = None):
			#Create entry in the list
			card = CTkFrame(self.listview,corner_radius=0,border_width=2,border_color="#808080")
			card.grid(row=self.rowEntry,column=0,sticky="ew",padx=5,pady=5)
			card.grid_columnconfigure(0, weight=1)   # main content column (text + icon)
			card.grid_columnconfigure(1, weight=0)
			if icon is not None and isinstance(icon,Image.Image):
				icon_image = CTkImage(dark_image=icon,size=(64,64))
				icon_label = CTkLabel(card,image=icon_image,text=" ")
				icon_label.image = icon_image
				icon_label.grid(row=0,column=0,rowspan=3,padx=5,pady=5)
				col_offset = 1
			else:
				col_offset = 0
			title = CTkLabel(card,text=title,font=CTkFont(size=14,weight='bold'))
			title.grid(row=0,column=col_offset,padx=5,sticky=W,pady=(5,0))
			if subtitle is not None and isinstance(subtitle,str) and subtitle != "":
				subtitle = CTkLabel(card,text=subtitle,font=CTkFont(size=12),anchor="n")
				subtitle.grid(row=1,column=col_offset,padx=5,sticky=W)
			if description is not None and isinstance(description,str) and description != "":
				description = CTkLabel(card,text=description,wraplength=400,justify="left")
				description.grid(row=2,column=col_offset,padx=5,sticky=W,pady=(0,5))
			#Buttons
			buttonFrame = CTkFrame(card)
			buttonFrame.grid(row=0,column=col_offset+1,rowspan=3,sticky="ne",padx=5,pady=5)
			selectmodPackbtn = CTkButton(buttonFrame,text="Import Modpack")
			modviewbtn = CTkButton(buttonFrame,text="View Modpack Mods")
			selectmodPackbtn.grid(row=0,column=0,padx=5,pady=2)
			modviewbtn.grid(row=1,column=0,padx=5,pady=2)
			if footnotes is not None and footnotes != "":
				card.grid_columnconfigure(0,weight=0)
				card.grid_columnconfigure(1,weight=1)
				footer_frame = CTkFrame(card, fg_color="#808080",corner_radius=0)  # grey footer bar
				footer_frame.grid(row=3, column=0, columnspan=col_offset+2, sticky="ew", padx=0, pady=0)
				footer_label = CTkLabel(footer_frame, text=footnotes, font=CTkFont(size=10), text_color="#FFFFFF", fg_color="#808080")
				footer_label.pack(anchor="e", padx=5, pady=2)
			self.entries.append({f'card_{self.rowEntry}':card,'index':int(self.rowEntry),'curseforge_id':int(objectID)})
			self.rowEntry += 1
			return

		def removeEntryByIndex(self,index:int | None = None):
			'Removes entry by the index'
			for i,entry in enumerate(self.entries):
				if entry['index'] == index:
					entry[f'card_{index}'].destroy()
					self.entries.pop(i)
					break
			self.listview.update_idletasks()
			return

		def removeEntryByModpack(self,modpackName:str | None = None):
			'Removes entry by the modpack name'
			for i,entry in enumerate(self.entries):
				cardWidget = entry[f"card_{entry['index']}"]
				for widget in cardWidget.winfo_children():
					if isinstance(widget,CTkLabel) and widget.cget("text") == modpackName:
						#Modpack found, remove it
						cardWidget.destroy()
						self.entries.pop(i)
			self.listview.update_idletasks()
			return

		def setImportCmdOnEntryIndex(self,index:int | None = None,cmd:Callable | None = None):
			'Configures the Import button by setting the command parameter to that button with whatever the cmd parameter is set to'
			if index is None or cmd is None:
				missing = [name for name,value in {'index':index,'command':cmd}.items() if value is None]
				if missing:
					raise MCSCInternalError(f"Missing required parameter(s): {', '.join(missing)}")
			else:
				if not isinstance(index,int):
					raise MCSCInternalError(f"Failed to find index. Expected an 'int', but got {type(index).__name__}")
				else:
					if not callable(cmd):
						raise MCSCInternalError(f"The 'command' parameter was {repr(cmd)}, and is not callable. Expected an callable object, but got {type(cmd).__name__}")
					else:
						#All is good
						card = next((e[f"card_{index}"] for e in self.entries if e['index'] == index),None)
						if card is None:
							raise IndexError(f"Entry with the index of {index} not found")
						buttonFrame = next((frame for frame in card.winfo_children() if isinstance(frame, CTkFrame) and any(isinstance(widget, CTkButton) and widget.cget("text") == "Import Modpack" for widget in frame.winfo_children())),None)
						if buttonFrame is None:
							raise MCSCInternalError(f"Expected CTkFrame object, but got {type(buttonFrame).__name__}")
						import_button = next((w for w in buttonFrame.winfo_children() if isinstance(w,CTkButton) and w.cget("text") == "Import Modpack"),None)
						if import_button is None:
							raise MCSCInternalError(f"Expected CTkButton object, but got {type(import_button).__name__}")
						import_button.configure(command=cmd)
						return

		def setViewerCmdOnEntryIndex(self,index:int | None = None,cmd:Callable | None = None):
			'Configures the View Modpack Mods button by setting the command parameter to that button with whatever the cmd parameter is set to'
			if index is None or cmd is None:
				missing = [name for name,value in {'index':index,'command':cmd}.items() if value is None]
				if missing:
					raise MCSCInternalError(f"Missing required parameter(s): {', '.join(missing)}")
			else:
				if not isinstance(index,int):
					raise MCSCInternalError(f"Failed to find index. Expected an 'int', but got {type(index).__name__}")
				else:
					if not callable(cmd):
						raise MCSCInternalError(f"The 'command' parameter was {repr(cmd)}, and is not callable. Expected an callable object, but got {type(command).__name__}")
					else:
						#All is good
						card = next((e[f"card_{index}"] for e in self.entries if e['index'] == index),None)
						if card is None:
							raise IndexError(f"Entry with the index of {index} not found")
						buttonFrame = next((frame for frame in card.winfo_children() if isinstance(frame, CTkFrame) and any(isinstance(widget, CTkButton) and widget.cget("text") == "Import Modpack" for widget in frame.winfo_children())),None)
						if buttonFrame is None:
							raise MCSCInternalError(f"Expected CTkFrame object, but got {type(buttonFrame).__name__}")
						import_button = next((w for w in buttonFrame.winfo_children() if isinstance(w,CTkButton) and w.cget("text") == "View Modpack Mods"),None)
						if import_button is None:
							raise MCSCInternalError(f"Expected CTkButton object, but got {type(import_button).__name__}")
						import_button.configure(command=cmd)
						return

	class CurseforgeRemoteModpackImport():
		def __init__(self):
			self.modpackPath = str(rootFilepath) + "/base/sandbox/Instances/Curseforge/Modpacks"
			self.currentpage = 1
			self.first_pg = 1
			self.last_pg = 1
			self.searchEntries = []
			self.currentpageEntries = []
			self.firstCardIndex = 0
			self.lastCardIndex= 11
			self.importerRoot = CTkToplevel()
			self.importerRoot.title("Minerva Server Crafter - Curseforge Modpack Importer - Results By: Modpack Index")
			self.importerRoot.after(200,lambda:self.importerRoot.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
			self.importerRoot.grid_rowconfigure(1, weight=1)
			self.importerRoot.grid_columnconfigure(0, weight=1)
			self.importerRoot.geometry("1000x700")
			self.importerRoot.minsize(700,600)
			self.searchFrame = CTkFrame(self.importerRoot)
			self.searchFrame.grid(row=0,column=0,sticky="ew")
			self.searchFrame.grid_columnconfigure(1,weight=1)
			self.searchLabel = CTkLabel(self.searchFrame,text="Modpack Search: ",anchor=W)
			self.searchLabel.grid(row=0,column=0)
			self.searchEntry = CTkEntry(self.searchFrame,placeholder_text="Search for Modpack")
			self.searchEntry.grid(row=0,column=1,sticky="ew")
			self.searchbtn = CTkButton(self.searchFrame,text="Search Modpack",command=lambda: self.searchModpack(modpackName=str(self.searchEntry.get())))
			self.searchbtn.grid(row=0,column=2)
			self.modpackListingFrame = CTkFrame(self.importerRoot)
			self.modpackListingFrame.grid(row=1,column=0,sticky="nsew")
			self.modpackListing = curseforgeUI.CurseforgeModImporter_ModpackTree(self.modpackListingFrame)
			#Navigation
			self.navFrame = CTkFrame(self.importerRoot)
			self.navFrame.grid(row=2,column=0)
			self.pgButtonEntries = []
			self.pageFrame = CTkFrame(self.navFrame)
			self.pageFrame.grid(row=0,column=0,columnspan=4)
			self.previousPgbtn = CTkButton(self.navFrame,text="<== Previous Page")
			self.previousPgbtn.grid(row=1,column=0)
			self.pageJumpLabel = CTkLabel(self.navFrame,text="Go to Page",)
			self.pageJumpLabel.grid(row=1,column=1)
			self.pgIntVar = IntVar(value=self.currentpage)
			self.pageJumpEntry = CTkEntry(self.navFrame,textvariable=self.pgIntVar,placeholder_text="Page Number")
			self.pageJumpEntry.grid(row=1,column=2)
			self.nextPgbtn = CTkButton(self.navFrame,text="Next Page ==>")
			self.nextPgbtn.grid(row=1,column=3)
			self.populate()
			return

		def populate(self):
			def worker():
				asyncio.run(self._asyncPopulateInitialModpacks())

			initialPopulatingThread = threading.Thread(target=worker, daemon=True, name="Async Initial Modpacks Thread")
			initialPopulatingThread.start()

		async def _asyncPopulateInitialModpacks(self):
			try:
				async with aiohttp.ClientSession() as session:
					async with session.get("https://www.modpackindex.com/api/v1/modpacks?limit=12&page=1") as resp:
						if resp.status != 200:
							return
						data = await resp.json()

					modpacks = data.get('data', [])
					self.modpackListing.listview.after(0, self.modpackListing.clearAllEntries)

					tasks = [self._asyncFetchModpackDetails(session, m['name']) for m in modpacks]
					results = await asyncio.gather(*tasks, return_exceptions=True)

					for result in results:
						if isinstance(result, dict):
							self.modpackListing.listview.after(0, lambda r=result: self.modpackListing.add_entry(title=str(r['modpackName']), subtitle=str(r['authorStr']), description=str(r['summary']), icon=r.get('thumbnail_img'), footnotes=r.get('footer'), objectID=int(r['curseforgeID'])))
			except Exception as e:
				print(f"[populateInitialModpacks] Error: {e}")

		def addModpackEntry(self,modpackName=None):
			#We need to get the modpack data from curseforge
			searchQuery = modpackName
			if re.search(r"\s",searchQuery):
				searchQuery = searchQuery.replace(" ","%20")
			modpackindexResponse = requests.get(f"https://www.modpackindex.com/api/v1/modpacks?limit=1&name={searchQuery}&page=1")
			if modpackindexResponse.status_code == 200:
				modpackindexDataRaw = modpackindexResponse.json()
				modpackindexData = modpackindexDataRaw['data'][0]
				#Grab data
				modpack_name = modpackindexData['name']
				summary = modpackindexData['summary']
				thumbnail = modpackindexData['thumbnail_url'] #Will be used later for the icon
				#Not a lot of data. We can go further with it
				curse_info = modpackindexData.get('curse_info')
				curseforgeID = None
				try:
					if curse_info and 'curse_id' in curse_info:
						curseforgeID = curse_info['curse_id']
					else:
						return
				finally:
					header = {'Accept': 'application/json','x-api-key': str(CurseforgeClass.decodeByteSecret())}
					curseforgeapiResponse = requests.get(f"https://api.curseforge.com/v1/mods/{curseforgeID}",headers=header)
					if curseforgeapiResponse.status_code == 200:
						curseforgeapiDataRaw = curseforgeapiResponse.json()
						curseforgeapiData = curseforgeapiDataRaw['data']
						#Get the authors
						modpack_authors = [a['name'] for a in curseforgeapiData['authors']]
						#We need the modloader data from the json manifest
						downloadCounter = curseforgeapiData['downloadCount']
						modpackZipUrl = curseforgeapiData['latestFiles'][0]['downloadUrl']
						if modpackZipUrl is None:
							return
						zipResponse = requests.get(str(modpackZipUrl))
						if zipResponse.status_code == 200:
							zipData = io.BytesIO(zipResponse.content)
							with zipfile.ZipFile(zipData,'r') as z:
								with z.open("manifest.json",'r') as f:
									manifestData = json.load(f)
									f.close()
								z.close()
							primaryLoader = next((m for m in manifestData['minecraft']['modLoaders'] if m.get('primary')), None)
							modloaderVersion = primaryLoader['id']
							MinecraftVersion_ = manifestData['minecraft']['version']
							#Build the foot note text
							footer = f"Total Downloads: {downloadCounter} | Using Minecraft Version: {MinecraftVersion_} | Modloader Version: {modloaderVersion}"
							author_textRaw = ", ".join(modpack_authors)
							authorStr = f"Made By: {author_textRaw}"
							#Get the thumbnail
							thumbnailResponse = requests.get(thumbnail)
							if thumbnailResponse.status_code == 200:
								thumbnailData = io.BytesIO(thumbnailResponse.content)
								thumbnail_img = Image.open(thumbnailData)
								#We	got the data. Add the card
								self.modpackListing.add_entry(title=str(modpackName),subtitle=str(authorStr),description=str(summary),icon=thumbnail_img,footnotes=str(footer),objectID=int(curseforgeID))
								return

		def setImportCommandByIndex(self,index_:int | None = None,cmd_:Callable | None = None):
			'Configures the Import Modpack Button'
			if index_ is None or cmd_ is None:
				missing = [name for name,value in {'index':index_,'command':cmd_}.items() if value is None]
				if missing:
					raise MCSCInternalError(f"Missing required parameter(s): {', '.join(missing)}")
			else:
				if not isinstance(index_,int):
					raise MCSCInternalError(f"Failed to find index. Expected an 'int', but got {type(index_).__name__}")
				else:
					if not callable(cmd_):
						raise MCSCInternalError(f"The 'command' parameter was {repr(cmd_)}, and is not callable. Expected an callable object, but got {type(cmd_).__name__}")
					else:
						self.modpackListing.setImportCmdOnEntryIndex(index=index_,cmd=cmd_)
						return

		def setViewerCommandByIndex(self,index_:int | None = None,cmd_:Callable | None = None):
			'Configures the View Modpack Button'
			if index_ is None or cmd_ is None:
				missing = [name for name,value in {'index':index_,'command':cmd_}.items() if value is None]
				if missing:
					raise MCSCInternalError(f"Missing required parameter(s): {', '.join(missing)}")
			else:
				if not isinstance(index_,int):
					raise MCSCInternalError(f"Failed to find index. Expected an 'int', but got {type(index_).__name__}")
				else:
					if not callable(cmd_):
						raise MCSCInternalError(f"The 'command' parameter was {repr(cmd_)}, and is not callable. Expected an callable object, but got {type(cmd_).__name__}")
					else:
						self.modpackListing.setViewerCmdOnEntryIndex(index=index_,cmd=cmd_)
						return

		def searchModpack(self, modpackName=None):
			self.modpackListing.didSearch = True

			def worker():
				asyncio.run(self._asyncSearchModpacks(modpackName))
			outputLog_ui.info_print(f"Searching for {modpackName} thats on Curseforge...")
			self.importerRoot.title("Searching on Modpack Index...")
			searchThread = threading.Thread(target=worker, daemon=True, name="Async SearchModpack Thread")
			searchThread.start()


		async def _asyncSearchModpacks(self, modpackName):
			try:
				async with aiohttp.ClientSession() as session:
					searchQuery = modpackName.replace(" ", "%20") if " " in modpackName else modpackName
					async with session.get(f"https://www.modpackindex.com/api/v1/modpacks?limit=12&name={searchQuery}&page=1") as resp:
						if resp.status != 200:
							return
						data = await resp.json()

					modpacks = data.get('data', [])
					searchLinks = data.get('meta', {}).get('links', [])

					# Pagination entries
					self.searchEntries = []
					pgNumber = 1
					for item in searchLinks:
						if item['label'] in ("&laquo; Previous", "Next &raquo;"):
							continue
						self.searchEntries.append({str(pgNumber): str(item['url'])})
						pgNumber += 1

					# Clear previous entries
					self.modpackListing.listview.after(0, self.modpackListing.clearAllEntries)

					# Fetch modpack details concurrently
					tasks = [self._asyncFetchModpackDetails(session, m['name']) for m in modpacks]
					results = await asyncio.gather(*tasks, return_exceptions=True)

					# Add each modpack to GUI
					try:
						for result in results:
							if isinstance(result, dict):
								self.modpackListing.listview.after(0, lambda r=result: self.modpackListing.add_entry(title=str(r['modpackName']),subtitle=str(r['authorStr']),description=str(r['summary']),icon=r.get('thumbnail_img'),footnotes=r.get('footer'),objectID=int(r['curseforgeID'])))
					finally:
						self.importerRoot.title("Minerva Server Crafter - Curseforge Modpack Importer - Results By: Modpack Index")
						return
			except Exception as e:
				print(f"[searchModpack] Error: {e}")


		async def _asyncFetchModpackDetails(self, session, modpackName):
			try:
				searchQuery = modpackName.replace(" ", "%20") if " " in modpackName else modpackName
				async with session.get(f"https://www.modpackindex.com/api/v1/modpacks?limit=1&name={searchQuery}&page=1") as resp:
					if resp.status != 200:
						return None
					dataRaw = await resp.json()
					data = dataRaw['data'][0]

				#Prompt the user
				modpack_name = data['name']
				summary = data.get('summary', '')
				thumbnail = data.get('thumbnail_url')
				curse_info = data.get('curse_info')
				if not curse_info or 'curse_id' not in curse_info:
					return None
				curseforgeID = curse_info['curse_id']

				# CurseForge API
				headers = {'Accept': 'application/json', 'x-api-key': str(CurseforgeClass.decodeByteSecret())}
				async with session.get(f"https://api.curseforge.com/v1/mods/{curseforgeID}", headers=headers) as cfResp:
					if cfResp.status != 200:
						return None
					cfData = (await cfResp.json())['data']

				modpack_authors = [a['name'] for a in cfData.get('authors', [])]
				authorStr = f"Made By: {', '.join(modpack_authors)}"

				downloadCounter = cfData.get('downloadCount', 0)
				modpackZipUrl = cfData['latestFiles'][0].get('downloadUrl')
				if not modpackZipUrl:
					return None

				async with session.get(str(modpackZipUrl)) as zipResp:
					if zipResp.status != 200:
						return None
					zipData = io.BytesIO(await zipResp.read())
					with zipfile.ZipFile(zipData, 'r') as z:
						with z.open("manifest.json", 'r') as f:
							manifestData = json.load(f)

				primaryLoader = next((m for m in manifestData['minecraft']['modLoaders'] if m.get('primary')), None)
				modloaderVersion = primaryLoader['id'] if primaryLoader else "Unknown"
				MinecraftVersion_ = manifestData['minecraft']['version']

				footer = f"Total Downloads: {downloadCounter} | Using Minecraft Version: {MinecraftVersion_} | Modloader Version: {modloaderVersion}"

				thumbnail_img = None
				if thumbnail:
					async with session.get(thumbnail) as tResp:
						if tResp.status == 200:
							thumbData = io.BytesIO(await tResp.read())
							thumbnail_img = Image.open(thumbData)

				return {'modpackName': modpack_name,'summary': summary,'authorStr': authorStr,'thumbnail_img': thumbnail_img,'footer': footer,'curseforgeID': curseforgeID}

			except Exception as e:
				print(f"[fetchModpackDetails] Error ({modpackName}): {e}")
				return None


	class TopographWarning_notReady():
		def __init__(self):
			self.root1 = CTkToplevel()
			self.root1.title("Minerva Server Crafter - Bummer")
			pygame.mixer.init()
			self.bummer_ = str(rootFilepath) + "/base/assets/sound/bummer.wav"
			self.bummerSound_ = pygame.mixer.Sound(file=self.bummer_)
			self.bummerSound_.play()
			
			#Message
			self.message_ = CTkLabel(self.root1,text="Please wait until the maps are done processing.")
			self.message_.grid(row=0,column=0)
			self.close_ = CTkButton(self.root1,text="Close",command=lambda:self.root1.destroy())
			self.close_.grid(row=1,column=0,pady=5)
			return
	class singleplayerSaveBrowser():
		def __init__(self,modpackName=None,minecraftVersion=None):
			from base.modules.config import curseforge_instancePath
			self.modpacksaves_CurseDir = str(curseforge_instancePath) + "/" + str(modpackName) + "/saves"
			self.modpackPath = str(curseforge_instancePath) + "/" + str(modpackName)
			self.modpack = modpackName
			self.version = minecraftVersion
			self.world = None
			self.canViewWorld = BooleanVar(value=False)
			self.worldPath = None
			self.topograph = None
			self.outputLog_world = MCSCKernelCore(module="Curseforge UI",logic="Singleplayer World Browser")
			#Create Widget
			self.root_1 = CTkToplevel()
			self.root_1.after(200,lambda:self.root_1.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
			self.root_1.protocol("WM_DELETE_WINDOW", lambda:self.onClose())
			self.root_1.title("Minerva Server Crafter - Singleplayer World Browser")
			self.worldListingFrame = CTkFrame(self.root_1)
			self.worldListingFrame.grid(row=0,column=0)
			self.worldListing = CTkListbox(self.worldListingFrame,height=300)
			self.worldListing.pack(fill=BOTH,expand=True)
			self.detailsFrame = CTkFrame(self.root_1)
			self.detailsFrame.grid(row=0,column=1,padx=10,pady=10)
			#World screenshot
			self.imagePath = str(rootFilepath) + "/base/assets/images/unknown_server_jar.png"
			self.worldImageData = Image.open(self.imagePath)
			self.worldImage = CTkImage(dark_image=self.worldImageData,size=(128,128))
			self.worldImageLabel = CTkLabel(self.detailsFrame,text=" ",image=self.worldImage)
			self.worldImageLabel.grid(row=0,column=0)
			self.world_metaDataFrame = CTkFrame(self.detailsFrame)
			self.world_metaDataFrame.grid(row=1,column=0)
			self.world_metaDataDict = None
			self.worldMetaDataLabel = CTkLabel(self.world_metaDataFrame,text="Select a world")
			self.metadataTable = None
			self.worldMetaDataLabel.grid(row=0,column=0,padx=5,pady=5)
			self.actionPanel_ = CTkFrame(self.root_1)
			self.actionPanel_.grid(row=1,column=0)
			self.button = CTkButton(self.actionPanel_,text="Open World Viewer",command=self.start)
			self.button.grid(row=0,column=0)
			self.worldListing.bind("<<ListboxSelect>>",self.onWorldSelected)
			self.populateSaves()
			return
		
		def onClose(self):
			from base.modules.utils import TopographMapLogic
			#Is the webserver running?
			if self.canViewWorld and isinstance(self.topograph,TopographMapLogic):
				outputLog_ui.info_print("Killing BlueMaps Web Server...")
				#Kill the webserver
				self.topograph.killGenerator()
				self.root.destroy()
				return
			else:
				self.root.destroy()
				return

		def populateSaves(self):
			saves = []
			for entry in os.listdir(self.modpacksaves_CurseDir):
				fullpath = os.path.join(self.modpacksaves_CurseDir,entry)
				if os.path.isdir(fullpath):
					saves.append(entry)
			for item in saves:
				self.worldListing.insert(END,item)
			return
		
		def onWorldSelected(self,event):
			from base.modules.utils import WorldDataClass
			selectedWorld = self.worldListing.get()
			world_path = str(self.modpacksaves_CurseDir) + f"/{selectedWorld}"
			worldAccess = WorldDataClass(worldPath=world_path)
			self.world_metaDataDict = worldAccess.worldData_metaData
			worldSeed = self.world_metaDataDict["WorldGenSettings"]["seed"] or self.world_metaDataDict['RandomSeed'] #For both modern and older worlds
			hasCheats = "Enabled" if self.world_metaDataDict['allowCommands'] == 1 else "Disabled"
			minecraft_version = self.world_metaDataDict.get("Version",{}).get("Name") or "Unknown"
			seed_verifier = "Yes" if worldAccess.wordVerifier(word_=worldSeed) else "No"
			if isinstance(self.worldMetaDataLabel,CTkLabel):
				self.worldMetaDataLabel.destroy()
			if isinstance(self.metadataTable,CTkTable) and self.metadataTable is not None:
				self.metadataTable.destroy()
			#World Meta Data
			self.metadataTable = CTkTable(self.world_metaDataFrame,column=2,row=9)
			self.metadataTable.grid(row=0,column=0)
			self.metadataTable.insert(row=0,column=0,value="World Name")
			self.metadataTable.insert(row=0,column=1,value=str(self.world_metaDataDict['LevelName']))
			self.metadataTable.insert(row=1,column=0,value="World Seed")
			self.metadataTable.insert(row=1,column=1,value=str(worldSeed))
			self.metadataTable.insert(row=2,column=0,value="Gamemode")
			self.metadataTable.insert(row=2,column=1,value=str(self.world_metaDataDict['GameType']))
			self.metadataTable.insert(row=3,column=0,value="Difficulty")
			self.metadataTable.insert(row=3,column=1,value=str(self.world_metaDataDict["Difficulty"]))
			self.metadataTable.insert(row=4,column=0,value="Hardcore World?")
			self.metadataTable.insert(row=4,column=1,value=str(self.world_metaDataDict["hardcore"]))
			self.metadataTable.insert(row=5,column=0,value="Last Played on")
			self.metadataTable.insert(row=5,column=1,value=str(self.world_metaDataDict["LastPlayed"]))
			self.metadataTable.insert(row=6,column=0,value="Cheats?")
			self.metadataTable.insert(row=6,column=1,value=str(hasCheats))
			self.metadataTable.insert(row=7,column=0,value="World Version")
			self.metadataTable.insert(row=7,column=1,value=str(minecraft_version))
			self.metadataTable.insert(row=8,column=0,value="Can Recreate Seed in Client?")
			self.metadataTable.insert(row=8,column=1,value=str(seed_verifier))
			#World Icon
			try:
				if os.path.isfile(str(world_path) + "/icon.png"):
					self.outputLog_world.info_print("World Icon detected")
					imagePath = str(world_path) + "/icon.png"
					self.worldImageLabel.configure(image=None)
					worldSaveImageData = Image.open(str(imagePath))
					worldSaveImageData = worldSaveImageData.resize((128,128), Image.LANCZOS)
					worldSaveImageData = worldSaveImageData.filter(ImageFilter.SHARPEN)
					worldImage = CTkImage(dark_image=worldSaveImageData,size=(128,128))
					self.worldImageLabel.configure(image=worldImage)
				else:
					self.root_1.after(500,lambda:self.setWorld())
					self.root_1.after(700,lambda:self.canViewWorld.set(True))
					return
			except Exception as e:
				raise MCSCInternalError(f"An exception was raised! Here is a detailed walkthrough: {e}",errors=e)

		def start(self):
			from base.modules.utils import TopographMapLogic

			host = InternetHost()
			ip = host.getIPV4()
			outputLog_ui.info_print(f"Setting up BlueMaps using {ip}:8100 via web server...")
		
			def worker():
				self.topograph = TopographMapLogic(clientFolder=self.modpackPath, savePath=self.modpacksaves_CurseDir, world=self.world, mc_version=self.version, moddedWorld=True)
				self.topograph.runMapWebGenerator()
				return
		
			viewer_thread = threading.Thread(target=worker, name="Bluemaps Viewer Thread", daemon=True)
			viewer_thread.start()
			return



		def setWorld(self):
			from base.modules.utils import TopographMapLogic, outputLog_utils
			selectedWorld = self.worldListing.get()
			self.world = str(selectedWorld)
			self.worldPath = self.modpacksaves_CurseDir + f"/{selectedWorld}"
			self.outputLog_world.info_print(f"Selected {self.world}. Setting up Topograph...")

			def worker():
				# Init or restart topograph
				if self.topograph is None:
					self.topograph = TopographMapLogic(clientFolder=self.modpackPath,savePath=self.modpacksaves_CurseDir,world=self.world,mc_version=self.version,moddedWorld=True)
				else:
					self.topograph.killGenerator()
					self.topograph = TopographMapLogic(clientFolder=self.modpackPath,savePath=self.modpacksaves_CurseDir,world=self.world,mc_version=self.version,moddedWorld=True)

				self.topograph.runMapGenerator()

				# Non-blocking read loop in background thread
				for line in self.topograph.genMap.stdout:
					decoded = line.decode('utf-8')
					if "Stopping..." in decoded:
						outputLog_utils.info_print(decoded)
						# safely set flag back in GUI thread
						self.root.after(0, lambda: setattr(self, "canViewWorld", True))
						self.topograph.killGenerator()
						self.topograph = None
						outputLog_utils.info_print("Map configurations has been generated successfully.")
						break
					
			# Run worker in background thread
			processing = threading.Thread(target=worker,name="BlueMaps Thread(worker)",daemon=True)
			processing.start()
			return
	
	class ModpackImportFinishedNotification():
		def __init__(self,modpackName:str | None = None,modlist:list | None = None):
			if modpackName is not None and isinstance(modpackName, str) and modlist is not None and isinstance(modlist,list):
				self.totalMods = len(modlist)
				self.root_2 = CTkToplevel()
				self.root_2.after(200,lambda:self.root_2.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
				self.root_2.title("Minerva Server Crafter - Modpack Import Finished")
				# === Widgets ===
				self.messageLabel = CTkLabel(self.root_2,text=f"The modpack '{modpackName}' has been successfully imported into Minerva Server Crafter! We are using {self.totalMods} mod(s) on the server")
				self.messageLabel.grid(row=0,column=0,padx=10,pady=10)
				self.closeBtn = CTkButton(self.root_2,text="Close",command=lambda:self.root_2.destroy())
				self.closeBtn.grid(row=1,column=0,pady=5)
				return

	class ModpackReviewer():
		def __init__(self, modpackName=None, clientmodListing=None, servermodListing=None, curseforge_handler=None):
			if modpackName is not None and isinstance(modpackName, str):
				self.modpack = modpackName
				self.curse_logic = curseforge_handler
				self.projectedclientmods = clientmodListing if clientmodListing is not None else []
				self.projectedservermods = servermodListing if servermodListing is not None else []
				self.clientMods = []
				self.serverMods = []
				self.mcVersion = self.curse_logic.gameversion
				self.singleplayerWorldName = None
				self.singleplayerWorldPath = None
				self.totalClient = len(self.projectedclientmods)
				self.totalServer = len(self.projectedservermods)
				self.totalCount = self.totalClient + self.totalServer
				self.outputLog_LocalModpackReview = MCSCKernelCore(module="Curseforge UI",logic="Local Modpack Reviewer")
				self.root_ = CTkToplevel()
				self.root_.after(200,lambda:self.root_.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
				self.root_.title(f"Minerva Server Crafter - Reviewing {modpackName} Data - Total Modpack Content: {self.totalCount}")

				# === Sound setup (Ready but silent) ===
				pygame.mixer.init()
				self.tada_soundFile = str(rootFilepath) + "/base/assets/sound/Ta-Da sfx.wav"
				self.tadaSound = pygame.mixer.Sound(file=self.tada_soundFile)
				pygame.mixer.set_num_channels(1)

				# === Main Review Widget Container ===
				self.reviewWidgets = CTkFrame(self.root_)
				self.reviewWidgets.pack(fill=BOTH, expand=True, padx=20, pady=20)

				# === Client Mods ===
				self.clientmodsFrame = CTkFrame(self.reviewWidgets, height=400)
				self.clientmodsFrame.grid(row=0, column=0, padx=10, pady=10)
				self.clientmodsLabel = CTkLabel(self.clientmodsFrame, text=f"Client Mods\nTotal Count: {self.totalClient}")
				self.clientmodsLabel.grid(row=0, column=0)
				self.clientmodsListbox = CTkListbox(self.clientmodsFrame, height=400)
				self.clientmodsListbox.grid(row=1, column=0)
				self.clientmodsAction = CTkFrame(self.reviewWidgets)
				self.clientmodsAction.grid(row=1, column=0, padx=10, pady=10)
				self.clientmodAction_revealModsInViewer = CTkButton(self.clientmodsAction,text="Show Mods in Mod Viewer",command=lambda: curseforgeUI.modViewer(modpackName=str(modpackName),overrideModListing=True,modlist=self.clientMods,modlist_tuple=self.projectedclientmods))
				self.clientmodAction_revealModsInViewer.grid(row=0, column=0, pady=3)
				self.clientmodAction_addToPendingTasks = CTkButton(self.clientmodsAction,text="Add to Pending",command=self.addClientToPending)
				self.clientmodAction_addToPendingTasks.grid(row=1, column=0, pady=3)

				# === Server Mods ===
				self.servermodsFrame = CTkFrame(self.reviewWidgets, height=400)
				self.servermodsFrame.grid(row=0, column=1, padx=10, pady=10)
				self.servermodsLabel = CTkLabel(self.servermodsFrame, text=f"Server Mods\nTotal Count: {self.totalServer}")
				self.servermodsLabel.grid(row=0, column=0)
				self.servermodsListbox = CTkListbox(self.servermodsFrame, height=400)
				self.servermodsListbox.grid(row=1, column=0)
				self.servermodsAction = CTkFrame(self.reviewWidgets)
				self.servermodsAction.grid(row=1, column=1, padx=10, pady=10)
				self.servermodsAction_revealModsInViewer = CTkButton(self.servermodsAction,text="Show Mods in Mod Viewer",command=lambda: curseforgeUI.modViewer(modpackName=str(modpackName),overrideModListing=True,modlist=self.serverMods,modlist_tuple=self.projectedservermods,AllowModpackReviewing=True,ModpackReviewerPointer=self))
				self.servermodsAction_revealModsInViewer.grid(row=0, column=0, pady=3)
				self.servermodsAction_addToPendingTasks = CTkButton(self.servermodsAction,text="Add to Pending",command=self.addServerToPending)
				self.servermodsAction_addToPendingTasks.grid(row=1, column=0, pady=3)

				# === Pending Tasks ===
				self.pending_col = 2
				self.pendingTasksFrame = CTkFrame(self.reviewWidgets, height=400)
				self.pendingTasksFrame.grid(row=0, column=self.pending_col, padx=10, pady=10)
				self.pendingTasksLabel = CTkLabel(self.pendingTasksFrame, text="Pending Modpack Content\n to Import")
				self.pendingTasksLabel.grid(row=0, column=0)
				self.pendingTasksListbox = CTkListbox(self.pendingTasksFrame, height=400)
				self.pendingTasksListbox.grid(row=1, column=0)
				self.pendingTasksAction = CTkFrame(self.reviewWidgets)
				self.pendingTasksAction.grid(row=1, column=self.pending_col, padx=10, pady=10)
				self.pendingTasksAction_removeFromPendingTasks = CTkButton(self.pendingTasksAction, text="Remove from Pending", command=self.removeFromPending)
				self.pendingTasksAction_removeFromPendingTasks.grid(row=0, column=0, pady=3)
				self.pendingTasksAction_includeConfigsFolderBool = CTkCheckBox(self.pendingTasksAction, text="Include Config Folder", onvalue=True, offvalue=False)
				self.pendingTasksAction_includeConfigsFolderBool.grid(row=1, column=0)
				self.pendingTasksAction_singleplayerworldInclusion = CTkCheckBox(self.pendingTasksAction, text="Use Singleplayer World", onvalue=True, offvalue=False, command=self.includeSinglePlayerSave)
				self.pendingTasksAction_singleplayerworldInclusion.grid(row=2, column=0)
				self.pendingTasksAction_browseForWorld = CTkButton(self.pendingTasksAction, text="Browse for World", state="disabled",command=self.browseForWorld)
				self.pendingTasksAction_browseForWorld.grid(row=3, column=0, pady=3)
				self.pendingTasksAction_finalize = CTkButton(self.pendingTasksAction, text="Begin Import", command=self.beginImporting)
				self.pendingTasksAction_finalize.grid(row=4, column=0, pady=3)

				# === Populate ===
				self.populateClientMods()
				self.populateServerMods()
				self.populatePendingItems()
				return

		def browseForWorld(self):
			worldBrowser = curseforgeUI.singleplayerSaveBrowser(modpackName=str(self.modpack),minecraftVersion=str(self.mcVersion))
			worldBrowser.root_1.wait_window()
			#Get the world
			worldPathTarget = worldBrowser.worldPath
			worldName = worldBrowser.world
			if worldName is None and worldPathTarget is None:
				return
			self.outputLog_LocalModpackReview.info_print("Singleplayer World has been selected.")
			self.outputLog_LocalModpackReview.info_print(f"World Name: {worldName}")
			self.outputLog_LocalModpackReview.info_print(f"World Save Path: {worldPathTarget}")
			#Set the variables
			self.singleplayerWorldName = worldName
			self.singleplayerWorldPath = worldPathTarget
			#Add to pending items
			self.pendingTasksListbox.insert(END,worldName)
			return

		def populateClientMods(self):
			self.clientmodsListbox.delete(0,END)
			for item in self.projectedclientmods:
				modName,id = item
				self.clientmodsListbox.insert(END,modName)
				self.clientMods.append(modName)
			return

		def populateServerMods(self):
			self.servermodsListbox.delete(0,END)
			for item in self.projectedservermods:
				modName,id = item
				self.servermodsListbox.insert(END,modName)
				self.serverMods.append(modName)
			return

		def populatePendingItems(self):
			projectedPending = []
			for item1 in self.projectedservermods:
				modName,id = item1
				projectedPending.append(modName)
			for item3 in projectedPending:
				self.pendingTasksListbox.insert(END,item3)
			return
			
		def translateListing(self):
			for item1 in self.projectedclientmods:
				modName,id = item1
				self.clientMods.append(modName)
			for item2 in self.projectedservermods:
				mod_name,id_ = item2
				self.serverMods.append(mod_name)
			return

		def parseListings(self,modName=None):
			searchResult = None
			if isinstance(modName,str):
				for modTuple in self.projectedclientmods:
					mod_name,id = modTuple
					if mod_name != modName:
						continue
					else:
						searchResult = (modName,id,"client")
						break
				if searchResult is None:
					for mod_tuple in self.projectedservermods:
						modname,id_ = mod_tuple
						if modname != modName:
							continue
						else:
							searchResult = (modName,id_,"server")
							break
					if searchResult is None:
						for resourcePack_tuple in self.resourcePacks:
							packName,_id = resourcePack_tuple
							if packName != modName:
								continue
							else:
								searchResult = (modName,_id,"resource-pack")
								break
						if searchResult is None:
							searchResult = (modName,None)
							return searchResult
						else:
							return searchResult
					else:
						return searchResult
				else:
					return searchResult
			else:
				raise TypeError(f"modName is expected as a string, but got {type(modName)}")

		def addClientToPending(self,overrideSelection=False,selectedVal=None):
			selectedMod = self.clientmodsListbox.get()
			if overrideSelection and isinstance(selectedVal,str):
				selectedMod = selectedVal #For the mod reviewer class
			searchQuery = self.parseListings(modName=selectedMod)
			if searchQuery is not None:
				clientModWarningResult = ModIsClientWarning.ask(modID=searchQuery[1])
				if clientModWarningResult == True:
					currentPendingItems = self.pendingTasksListbox.get("all")
					newPendingListing = []
					for item in currentPendingItems:
						newPendingListing.append(item)
					newPendingListing.append(selectedMod)
					self.pendingTasksListbox.delete(0,END)
					for item_ in newPendingListing:
						self.pendingTasksListbox.insert(END,item_)
					return
				else:
					return

		def addServerToPending(self,overrideSelection=False,selectedval=None):
			selectedmod = self.servermodsListbox.get()
			if overrideSelection and isinstance(selectedval,str):
				selectedmod = selectedval
			searchquery = self.parseListings(modName=selectedmod)
			if searchquery is not None:
				if searchquery[2] == "server":
					current_pending = self.pendingTasksListbox.get("all")
					new_pendingListing = []
					for item in current_pending:
						new_pendingListing.append(item)
					new_pendingListing.append(selectedmod)
					self.pendingTasksListbox.delete(0,END)
					for _item in new_pendingListing:
						self.pendingTasksListbox.insert(END,_item)
					return
				else:
					return
			else:
				return

		def addResourcePackToPending(self,overrideSelection=False,selectedVal=None):
			selectedmod = self.resourcePacksListbox.get()
			if overrideSelection and isinstance(selectedVal,str):
				selectedmod = selectedVal
			searchquery = self.parseListings(modName=selectedmod)
			if searchquery is not None:
				if searchquery[2] == "resource-pack":
					current_pending = self.pendingTasksListbox.get("all")
					new_pendingListing = []
					for item in current_pending:
						new_pendingListing.append(item)
					new_pendingListing.append(selectedmod)
					self.pendingTasksListbox.delete(0,END)
					for _item in new_pendingListing:
						self.pendingTasksListbox.insert(END,_item)
					return
				else:
					return
			else:
				return

		def removeFromPending(self):
			index = self.pendingTasksListbox.curselection()
			self.pendingTasksListbox.delete(index=index)
			return

		def includeSinglePlayerSave(self):
			CanUseSingleplayerworldBool = self.pendingTasksAction_singleplayerworldInclusion.get()
			if CanUseSingleplayerworldBool == True:
				self.pendingTasksAction_browseForWorld.configure(state="normal")
				return
			else:
				self.pendingTasksAction_browseForWorld.configure(state="disabled")
				#We need to remove the world from pending
				current_pending = self.pendingTasksListbox.get("all")
				new_pending = []
				for item in current_pending:
					if item != str(self.singleplayerWorldName):
						new_pending.append(item)
					else:
						continue
				self.pendingTasksListbox.delete(0,END)
				for NewItem in new_pending:
					self.pendingTasksListbox.insert(END,NewItem)
				#Clear the variables
				self.singleplayerWorldName = None
				self.singleplayerWorldPath = None
				return

		def beginImporting(self):
			'Imports the Curseforge Profile as an instance'
			from base.modules.config import curseforge_instancePath, rootFilepath
			from base.modules.server import InstanceFramework,ServerTypeInstaller

			def print_lineoutput(process):
				for line in process.stdout:
					decodedLine = line.decode('utf-8')
					if re.search(r"\b(error|exception|failed)\b", decodedLine, re.IGNORECASE):
						outputLog_ui.error_print(f"[{server_type} Installer]: {decodedLine.strip()}")
					else:
						outputLog_ui.info_print(f"[{server_type} Installer]: {decodedLine.strip()}")
					time.sleep(0.1)
				code = process.wait()
				outputLog_ui.info_print(f"{server_type} Installer exited with code {code}")
				return

			#Make the directory
			os.makedirs(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}",exist_ok=True)
			os.makedirs(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/mods",exist_ok=True)
			outputLog_ui.info_print(f"Creating instance directory for {self.modpack}...")
			currentpendingItems = self.pendingTasksListbox.get("all")
			includeConfigFolder = self.pendingTasksAction_includeConfigsFolderBool.get()
			#We need to translate the current pending items from names to ids for parsing curseforge api. List of ids are ideal 
			translatedPending = []
			for item in currentpendingItems:
				searchResult = self.parseListings(modName=item)
				if searchResult is not None and len(searchResult) == 3:
					translatedPending.append((searchResult[0],searchResult[1],searchResult[2]))
				else:
					continue
			totalTranslated = len(translatedPending)
			outputLog_ui.info_print(f"Total mods to download: {totalTranslated}")
			outputLog_ui.info_print("Beginning mod downloads(this might take awhile depending on the number of mods)...")
			url_list = []
			#Process the mods from using the mod ids and cross reference the file ids with the mod names in the minecraftinstance json file in the modpack folder in the curseforge instance folder
			with open(str(curseforge_instancePath) + f"/{self.modpack}/minecraftinstance.json","r",encoding='utf-8') as f:
				instanceData = json.load(f)
				mcversion = instanceData['gameVersion']
				#server type version
				server_type_version = instanceData['baseModLoader']['forgeVersion'] #Contextually correct even for fabric modpacks
				server_typeRaw = instanceData['baseModLoader']['name']
				server_type = server_typeRaw.split("-")[0]
				#Mod files
				mod_list = instanceData["installedAddons"]
				for item in mod_list:
					currentMod = item["name"]
					if currentMod in currentpendingItems:
						#Append the download url
						download_url = item["installedFile"]["downloadUrl"]
						file_name = item["installedFile"]["fileNameOnDisk"]
						url_list.append((download_url,file_name))
						continue
					else:
						continue
			for url in url_list:
				response = requests.get(url[0])
				if response.status_code == 200:
					with open(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/mods/{url[1]}","wb") as file:
						file.write(response.content)
						continue
			#Config folder?
			try:
				if includeConfigFolder:
					sourceConfig = str(curseforge_instancePath) + f"/{self.modpack}/config"
					targetConfig = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/config"
					shutil.copytree(sourceConfig,targetConfig,dirs_exist_ok=True)
					outputLog_ui.info_print("Config folder has been copied.")
				else:
					outputLog_ui.info_print("Config folder inclusion was not selected. Skipping...")
			except Exception as e:
				outputLog_ui.error_print(f"An exception was raised while copying the config folder! Here is a detailed walkthrough: {e}")
				return
			finally:
				#Singleplayer world?
				if self.singleplayerWorldPath is not None:
					try:
						shutil.copytree(self.singleplayerWorldPath,str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/",dirs_exist_ok=True)
						outputLog_ui.info_print(f"World {self.singleplayerWorldName} has been copied to the Instance successfully.")
					except Exception as e:
						outputLog_ui.error_print(f"An exception was raised while copying the singleplayer world! Here is a detailed walkthrough: {e}")
						return
				#Create the instance config. Initialize the framework
				instanceFramework = InstanceFramework()
				instanceFramework.generateInstanceSchema(instance_name=str(self.modpack),is_curseforge=True,is_imported=True,server_type=str(server_type),minecraft_version_=str(mcversion))
				instanceFramework.createInstanceConfig(instance_name=str(self.modpack),is_curseforge=True,is_imported=True,mod_list=currentpendingItems,serverType=str(server_type),server_type_version=str(server_type_version),minecraft_version=str(mcversion))
				with open(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/eula.txt", "w") as eulafile:
					eulafile.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Jun 12 07:54:40 EDT 2024\neula=true")
					eulafile.close()
				#We need to install the server type
				destination = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/"
				version = str(mcversion) + "-" + str(server_type_version)
				serverInstaller = ServerTypeInstaller(destination)
				with SoftwareSpec.changeDir(path=destination):
					serverInstaller.installServerType(server_type=str(server_type),serverTypeVersion=str(server_type_version),minecraft_version=str(mcversion))
				outputLog_ui.info_print("Cleaning up instance folder...")
				#Remove installer
				for root_,dirs,files in os.walk(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/"):
					if server_type == "fabric":
						for file_ in files:
							if file_.startswith(f"{server_type}-installer-") and file_.endswith(".jar"):
								file_path = os.path.join(root_,file_)
								os.remove(file_path)
								break
					else:
						if server_type == "forge":
							for file_ in files:
								if file_.startswith(f"{server_type}-{version}") and file_.endswith(".jar"):
									file_path = os.path.join(root_,file_)
									os.remove(file_path)
									break
				#Get the json object from the curseforge instance for file updates
				outputLog_ui.info_print("Backing up instance data...")
				with open(str(curseforge_instancePath) + f"/{self.modpack}/minecraftinstance.json","r",encoding='utf-8') as curse_instance:
					instance_jsonData = json.load(curse_instance)
					curse_instance.close()
				with open(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/curseforge_instanceData.json","w",encoding='utf-8') as curseDatafile:
					json.dump(instance_jsonData,curseDatafile,indent=4)
					curseDatafile.close()
				#Backup the instance data
				zip_buffer = io.BytesIO()
				with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
					for root, dirs, files in os.walk(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}"):
						for file in files:
							file_path = os.path.join(root, file)
							# Keep folder structure inside the ZIP
							rel_path = os.path.relpath(file_path,str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}")
							if rel_path in ("config.json", "schema_instance.json"):
								continue
							zipf.write(file_path, rel_path)
				zip_buffer.seek(0)
				with open(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/schema_instance.json","r") as schem:
					schema_data = json.load(schem)
					schem.close()
				with open(str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/config.json","r") as configf:
					config_data = json.load(configf)
					configf.close()
				locationTarget = str(rootFilepath) + f"/base/sandbox/Instances/Curseforge/imported/{self.modpack}/instance_backup.msczip"
				msczipfile = MSCZipLib(schema=schema_data,instanceData=config_data,zipobj=zip_buffer.getvalue(),disablePrompt=True,destination=locationTarget)
				msczipfile.createMSCArchive()
				#All done :)
				outputLog_ui.info_print(f"{server_type.capitalize()} server installation completed successfully.")
				notification = curseforgeUI.ModpackImportFinishedNotification(modpackName=str(self.modpack),modlist=currentpendingItems)
				self.tadaSound.play()
				notification.root_2.wait_window()
				self.root_.destroy()
				return
	
	class NewInstanceFromLocal():
		def __init__(self):
			from base.modules.config import curseforge_localization
			if curseforge_localization == True:
				from base.modules.utils import CurseforgeClass
				self.outputLog_localProfiles = MCSCKernelCore(module="Curseforge UI",logic="Local Curseforge Profile Importer")
				self.CurseforgeHandler = CurseforgeClass()
				self.CurseforgeHandler.scanForInstances()
				self.localProfiles_raw = self.CurseforgeHandler.profiles
				self.localProfilesFiltered = []
				self.currentProfilesImported = []
				self.selectedModpack = None
				self.root = CTkToplevel()
				self.root.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
				self.root.title("Minerva Server Crafter - Curseforge Local Profile Importer")

				#Profiles
				self.profileListbox = CTkListbox(self.root,width=400,height=400)
				self.profileListbox.grid(row=0,column=0,columnspan=2)
				self.actionPanel = CTkFrame(self.root)
				self.actionPanel.grid(row=0,column=2)
				self.modViewer = CTkButton(self.actionPanel,text="View Mods",command=lambda:curseforgeUI.modViewer(modpackName=self.profileListbox.get()))
				self.modViewer.grid(row=0,column=0,pady=4,padx=2)
				self.RevealInExplorer = CTkButton(self.actionPanel,text="Show in File Manager",command=self.revealModpack)
				self.RevealInExplorer.grid(row=1,column=0,pady=4,padx=2)
				self.select = CTkButton(self.actionPanel,text="Select Modpack",command=self.processModpack)
				self.select.grid(row=2,column=0,pady=4,padx=2)
				self.closeButton = CTkButton(self.root,text="Close",command=lambda:self.root.destroy())
				self.closeButton.grid(row=4,column=0,pady=5)
				self.populateProfiles()
				return
			else:
				#Technically, by logic, this would be unreachable code based on its intended use. However, a neat easter egg
				self.root = CTkToplevel()
				self.root.title("Minerva Server Crafter - Bummer")
				pygame.mixer.init()
				self.bummer = str(rootFilepath) + "/base/assets/sound/bummer.wav"
				self.bummerSound = pygame.mixer.Sound(file=self.bummer)
				self.bummerSound.play()
				
				#Message
				self.message = CTkLabel(self.root,text="You must have the Curseforge Application installed on your computer. Will not proceed.")
				self.message.grid(row=0,column=0)
				self.close = CTkButton(self.root,text="Close",command=lambda:self.root.destroy())
				self.close.grid(row=1,column=0,pady=5)
				return
		
		def populateProfiles(self):
			#We need to omit modpacks that was installed
			for item in self.localProfiles_raw:
				#We need to open the json
				profileData = self.CurseforgeHandler.getCurseprofileData(curse_profile=str(item))
				#Check if its an installed modpack
				installedModpackCheck = profileData['installedModpack']
				if installedModpackCheck is None:
					self.localProfilesFiltered.append(item)
					continue
				else:
					continue
			totallocalProfiles = len(self.localProfilesFiltered)
			totalprofiles = len(self.CurseforgeHandler.profiles)
			totalomittedprofiles = int(totalprofiles) - int(totallocalProfiles)
			#We need to know if theres any profiles already imported
			for item in os.listdir(str(rootFilepath) + "/base/sandbox/Instances/Curseforge/imported/"):
				if item in self.localProfilesFiltered:
					outputLog_ui.info_print(f"Profile {item} was already imported. Skipping...")
					self.localProfilesFiltered.remove(item)
					self.currentProfilesImported.append(item)
					totalomittedprofiles += 1
					totallocalProfiles -= 1
					continue
				else:
					continue
			self.CurseforgeHandler.outputLog_curseforge.info_print(f"Total Profiles: {totalprofiles}, Total Omitted Profiles: {totalomittedprofiles}, Total Local Profiles: {totallocalProfiles}")
			for item_ in self.localProfilesFiltered:
				self.profileListbox.insert(END,option=item_)
				continue
			return
		
		def processModpack(self):
			targetModpack = self.profileListbox.get()
			if not targetModpack:
				self.outputLog_localProfiles.info_print("Modpack was not selected. Will not proceed")
				return
			self.selectedModpack = str(targetModpack)
			outputLog_ui.info_print(f"Processing Modpack: {self.selectedModpack}")
			self.CurseforgeHandler.processModpack(curseProfile=self.selectedModpack)
			outputLog_ui.info_print("Modpack Data Processing Done.")
			totalPossibleClient = len(self.CurseforgeHandler.clientmods)
			totalPossibleServer = len(self.CurseforgeHandler.servermods)
			outputLog_ui.info_print(f"Possible Client Mods: {totalPossibleClient}, Possible Server Mods: {totalPossibleServer}")
			modpackReview = curseforgeUI.ModpackReviewer(modpackName=self.selectedModpack,clientmodListing=self.CurseforgeHandler.clientmods,servermodListing=self.CurseforgeHandler.servermods,curseforge_handler=self.CurseforgeHandler)
			modpackReview.root_.wait_window()
			self.root.destroy()
			return
		
		def revealModpack(self):
			'Shows the local modpack profile folder in the Operating Systems File Manager'
			from base.modules.config import curseforge_instancePath
			#We need the path to the modpack
			selectedModpack = self.profileListbox.get()
			if selectedModpack is None:
				self.outputLog_localProfiles.info_print("Modpack was not selected. Will not proceed")
				return
			fileTarget = os.path.join(str(curseforge_instancePath),selectedModpack)
			self.open_file_explorer(str(fileTarget))
			return
		
		@staticmethod
		def open_file_explorer(path):
			from base.modules.config import operatingSystem
			if operatingSystem == "win32":
				os.startfile(path)
			else:
				if operatingSystem == "darwin":
					subprocess.Popen(["open", path])
				else:
					subprocess.Popen(["xdg-open", path])
			return
		
	class modViewer():
		def __init__(self,modpackName=None,overrideModListing=False,modlist=[],modlist_tuple=[],AllowModpackReviewing=False,ModpackReviewerPointer=None):
			from base.modules.utils import CurseforgeClass
			self.outputLog_modView = MCSCKernelCore(module="Curseforge UI",logic="Mod Viewer")
			if modpackName is None:
				self.outputLog_modView.info_print("Modpack was not selected. Will not proceed")
				return
			self.lineData = {}
			self.tips = {}
			self.descriptionData = {}
			self.reviewerBool = AllowModpackReviewing
			self.reviewer = None
			if AllowModpackReviewing:
				self.reviewer = ModpackReviewerPointer
			self.curseHandle = CurseforgeClass()
			self.root = CTkToplevel()
			self.root.title("Minerva Server Crafter - Mod Viewer")
			self.root.after(200,lambda:self.root.iconbitmap(str(rootFilepath) + "/base/assets/icons/minecraftservercrafter.ico"))
			self.root.grid_columnconfigure(0,weight=1)
			self.root.grid_columnconfigure(1,weight=1)
			self.root.grid_rowconfigure(0,weight=0)
			self.root.protocol("WM_DELETE_WINDOW", lambda: self.onClose())
			self.root.geometry("1061x460")
			self.overrideListing = overrideModListing
			self.listing_names = []
			self.listingData = [] #list of tuples
			if self.overrideListing == True:
				self.listing_names = modlist
				self.listingData = modlist_tuple
			self.videoButtons = {}
			self.totalVideos = 0
			self.modpack = str(modpackName)
			#Mod List
			self.modlistFrame = CTkFrame(self.root)
			self.modlistFrame.grid(row=0,column=0)
			self.modlistFrame.grid_propagate(True)
			self.modlist = CTkListbox(self.modlistFrame,width=400,height=400,command=lambda *ignored:self.populateDetails())
			self.modlist.pack(fill=BOTH,expand=True)
			#Mod Details
			self.detailPanel = CTkScrollableFrame(self.root,width=400,height=400)
			self.detailPanel.grid(row=0,column=1,sticky="nesw")
			if AllowModpackReviewing:
				self.addMod = CTkButton(self.modlistFrame,text="Add to Pending in Modpack Review",command=lambda:self.onSendData_addToPendingItems())
				self.addMod.pack(side=RIGHT,anchor=W)
			self.close = CTkButton(self.modlistFrame,text="Close",command=lambda: self.onClose())
			self.close.pack(padx=5,pady=5)
			#Table
			self.modDescription = CTkLabel(self.detailPanel,text="To begin, click on a mod in the list\n<=======")
			self.modDescription.grid(row=0,column=0)
			self.populateModlisting()
			self.modlisting_bindTips()
			return

		def onClose(self):
			from base.modules.config import rootFilepath

			targetPath = str(rootFilepath) + "/base/assets/temp"
			for _root_,_dirs,_files in os.walk(targetPath):
				for _file in _files:
						fileTarget = os.path.join(targetPath,_file)
						if fileTarget.endswith(".png"):
							os.unlink(fileTarget)
							continue
			self.root.destroy()
			return

		def modlisting_bindTips(self):
			#We need to iterate through the listbox buttons
			counter = 0
			modlisting = {}
			profileData_= self.curseHandle.getCurseprofileData(curse_profile=str(self.modpack))
			for cursedata in profileData_["installedAddons"]:
				name = cursedata["name"]
				authors = []
				for author in cursedata["authors"]:
					authors.append(author["Name"])
				modlisting[str(name)] = authors
				continue
			for key,val in self.modlist.buttons.items():
				for mod,authors_ in modlisting.items():
					modCheck = str(val.cget("text")) == str(mod)
					message = f"Mod Author(s): {', '.join(authors_)}"
					if modCheck:
						self.tips[counter] = CTkToolTip(widget=val,message=str(message))
						counter += 1
						continue
			return
		
		def populateModlisting(self):
			#Get the profile data
			if self.overrideListing == False:
				profileRaw = self.curseHandle.getCurseprofileData(curse_profile=str(self.modpack))
				modlistingData = []
				for item in profileRaw['installedAddons']:
					modListingDataRaw = item
					modName = modListingDataRaw['name']
					modData = modListingDataRaw['installedFile']['projectId']
					fileID = modListingDataRaw['installedFile']['id']
					resultTarget = (str(modName),modData,int(fileID))
					modlistingData.append(resultTarget)
					continue
				#We need to slice the tuple
				for entry in modlistingData:
					targetModname = entry[0]
					self.listing_names.append(targetModname)
					continue
				#We need to save the modlisting data
				self.listingData = modlistingData
				#Populate the listbox
				for mod in self.listing_names:
					self.modlist.insert(END,option=str(mod))
				return
			else:
				for mod_ in self.listing_names:
					self.modlist.insert(END,mod_)
				return
		
		@staticmethod
		def extractImageURLs(html=None):
			'Extracts the image urls sources. Returns a list of image urls'
			return re.findall(r'<img [^>]*src=["\']([^"\']+)["\']',html,re.IGNORECASE)
		
		@staticmethod
		def stripImages(html=None):
			'Replaces all img html tags with a placeholder like [Image: URL]'
			def replacer(match):
				src = match.group(1)
				return f'[Image: {src}]'
			return re.sub(r'<img [^>]*src=["\']([^"\']+)["\'][^>]*>', replacer, html, flags=re.IGNORECASE)
		
		@staticmethod
		def stripHyperlinks(html=None):
			# This pattern captures href and inner text of the <a> tag
			pattern = r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
		
			def replacer(match):
				url = match.group(1)
				text = match.group(2)
				return f'{text} [Link: {url}]'
		
			return re.sub(pattern, replacer, html, flags=re.IGNORECASE | re.DOTALL)
		
		@staticmethod
		def extractModDescription_htmlToMultilinePlain(html: str) -> str:
			'Converts HTML text to multiline plain text. Returns the mod description in a multiline plain text'
			# Replace some block tags with newlines
			# Add newline before <p>, <li>, <br> tags to simulate line breaks
			html_ = re.sub(r'</?(p|div|li|br|h[1-6])[^>]*>', '\n', html, flags=re.IGNORECASE)
		
			# Remove remaining tags
			text = re.sub(r'<[^>]+>', '', html_)
		
			# Replace some common HTML entities manually
			entities = {
				'&nbsp;': ' ',
				'&amp;': '&',
				'&lt;': '<',
				'&gt;': '>',
				'&quot;': '"',
				'&#39;': "'",
			}
			for entity, char in entities.items():
				text = text.replace(entity, char)
		
			# Replace multiple whitespace/newlines with single newline or space
			# First collapse multiple newlines into max two newlines (paragraph spacing)
			text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
		
			# Then replace remaining single newlines with actual newlines
			# And normalize spaces on each line
			lines = [line.strip() for line in text.split('\n')]
		
			# Remove empty lines at start and end and inside
			cleaned_lines = [line for line in lines if line]
		
			return '\n'.join(cleaned_lines)
		
		@staticmethod
		def extractYoutubeLinks(description: str) -> list:
			pattern = r'<iframe[^>]+src="(https://www\.youtube\.com/embed/[^"]+)"'
			return re.findall(pattern, description, re.IGNORECASE)
		
		@staticmethod
		def extractHyperlinkURLs(html: str) -> list[str]:
			# This regex grabs href values from <a> tags
			pattern = r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\']'
			return re.findall(pattern, html, re.IGNORECASE)
		
		@staticmethod
		def extractModDescription_htmlToDict(html=None,start_at_one=True):
			'Converts the html source to a dictionary'
			lines = html.splitlines(True)
			offset = 1 if start_at_one else 0
			return {i + offset: line for i,line in enumerate(lines)}

		
		@staticmethod
		def stripYoutube_iframes(description: str) -> tuple[str, int]:
			"""
			Replace only YouTube <iframe>…</iframe> blocks with a placeholder.
			Other iframes remain intact.
	
			Returns (cleaned_html, number_of_replacements).
			"""
			count = 0
			def _repl(match):
				nonlocal count
				count += 1
				return f'<p><i>[YouTube video #{count} removed—use the button below]</i></p>'
	
			yt_pattern = r'<iframe[^>]+src="https?://(?:www\.)?youtube\.com/embed/[^"]+"[^>]*>.*?</iframe>'
			cleaned = re.sub(yt_pattern, _repl, description, flags=re.IGNORECASE | re.DOTALL)
			return cleaned, count
		
		def openVideoViewer(self,embeddedUrl: str = None):
			webview.create_window(title="Mod Video Preview",url=embeddedUrl,width=800,height=450,resizable=True)
			webview.start(gui='edgechromium')
			return
			
		@staticmethod
		def getImageDataFromURL(url=None):
			import io
			urlLink = str(url)
			try:
				response = requests.get(url=urlLink, headers={"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) ""AppleWebKit/537.36 (KHTML, like Gecko) ""Chrome/122.0.0.0 Safari/537.36")})
				if response.status_code == 404:
					return
				response.raise_for_status()
				contentType = response.headers.get('Content-Type', '')
				image_bytes = response.content
		
				# SVG: convert to PNG with cairosvg
				if 'image/svg' in contentType or urlLink.lower().endswith('.svg'):
					return cairosvg.svg2png(bytestring=image_bytes)
		
				# GIF or WebP: return as-is
				elif 'image/gif' in contentType or urlLink.lower().endswith('.gif'):
					return image_bytes
				elif 'image/webp' in contentType or urlLink.lower().endswith('.webp'):
					return image_bytes
		
				# All other standard formats: decode and re-encode as PNG
				elif 'image' in contentType:
					try:
						with Image.open(io.BytesIO(image_bytes)) as img:
							img = img.convert("RGBA")
							out_buf = io.BytesIO()
							img.save(out_buf, format="PNG")
							return out_buf.getvalue()
					except Exception as e:
						print(f"[ERROR] Pillow failed to decode image: {e}")
						return
		
				else:
					print(f"[WARNING] URL did not return recognizable image content: {contentType}")
					return
		
			except requests.exceptions.RequestException as e:
				raise MCSCInternalError(f"Failed to get image from URL {url}", errors=e)
		
		@staticmethod
		def doImageCleanup():
			'Deletes everything in the assets/temp directory'
			from base.modules.config import rootFilepath

			targetPath = str(rootFilepath) + "/base/assets/temp"
			for _root_,_dirs,_files in os.walk(targetPath):
				for _file in _files:
						fileTarget = os.path.join(targetPath,_file)
						if fileTarget.endswith(".png"):
							os.unlink(fileTarget)
			return
		
		def openURL(url_=None):
			import webbrowser
			webbrowser.open(str(url_))
			return

		@staticmethod
		def checkForLink(line):
			lineData = str(line)
			lineQuery = re.compile(r"\[Link:\s*(.*?)\]")
			segment = []
			lastEnd = 0
			for m in lineQuery.finditer(lineData):
				if m.start() > lastEnd:
					segment.append(("text",lineData[lastEnd:m.start()]))
				segment.append(("link",m.group(1)))
				lastEnd = m.end()
			if lastEnd < len(lineData):
				segment.append(("text",lineData[lastEnd:]))
			return segment
		
		def searchImagePlaceholders(self, line):
			return len(re.findall(r'\[Image: [^\]]+\]', line))
		
		def generateWidgets(self, imageUrls=None, youtubeUrls=None):
			from base.modules.config import rootFilepath
			from tempfile import NamedTemporaryFile
			from PIL import Image,ImageFilter
			import re

			# Clear previous widgets
			for widget in self.detailPanel.winfo_children():
				widget.destroy()
			if isinstance(self.modDescription, CTkLabel):
				self.modDescription.destroy()
			self.detailPanel._parent_canvas.yview_moveto(0.0)
			row = 0
			yt_button_count = 1

			for key, val in self.lineData.items():
				line = str(val).strip()
				if not line:
					continue
				
				totalImages = self.searchImagePlaceholders(line)
				targetFrame = self.detailPanel

				if totalImages > 1:
					# Split line into separate [Image: ...] parts
					parts = re.findall(r'(\[Image: [^\]]+\])', line)
					targetFrame = CTkFrame(self.detailPanel)
					targetFrame.grid(row=row, column=0, sticky="w", pady=5)
					col = 0
					for part in parts:
						match = part[7:-1].strip()
						if imageUrls and match in imageUrls:
							imageDataQuery = self.getImageDataFromURL(url=match)
							if imageDataQuery:
								with NamedTemporaryFile(suffix=".png") as temp:
									tempPath = temp.name
								name = os.path.basename(tempPath)
								with open(str(rootFilepath) + f"/base/assets/temp/{name}","wb") as image_data:
									image_data.write(imageDataQuery)
									image_data.close()
								imageData = Image.open(str(rootFilepath) + f"/base/assets/temp/{name}")
								maxWidth, maxHeight = 400, 400
								originalWidth, originalHeight = imageData.size
								if originalWidth > maxWidth or originalHeight > maxHeight:
									scale = min(maxWidth / originalWidth, maxHeight / originalHeight)
									newSize = (int(originalWidth * scale), int(originalHeight * scale))
									imageData = imageData.resize(newSize)
								ctk_img = CTkImage(dark_image=imageData, size=imageData.size)
								label = CTkLabel(targetFrame, image=ctk_img, text="", compound="center")
								label.image = ctk_img
								label.grid(row=0, column=col, padx=5, pady=5, sticky="w")
							else:
								label = CTkLabel(targetFrame, text=part, wraplength=400, justify="left", anchor="w")
								label.grid(row=0, column=col, padx=5, pady=5, sticky="w")
						else:
							label = CTkLabel(targetFrame, text=part, wraplength=400, justify="left", anchor="w")
							label.grid(row=0, column=col, padx=5, pady=5, sticky="w")
						col += 1
					row += 1
					continue
				
				# Single image placeholder line
				if line.startswith("[Image:") and imageUrls:
					match = line[7:-1].strip()
					if match in imageUrls:
						imageDataQuery = self.getImageDataFromURL(url=match)
						if imageDataQuery:
							with NamedTemporaryFile(suffix=".png") as temp:
								tempPath = temp.name
							name = os.path.basename(tempPath)
							with open(str(rootFilepath) + f"/base/assets/temp/{name}","wb") as _image_data:
								_image_data.write(imageDataQuery)
								_image_data.close()
							imageData = Image.open(str(rootFilepath) + f"/base/assets/temp/{name}").convert("RGBA")
							maxWidth, maxHeight = 400, 400
							originalWidth, originalHeight = imageData.size
							if originalWidth > maxWidth or originalHeight > maxHeight:
								scale = min(maxWidth / originalWidth, maxHeight / originalHeight)
								newSize = (int(originalWidth * scale), int(originalHeight * scale))
								imageData = imageData.resize(newSize,Image.LANCZOS)
								imageData = imageData.filter(ImageFilter.SHARPEN)
							ctk_img = CTkImage(dark_image=imageData, size=imageData.size)
							label = CTkLabel(targetFrame, image=ctk_img, text="", compound="center")
							label.image = ctk_img
							label.grid(row=row, column=0, padx=5, pady=5, sticky="w")
						else:
							label = CTkLabel(targetFrame, text=line, wraplength=400, justify="left", anchor="w")
							label.grid(row=row, column=0, padx=5, pady=5, sticky="w")
					else:
						label = CTkLabel(targetFrame, text=line, wraplength=400, justify="left", anchor="w")
						label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

				# YouTube video button line
				elif line.startswith("[YouTube video #") and youtubeUrls:
					if yt_button_count <= len(youtubeUrls):
						CTkButton(targetFrame, text=f"Play Video #{yt_button_count}",
							command=lambda url=youtubeUrls[yt_button_count-1]: self.openVideoViewer(url)
						).grid(row=row, column=0, sticky="w", padx=5, pady=5)
						yt_button_count += 1
					else:
						label = CTkLabel(targetFrame, text=line, wraplength=400, justify="left", anchor="w")
						label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

				# Plain text line
				else:
					label = CTkLabel(targetFrame, text=line, wraplength=400, justify="left", anchor="w")
					label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

				row += 1
			return
		
		def populateDetails(self):
			#get the current item
			currentMod = self.modlist.get()
			#We need to get the tuple with the modname
			for entry in self.listingData:
				modentryQuery_name = entry[0]
				if modentryQuery_name == str(currentMod):
					#this is the tuple we need
					mod_dataTuple = entry
					break
				else:
					continue
			#We need to get the project ID
			selectedModID = mod_dataTuple[1]
			#Parse the curseID
			modDescription = self.curseHandle.getdescription(id=int(selectedModID))
			youtubeLinks = self.extractYoutubeLinks(modDescription)
			modDescription = self.stripYoutube_iframes(modDescription)
			imageLinks = self.extractImageURLs(html=modDescription[0])
			modDescription = self.stripImages(html=modDescription[0])
			hyperLinkURLs = self.extractHyperlinkURLs(html=modDescription)
			modDescription = self.stripHyperlinks(html=modDescription)
			modDescription = re.sub(r'\[Link:\s*.*?\]', '', modDescription)
			modDescription = self.extractModDescription_htmlToMultilinePlain(html=modDescription)
			self.lineData = self.extractModDescription_htmlToDict(html=modDescription)
			self.root.after(10,lambda:self.generateWidgets(imageUrls=imageLinks,youtubeUrls=youtubeLinks))
			return
		
		def onSendData_addToPendingItems(self):
			if self.reviewer is not None:
				if self.reviewerBool:
					#Get the selected mod
					currentmod = self.modlist.get()
					#Communicate to the Modpack Reviewer and tell it to add the mod to pending items
					searchQuery = self.reviewer.parseListings(modName=str(currentmod)) #Returns as a tuple
					if searchQuery[2] == "client":
						#Its in a possible client mod, but may not be a client-only mod
						self.reviewer.addClientToPending(overrideSelection=True,selectedVal=currentmod)
						return
					else:
						if searchQuery[2] == "server":
							self.reviewer.addServerToPending(overridSelection=True,selectedVal=currentmod)
							return
						else:
							if searchQuery[2] == "resource-pack":
								self.reviewer.addResourcePackToPending(overrideSelection=True,selectedVal=currentmod)
								return
				else:
					#Do nothing
					return
			else:
				#Do nothing
				return

outputLog_ui.info_print("Loaded User Interfaces.")
