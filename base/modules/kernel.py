import logging
import builtins
import inspect
import sys
import io
from contextlib import contextmanager


#Disable all print-statements
def restore(*args, sep=' ', end='\n', file=sys.stdout, flush=False):
	output = sep.join(map(str, args)) + end
	file.write(output)
	if flush:
		file.flush()
	return

def printOverride(*args,**kwargs):
	#Obtain the frame
	frame = inspect.currentframe()
	frameCalling = frame.f_back if frame else None
	if frameCalling is None:
		raise RuntimeError("[Minerva Server Crafter]: print() function is disabled (unknown caller). Use MCSCKernelCore instead.")
	
	filename = frameCalling.f_code.co_filename
	line_number = frameCalling.f_lineno
	error = RuntimeError(f"[Minerva Server Crafter]: print() function is disabled. Use MCSCKernelCore for console output. Called from {filename} on line {line_number}")
	raise error.with_traceback(frame.f_trace)

#Override the builtin
builtins.print = printOverride

@contextmanager
def briefRestore():
	'Temporarily restores functionality of the print() function'
	builtins.print = restore
	try:
		yield
	finally:
		builtins.print = printOverride
		return

class MCSCKernelCore():
	def __init__(self,module=None,logic=None):
		self.module_ = module
		self.logic_ = logic
		if module is None and logic is None:
			self.module_prefix = "[Minerva Server Crafter]"
		if module is not None and logic is None:
			self.module_prefix = f"[Minerva Server Crafter - {str(module)}]"
		if module is not None and logic is not None:
			self.module_prefix = f"[Minerva Server Crafter - {str(module)} - {str(logic)}]"
		self.logging = logging.Logger(name="MCSCKernel")
		self.loggingStream = logging.StreamHandler()
		self.loggingFormat = logging.Formatter(f'{self.module_prefix}' + '[%(levelname)s]: %(message)s')
		self.loggingStream.setFormatter(self.loggingFormat)
		self.logging.addHandler(self.loggingStream)
		return
	
	def setLogic(self,logic=None):
		if logic is not None:
			self.module_prefix = self.module_prefix = f"[Minerva Server Crafter - {str(self.module_)} - {str(logic)}]"
			self.newLoggingformat = logging.Formatter(f'{self.module_prefix}' + '[%(levelname)s]: %(message)s')
			self.loggingStream.setFormatter(self.newLoggingformat)
		elif logic is None:
			self.module_prefix = self.module_prefix = f"[Minerva Server Crafter - {str(self.module_)}]"
			self.newLoggingformat = logging.Formatter(f'{self.module_prefix}' + '[%(levelname)s]: %(message)s')
			self.loggingStream.setFormatter(self.newLoggingformat)
		return
		
	def info_print(self,msg):
		#Set up the logging
		self.logging.setLevel(level=logging.INFO)
		self.logging.info(str(msg))
		return
	
	def error_print(self,msg):
		#Set up the logging
		self.logging.setLevel(level=logging.ERROR)
		self.logging.error(str(msg))
		return
	
	def warning_print(self,msg):
		self.logging.setLevel(level=logging.WARNING)
		self.logging.warning(str(msg))
		return
	
	def debug_print(self,msg):
		self.logging.setLevel(level=logging.DEBUG)
		self.logging.debug(msg=str(msg))
		return
