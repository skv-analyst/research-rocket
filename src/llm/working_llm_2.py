import os
import json
import time
import re
from dotenv import load_dotenv
from datetime import datetime
from loguru import logger
from tqdm import tqdm
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from src.paths import PATH_TO_LOG
from src.data import working_db_2 as db
from src.llm.prompt_templates import INTERVIEW_QUESTIONS, SUMMARY_QUESTIONS

load_dotenv()
logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")

LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLM_MODEL = "claude-3-haiku-20240307"
LLM_DEFAULT_TEMPERATURE = 0.25


def llm_response_to_json(response):
    metadata = {
        "model": response.response_metadata["model"],
        "input_tokens": response.response_metadata["usage"]["input_tokens"],
        "output_tokens": response.response_metadata["usage"]["output_tokens"]
    }

    try:
        content = re.sub(r'\n', '', response.content)
        content = json.loads(content)
    except Exception as e:
        content = {"ERROR": "Something went wrong and the response was not parsed in json."}
        logger.error(e)

    return metadata, content


class LlmProcessInterview:
    def __init__(self, project_name: str = None, questions: dict = None):
        self.project_name = project_name
        self.questions = questions
        self.project_id = db.read_db(
            "SELECT DISTINCT id FROM projects WHERE name = $name", {"name": project_name}
        )[0]
        self.interviews = db.read_db(
            "SELECT DISTINCT id, content FROM interviews WHERE project = $id", {"id": self.project_id}
        )
        self.previous_answers = {}

    def create_prompt(self, text_template: str = None, input_variables: list = None) -> PromptTemplate:
        ru_lang = "\nВнимание, это важно! Всегда отправляйте полный текст ответа только на русском языке. Спасибо!"
        prompt = PromptTemplate(template=text_template + ru_lang,
                                input_variables=input_variables)

        return prompt

    def run(self):
        interviews = {id_: content for id_, content in self.interviews}

        for interview_id, interview_content in interviews.items():
            try:
                for question, parameters in tqdm(sorted(self.questions.items())):
                    prompt = self.create_prompt(text_template=parameters["text_template"],
                                                input_variables=parameters["input_variables"])
                    if parameters["llm_temperature"] is False:
                        chain = prompt | ChatAnthropic(api_key=LLM_API_KEY,
                                                       model=LLM_MODEL,
                                                       max_tokens=4096,
                                                       temperature=LLM_DEFAULT_TEMPERATURE)
                    else:
                        chain = prompt | ChatAnthropic(api_key=LLM_API_KEY,
                                                       model=LLM_MODEL,
                                                       max_tokens=4096,
                                                       temperature=parameters["llm_temperature"])

                    if parameters["previous_answers"] is True:
                        previous_answers = self.previous_answers[question - 1]
                    else:
                        previous_answers = None

                    response = chain.invoke({"raw_interview": interview_content, "previous_answers": previous_answers})
                    metadata, content = llm_response_to_json(response)
                    self.previous_answers[question] = content

                    db.save_to_db(table_name="llm_answers",
                                  project=self.project_id,
                                  interview=interview_id,
                                  analysis_step=int(question),
                                  created=datetime.now(),
                                  model=str(metadata["model"]),
                                  input_tokens=int(metadata["input_tokens"]),
                                  output_tokens=int(metadata["output_tokens"]),
                                  prompt=str(prompt),
                                  answer_full=str(response),
                                  answer_clear=content
                                  )
                    time.sleep(30)

            except Exception as e:
                logger.error(e)


class LlmProcessProject:
    def __init__(self, project_name: str = None, all_llm_answers_interviews: str = None, questions: dict = None):
        self.project_name = project_name
        self.all_llm_answers_interviews = all_llm_answers_interviews
        self.questions = questions
        self.project_id = db.read_db(
            "SELECT DISTINCT id FROM projects WHERE name = $name", {"name": project_name}
        )[0]
        self.previous_answers = {}

    def create_prompt(self, text_template: str = None, input_variables: list = None):
        ru_lang = "\nВнимание, это важно! Всегда отправляйте полный текст ответа только на русском языке. Спасибо!"

        prompt = PromptTemplate(template=text_template + ru_lang,
                                input_variables=input_variables)

        return prompt

    def run(self):
        for question, parameters in tqdm(sorted(self.questions.items())):
            prompt = self.create_prompt(text_template=parameters["text_template"],
                                        input_variables=parameters["input_variables"])

            if parameters["llm_temperature"] is False:
                chain = prompt | ChatAnthropic(api_key=LLM_API_KEY,
                                               model=LLM_MODEL,
                                               max_tokens=4096,
                                               temperature=LLM_DEFAULT_TEMPERATURE)
            else:
                chain = prompt | ChatAnthropic(api_key=LLM_API_KEY,
                                               model=LLM_MODEL,
                                               max_tokens=4096,
                                               temperature=parameters["llm_temperature"])

            if parameters["previous_answers"] is True:
                previous_answers = self.previous_answers[question - 1]
            else:
                previous_answers = None

            try:
                response = chain.invoke(
                    {"raw_interview": self.all_llm_answers_interviews, "previous_answers": previous_answers})
                metadata, content = llm_response_to_json(response)
                self.previous_answers[question] = content

                db.save_to_db(table_name="llm_answers_merged",
                              project=self.project_id,
                              created=datetime.now(),
                              model=str(metadata["model"]),
                              input_tokens=int(metadata["input_tokens"]),
                              output_tokens=int(metadata["output_tokens"]),
                              merged_interview=str(self.all_llm_answers_interviews),
                              prompt=str(prompt),
                              answer_full=str(response),
                              answer_clear=content,
                              answer_content=str(response.content)
                              )

                time.sleep(30)

            except Exception as e:
                logger.error(e)


if __name__ == "__main__":
    ...
