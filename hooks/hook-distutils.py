# Custom hook to prevent distutils conflicts
# This overrides PyInstaller's default distutils hook

# Do nothing - prevent any distutils processing
hiddenimports = []
datas = []
binaries = []
