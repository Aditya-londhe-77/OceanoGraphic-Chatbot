import chromadb
from sentence_transformers import SentenceTransformer


documents = [
    "Konkan Coast ARGO Data: The 'argo_trajectory' table contains location data for the ARGO float deployed along the Konkan Coast, including latitude and longitude for each measurement point, showing its path.",
    "Konkan Coast ARGO Data: The 'argo_profiles' table holds the scientific oceanographic measurements collected by the Konkan Coast floats. It includes columns for pressure (PRES), temperature (TEMP), and salinity (PSAL) at various depths.",
    "Konkan Coast ARGO Data: The 'argo_technical' table contains operational logs and technical parameters for the Konkan Coast ARGO float. This includes information about cycle numbers, data transmission, and system health checks.",
    "Konkan Coast ARGO Data: The 'argo_metadata' table contains static identification and configuration details for the Konkan Coast float. This includes information like the float's serial number, project name, PI name, launch date, and sensor types."
]

metadatas = [
    {'table_name': 'argo_trajectory', 'float_name': 'Konkan Coast Float'},
    {'table_name': 'argo_profiles',   'float_name': 'Konkan Coast Float'},
    {'table_name': 'argo_technical',  'float_name': 'Konkan Coast Float'},
    {'table_name': 'argo_metadata',   'float_name': 'Konkan Coast Float'}
]

ids = [f"doc_{i+1}" for i in range(len(documents))]



model = SentenceTransformer('all-MiniLM-L6-v2')


client = chromadb.PersistentClient(path="argo_vectordb")

collection_name = "argo_tables_schema"
if collection_name in [c.name for c in client.list_collections()]:
    client.delete_collection(name=collection_name)

collection = client.create_collection(name=collection_name)

embeddings = model.encode(documents).tolist()

collection.add(
    embeddings=embeddings,
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("\n Vector Store Complete with float-specific metadata!")



query_text = "What was the water temperature at different depths for the Konkan Coast float?"
query_embedding = model.encode([query_text]).tolist()

results = collection.query(
    query_embeddings=query_embedding,
    n_results=1,
    where={"float_name": "Konkan Coast Float"} 
)

print(f"\nQuery: '{query_text}'")
print("Most relevant document found using the filter:")
print(f"  - Document: {results['documents'][0][0]}")
print(f"  - Associated Metadata: {results['metadatas'][0][0]}")