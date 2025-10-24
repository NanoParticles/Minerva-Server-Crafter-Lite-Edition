from base.modules.server import ServerFileIO
from base.modules.kernel import MCSCKernelCore
outputLog_framework = MCSCKernelCore(module="Framework")
from base.modules.gui.ui import AboutDialogWindowClass,ResourcePackWindow,MOTDWindow,curseforgeUI
from base.modules.utils import MCSCInternalError
from base.modules.msc_zipfile import MSCZipLib,MSCZipAccessLib
from base.modules.config import operatingSystem,ServerIsRunning,rootFilepath
import sys
import os

if operatingSystem == "Windows":
	import ctypes

class MCSC_Framework():
	def onMainWindow_remoteModpack():
		remoteModpack = curseforgeUI.CurseforgeRemoteModpackImport()
		return
	def onMainWindow_import():
		mscAccess = MSCZipAccessLib()
		mscAccess.readInstanceArchive()
		if not mscAccess.instance_data:
			outputLog_framework.info_print("Operation Cancelled by the user.")
			return
		instance_name = mscAccess.instance_data["Instance Name"]
		category = mscAccess.instance_data["server_type"].capitalize()
		ServerFileIO.loadJSONProperties(instanceName=str(instance_name),category=str(category))
		return

	def onMainWindow_export(category=None,id=None):
		import zipfile
		import json

		path = str(rootFilepath) + f"/base/sandbox/Instances/{category}/{id}"
		with open(str(path) + "/schema_instance.json","r") as schema:
			schema_data = json.load(schema)
		with open(str(path) + "/config.json","r") as instance:
			instance_data = json.load(instance)
		with zipfile.ZipFile(str(path) + "/sample.zip","r") as zipObjectTarget:
			test = MSCZipLib(schema=schema_data,instanceData=instance_data,zipobj=zipObjectTarget)
		test.createMSCArchive()
		return
	def onMainWindow_openAbout(parent):
		aboutdlg = AboutDialogWindowClass(parent)
		return
	def onMainWindow_setTabState(widget,tabName,state):
		selectedWidget = widget
		selectedWidget._segmented_button._buttons_dict[str(tabName)].configure(state=str(state))
		return
	def onMainWindow_onExit(parent):
		global ServerIsRunning
		#We need to handle the autosaving to prevent data loss
		currentInstance = ServerFileIO.getLastConfigData()
		name = currentInstance['id']
		category = currentInstance['category']
		ServerFileIO.exportPropertiestoJSON(instanceName=str(name),category=str(category))
		ServerFileIO.onExit_setInstancePointer(instanceName=str(name),category=str(category))
		mcsc_sysExit = SystemExit()
		#Is the server running?
		if ServerIsRunning:
			#Terminate the server
			global process2
			global outputThread
			process2.stdin.write('/stop\n')
			process2.stdin.flush()
			outputLog_framework.info_print("Shutting down server...")
			returncode = process2.wait()
			outputThread.join()
			mcsc_sysExit.code = returncode
			if returncode == 0:
				outputLog_framework.info_print(f"Server was shutdown successfully (Internal Server Process Return Code: {returncode})")
			else:
				outputLog_framework.error_print(f"Something unexpected happened while trying to close the program (Internal Server Process Return Code: {returncode})")
				raise MCSCInternalError(msg=f"Something unexpected happend while trying to close the program (Internal Server Process Return Code: {returncode})")
		if mcsc_sysExit.code is None:
			mcsc_sysExit.code = 0
		mcsc_sysExit.add_note(f"Program has been successfully closed by the user. Return code: {mcsc_sysExit.code}")
		outputLog_framework.info_print(mcsc_sysExit.__notes__[0])
		parent.destroy()
		sys.exit(0)

	def onMainWindow_openResourcePackConfig(parent):
		resourcePackConfig = ResourcePackWindow(parent)
		return
	
	def onMainWindow_openMOTDConfig(parent):
		motdConfig = MOTDWindow(parent)
		return
	
	def onMainWindow_refreshWindowSize(window_widget=None,width=None,height=None):
		#Window Scaling helper
		window_widget.geometry(f"{width}x{height}")
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
outputLog_framework.info_print("Loaded Minerva Server Crafter Framework.")