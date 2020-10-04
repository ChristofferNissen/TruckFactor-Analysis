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

    f = io.StringIO()
    with redirect_stdout(f):

        if not os.path.exists("repository/"):
            subprocess.check_output(['git', 'clone', req, 'repository'], text=True)
        try:
            output = subprocess.check_output(['github-linguist --breakdown'], text=True, cwd="repository/", shell=True)
            print(output)
        finally:
            shutil.rmtree("repository/")
    
    out = f.getvalue()
    
    arr = out.split('\n')

    res = ""
    for l in arr:
        if not l == "Cloning into 'repository'...":
            res = res + l

    return res
