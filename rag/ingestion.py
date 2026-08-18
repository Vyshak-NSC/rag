import os, re

def stringify_list(lst):
    return ",".join(lst).replace(" ", "-").lower()

def load_md_files(path):
    data = []
    files = [file for file in os.listdir(path) if file.endswith('.md')]
    
    for file in files:
        full_path = os.path.join(path,file)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            links = re.findall(r'\[\[(.*?)\]\]', content)
            links = [link.split("|")[0].strip() for link in links]
            
            res = { "filename" : file.removesuffix('.md'), "text" : content, "links":links}
            data.append(res)
    return data