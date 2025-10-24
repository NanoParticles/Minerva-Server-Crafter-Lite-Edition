from base.modules.kernel import MCSCKernelCore
outputLog_mscZip = MCSCKernelCore(module="File Operation", logic="msczipLib")
import os
import json
import json5
import zipfile
import io
import zlib
import hashlib
import stat
import platform
import time
from tkinter import filedialog
from datetime import datetime,timezone
from base.modules.utils import MCSCInternalError

class MSCZipLib:
	def __init__(self, schema: dict | None = None, instanceData: dict | None = None, zipobj: zipfile.ZipFile | bytes | None = None, disablePrompt:bool | None = False, destination:str | None = None):
		if schema is not None and instanceData is not None and zipobj is not None:
			self.promptDisabled = disablePrompt
			if self.promptDisabled:
				self.dst = destination
			try:
				# --- Type validation ---
				if not isinstance(schema, dict):
					raise MCSCInternalError(f"schema must be a dict-like object, not {type(schema).__name__}")
				if not isinstance(instanceData, dict):
					raise MCSCInternalError(f"instanceData must be a dict-like object, not {type(instanceData).__name__}")
				if not isinstance(zipobj, (zipfile.ZipFile, bytes, bytearray)):
					raise MCSCInternalError(f"zipobj must be a zipfile.ZipFile or bytes-like object, not {type(zipobj).__name__}")

				# --- Normalize zipobj into a BytesIO buffer ---
				if isinstance(zipobj, zipfile.ZipFile):
					# Read its raw bytes from the underlying file pointer
					if zipobj.fp is None:
						raise MCSCInternalError("zipfile.ZipFile object has no open file pointer (fp is None)")
					zipobj.fp.seek(0)
					self.zip_buff = io.BytesIO(zipobj.fp.read())
				elif isinstance(zipobj, (bytes, bytearray)):
					# Convert bytes-like object into a file-like buffer
					self.zip_buff = io.BytesIO(zipobj)
				else:
					raise MCSCInternalError("Invalid zipobj type after normalization")

				# --- Try opening as a ZipFile ---
				try:
					with zipfile.ZipFile(self.zip_buff, "r") as rawZip:
						listing = rawZip.namelist()
						directories = [info for info in rawZip.infolist() if info.is_dir()]
						last = rawZip.infolist()[-1] if rawZip.infolist() else None
						name = last.filename if last else "N/A"
						size = last.file_size if last else 0
				except zipfile.BadZipFile as zerr:
					raise MCSCInternalError(f"Provided bytes are not a valid ZIP archive: {zerr}")

				# --- Metadata creation ---
				self.meta = {"file_version": "1.0","program_name": "Minerva Server Crafter","created_at": str(datetime.now(timezone.utc).isoformat()),"modified_at": str(datetime.now(timezone.utc).isoformat()),"compressed": True,"encoding": 'utf-8',"schema-version": "1.0","schema-data": schema,"permissions": {'read': True, 'write': False,'configure-modpack': True, 'share': True, 'os-control': True}}
				self.instanceData = instanceData
				self.file_location = None
				self.internal_computeChecksums = False
				self.sha512 = None
				self.crc32 = None

				# Reset position before re-reading
				self.zip_buff.seek(0)
				self.data_bytes = self.zip_buff.read()
				self.hexObj = self.data_bytes.hex()

				self.zipDict = {'name': name,'file_size': size,'dirs': str(directories),'files': str(listing),'Zip-Obj': str(self.hexObj)}

				# --- Combine data ---
				self.meta_bytes = json5.dumps(self.meta).encode('utf-8')
				self.instanceData_bytes = json5.dumps(self.instanceData).encode('utf-8')

				self.merge = (len(self.meta_bytes).to_bytes(4, "big") + self.meta_bytes + len(self.instanceData_bytes).to_bytes(4, "big") + self.instanceData_bytes + len(self.data_bytes).to_bytes(8, "big") + self.data_bytes)

				# --- Compress final payload ---
				self.compression = zlib.compress(self.merge, level=9)
				return

			except MCSCInternalError as e:
				outputLog_mscZip.error_print(f"An error occurred while processing the MSCZip file:\n{e}")
				return
	
	def runComputing(self):
		'Calculates the SHA-512 and the CRC32 checksum'
		self.internal_computeChecksums = True
		retries = 4
		attempt = 1
		while self.internal_computeChecksums and self.sha512 is None and self.crc32 is None:
			if attempt == retries:
				self.internal_computeChecksums = False
				break
			else:
				if self.file_location is not None:
					self.sha512 = self.computeChecksum_sha512()
					self.crc32 = self.computeChecksum_crc32()
					self.internal_computeChecksums = False
				else:
					attempt += 1
					time.sleep(0.1)
					continue
		return
	
	def computeChecksum_sha512(self):
		if self.file_location is not None:
			sha512_hash = hashlib.sha512()
			with open(str(self.file_location), "rb") as f:
				while chunk := f.read(8192):
					sha512_hash.update(chunk)
			return sha512_hash.hexdigest()
	
	def computeChecksum_crc32(self):
		if self.file_location is not None:
			crc = 0
			with open(str(self.file_location), "rb") as f:
				while chunk := f.read(8192):
					crc = zlib.crc32(chunk,crc)
			crc &= 0xFFFFFFFF
			crcVal = f"{crc:08x}"
			return crcVal

	def createMSCArchive(self):
		'Creates Minerva Server Crafter instance file to disk.'
		savedialog = None
		prompted = False
		if self.promptDisabled:
			with open(str(self.dst),"wb") as instance_archive:
				instance_archive.write(b'MSCZIP')
				instance_archive.write(self.compression)
				instance_archive.close()

		elif not self.promptDisabled:
			savedialog = filedialog.asksaveasfile(mode="wb",confirmoverwrite=True,defaultextension=".msczip",filetypes=(('Minerva Server Crafter Instance Archive','*.msczip'),),title="Save Instance As")
			prompted = True
		if savedialog is None and not self.promptDisabled:
			outputLog_mscZip.info_print("Operation cancelled. Will not proceed.")
			return
		try:
			if prompted:
				savedialog.write(b'MSCZIP')
				#We need to calculate the checksums
				savedialog.write(self.compression)
		except Exception as e:
			outputLog_mscZip.error_print(f"Failed to save MSCZip: {e}")
		finally:
			location = savedialog.name if prompted else self.dst
			self.file_location = location
			if prompted:
				savedialog.close()
			self.runComputing()
			outputLog_mscZip.info_print("Checksums")
			outputLog_mscZip.info_print("=========")
			outputLog_mscZip.info_print(f"SHA-512: {self.sha512}")
			outputLog_mscZip.info_print(f"CRC32: {self.crc32}")
			try:
				if self.meta.get("permissions",{}).get("os-control",False):
					if platform.system() in ["Linux","Darwin"]:
						mode = 0
						if self.meta.get("permissions",{}).get("read",False):
							mode |= stat.S_IREAD
						if self.meta.get("permissions",{}).get("write",False):
							mode |= stat.S_IWRITE
						os.chmod(location,mode)
					elif platform.system() == "Windows":
						if self.meta.get("permissions",{}).get("read",False) and not self.meta.get("permissions",{}).get("write",True):
							os.chmod(location,stat.S_IREAD)
						if self.meta.get("permissions",{}).get("write",False):
							os.chmod(location,stat.S_IWRITE)		
			finally:
				outputLog_mscZip.info_print(f'Instance saved successfully to {location}')
				return location

class MSCZipAccessLib():
	def __init__(self):
		self.meta_data = None
		self.instance_data = None
		self.zip_object = None
		self.checksum_sha512 = None
		self.checksum_crc32 = None
		return
	
	def readInstanceArchive(self):
		from base.modules.config import rootFilepath
		try:
			file = filedialog.askopenfile(mode="rb",defaultextension=".msczip",filetypes=[("Minerva Server Crafter Instance Archive","*.msczip")],title="Open MSCZip Archive")
			if file is None:
				outputLog_mscZip.info_print("Operation cancelled by the user")
				return
			data = file.read()
			file.close()

			if data[:6] != b"MSCZIP":
				raise ValueError("Not a valid MSCZip file(missing signature)")
			
			sha512_hash = hashlib.sha256()
			crc = 0
			with open(file.name, "rb") as f:
				while chunk := f.read(8192):
					sha512_hash.update(chunk)
					crc = zlib.crc32(chunk,crc)
			
			crc &= 0xFFFFFFFF
			self.checksum_sha512 = sha512_hash.hexdigest()
			self.checksum_crc32 = f"{crc:08x}"

			compressed_payload = data[6:]
			

			outputLog_mscZip.info_print("Checksums")
			outputLog_mscZip.info_print("=========")
			outputLog_mscZip.info_print(f"SHA-512: {self.checksum_sha512}")
			outputLog_mscZip.info_print(f"CRC32: {self.checksum_crc32}")

			try:
				payload = zlib.decompress(compressed_payload)
			except zlib.error as e:
				raise ValueError(f"Failed to decompress MSCZip payload: {e}")
			#Parse payload
			meta_len = int.from_bytes(payload[0:4],"big")
			meta_json = payload[4:4 + meta_len]
			instance_len_start = 4 + meta_len
			instance_len = int.from_bytes(payload[instance_len_start:instance_len_start + 4],"big")
			instanceJSON = payload[instance_len_start + 4:instance_len_start + 4 + instance_len]
			zip_len_start = instance_len_start + 4 + instance_len
			zip_len = int.from_bytes(payload[zip_len_start:zip_len_start + 8],'big')
			zipbytes = payload[zip_len_start + 8:zip_len_start + 8 + zip_len]

			self.meta_data = json5.loads(meta_json.decode('utf-8'))
			self.instance_data = json5.loads(instanceJSON.decode('utf-8'))
			self.zip_object = io.BytesIO(zipbytes)
			self.schema = self.meta_data.get('schema-data',{})
			#Get the name of the instance and the server type
			name = self.instance_data.get("Instance Name",None)
			serverType = self.instance_data.get("server_type",None)
			if name is not None and serverType is not None:
				path_root = str(rootFilepath) + f"/base/sandbox/Instances/{serverType.capitalize()}/{name}"
				os.makedirs(str(path_root),exist_ok=True)
				with open(str(path_root) + "/config.json","w") as jsonData:
					json.dump(self.instance_data,jsonData,indent=4)
				with open(str(path_root) + "/schema_instance.json","w") as jsonSchema:
					json.dump(self.schema,jsonSchema,indent=4)
				self.zip_object.seek(0)
				with zipfile.ZipFile(self.zip_object) as zf:
					zf.extractall(str(path_root))
				return
			
			else:
				raise Exception("Failed to saved. REASON: Missing or Malformed instance data")

		except Exception as e:
			outputLog_mscZip.error_print(f"Failed to process MSCZip: {e}")
			return
