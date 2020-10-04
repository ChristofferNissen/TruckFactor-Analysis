import subprocess

def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """

    subprocess.check_output(['git', 'clone', req, 'repository'])
    subprocess.check_output(['cd', 'repository'])
    output = subprocess.check_output(['github-linquist', '--breakdown'], text=True)
    
    return output
