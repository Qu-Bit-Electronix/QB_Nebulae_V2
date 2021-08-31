from re import compile
import os

scale_reg = compile(r'scale +[A-Za-z_][A-Za-z_0-9]* *, *([0-9.\-]+) *, *([0-9.\-]+)')

def fix_string(string):
  if not 'scale' in string:
    return
  match = scale_reg.search(string)
  if match is not None:
    num1 = match.group(1)
    num2 = match.group(2)

    if (float(num1) > float(num2)):
      raise ValueError('Warning: a scale value was found in the expected order')

    string = string[:match.start(1)] + num2 + string[match.end(1):]
    string = string[:match.start(2)] + num1 + string[match.end(2):]

  return string

def getInstr(dir):
  for file in os.listdir(dir):
    if not os.path.isdir(file) and '.instr' in file:
      return file
  return None

def fixFile(filepath):
  strings = []
  with open(filepath, 'r') as file:
    for line in file:
      try:
        strings.append(fix_string(line))
      except ValueError:
        print(f'Error in file "{filepath}" with line:\n{line}')
        strings.append(line)
  
  with open(filepath, 'w') as file:
    file.write(''.join(strings))

for dir in os.listdir('.'):
  if os.path.isdir(dir):
    instr = getInstr(dir)
    if instr is not None:
      fullpath = os.path.join(dir, instr)
      print(f'Fixing {fullpath}...')
      fixFile(fullpath)

print('Correction complete!')

