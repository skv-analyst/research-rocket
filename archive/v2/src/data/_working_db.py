import os
import json
from datetime import datetime
from pony.orm import db_session, select
from archive.v2.src.data.models import Project, Interview, LLMAnswer, LLMAnswerMerged, db


@db_session
def sav_interview_files_to_database(project_name: str = None, folder_path: str = None,
                                    file_endswith: str = ".txt") -> None:
    """
    Saves interviews from the project folder to the database.
    :param project_name:
    :param folder_path:
    :param file_endswith:
    :return:
    """
    with db_session:
        project = Project.get(name=project_name)
        if not project:
            project = Project(name=project_name)
        # We read everything .txt files from the specified folder
        cnt_files = 0
        for filename in os.listdir(folder_path):
            if filename.endswith(file_endswith):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    # Adding interviews to the database
                    Interview(project=project, content=content)
                    cnt_files += 1

        # Saving changes to the database
        db.commit()
        return cnt_files


@db_session
def fetch_project_id(project_name: str = None) -> int:
    """
    Get the project_id by its name.
    :param project_name:
    :return:
    """
    data = db.select("""SELECT DISTINCT id FROM projects WHERE name = $tmp""", {"tmp": project_name})
    return data[0]


@db_session
def fetch_all_interviews_project(project_id: int = None) -> dict[int, str]:
    """
    Get all project interviews by project_id.
    :param project_id:
    :return:
    """
    results = {}
    interviews = select(i for i in Interview if i.project.id == project_id)
    for interview in interviews:
        results[interview.id] = interview.content

    return results


@db_session
def save_processed_interview(project_id, interview_id, question, metadata, prompt, response, content):
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


@db_session
def fetch_latest_llm_answer_from_interview(project_id) -> dict:
    data = db.select("""SELECT 
                            interview, analysis_step, answer_clear
                        FROM (SELECT project,
                                     interview,
                                     analysis_step,
                                     created,
                                     row_number() OVER (PARTITION BY project, interview, analysis_step ORDER BY interview, analysis_step, created DESC) AS latest,
                                     answer_clear
                              FROM llm_answers
                              WHERE project == $id
                              ORDER BY interview, analysis_step, created DESC)
                        WHERE latest == 1""",
                     {"id": project_id})

    result_dict = {}
    # for outer_key, inner_key, value in data:
    #     if outer_key not in result_dict:
    #         result_dict[outer_key] = {}
    #     result_dict[outer_key][inner_key] = value

    for outer_key, inner_key, value in data:
        # Распаковываем JSON строку в словарь
        try:
            value_dict = json.loads(value)
        except json.JSONDecodeError:
            value_dict = {"error": "Invalid JSON"}

        if outer_key not in result_dict:
            result_dict[outer_key] = {}

        result_dict[outer_key][inner_key] = value_dict
    return result_dict


@db_session
def save_processed_results_interview(project_id, metadata, merged_interview, prompt, response, content):
    LLMAnswerMerged(
        project=project_id,
        created=datetime.now(),
        model=str(metadata["model"]),
        input_tokens=int(metadata["input_tokens"]),
        output_tokens=int(metadata["output_tokens"]),
        merged_interview=str(merged_interview),
        prompt=str(prompt),
        answer_full=str(response),
        answer_clear=content
    )
    db.commit()


class PackInterviewResults:
    def __init__(self, project_id):
        self.project_id = project_id
        self.llm_answers = fetch_latest_llm_answer_from_interview(project_id)
        self.replace = {
            1: "Основные разделы",
            2: "Кодирование интервью",
            3: "Категории кодов в интервью",
            4: "Проблемы обозначенные респондентом в интервью",
            5: "Сгруппированные проблемы",
            6: "Итоговые выводы по интервью",
            "reflections": "Категории проблем",
            "results": "Трудности Респондентов",
            "unexpected": "Неожиданности в данных",
            "hypothesis": "Гипотезы возникновения проблем",
            "alternatives": "Альтернативные гипотезы возникновения проблем",
            "additional": "Рекомендованные дополниетельные исследования"
        }

    def answer_to_string(self, interview_num, interview_answers):
        str = f"ИНТЕРВЬЮ №{interview_num}\n"
        for question, answer in interview_answers.items():
            if question in self.replace.keys():
                str += f"\nШаг:{question}. {self.replace[question].upper()}\n"
                try:
                    for a_key, a_val in answer.items():
                        if a_key in self.replace.keys():
                            str += f"{self.replace[a_key]}: {a_val}\n\n"
                        elif a_key not in self.replace.keys():
                            str += f"{a_key}: {a_val}\n"
                except:
                    str += f"\n"

        return str

    def get_results(self) -> str:
        results = ""
        for key, value in self.llm_answers.items():
            row = self.answer_to_string(interview_num=key, interview_answers=value)
            results += row
            results += "---" * 50 + "\n"
        return results


@db_session
def fetch_latest_merged_interviews(project_id: int = None):
    data = db.select("""SELECT merged_interview
                        FROM (SELECT project,
                                     created,
                                     row_number() OVER (PARTITION BY project ORDER BY created DESC) AS latest,
                                     merged_interview, answer_clear
                              FROM llm_answers_merged
                              WHERE project == $id
                              ORDER BY created DESC)
                        WHERE latest == 1""",
                     {"id": project_id})

    return data


@db_session
def fetch_latest_summarize_interviews(project_id: int = None):
    data = db.select("""SELECT answer_clear
                        FROM (SELECT project,
                                     created,
                                     row_number() OVER (PARTITION BY project ORDER BY created DESC) AS latest,
                                     answer_clear
                              FROM llm_answers_merged
                              WHERE project == $id
                              ORDER BY created DESC)
                        WHERE latest == 1""",
                     {"id": project_id})

    return data


class CreateSTR2PDF:
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_id = fetch_project_id(self.project_name)
        self.latest_merged_interviews = fetch_latest_merged_interviews(self.project_id)
        self.latest_summarize_interviews = fetch_latest_summarize_interviews(self.project_id)
        self.replace = {
            "step_01": "Основные разделы",
            "step_02": "Кодирование интервью",
            "step_03": "Категории кодов в интервью",
            "step_04": "Проблемы обозначенные респондентом в интервью",
            "step_05": "Сгруппированные проблемы",
            "step_06": "Итоговые выводы по интервью"
        }

    def create_summarize_output(self):
        main_string = ""
        summarize_dict = json.loads(self.latest_summarize_interviews[0])
        for key, val in summarize_dict.items():
            if key in self.replace.keys():
                main_string += f"{self.replace[key].upper()}: {val}\n\n"

        return main_string

    def run(self):
        return self.latest_merged_interviews, self.create_summarize_output()

if __name__ == "__main__":
    # print(fetch_project_id(project_name="test_real_estate_2"))
    # print(fetch_all_interviews_project(project_id=1))
    # fetch_latest_llm_answer_from_interview(project_id=2)
    print(PackInterviewResults(project_id=2).get_results())

