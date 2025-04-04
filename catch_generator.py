from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from pymongo import MongoClient
import urllib


def check_query_present(query):

    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    embeddings  = HuggingFaceEmbeddings(
                model_name='sentence-transformers/msmarco-bert-base-dot-v5',
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
    
    vector_store = FAISS.load_local('faiss_index', embeddings=embeddings , allow_dangerous_deserialization=True)

    

    # print("count before:", vector_store.index.ntotal)
    # vector_store.delete([vector_store.index_to_docstore_id[0]])
    # print("count after:", vector_store.index.ntotal)
    # vector_store.save_local('faiss_index')

    similer_query = vector_store.similarity_search_with_score(query , k=1)
    score = similer_query[0][1]

    if score <= 0.05:
        return similer_query[0][0].page_content
    else:
        vector_store.add_texts([query])
        vector_store.save_local('faiss_index')
        return False
    



def get_cached_document(similar_query , username , pwd , database_name , collection_name):

    client = MongoClient('mongodb+srv://' + urllib.parse.quote_plus(username) + ":" + urllib.parse.quote_plus(pwd) + '@cluster0.jjbz59l.mongodb.net/?retrywrites=true&w=majority&appName=Cluster0')
    db = client['talk_mongo']  # replace with your database name
    collection = db['cache_data']  # replace with your collection name

    document = collection.find_one({"query": similar_query})
    print(document)
    client.close()

    if document:
        return document['docs']
    else:
        return []




def add_document(query, docs , username , pwd):
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://' + urllib.parse.quote_plus(username) + ":" + urllib.parse.quote_plus(pwd) + '@cluster0.jjbz59l.mongodb.net/?retrywrites=true&w=majority&appName=Cluster0')
    db = client['talk_mongo']  # replace with your database name
    collection = db['cache_data']  # replace with your collection name
    # Insert the new document
    collection.insert_one({"query": query, "docs": docs})
    # Close the connection
    client.close()

