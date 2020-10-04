import subprocess
import os
import shutil
import io
from contextlib import redirect_stdout
import time

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    start = time.time()

    arr = req.split("/")
    folderName = arr[arr.__len__()-1] + "/"

    if folderName.__contains__(".git"):
        folderName = folderName.split(".")[0]

    if not os.path.exists(folderName):
        FNULL = open(os.devnull, 'w')
        subprocess.check_output(['git', 'clone', req], stderr=FNULL)
    
    cloneDone = time.time()

    f = io.StringIO()
    with redirect_stdout(f):
        try:
            output = subprocess.check_output(['github-linguist --breakdown'], text=True, cwd=folderName, shell=True)
            print(output)
        finally:
            shutil.rmtree(folderName)
        linguistDone = time.time()
        print("Clone took:", cloneDone-start, "s")
        print("Linguist took:", linguistDone-cloneDone, "s")
        print("Total:", linguistDone-start, "s")
    
    return f.getvalue()
