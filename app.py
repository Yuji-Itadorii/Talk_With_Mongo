from langchain_community.llms import HuggingFaceEndpoint
import os, io, json
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from Generate_Schema import get_schema
import urllib
import pandas as pd
import re
from langchain_community.chat_models import ChatHuggingFace
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from catch_generator import check_query_present, add_document, get_cached_document

load_dotenv()
HF_TOKEN = os.environ.get('HUGGINGFACEHUB_API_TOKEN')

with io.open("sample.txt", "r", encoding="utf-8") as f1:
    sample = f1.read()

st.title("Talk to MongoDB")
st.write("Ask anything and get an answer")

# Dynamic user inputs for MongoDB connection
username = st.text_input("Enter MongoDB Username:")
pwd = st.text_input("Enter MongoDB Password:", type="password")
database_name = st.text_input("Enter Database Name:")
collection_name = st.text_input("Enter Collection Name:")

input_question = st.text_area("Enter your question here")

def extract_query(text):
    pattern = re.compile(r'\[\s*.*\s*\]', re.DOTALL)
    
    match = pattern.search(text)
    
    if match:
        query_str = match.group()
        
        try:
            # Parse the JSON string to a Python object
            query = json.loads(query_str)
            return query
        except json.JSONDecodeError as e:
            return "Failed to parse query"
    else:
        return "No query found in the text."


def create_messages(question, schema, sample):
    system_message_content = (
        "You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into NoSQL MongoDB aggregation pipeline queries. "
        "Note: You have to just return the query as to use in the aggregation pipeline, nothing else. Don't return any other thing. "
        "Please use the below schema to write the only 1 MongoDB queries; don't use any other queries. "
        "Schema: The mentioned MongoDB collection contains information about movies. The schema for this document represents the structure of the data, describing various properties related to the movie, cast, directors, and additional features. "
        "Here’s a breakdown of its schema with descriptions for each field: {schema} "
        "This schema provides a comprehensive view of the data structure for a movie in MongoDB, including nested and embedded data structures that add depth and detail to the document. "
        "Use the below sample examples to generate your queries perfectly. "
        "Sample Example: Below are several sample user questions and the corresponding MongoDB aggregation pipeline queries that can be used to fetch the desired data. {sample} "
        "Very Important Note: You have to just return 1 query code, nothing else. Don't return any additional text with the query. Please follow this strictly."
    ).format(schema=schema, sample=sample)

    user_message_content_1 = "Get the First Document of Database"
    assistant_message_content ="""
        [
              { "$limit" : 1}
              ]
        """
    user_message_content_2 = f"{question}"
    

    messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=user_message_content_1),
            AIMessage(content=assistant_message_content),
            HumanMessage(content=user_message_content_2),
        ]

    
    return messages

# try:
if st.button("Submit"):
  if username and pwd and database_name and collection_name and input_question:

    check = check_query_present(input_question)
    
    if type(check) == str:
        print("Getting cached document. . .")
        cached_document = get_cached_document(check)
        # Display results
        st.write("Results:")
        st.dataframe(pd.DataFrame(list(cached_document)))

    else:
        print("Getting new document. . .")
            # Connect to MongoDB
        client = MongoClient('mongodb+srv://' + urllib.parse.quote_plus(username) + ":" + urllib.parse. quote_plus(pwd) + '@cluster0.jjbz59l.mongodb.net/?retrywrites=true&w=majority&appName=Cluster0')
        db = client[database_name]
        collection = db[collection_name]

            # Get schema
        schema = get_schema(username, pwd, database_name, collection_name)

            # Define the language model and chain
        repo_id = "microsoft/Phi-3-mini-4k-instruct"
        llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                max_length=128,
                    temperature=0.01,
                huggingfacehub_api_token='YOUR_TOKEN',
        )

        chatllm = ChatHuggingFace(llm=llm)

        message = create_messages(input_question, schema, sample)

        response = (chatllm(messages=message).content)
        print(response)
        query = extract_query(response)
        results = []
        for doc in collection.aggregate(query):
            results.append(doc)

         # Display results
        st.write("Results:")
        st.dataframe(pd.DataFrame(results))

        # print("document to insert" , results)
        # Adding docs to cached documents
        add_document(input_question, results)


else:
    st.warning("Please fill in all fields and enter a question.")
# except Exception as e:
#     st.error(f"An error occurred: {e}")
