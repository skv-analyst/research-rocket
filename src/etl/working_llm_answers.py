import re
from loguru import logger
from src.paths import PATH_TO_LOG
from src.data import working_db as db

logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")

SQL_FOR_LATEST_INTERVIEWS = """SELECT interview, group_concat(answer_content, CHAR(10))
            FROM (
                SELECT
                    project, interview, analysis_step, created, answer_content,
                    row_number() OVER (PARTITION BY project, interview, analysis_step ORDER BY interview, analysis_step, created DESC) AS latest
                    FROM llm_answers
                WHERE analysis_type == 'interview' AND project == $id)
            WHERE latest == 1
            GROUP BY interview"""

SQL_FOR_LATEST_SUMMARY = """SELECT answer_content
            FROM (
                SELECT project,
                   interview,
                   analysis_step,
                   created,
                   answer_content,
                   row_number() OVER (PARTITION BY project, interview, analysis_step ORDER BY interview, analysis_step, created DESC) AS latest
            FROM llm_answers
            WHERE analysis_type == 'project' AND project == $id)
            WHERE latest == 1"""


def fetch_latest_llm_answer_from_interview(sql: str, project_id: int) -> list[str]:
    data = db.read_db(sql=sql, params={"id": project_id})

    return data


def process_text(text):
    # Remove the initial "-" and add a period at the end of each sentence
    sentences = [sentence.strip('- ').strip() + '.' for sentence in text.split('\n') if sentence.strip()]
    return ' '.join(sentences)


class PrepareInterviewForSummary:
    def __init__(self, project_id: int = None) -> None:
        self.project_id = project_id
        self.sql = SQL_FOR_LATEST_INTERVIEWS
        self.latest_llm_answers = fetch_latest_llm_answer_from_interview(sql=self.sql, project_id=self.project_id)
        self.replace = {
            "keywords": "Ключевые фразы интервью:",
            "codes": "Кодирование интервью:",
            "code_connections": "Взаимосвязи кодов:",
            "code_groups": "Группировка кодов:",
            "problems": "Проблемы обозначенные в интервью:",
            "problem_connections": "Взаимосвязи обозначенных проблем:",
            "problem_groups": "Группировка обозначенных проблем:",
            "reflections": "Проблемы и частота их появления:",
            "results": "Анализ проблем:",
            "unexpected": "Неожиданные закономерности в ответах:",
            "hypothesis": "Гипотезы возникновения проблем:",
            "alternatives": "Альтернативные объяснения проблем:",
            "additionals": "Дополнительные исследования:"
        }

    def run(self):
        tags = ("keywords|codes|code_connections|code_groups|problems|problem_connections|problem_groups|"
                "reflections|results|unexpected|hypothesis|alternatives|additionals")
        pattern = re.compile(fr"<({tags})>\s*(.*?)\s*</\1>", re.DOTALL)

        results = ""
        for index, interview in enumerate(self.latest_llm_answers):
            matches = pattern.findall(interview[1])

            results += f"\nИНТЕРВЬЮ № {index + 1}"
            for tag, content in matches:
                processed_content = process_text(content)
                if tag in ("keywords", "codes"):
                    results += f"\n{self.replace[tag]}\n{processed_content}\n"
                elif tag in ("code_connections", "code_groups"):
                    results += f"\n{self.replace[tag]}\n{processed_content}\n"
                elif tag in ("problems"):
                    results += f"\n{self.replace[tag]}\n{processed_content}\n"
                elif tag in ("problem_connections", "problem_groups"):
                    results += f"\n{self.replace[tag]}\n{processed_content}\n"
                elif tag in ("reflections", "results", "unexpected", "hypothesis", "alternatives", "additionals"):
                    results += f"\n{self.replace[tag]}\n{processed_content}\n"

        return results


class UnpackingSummary:
    def __init__(self, project_id: int = None, project_name: str = None) -> None:
        self.project_id = project_id
        self.project_name = project_name
        self.sql = SQL_FOR_LATEST_SUMMARY
        self.latest_llm_answers = fetch_latest_llm_answer_from_interview(sql=self.sql, project_id=self.project_id)
        self.replace = {
            "keywords": "Ключевые фразы интервью:",
            "codes": "Кодирование интервью:",
            "code_connections": "Взаимосвязи кодов:",
            "code_groups": "Группировка кодов:",
            "problems": "Проблемы обозначенные в интервью:",
            "problem_connections": "Взаимосвязи обозначенных проблем:",
            "problem_groups": "Группировка обозначенных проблем:",
            "reflections": "Проблемы и частота их появления:",
            "results": "Анализ проблем:",
            "unexpected": "Неожиданные закономерности в ответах:",
            "hypothesis": "Гипотезы возникновения проблем:",
            "alternatives": "Альтернативные объяснения проблем:",
            "additionals": "Дополнительные исследования:"
        }

    def run(self):
        tags = ("keywords|codes|code_connections|code_groups|problems|problem_connections|problem_groups|"
                "reflections|results|unexpected|hypothesis|alternatives|additionals")
        pattern = re.compile(fr"<({tags})>\s*(.*?)\s*</\1>", re.DOTALL)

        # results = ""
        # for index, interview in enumerate(self.latest_llm_answers):
        matches = pattern.findall(self.latest_llm_answers[0])

        results = f"ИТОГОВЫЕ РЕЗУЛЬТАТЫ ПО ПРОЕКТУ {self.project_name}"
        for tag, content in matches:
            processed_content = process_text(content)
            if tag in ("keywords", "codes"):
                results += f"\n{self.replace[tag]}\n{processed_content}\n"
            elif tag in ("code_connections", "code_groups"):
                results += f"\n{self.replace[tag]}\n{processed_content}\n"
            elif tag in ("problems"):
                results += f"\n{self.replace[tag]}\n{processed_content}\n"
            elif tag in ("problem_connections", "problem_groups"):
                results += f"\n{self.replace[tag]}\n{processed_content}\n"
            elif tag in ("reflections", "results", "unexpected", "hypothesis", "alternatives", "additionals"):
                results += f"\n{self.replace[tag]}\n{processed_content}\n"

        return results


if __name__ == "__main__":
    ...
