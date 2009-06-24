import glob

for text_file in glob.glob("*.txt"):
    src = open(text_file)
    content = src.read()
    src.close()
    content = content.replace('\r', '')
    content = content.replace('\n', '\r\n')
    dest = open(text_file, 'w')
    dest.write(content)
    dest.close()