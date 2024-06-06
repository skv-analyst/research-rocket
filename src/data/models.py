from datetime import datetime
from pony.orm import Database, PrimaryKey, Required, Set, Optional, Json
from src.paths import PATH_TO_DATA

# Creating a database object
db = Database()


class Project(db.Entity):
    _table_ = "projects"
    project_id = PrimaryKey(int, auto=True)
    project_name = Required(str)
    interviews = Set('Interview', reverse='project')
    llm_answers = Set('LLMAnswer', reverse='project')


class Interview(db.Entity):
    _table_ = "interviews"
    interview_id = PrimaryKey(int, auto=True)
    project = Required(Project, reverse='interviews')
    date = Optional(datetime)
    content = Required(str)
    llm_answers = Set('LLMAnswer', reverse='interview')


class LLMAnswer(db.Entity):
    _table_ = "llm_answers"
    id = PrimaryKey(int, auto=True)
    project = Required(Project, reverse='llm_answers')
    interview = Optional(Interview, reverse='llm_answers')
    analysis_type = Required(str)
    analysis_step = Optional(int)
    created = Required(datetime, default=datetime.now)
    model = Required(str)
    input_tokens = Required(int)
    output_tokens = Required(int)
    prompt = Required(str)
    answer_full = Optional(str)
    answer_content = Optional(str)
    answer_content_clear = Optional(str)
    # prepared_interviews = Optional(str)


# Connecting to the SQLite database
db.bind('sqlite', f'{PATH_TO_DATA}/db_2.sqlite', create_db=True)

# Generating tables in the database
db.generate_mapping(create_tables=True)
