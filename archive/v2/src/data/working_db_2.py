import os
from loguru import logger
from pony.orm import db_session
from src.paths import PATH_TO_DATA, PATH_TO_LOG
from archive.v2.src.data import models as MODELS

logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")


@db_session
def read_db(sql: str = None, params: dict = None):
    data = models.db.select(sql, params)
    return data


@db_session
def save_to_db(table_name: str = None, **kwargs):
    """
    Saving data to an sqlite database.
    :param table_name: table_name
    :param kwargs: data to save: column_name=column_value
    :return:
    """
    class_table_map = {entity._table_: entity for entity in models.db.entities.values()}
    class_ = class_table_map.get(table_name, None)
    try:
        class_(**kwargs)
        models.db.commit()
    except Exception as e:
        logger.error(e)


@db_session
def save_files_to_db(project_name: str = None, file_endswith: str = ".txt", ) -> None:
    folder_path = f"{PATH_TO_DATA}/raw/{project_name}"
    project = models.db.Project.get(name=project_name)

    try:
        for filename in os.listdir(folder_path):
            if filename.endswith(file_endswith):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    save_to_db(table_name="interviews", project=project, content=content)
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    ...
