import os
import re
import shutil
import hashlib

def exact_line_deduplication(input_files, output_dir):
    # generate hash/dict
    line_dict = {}
    file_dict = {}

    for file in input_files:
        with open(file, 'r') as f:
            content = f.read()
        
        lines = re.split(r'\n+', content)

        for i, line in enumerate(lines):
            if not line.strip():  # skip empty lines
                continue
            hash = hashlib.md5(line.encode()).hexdigest()
            file_basename = os.path.basename(file)
            if hash not in line_dict:
                line_dict[hash] = {
                    "line_id": [i],
                    "file_basenames": [file_basename]
                }
            else:
                line_dict[hash]["line_id"].append(i)
                line_dict[hash]["file_basenames"].append(file_basename)

    # file as key, duplicated line_ids as value
    for _, v in line_dict.items():
        line_ids, file_basenames = v.values()
        if len(set(file_basenames)) == 1:
            continue
        for line_id, file_basename in zip(line_ids, file_basenames):
            if file_basename not in file_dict:
                file_dict[file_basename] = [line_id]
            else:
                file_dict[file_basename].append(line_id)

    # write new file to output dir
    for file in input_files:
        file_basename = os.path.basename(file)
        file_tgt = os.path.join(output_dir, file_basename)

        # if file has no duplication, just make a copy
        if file_basename not in file_dict:
            shutil.copy(file, file_tgt)
            continue

        with open(file, 'r') as f:
            content = f.read()
        
        lines = re.split(r'\n+', content)
        lines2rm_ids = file_dict[file_basename]

        new_lines = [lines[i] for i in range(len(lines)) if i not in lines2rm_ids]
        with open(file_tgt, 'w') as f:
            f.write("\n".join(new_lines))