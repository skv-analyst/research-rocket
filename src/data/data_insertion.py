import os
from pony.orm import db_session
from datetime import datetime
from src.data.models import Project, Interview, db
from src.paths import PATH_TO_DATA


@db_session
def add_interviews_from_folder(project_name, folder_path):
    with db_session:
        # Adding a project or finding an existing one
        project = Project.get(name=project_name)
        if not project:
            project = Project(name=project_name)

        # We read everything .txt files from the specified folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                    # Extract the date from the file name (the format is assumed YYYY-MM-DD.txt )
                    # date_str = filename.split('.')[0]
                    # interview_date = datetime.strptime(date_str, '%Y-%m-%d')

                    # Adding interviews to the database
                    Interview(project=project, content=content)

        # Saving changes to the database
        db.commit()


if __name__ == '__main__':
    project_name = 'test'
    folder_path = f'{PATH_TO_DATA}/raw/test_interviews'
    add_interviews_from_folder(project_name, folder_path)

