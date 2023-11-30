# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iGfjr_6y9lrnbVVJP5DX3oGICOOHYuBK
"""

import streamlit as st
from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import pipeline
from huggingface_hub import notebook_login
import os
import sys
import torch
import transformers




def conversational_ai():



    # Retrieve the Hugging Face API token from the environment variable
    # huggingface_token = os.environ.get("HUGGINGFACE_TOKEN", None)
    huggingface_token = st.secrets["HUGGINGFACE_TOKEN"]


    if huggingface_token is None:
        st.warning("Hugging Face API token not found.")
    else:
    # Your code that uses the Hugging Face API token goes here
        st.success("Hugging Face API token found.")
    
    # Load the Documents and Extract Text From Them

     
    docs_folder = "docs"  # Your folder name

    # Get the absolute path to the "docs" folder
    docs_path = os.path.join(os.getcwd(), docs_folder)

    document = []

    for file in os.listdir(docs_path):
        file_path = os.path.join(docs_path, file)

        if file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            document.extend(loader.load())
        elif file.endswith('.docx') or file.endswith('.doc'):
            loader = Docx2txtLoader(file_path)
            document.extend(loader.load())
        elif file.endswith('.txt'):
            loader = TextLoader(file_path)
            document.extend(loader.load())


    # Split the Document into Chunks

    document_splitter = CharacterTextSplitter(separator='\n', chunk_size=500, chunk_overlap=100)
    document_chunks = document_splitter.split_documents(document)

    # Download the Embeddings from Hugging Face

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

    # Setting Up Chroma as our Vector Database

    vectordb = Chroma.from_documents(document_chunks, embedding=embeddings, persist_directory='./data')

    vectordb.persist()


    #  Download the Llama 2 7B Chat Model
    # Load tokenzier and model with authentication
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf", use_auth_token=True)
    model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf", device_map='auto', torch_dtype=torch.float16, use_auth_token=True)


    # Creating a Hugging Face Pipeline

    pipe = pipeline("text-generation",
                   model=model,
                   tokenizer=tokenizer,
                   torch_dtype=torch.bfloat16,
                   device_map='auto',
                   max_new_tokens=512,
                   min_new_tokens=-1,
                   top_k=30)

    llm = HuggingFacePipeline(pipeline=pipe, model_kwargs={'temperature': 0})

    # Creating a memory object to track inputs/outputs

    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

    # Creating a Conversation Retrieval QA Chain

    pdf_qa = ConversationalRetrievalChain.from_llm(llm=llm,
                                                  retriever=vectordb.as_retriever(search_kwargs={'k': 6}),
                                                  verbose=False, memory=memory)

    # Streamlit UI for User Interaction
    st.subheader("Ask a question:")
    query = st.text_input("Enter your query here:")

    if st.button("Submit"):
        if query == "exit" or query == "quit" or query == "q" or query == "f":
            st.info("Exiting...")
            sys.exit()

        if query == "":
            st.warning("Please enter a query.")

        result = pdf_qa({"question": query})
        st.info("Answer: " + result["answer"])


if __name__ == "__main__":
    conversational_ai()
