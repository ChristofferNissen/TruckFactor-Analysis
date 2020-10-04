import subprocess
import os
import shutil
import io
from contextlib import redirect_stdout

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    arr = req.split("/")
    folderName = arr[arr.__len__()-1] + "/"

    if not os.path.exists(folderName):
        FNULL = open(os.devnull, 'w')
        subprocess.check_output(['git', 'clone', req], stderr=FNULL)
    
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            output = subprocess.check_output(['github-linguist --breakdown'], text=True, cwd=folderName, shell=True)
            print(output)
        finally:
            shutil.rmtree(folderName)
    
    return f.getvalue()
