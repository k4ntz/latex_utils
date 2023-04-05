"""
https://tex.stackexchange.com/a/551996 for the original message and script.

I use it to generate a new clean LaTex folder with all the used files directly at the root of the folder, instead of spread in multiple subdirectories. This is a requirement for preprint servers like arXiv and HAL.

(If you only want to delete unused files, then simply use the content of the newly created clean folder)

The script takes as input:
* a list of TeX file to parse (in case you split your documents in multiple files, located in the same folder)
* a list of file extensions of the potentially unused files we wish to look for
* some other self-explanatory options
The script looks in the specified TeX files for all occurrences of the specified extension and builds a list of all used files with this extension. All these files are copied over to a new specified folder. Other files found at the root of the TeX folder are also copied for convenience (except TeX compilation files, and the previous unused files). The provided TeX files are copied over as well, but all their references to the files are changed so that they point directly to the new files at the root of the new folder.

That way, you directly obtain a compilation-ready LaTex folder with all the files you need.

"""
import os, sys, shutil
import re
import ntpath
import argparse
from pathlib import Path
from pprint import pprint
import subprocess
try:
  from termcolor import colored
except ImportError:
  colored = lambda *args: args
  print("You can use the termcolor module for better prints :)")
try:
  from PyPDF2 import PdfReader, PdfWriter
  PyPDF2_imported = True
except ImportError:
  print("You can install PyPDF2 for (without loss) compression")
  PyPDF2_imported = False


def move_and_compress(orifilepath, newfilepath, hard_compress_folders=[]):
  os.makedirs(os.path.dirname(absoluteCopyPath), exist_ok=True)
  could_compress = False
  if orifilepath[-4:] == ".pdf":
    ori_size = get_size(orifilepath)
    to_be_hard_compress = False
    hard_compressed = False
    for hcf in hard_compress_folders:
      if hcf in orifilepath:
        to_be_hard_compress = True
    if to_be_hard_compress:
      p = subprocess.Popen(['ps2pdf', orifilepath, newfilepath], stdout=subprocess.PIPE)
      p.communicate()
      if p.returncode == 0:
        new_size = get_size(newfilepath)
        if new_size < ori_size:
          print(f"X  {orifilepath} ({format_file_size(ori_size)}) -> {newfilepath} ({format_file_size(new_size, colorize=True)}) (HARD compressed)")
          hard_compressed = True
          could_compress = True
    if not hard_compressed and not args.no_compress and PyPDF2_imported:
      reader = PdfReader(orifilepath)
      writer = PdfWriter()
      for page in reader.pages:
          page.compress_content_streams()  # This is CPU intensive!
          writer.add_page(page)
      with open(newfilepath, "wb") as f:
          writer.write(f)
      new_size = get_size(newfilepath)
      print(f"  {orifilepath} ({format_file_size(ori_size)}) -> {newfilepath} ({format_file_size(new_size, colorize=True)}) (compressed)")
      could_compress = True
  if not could_compress:
    shutil.copy(absoluteOriPath, absoluteCopyPath)
    print(f"   {orifilepath} -> {newfilepath}")


def get_size(filepath):
  if os.path.isfile(filepath):
    file_size = os.path.getsize(filepath)
  else:
    file_size = 0
    for dirpath, _, filenames in os.walk(filepath):
      for f in filenames:
          fp = os.path.join(dirpath, f)
          # skip if it is symbolic link
          if not os.path.islink(fp):
              file_size += os.path.getsize(fp)
  return file_size


def format_file_size(file_size, rnd=1, colorize=False):
  modif = colored if colorize else lambda x, y:x
  if file_size > 1073741824:
    file_size = file_size / 1073741824
    return str(round(file_size, rnd)) + modif('GB', 'red')
  elif file_size > 1048576:
    file_size = file_size / 1048576
    return str(round(file_size, rnd)) + modif('MB', 'yellow')
  elif file_size > 1024:
    file_size = file_size / 1024
    return str(round(file_size, rnd)) + modif('KB', 'blue')
  else:
    return str(file_size) + 'B' 


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                      prog='clean_unused',
                      description='Clean the unused tex and figures.')
  parser.add_argument('folder', help='main folder path, base argument')           # positional argument
  parser.add_argument('--tex_files', '-tf', nargs='+',
                      help='list of main tex files, if none given, take all the tex_files of folder root')
  # parser.add_argument('--exclude', '-e', nargs='+', default=[],
  #                     help='path to exclude')
  parser.add_argument('--hard_compress', '-hc', nargs='+', default=[],
                      help='path to PDF files that will be hard compress (with loss of quality using "ps2pdf") linux command')
  parser.add_argument('--all_in_root', '-air',
                      help='moves every file to root directory and modify the tex files accordingly')
  parser.add_argument('--no_compress', '-nc', action="store_true",
                      help='Avoid compression of the PDF images files without loss of quality if possible (using PyPDF2)')

  args = parser.parse_args()

  if not args.tex_files:
    all_tex_files = []
    for texfile in os.listdir(args.folder):
      if texfile.endswith(".tex"):
          all_tex_files.append(os.path.join(args.folder, texfile))
  else:
    all_tex_files = args.texfiles

  found_included_files = False
  for main_tex_path in all_tex_files:
    with open(main_tex_path,'r') as f:
      text = f.read()
    included_files = re.findall(pattern=r"\\include{[a-zA-Z0-9_/]*}", string=text) + \
                      re.findall(pattern=r"\\input{[a-zA-Z0-9_/]*}", string=text)
    if included_files:
      found_included_files = True
      pardir = Path(main_tex_path).parent.as_posix()
      for included in included_files:
        included_filename = included[:-1].replace("\\include{", '').replace("\\input{", '') + '.tex'
        included_filepath = os.path.join(pardir, included_filename)
        if included_filepath not in all_tex_files:
          all_tex_files.append(included_filepath)

  if found_included_files:
    print(colored("Found included files, new extended tex files to be searched in:", "blue"))
    pprint(all_tex_files)
    print()

  # extensions to search
  extensions=[".pdf", ".png", ".jpg", ".jpeg", ".eps"]

  bExcludeComments = True # if True, files appearing in comments will not be kept
  # path where all used images and the modified TeX files should be copied
  # (you can then copy over missing files, e.g. other types of images, Bib files...)

  # location of the new folder (should not exist already)
  exportFolder = args.folder + '_cleaned'
  if os.path.exists(exportFolder):
    print(colored(f'WARNING: {exportFolder} already exist, remove it for a new clean folder.' ,'red'))

  #  should all other files in the root folder (not in subfolders) be copied ?
  # (temporary TeX compilation files are not copied)
  bCopyOtherRootFiles = True

  ############## CREATE CLEAN FOLDER #################
  # 1 - load TeX files
  text=''
  global_matches = []
  for filepath in all_tex_files:
    with open(filepath,'r') as f:
      text = f.read()   
    # 2 - find all occurrences of the extension (for each tex file)
    found_any = False
    warned_for_discard = False
    for extension in extensions:
      escaped_extension = '\\'+extension # so that the point is correctly accounted for
      pattern=r'\{[^}]+'+escaped_extension+'}'
      if not bExcludeComments: # simply find all occurrences
        matches = re.findall(pattern=pattern, string=text) # does not give the position
      else: # more involved search
        # 2.1 - find all matches
        positions, matches = [], []
        regex = re.compile(pattern)
        found_matches = regex.finditer(text)
        for m in found_matches:
            found_filename = m.group()
            if "]" in found_filename:
              idx = found_filename.find(']')
              found_filename = found_filename[idx+1:]
            if not found_any:
              print(f"Finding these references to files (with their position in {filepath})\npos\t filename")
              found_any = True
            print(m.start(), "\t", found_filename[1:-1])
            positions.append(m.start())
            matches.append(found_filename)
        # 2.2 - remove matches which appear in a commented line
        # parse list in reverse order and remove if necessary
        for i in range(len(matches)-1,-1,-1):
          # look backwards in text for the first occurrence of '\n' or '%'
          startPosition = positions[i]
          while True:
            if text[startPosition]=='%':
              # the line is commented
              if not warned_for_discard:
                print(colored('The following files are commented, so are not going to be included:', 'yellow'))
                warned_for_discard = True
              print(colored('--> file "{}"'.format(matches[i]), 'yellow'))
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
  if not os.path.exists(exportFolder):
    os.makedirs(exportFolder)

  print(f"Moving files over to the new {exportFolder}")
  if args.all_in_root:
    texRoot = args.folder
    for m in fileList:
      absolutePath = os.path.join(texRoot, m)
      move_and_compress(absolutePath, exportFolder, args.hard_compress)
  else:
    texRoot = args.folder
    for m in fileList:
      absoluteOriPath = os.path.join(texRoot, m)
      absoluteCopyPath = os.path.join(exportFolder, m)
      move_and_compress(absoluteOriPath, absoluteCopyPath, args.hard_compress)

  # 5 - copy the TeX files also, and modify the image paths they refer to
  print(colored("Copying over :", "blue"))
  if args.all_in_root:
    for path in all_tex_files:
      with open(path,'r') as f:
        text = f.read()
      for m in fileList:
        text = text.replace(m, ntpath.basename(m) )
      newPath = os.path.join(exportFolder, ntpath.basename(path))
      with open(newPath, 'w') as f:
        f.write(text)
      print(f"  {path} -> {newPath}")
  else:
    for orifilepath in all_tex_files:
      could_compress = False
      newfilepath = orifilepath.replace(args.folder, exportFolder)
      if not os.path.exists(newfilepath):
        os.makedirs(os.path.dirname(newfilepath), exist_ok=True)
        shutil.copy(orifilepath, newfilepath)
        print(f"  {orifilepath} -> {newfilepath}")


  # 6 - if chosen, copy over all the other files (except TeX temp files)
  # which are directly at the root of the original TeX folder
  if bCopyOtherRootFiles:
    excludedExtensions = ['.aux', '.bak', '.blg', '.bbl', '.spl', '.gz', '.out', '.log']
    for filename in os.listdir(texRoot):
      fullPath = os.path.join(texRoot, filename)
      if os.path.isfile(fullPath):
        ext = os.path.splitext(filename)[1]
        # do not copy already modified TeX files
        if not (filename in [ntpath.basename(tex) for tex in all_tex_files]):
          # do not copy temporary files
          if not (ext.lower() in excludedExtensions ):
            # do not copy files we have already taken care of
            if not (ext.lower() in extensions ):
              shutil.copy(fullPath, exportFolder)

  if not args.no_compress and not PyPDF2_imported:
    print("Cannot compress the PDF as could not import PyPDF2 module, avoid with --no_compress", "red")
    print("-> pip install PyPDF2", "red")

  # The export folder now contains the modified TeX files and all the required files !
  print(colored(f"\n\tSaved clean new repo in {exportFolder}", 'green'))
  ofs = format_file_size(get_size(args.folder))
  nfs = format_file_size(get_size(exportFolder))
  print(colored(f"\tOriginal folder size: {ofs}", 'green'))
  print(colored(f"\tNew folder size:      {nfs}", 'green'))