import base64
from PIL import Image
import requests
from io import BytesIO

def render_mermaid(graph):
    graphbytes = graph.encode("ascii")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    url = f"https://mermaid.ink/img/{base64_string}"
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    return image, url