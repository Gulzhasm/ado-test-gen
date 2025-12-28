import base64

def build_auth_header(pat: str) -> str:
    """
    Builds a Base64-encoded Authorization header for Azure DevOps PAT auth.
    Format: Authorization: Basic <base64(:PAT)>
    
    :param pat: Description
    :type pat: str
    :return: Description
    :rtype: str
    """
    env_file_encoding = "utf-8"
    token = f":{pat}".encode(env_file_encoding)
    encoded_token = base64.b64encode(token).decode(env_file_encoding)
    return f"Basic {encoded_token}"