import os
import json
import sqlite3
import tiktoken
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from pprint import pprint
from langchain_community.document_loaders import DirectoryLoader
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic

# TODO:
#   + Подключение к БД и выбор всех данных по эксперименту
#   - Pipeline всех вопросов к одному интервью. Результат каждого вопроса/ответа сохранять в БД


""" --− START SETUP --− """
logger.add("logs/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")
load_dotenv()
DB = sqlite3.connect("data/project.db")
db_connect = sqlite3.connect("data/project.db")
db_cursor = db_connect.cursor()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

llm_haiku = ChatAnthropic(api_key=ANTHROPIC_API_KEY, model="claude-3-haiku-20240307", max_tokens=4096, temperature=0.0)
llm_haiku_t = ChatAnthropic(api_key=ANTHROPIC_API_KEY, model="claude-3-haiku-20240307", max_tokens=4096,
                            temperature=0.5)

""" --− END SETUP --− """


def get_raw_data(db: sqlite3.Connection = DB, project_id: int = None, project_name: str = None) -> list:
    cursor = db.cursor()
    cursor.execute(f"SELECT raw_data FROM projects WHERE id = {project_id}")
    return [i[0] for i in cursor.fetchall()]


def asks_llm(llm: ChatAnthropic = None,
             raw_data: list[str] = None,
             text_template: str = None,
             input_variables: list[str] = None):
    """

    :param llm:
    :param raw_interview:
    :param text_template:
    :param input_variables:
    :param input_chain:
    :return:
    """

    upd = "\nAttention, this is important! Always send the full text of the response in Russian only. Thanks!"

    prompt = PromptTemplate(input_variables=input_variables, template=text_template + upd)
    chain = prompt | llm

    input_chain = {}
    for var, data in zip(input_variables, raw_data):
        input_chain[var] = data

    answer = chain.invoke(input_chain)
    return answer, prompt


def get_json_from_llm_response(raw_answer):
    metadata = {
        "model": raw_answer.response_metadata["model"],
        "input_tokens": raw_answer.response_metadata["usage"]["input_tokens"],
        "output_tokens": raw_answer.response_metadata["usage"]["output_tokens"]
    }

    content = json.loads(raw_answer.content)

    return metadata, content


def save_llm_response_in_database(cursor, project_id, project_name, project_part, metadata, prompt, answer,
                                  answer_clear):
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute(
        f"INSERT OR IGNORE INTO llm_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            project_id,
            project_name,
            project_part,
            ts,
            metadata["model"],
            metadata["input_tokens"],
            metadata["input_tokens"],
            str(prompt),
            str(answer),
            str(answer_clear)
        )
    )
    db_connect.commit()


def get_answer_1(raw_data: list[str] = None):
    answer = asks_llm(
        llm=llm_haiku, raw_data=raw_data,
        text_template="""
        Пожалуйста, внимательно прочтите предоставленное вам интервью и следуйте приведенным ниже пошаговым инструкциям: <interview>{raw_interview}</interview>

        Пошаговые инструкции:
        1. Используйте только информацию, предоставленную вам в интервью, не придумывайте ничего самостоятельно.
        2. Выделите основные разделы или фазы интервью. Например: введение, общие вопросы, основные темы, заключительные замечания.
        3. Для каждого выделенного основного раздела приведите не более пяти цитат из вопросов в этом разделе. Важно, чтобы цитаты были короткими, но описывали этот раздел как можно полнее. Используйте только цитаты из вопросов интервьюера. Если в цитате встречается имя интервьюера или респондента, то удалите это имя.
        4 Верните окончательный ответ в формате json, где ключом будет название основного раздела интервью, а значениями список всех выбранных вами цитат. 
        """,
        input_variables=["raw_interview"],
    )

    return answer


def main() -> None:
    project_id = 1
    project_name = 'test'
    raw_data = get_raw_data(project_id=project_id, project_name=project_name)

    for part, data in enumerate(raw_data[:1]):
        try:
            answer_1_raw, prompt = get_answer_1(raw_data=[data])
            metadata, content = get_json_from_llm_response(answer_1_raw)
            save_llm_response_in_database(
                cursor=db_cursor,
                project_id=project_id, project_name=project_name, project_part=part + 1,
                metadata=metadata, prompt=prompt, answer=answer_1_raw, answer_clear=content
            )
        except Exception as e:
            logger.error(f"Get answer : {e}")


if __name__ == '__main__':
    main()
