import subprocess
import os
import shutil

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    if not os.path.exists("repository/"):
        subprocess.check_output(['git', 'clone', req, 'repository'])

    try:
        output = subprocess.check_output(['github-linquist', '--breakdown'], text=True, cwd="repository/", shell=True)
    finally:
        shutil.rmtree("repository/")

    return output
