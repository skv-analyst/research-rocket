import os
import json
import time
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from src.data.working_db import fetch_project_id, fetch_all_interviews_project, save_processed_interview, \
    fetch_latest_llm_answer_from_interview, PackInterviewResults, save_processed_results_interview
from src.paths import PATH_TO_LOG
from src.llm.prompt_templates import INTERVIEW_QUESTIONS, SUMMARY_QUESTIONS

load_dotenv()
logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")

LLM = ChatAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"),
                    model="claude-3-haiku-20240307",
                    max_tokens=4096, temperature=0.25)


class ProcessAllInterviewsProject:
    def __init__(self, project_name: str = None, questions: dict = None, llm: ChatAnthropic = LLM):
        self.project_name = project_name
        self.questions = questions
        self.llm = llm
        self.project_id = fetch_project_id(self.project_name)
        self.interviews = fetch_all_interviews_project(self.project_id)
        self.previous_answers = {}

    def llm_response_to_json(self, response):
        metadata = {
            "model": response.response_metadata["model"],
            "input_tokens": response.response_metadata["usage"]["input_tokens"],
            "output_tokens": response.response_metadata["usage"]["output_tokens"]
        }

        try:
            content = json.loads(response.content)
        except Exception as e:
            content = {"ERROR": "Something went wrong and the response was not parsed in json."}
            logger.error(f"{e}")

        return metadata, content

    def create_prompt(self, question):
        ru_lang = "\nВнимание, это важно! Всегда отправляйте полный текст ответа только на русском языке. Спасибо!"
        prompt = PromptTemplate(template=self.questions[question]["text_template"] + ru_lang,
                                input_variables=self.questions[question]["input_variables"])

        return prompt

    def run(self):
        for interview_id, interview in tqdm(self.interviews.items(), desc="Processing the interview"):
            try:
                for question in sorted(self.questions.keys()):
                    prompt = self.create_prompt(question)
                    chain = prompt | self.llm

                    if self.questions[question]["previous_answers"] is True:
                        previous_answers = self.previous_answers[question - 1]
                    else:
                        previous_answers = None

                    response = chain.invoke({"raw_interview": interview, "previous_answers": previous_answers})
                    metadata, content = self.llm_response_to_json(response)
                    self.previous_answers[question] = content
                    save_processed_interview(
                        project_id=self.project_id, interview_id=interview_id,
                        question=question, metadata=metadata, prompt=prompt, response=response, content=content
                    )
                    time.sleep(60)

            except Exception as e:
                logger.error(e)


class ProcessResultsAllInterviews:
    def __init__(self, project_name: str = None, questions: dict = None, llm: ChatAnthropic = LLM):
        self.project_name = project_name
        self.questions = questions
        self.llm = llm
        self.project_id = fetch_project_id(self.project_name)
        self.str_for_llm = PackInterviewResults(self.project_id).get_results()

    def llm_response_to_json(self, response):
        metadata = {
            "model": response.response_metadata["model"],
            "input_tokens": response.response_metadata["usage"]["input_tokens"],
            "output_tokens": response.response_metadata["usage"]["output_tokens"]
        }

        try:
            content = json.loads(response.content)
        except Exception as e:
            content = {"ERROR": "Something went wrong and the response was not parsed in json."}
            logger.error(f"{e}")

        return metadata, content

    def create_prompt(self):
        ru_lang = "\nВнимание, это важно! Всегда отправляйте полный текст ответа только на русском языке. Спасибо!"

        prompt = PromptTemplate(template=self.questions[1]["text_template"] + ru_lang,
                                input_variables=self.questions[1]["input_variables"])

        return prompt

    def run(self):
        try:
            prompt = self.create_prompt()
            chain = prompt | self.llm
            response = chain.invoke({"raw_interview": self.str_for_llm})
            metadata, content = self.llm_response_to_json(response)

            save_processed_results_interview(
                project_id=self.project_id, metadata=metadata, merged_interview=self.str_for_llm,
                prompt=prompt, response=response, content=content
            )

        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    # ProcessAllInterviewsProject()
    ProcessResultsAllInterviews(project_name="real_estate_test", questions=SUMMARY_QUESTIONS).run()

