import os, io, json
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from Generate_Schema import get_schema
from google import genai
import urllib
import pandas as pd
import re
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from catch_generator import check_query_present, add_document, get_cached_document
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

from pydantic import BaseModel
from typing import List, Dict, Any

class MongoQueryOutput(BaseModel):
    query: List[Dict[str, Any]]  # List of aggregation stages


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


def create_messages(input_question, schema, sample):
    

    parser = PydanticOutputParser(pydantic_object=MongoQueryOutput)

    prompt_template = PromptTemplate.from_template(
        """
    You are an intelligent AI assistant specialized in converting user questions into MongoDB aggregation pipeline  queries.

    Rules:
    - Only return a valid MongoDB aggregation pipeline as a Python list.
    - DO NOT include any explanations, comments, or text—only the query.
    - Use the schema and examples provided for reference.
    - Strictly follow JSON-compatible formatting.

    Schema:
    {schema}

    Sample Examples:
    {sample}

    User Question:
    {question}

    {format_instructions}
    """
    )

    formatted_prompt = prompt_template.format(
        schema=schema,  # Your dynamic schema string
        sample=sample,  # Your sample Q&A pairs
        question=input_question,
        format_instructions=parser.get_format_instructions()
    )

    print("Formatted Prompt: ", formatted_prompt)

    return formatted_prompt



# try:
if st.button("Submit"):
  if username and pwd and database_name and collection_name and input_question:

    check = check_query_present(input_question)
    
    if type(check) == str:
        print("Getting cached document. . .")
        cached_document = get_cached_document(check , username , pwd , database_name , collection_name)
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

        message = create_messages(input_question, schema, sample)

        client = genai.Client(api_key="AIzaSyDLXYyLWxc4GnlRZXRGhfuZOlz1yGur8eA")
        response = client.models.generate_content(
                model="gemini-2.0-flash", contents=message
        )

        print("Response : ", response.text)
        query = extract_query(response.text)
        results = []
        for doc in collection.aggregate(query):
            doc['_id'] = str(doc['_id'])
            results.append(doc)

         # Display results
        st.write("Results:")
        st.dataframe(pd.DataFrame(results))

        # print("document to insert" , results)
        # Adding docs to cached documents
        add_document(input_question, results , username , pwd)


else:
    st.warning("Please fill in all fields and enter a question.")
# except Exception as e:
#     st.error(f"An error occurred: {e}")
