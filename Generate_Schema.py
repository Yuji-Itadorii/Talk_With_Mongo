from pymongo import MongoClient
from urllib.parse import quote_plus
from collections import defaultdict


def get_schema( username , pwd, databse_name , collection_name):
    
    # URL encode the username and password
    username_encoded = quote_plus(username)
    pwd_encoded = quote_plus(pwd)

    uri = f'mongodb+srv://{username_encoded}:{pwd_encoded}@cluster0.jjbz59l.mongodb.net/?retrywrites=true&w=majority&appName=Cluster0'
    client = MongoClient(uri)
    db_name = client[databse_name]
    collection = db_name[collection_name]

    # Sample documents from the collection
    sample_size = 100  # Adjust the sample size as needed
    pipeline = [
        {"$sample": {"size": sample_size}}
    ]

    sample_docs = list(collection.aggregate(pipeline))

    # Function to infer schema from a sample document
    def infer_schema(doc, schema=None):
        if schema is None:
            schema = defaultdict(dict)

        for key, value in doc.items():
            value_type = type(value).__name__
            if isinstance(value, dict):
                schema[key] = infer_schema(value, schema.get(key, {}))
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                schema[key] = [infer_schema(value[0], schema.get(key, [{}])[0])]
            else:
                schema[key] = value_type

        return schema

    # Infer schema from the sample documents
    schema = {}
    for doc in sample_docs:
        schema = infer_schema(doc, schema)

    # Print the inferred schema
    def print_schema(schema, indent=0):
        for key, value in schema.items():
            if isinstance(value, dict):
                print(" " * indent + f"{key}:")
                print_schema(value, indent + 2)
            elif isinstance(value, list) and isinstance(value[0], dict):
                print(" " * indent + f"{key}: [")
                print_schema(value[0], indent + 2)
                print(" " * indent + "]")
            else:
                print(" " * indent + f"{key}: {value}")

    return (schema)
