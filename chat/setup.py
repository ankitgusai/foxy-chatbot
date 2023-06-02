import openai
import os
import requests
import numpy as np
import pandas as pd
from typing import Iterator
import tiktoken
import textract
from numpy import array, average
from redis import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import (
    TextField,
    VectorField,
    NumericField
)
from redis.commands.search.indexDefinition import (
    IndexDefinition,
    IndexType
)

from database import (get_redis_connection, get_redis_results) 


# Set our default models and chunking size
from config import COMPLETIONS_MODEL, EMBEDDINGS_MODEL, CHAT_MODEL, TEXT_EMBEDDING_CHUNK_SIZE, VECTOR_FIELD_NAME

from transformers import handle_file_string

# Ignore unclosed SSL socket warnings - optional in case you get these errors
import warnings

warnings.filterwarnings(action="ignore", message="unclosed", category=ImportWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning) 

def setup_and_ingest():
    VECTOR_DIM = 1536 #len(data['title_vector'][0]) # length of the vectors
    PREFIX = "sportsdoc"                            # prefix for the document keys
    DISTANCE_METRIC = "COSINE"                # distance metric for the vectors (ex. COSINE, IP, L2)

    INDEX_NAME = "f1-index"           
    VECTOR_FIELD_NAME = 'content_vector'

    filename = TextField("filename")
    text_chunk = TextField("text_chunk")
    file_chunk_index = NumericField("file_chunk_index")
    
    text_embedding = VectorField(VECTOR_FIELD_NAME,
        "HNSW", {
            "TYPE": "FLOAT32",
            "DIM": VECTOR_DIM,
            "DISTANCE_METRIC": DISTANCE_METRIC
        }
    )
    
    fields = [filename,text_chunk,file_chunk_index,text_embedding]

    redis_client = get_redis_connection()
    #redis_client.ping()
    try:
        redis_client.ft(INDEX_NAME).info()
        print("Index already exists")
    except Exception as e:
        print(e)
        print('Not there yet. Creating')
        redis_client.ft(INDEX_NAME).create_index(
            fields = fields,
            definition = IndexDefinition(prefix=[PREFIX], index_type=IndexType.HASH)
        )


    tokenizer = tiktoken.get_encoding("cl100k_base")
    data_dir = os.path.join(os.curdir,'data')
    pdf_files = sorted([x for x in os.listdir(data_dir) if 'DS_Store' not in x])
    
    for pdf_file in pdf_files:
    
        pdf_path = os.path.join(data_dir,pdf_file)
        print(pdf_path)
    
        # Extract the raw text from each PDF using textract
        text = textract.process(pdf_path, method='pdfminer')
    
        # Chunk each document, embed the contents and load to Redis
        handle_file_string((pdf_file,text.decode("utf-8")),tokenizer,redis_client,VECTOR_FIELD_NAME,INDEX_NAME)
    
    info = redis_client.ft(INDEX_NAME).info()
    print("Docs inserted: {}".format(info['num_docs']))