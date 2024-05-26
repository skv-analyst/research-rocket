import os
import sqlite3
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader


def load_raw_files_to_database(source_data_path, source_file_format: str = None, project_metadata: dict = None) -> None:
    loader = DirectoryLoader(path=source_data_path, glob=source_file_format)
    documents = loader.load()
    db_connect = sqlite3.connect("data/project.db")
    db_cursor = db_connect.cursor()

    for num, doc in enumerate(documents):
        db_cursor.execute(
            f"INSERT OR IGNORE INTO projects VALUES (?, ?, ?, ?, ?, ?)",
            (
                project_metadata["id"],
                project_metadata["name"],
                project_metadata["description"],
                num + 1,
                len(doc.page_content),
                doc.page_content
            )
        )
        db_connect.commit()
    db_connect.close()
    print("Save")


if __name__ == "__main__":
    source_data_path = "data/demo/"
    source_file_format = "*.txt"
    project_metadata = {"id": 1, "name": "test", "description": "test"}

    load_raw_files_to_database()
