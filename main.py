
from src.data import working_db_2 as db
from src.llm.prompt_templates import INTERVIEW_QUESTIONS, SUMMARY_QUESTIONS
from src.llm import working_llm_2 as llm2
from src.etl import working_text as etl

def main(project_name: str = None, full_pipeline: bool = False) -> None:
    if full_pipeline:
        db.save_to_db(table_name="projects", name=project_name)
        db.save_files_to_db(project_name=project_name)


    # Обрабатываем каждое интервью проекта
    # llm2.LlmProcessInterview(project_name=project_name, questions=INTERVIEW_QUESTIONS).run()

    # Получаем строку с результатами обработки всех интервью проекта
    all_llm_answer_interviews = etl.PrepareInterviewForSummary(project_name=project_name).run()

    # Запускаем LlmProcessProject

    # Отдельный модуль подготовки данных для pdf и сбора pdf




if __name__ == "__main__":
    name = "test_real_estate_2"
    main(project_name=name, full_pipeline=False)
