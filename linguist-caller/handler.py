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

    if not os.path.exists("repository/"):
        subprocess.check_output(['git', 'clone', req, 'repository'], text=True)
    
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            output = subprocess.check_output(['github-linguist --breakdown'], text=True, cwd="repository/", shell=True)
            print(output)
        finally:
            shutil.rmtree("repository/")
    
    out = f.getvalue()
    
    arr = out.split('\n', 2)[2]

    res = ""
    for l in arr:
        if not res == "":
            res = res + l + "\n"
        else: 
            res = l + "\n"

    return res
