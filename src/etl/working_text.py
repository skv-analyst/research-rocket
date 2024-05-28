import json
from loguru import logger
from src.paths import PATH_TO_LOG
from src.data import working_db_2 as db


def fetch_latest_llm_answer_from_interview(project_id) -> dict:
    data = db.read_db("""SELECT 
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

    return data


def transform_sql_str_to_json(data) -> dict:
    result_dict = {}
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


class PrepareInterviewForSummary:
    def __init__(self, project_name: str = None):
        self.project_name = project_name
        self.project_id = db.read_db(
            "SELECT DISTINCT id FROM projects WHERE name = $name", {"name": project_name}
        )[0]
        self.latest_llm_answers = fetch_latest_llm_answer_from_interview(project_id=self.project_id)
        self.answers = transform_sql_str_to_json(self.latest_llm_answers)
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
        string = f"ИНТЕРВЬЮ №{interview_num}\n"
        for question, answer in interview_answers.items():
            if question in self.replace.keys():
                string += f"\nШаг:{question}. {self.replace[question].upper()}\n"
                try:
                    for a_key, a_val in answer.items():
                        if a_key in self.replace.keys():
                            string += f"{self.replace[a_key]}: {a_val}\n\n"
                        elif a_key not in self.replace.keys():
                            string += f"{a_key}: {a_val}\n"
                except:
                    string += f"\n"

        return string

    def run(self) -> str:
        results = ""
        for key, value in self.answers.items():
            row = self.answer_to_string(interview_num=key, interview_answers=value)
            results += row
            results += "---" * 50 + "\n"
        return results


if __name__ == "__main__":
    PrepareInterviewForSummary(project_name="test_real_estate_2")
