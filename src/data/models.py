from datetime import datetime
from pony.orm import Database, PrimaryKey, Required, Set, Optional, Json
from src.paths import PATH_TO_DATA

# Creating a database object
db = Database()


class Project(db.Entity):
    _table_ = "projects"
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    interviews = Set('Interview')                       # One project can have many interviews
    llm_answers = Set('LLMAnswer')                      # One project can have many llm_answer
    llm_answers_merged = Set('LLMAnswerMerged')         # One project can have many llm_answers_merged


class Interview(db.Entity):
    _table_ = "interviews"
    id = PrimaryKey(int, auto=True)
    project = Required(Project)                         # Each interview is related to one project
    date = Optional(datetime)                           # Date of the interview (optional)
    content = Required(str)                             # Interview Content
    llm_answers = Set('LLMAnswer')                      # One interview can have many answers


class LLMAnswer(db.Entity):
    _table_ = "llm_answers"
    id = PrimaryKey(int, auto=True)
    project = Required(Project)                         # Each answer is associated with one project
    interview = Required(Interview)                     # Each answer is associated with one interview
    analysis_step = Required(int)                       # The interview analysis step
    created = Required(datetime, default=datetime.now)  # Date and time the response was created
    model = Required(str)                               # Name of the LLM model
    input_tokens = Required(int)                        # Number of input tokens
    output_tokens = Required(int)                       # Number of output tokens
    prompt = Required(str)                              # Request text
    answer_full = Required(str)                         # Full text of the response llm
    answer_clear = Required(Json)                       # Cleared and short response text


class LLMAnswerMerged(db.Entity):
    _table_ = "llm_answers_merged"
    id = PrimaryKey(int, auto=True)
    project = Required(Project)                         # Each final_results is associated with one project
    created = Required(datetime, default=datetime.now)  # Date and time the response was created
    model = Required(str)                               # Name of the LLM model
    input_tokens = Required(int)                        # Number of input tokens
    output_tokens = Required(int)                       # Number of output tokens
    merged_interview = Required(Json)                   # The results of all interviews of the project
    prompt = Required(str)                              # Request text
    answer_full = Required(str)                         # Full text of the response llm
    answer_clear = Optional(Json)                       # Cleared response text
    answer_content = Required(str)


# Connecting to the SQLite database
db.bind('sqlite', f'{PATH_TO_DATA}/db.sqlite', create_db=True)

# Generating tables in the database
db.generate_mapping(create_tables=True)
