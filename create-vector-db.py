# Description: This script creates a vector database from a list of documents.
# input: A list of directories containing processed markdown document.



import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

import argparse
# check if the environment variable is set 'AZURE_OPENAI_API_KEY' and 'AZURE_OPENAI_ENDPOINT'
if not os.environ.get('AZURE_OPENAI_API_KEY'):
    raise ValueError("Please set the environment variable 'AZURE_OPENAI_API_KEY' with your Azure OpenAI API key")

if not os.environ.get('AZURE_OPENAI_ENDPOINT'):
    raise ValueError("Please set the environment variable 'AZURE_OPENAI_ENDPOINT' with your Azure OpenAI endpoint")

def add_text_if_not_exists(text, metadata, db):
  docs = db.similarity_search(text, k=1)
  if docs[0].page_content == text:
    print("Text already exists in the database, first 50 characters:", text[:50].replace('\n', '\\n'))
    return False
  db.add_texts([text], [metadata])
  print(f"Text added to the database, first 50 characters:", text[:50].replace('\n', '\\n'))
  return True

def add_docs_if_not_exists(docs, db):
  for doc in docs:
    add_text_if_not_exists(doc.page_content, doc.metadata, db)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process specified files and save them to an output directory.')
    
    # Add the output directory
    parser.add_argument('-o', '--output_dir', type=str, required=True,
                        help='Output directory path')
    
    # Add the list of input files, separated by commas
    parser.add_argument('-f', '--files', type=str, required=True,
                        help='Comma-separated list of file paths to process')
    
    # Parse the command-line arguments
    args = parser.parse_args()

    if args.output_dir is None:
      print("Error: Output directory not specified")
      return
    

    output_dir = args.output_dir
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="AA-text-embedding-3-large",
        openai_api_version="2024-02-01",
    )

    # if output dir exists, try to load the database
    db = None
    if os.path.exists(output_dir):
      db = Chroma(persist_directory=output_dir, embedding_function=embeddings)  # Load from storage
      print("Database loaded successfully")

    # Parse the command-line arguments
    args = parser.parse_args()
    # Split the comma-separated file list into a list of file paths
    file_list = args.files.split(',')
    for file in file_list:
      if not os.path.exists(file):
          print(f"Error: File '{file}' does not exist.")
          return
      
      loader = TextLoader(file)
      docs = loader.load()
      text_splitter = RecursiveCharacterTextSplitter(separators=["\n#\s*\w+"], is_separator_regex=True, chunk_size=4000, chunk_overlap=200)
      splits = text_splitter.split_documents(docs)
      print(f"File: {file}: Split {len(docs)} documents into {len(splits)} chunks")
      if db is None:
        db = Chroma.from_documents(splits, embeddings, persist_directory=output_dir)
      else:
        add_docs_if_not_exists(splits, db)

    print("Database created successfully")


if __name__ == "__main__":
    main()