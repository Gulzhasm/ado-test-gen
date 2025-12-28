from ado.client import ADOClient

client = ADOClient()

response = client.get(
    "_apis/projects",
    params={"api-version": "7.1-preview.4"}
)

data = response.json()
print("Connected OK. Projects count:", len(data.get("value", [])))