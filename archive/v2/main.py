from src.data import working_db as db
from src.llm.prompt_templates import INTERVIEW_QUESTIONS_v3, SUMMARY_QUESTIONS_v3
from src.llm import working_llm_2 as llm2
from src.etl import working_text as etl
from src.output import working_pdf as pdf


def main(project_name: str = None, full_pipeline: bool = False) -> None:
    if full_pipeline:
        db.save_to_db(table_name="projects", name=project_name)
        db.save_files_to_db(project_name=project_name)

    # Обрабатываем каждое интервью проекта
    # llm2.LlmProcessInterview(project_name=project_name, questions=INTERVIEW_QUESTIONS_v3).run()

    # Собираем результаты предыдущего этапа в одну строку для промпта
    # all_llm_answer_interviews = etl.PrepareInterviewForSummary(project_name=project_name).run()

    # Обрабатываем собранные итоги всех интервью проекта
    # llm2.LlmProcessProject(project_name=project_name, all_llm_answers_interviews=all_llm_answer_interviews,
    #                        questions=SUMMARY_QUESTIONS_v3).run()

    # Сохраняем данные в json и pdf
    # pdf.CreatePdf(project_name=project_name).run()


if __name__ == "__main__":
    name = "test_real_estate_12_new_flow"
    main(project_name=name, full_pipeline=True)
