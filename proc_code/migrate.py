import json
import os
import shutil
from typing import List

from . import path_tools
from . import metadata
from . import load_data

def main_addv():
    return
    
    folders: List[str] = load_data.find_experiment_folders(os.path.join(path_tools.DATA_BASE_DIR,"chargers", "USCA"))

    for exp in folders:
        bak_file = os.path.join(exp, "backup.bak.txt")
        if os.path.isfile(bak_file):
            with open(bak_file, "r") as f:
                baklines = f.readlines()
            info_entry = json.loads(baklines[1])
            print(info_entry["type"])
            if info_entry["type"] == "INFO":
                if "v" in info_entry["data"] and info_entry["data"]['v'] is not None:
                    #print("Skipping ", exp)
                    continue
                else:
                    print("Fixing ", exp)
                info_entry["data"] = {"v":0} | info_entry["data"]
                info_entry["data"]["v"] = 7
                baklines[1] = json.dumps(info_entry, indent = None) + "\n"
                with open(bak_file, "w") as f:
                    f.writelines(baklines)
            else:
                print("Skipping incompatible ", exp)

        main_file = os.path.join(exp, "result.json")
        if os.path.isfile(main_file):
            with open(main_file, "r") as f:
                content = json.load(f)
            content["data"][0]["data"] = {"v":0} | content["data"][0]["data"]
            content["data"][0]["data"]["v"] = 7
            with open(main_file, "w") as f:
                json.dump(content, f, indent=2)

if __name__ == "__main__":
    main_addv()