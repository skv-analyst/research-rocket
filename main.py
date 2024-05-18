import os
from dotenv import load_dotenv
import tiktoken
from langchain_community.document_loaders import DirectoryLoader

# Setup
encoding = tiktoken.get_encoding("cl100k_base")


def load_files(path: str = "data/demo", glob: str = "*.txt") -> list:
    loader = DirectoryLoader(path=path, glob=glob)
    documents = loader.load()

    for num, doc in enumerate(documents):
        print(f"index: {num}, file: {doc.metadata['source'][-15:]}, length: {len(doc.page_content)}, tokens: {len(encoding.encode(doc.page_content))}.")

    return documents

def main():
    documents = load_files()
    # def Init llm
    # def get llm_answer
    pass


if __name__ == '__main__':
    main()
