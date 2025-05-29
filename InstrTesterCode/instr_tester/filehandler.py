import glob

class FileHandler(object):
	def __init__(self, directory, extensions):
		print directory;
		self.files = []
		#self.files = glob.glob(directory + '*' + extension)
		for ext in extensions:
			self.files.extend(glob.glob(directory + '*' + ext))
		self.fileCount = len(self.files)

	def numFiles(self):
		return self.fileCount

