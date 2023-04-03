"""
https://tex.stackexchange.com/a/551996 for the original message and script.

I use it to generate a new clean LaTex folder with all the used files directly at the root of the folder, instead of spread in multiple subdirectories. This is a requirement for preprint servers like arXiv and HAL.

(If you only want to delete unused files, then simply use the content of the newly created clean folder)

The script takes as input:

a list of TeX file to parse (in case you split your documents in multiple files, located in the same folder)
a list of file extensions of the potentially unused files we wish to look for
some other self-explanatory options
The script looks in the specified TeX files for all occurrences of the specified extension and builds a list of all used files with this extension. All these files are copied over to a new specified folder. Other files found at the root of the TeX folder are also copied for convenience (except TeX compilation files, and the previous unused files). The provided TeX files are copied over as well, but all their references to the files are changed so that they point directly to the new files at the root of the new folder.

That way, you directly obtain a compilation-ready LaTex folder with all the files you need.

"""

import os, sys, shutil
import re
import ntpath

############ INPUTS ###############
# list of Tex files to parse
# (they should all be within the same folder, as the image paths
# are computed relative to the first TeX file)
texPathList = ["/home/my/tex/folder/my_first_file.tex",
               "/home/my/tex/folder/my_second_file.tex"]

# extensions to search
extensions=[".png", ".jpg", ".jpeg", ".pdf", ".eps"]

bExcludeComments = True # if True, files appearing in comments will not be kept
# path where all used images and the modified TeX files should be copied
# (you can then copy over missing files, e.g. other types of images, Bib files...)

# location of the new folder (should not exist already)
exportFolder = '/home/my/new/folder/clean_article/'

#  should all other files in the root folder (not in subfolders) be copied ?
# (temporary TeX compilation files are not copied)
bCopyOtherRootFiles = True

############## CREATE CLEAN FOLDER #################
# 1 - load TeX files
text=''
for path in texPathList:
  with open(path,'r') as f:
    text = text + f.read()
    
# 2 - find all occurrences of the extension
global_matches = []
for extension in extensions:
  escaped_extension = '\\'+extension # so that the point is correctly accounted for
  pattern=r'\{[^}]+'+escaped_extension+'}'
  if not bExcludeComments: # simply find all occurrences
    matches = re.findall(pattern=pattern, string=text) # does not give the position
  else: # more involved search
    # 2.1 - find all matches
    positions, matches = [], []
    regex = re.compile(pattern)
    for m in regex.finditer(text):
        print(m.start(), m.group())
        positions.append( m.start() )
        matches.append( m.group())
    # 2.2 - remove matches which appear in a commented line
    # parse list in reverse order and remove if necessary
    for i in range(len(matches)-1,-1,-1):
      # look backwards in text for the first occurrence of '\n' or '%'
      startPosition = positions[i]
      while True:
        if text[startPosition]=='%':
          # the line is commented
          print('file "{}" is commented (discarded)'.format(matches[i]))
          positions.pop(i)
          matches.pop(i)
          break
        if text[startPosition]=='\n':
          # the line is not commented --> we keep it
          break
        startPosition -= 1
  global_matches = global_matches + matches
  
# 3 - make sure there are no duplicates
fileList = set(global_matches)
if len(global_matches) != len(fileList):
  print('WARNING: it seems you have duplicate images in your TeX')
# 3.1 - remove curly braces
fileList = [m[1:-1] for m in fileList]

# 4 - copy the used images to the designated new location
try:
  os.makedirs(exportFolder)
except FileExistsError:
  raise Exception('The new folder already exists, please delete it first')

texRoot = os.path.dirname(texPathList[0])
for m in fileList:
  absolutePath = os.path.join(texRoot, m)
  shutil.copy(absolutePath, exportFolder)

# 5 - copy the TeX files also, and modify the image paths they refer to
for path in texPathList:
  with open(path,'r') as f:
    text = f.read()
  for m in fileList:
    text = text.replace(m, ntpath.basename(m) )
  newPath = os.path.join(exportFolder, ntpath.basename(path))
  with open(newPath, 'w') as f:
    f.write(text)

# 6 - if chosen, copy over all the other files (except TeX temp files)
# which are directly at the root of the original TeX folder
if bCopyOtherRootFiles:
  excludedExtensions = ['.aux', '.bak', '.blg', '.bbl', '.spl', '.gz', '.out', '.log']
  for filename in os.listdir(texRoot):
    fullPath = os.path.join(texRoot, filename)
    if os.path.isfile(fullPath):
      ext = os.path.splitext(filename)[1]
      # do not copy already modified TeX files
      if not ( filename in [ntpath.basename(tex) for tex in texPathList]):
        # do not copy temporary files
        if not ( ext.lower() in excludedExtensions ):
          # do not copy files we have already taken care of
          if not ( ext.lower() in extensions ):
            shutil.copy( fullPath, exportFolder)

# The export folder now contains the modified TeX files and all the required files !
