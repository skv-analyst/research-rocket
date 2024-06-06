from src.data import working_db as db
from src.llm.prompt_templates import INTERVIEW_QUESTIONS_v4
from src.llm import working_llm as llm3


def main(project_name: str = None, full_pipeline: bool = False) -> None:
    if full_pipeline:
        db.save_to_db(table_name="projects", name=project_name)
        db.save_files_to_db(project_name=project_name)

    project_id = db.read_db(
        "SELECT DISTINCT id FROM projects WHERE name = $name", {"name": project_name}
    )[0]

    # Обрабатываем каждое интервью проекта
    llm3.LlmProcessInterview(project_id=project_id, questions=INTERVIEW_QUESTIONS_v4).run()

    # llm2.LlmProcessInterview(project_name=project_name, questions=INTERVIEW_QUESTIONS_v3).run()

    # Собираем результаты предыдущего этапа в одну строку для промпта
    # all_llm_answer_interviews = etl.PrepareInterviewForSummary(project_name=project_name).run()

    # Обрабатываем собранные итоги всех интервью проекта
    # llm2.LlmProcessProject(project_name=project_name, all_llm_answers_interviews=all_llm_answer_interviews,
    #                        questions=SUMMARY_QUESTIONS_v3).run()

    # Сохраняем данные в json и pdf
    # pdf.CreatePdf(project_name=project_name).run()


if __name__ == "__main__":
    name = "test_v3_real_estate_01"
    main(project_name=name, full_pipeline=False)


