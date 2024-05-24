import os
import json
from itertools import islice

import tiktoken
import time
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from pony.orm import db_session, select
from src.data.models import Project, Interview, LLMAnswer, db
from datetime import datetime
from loguru import logger
from tqdm import tqdm

logger.add("logs/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")

load_dotenv()

encoding = tiktoken.get_encoding("cl100k_base")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

questions = {
    1: {
        "llm_temperature": 0.0,
        "input_variables": ["raw_interview"],
        "previous_answers": False,
        "text_template": """
            Пожалуйста, внимательно прочтите предоставленное вам интервью и следуйте приведенным ниже пошаговым инструкциям: <interview>{raw_interview}</interview>
            
            Пошаговые инструкции:
            1. Используйте только информацию, предоставленную вам в интервью, не придумывайте ничего самостоятельно.
            2. Выделите основные разделы или фазы интервью. Например: введение, общие вопросы, основные темы, заключительные замечания.
            3. Для каждого выделенного основного раздела приведите не более пяти цитат из вопросов в этом разделе. Важно, чтобы цитаты были короткими, но описывали этот раздел как можно полнее. Используйте только цитаты из вопросов интервьюера. Если в цитате встречается имя интервьюера или респондента, то удалите это имя.
            4 Верните окончательный ответ в формате json, где ключом будет название основного раздела интервью, а значениями список всех выбранных вами цитат. 
        """
    },
    2: {
        "llm_temperature": 0.0,
        "input_variables": ["raw_interview"],
        "previous_answers": False,
        "text_template": """
            Пожалуйста, внимательно прочтите предоставленное вам интервью и следуйте приведенным ниже пошаговым инструкциям: <interview>{raw_interview}</interview>

            Пошаговые инструкции:
            1. Используйте только информацию, предоставленную вам в интервью, не придумывайте ничего самостоятельно.
            2. Выделите ключевые фразы, словосочетания или предложения, отражающие важные идеи, концепции или опыт. 
            3. Присвоите получившимся выделенным сегментам короткие ярлыки. Используя короткие описательные фразы или слова, которые обобщают основную идею.
            4. Верните окончательный ответ в формате json, где ключом будет короткий ярлык, а значениями будут описания этого кода-ярлыка.
            """
    },
    3: {
        "llm_temperature": 0.0,
        "input_variables": ["raw_interview", "previous_answers"],
        "previous_answers": True,
        "text_template": """
            Пожалуйста, внимательно прочтите предоставленное вам интервью и следуйте приведенным ниже пошаговым инструкциям: <interview>{raw_interview}</interview>

            Пошаговые инструкции:
            1. Используйте только информацию, предоставленную вам в интервью, не придумывайте ничего самостоятельно.
            2. Просмотрите тематические коды <interview_code>{previous_answers}</interview_code> и найдите среди них сходства или взаимосвязи.
            3. Сгруппируйте связанные тематические коды в более широкие категории или темы, которые охватывают основные темы, обсуждавшиеся в интервью.
            4. Определите любые подтемы в рамках каждой основной темы, чтобы обеспечить более детальное понимание тем.
            5. Верните окончательный ответ в формате json, где ключами будут основные темы, а значениями список подтем. 
            """
    },
    4: {
        "llm_temperature": 0.0,
        "input_variables": ["raw_interview"],
        "previous_answers": False,
        "text_template": """
            Пожалуйста, внимательно прочтите предоставленное вам интервью и следуйте приведенным ниже пошаговым инструкциям: <interview>{raw_interview}</interview>

            Пошаговые инструкции:
            1. Используйте только информацию, предоставленную вам в интервью, не придумывайте ничего самостоятельно.
            2. Составьте список всех конкретных проблем, упомянутых респондентами.
            2. Подсчитайте, сколько раз упоминалась каждая проблема. 
            3. Верните окончательный ответ в формате json, где ключами будут проблемы, а значениями количество упоминаний проблем в интервью. 
            """
    },
    5: {
        "llm_temperature": 0.0,
        "input_variables": ["raw_interview", "previous_answers"],
        "previous_answers": True,
        "text_template": """
            Пожалуйста, внимательно прочтите предоставленное вам интервью и следуйте приведенным ниже пошаговым инструкциям: <interview>{raw_interview}</interview>

            Пошаговые инструкции:
            1. Используйте только информацию, предоставленную вам в интервью, не придумывайте ничего самостоятельно.
            2. Просмотрите список проблем <interview_problems>{previous_answers}</interview_problems> и найдите среди них сходства или взаимосвязи.
            3. Сгруппируйте связанные проблемы в более широкие типы проблем, которые охватывают различные упомянутые проблемы в интервью. 
            4. Верните окончательный ответ в формате json, где ключами будут широкие типы проблем, а значениями списки проблем входящих в них.
            """
    },
    6: {
        "llm_temperature": 0.0,
        "input_variables": ["raw_interview", "previous_answers"],
        "previous_answers": True,
        "text_template": """
             Пожалуйста, внимательно прочтите предоставленное вам интервью и категории проблем, которые были выявлены при первичном анализе данного интервью: <interview>{raw_interview}</interview> and <interview_problems>{previous_answers}</interview_problems> 
             
            Пошаговые инструкции:
            1. Используйте только информацию, предоставленную вам в интервью и в выявленных категориях проблем, не придумывайте ничего самостоятельно.
            
            2. Проанализируйте темы и частоту возникновения проблем и их категории. Дайте ответ в форме вложенного json, верхнеуровневым ключом будет – "reflections", вложенными ключами будут категория проблем, а значениями будет список содержащий результаты проведенного анализа.  
            
            3. Проанализируйте, что результаты "reflections" говорят об опыте, взглядах или трудностях респондента. Дайте ответ в форме вложенного json, верхнеуровневым ключом будет – "results", вложенными ключами будут категория опыта, а значениями будет список содержащий результаты проведенного анализа.
            
            4. Обратите внимание на любые неожиданные закономерности, связи или контрасты в данных. Поделитесь этими наблюдениями. Дайте ответ в форме вложенного json, верхнеуровневым ключом будет – "unexpected", вложенными ключами будут категория контрастов, а значениями будет список содержащий результаты проведенного анализа.
            
            5. Разработайте предварительные объяснения или гипотезы о том, почему возникли определенные темы или проблемы и как они могут быть связаны друг с другом или с более широкими контекстуальными факторами. Дайте ответ в форме json, где будет только один ключ – "hypothesis", а значениями будет список содержащий результаты проведенного анализа.
            
            6. Рассмотрите альтернативные объяснения и контрпримеры, чтобы прояснить гипотезы сформированные в разделе "hypothesis". Дайте ответ в форме json, где будет только один ключ – "alternatives", а значениями будет список содержащий результаты проведенного анализа.
            
            7. Укажите области, в которых могут потребоваться дополнительные исследования или анализ для подтверждения ваших идей из раздела "alternatives". Дайте ответ в форме json, где будет только один ключ – "additional", а значениями будет список содержащий результаты проведенного анализа.
            """
    }
}


@db_session
def get_all_interviews_project(project_id: int = None) -> dict[int, str]:
    results = {}
    interviews = select(i for i in Interview if i.project.id == project_id)
    for interview in interviews:
        results[interview.id] = interview.content

    return results


class LLMProcessor:
    def __init__(self, llm, questions, interview, project_id, interview_id):
        self.llm = llm
        self.questions = questions
        self.interview = interview
        self.project_id = project_id
        self.interview_id = interview_id
        self.previous_answers = {}

    @db_session
    def save_llm_answer(self, project_id, interview_id, question, metadata, prompt, response, content):
        LLMAnswer(
            project=project_id,
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
        db.commit()

    def get_response_json(self, response):
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

    def get_prompt(self, question):
        ru_lang = "\nВнимание, это важно! Всегда отправляйте полный текст ответа только на русском языке. Спасибо!"
        prompt = PromptTemplate(template=self.questions[question]["text_template"] + ru_lang,
                                input_variables=self.questions[question]["input_variables"])

        return prompt

    def process_steps(self):
        try:
            for question in tqdm(sorted(self.questions.keys())):
                prompt = self.get_prompt(question)
                chain = prompt | self.llm

                if self.questions[question]["previous_answers"] is True:
                    previous_answers = self.previous_answers[question - 1]
                else:
                    previous_answers = None

                response = chain.invoke({"raw_interview": self.interview, "previous_answers": previous_answers})
                metadata, content = self.get_response_json(response)
                self.previous_answers[question] = content
                self.save_llm_answer(
                    project_id=self.project_id, interview_id=self.interview_id,
                    question=question, metadata=metadata, prompt=prompt, response=response, content=content
                )
                time.sleep(60)
        except Exception as e:
            logger.error(f"{e}")


def main(project_id):
    llm_haiku = ChatAnthropic(
        api_key=ANTHROPIC_API_KEY,
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=0.25
    )

    all_interviews = get_all_interviews_project(project_id)
    sliced_data = islice(all_interviews.items(), 3, None, 1)  # islice(iterable, start, stop[, step])

    for i, (interview_id, interview_data) in enumerate(tqdm(sliced_data)):
        processor = LLMProcessor(
            project_id=project_id,
            interview_id=interview_id,
            questions=questions,
            interview=interview_data,
            llm=llm_haiku)
        processor.process_steps()


if __name__ == "__main__":
    main(project_id=1)
