from src.data import working_db as db
from src.llm.prompts import INTERVIEW_QUESTIONS, SUMMARY_QUESTIONS
from src.llm import working_llm as llm
from src.etl import working_llm_answers as etl
from src.etl import working_pdf as pdf


def main(project_name: str, save_files, process_interviews, process_project: bool, ) -> None:
    # 01. Adding a project and an interview to the database.
    if save_files:
        db.save_to_db(table_name="projects", project_name=project_name)
        db.save_files_to_db(project_name=project_name)

    project_id = db.read_db(
        "SELECT DISTINCT project_id FROM projects WHERE project_name = $name", {"name": project_name}
    )[0]

    # 02. Processing all interviews in the project.
    if process_interviews:
        llm.LlmProcessingInterview(project_id=project_id, project_name=project_name,
                                   questions=INTERVIEW_QUESTIONS).run()

    # 03. Transformation of all answers for all interviews of the project into one structured line.
    all_llm_answer_interviews = etl.PrepareInterviewForSummary(project_id=project_id).run()
    # print(all_llm_answer_interviews)

    # 04. Getting the final summary based on the results of all interviews of the project.
    if process_project:
        llm.LlmProcessingProject(project_id=project_id, all_llm_answers=all_llm_answer_interviews,
                                 questions=SUMMARY_QUESTIONS).run()

    # 05. Converting the final sammari into a structured string.
    summary_llm_answer = etl.UnpackingSummary(project_id=project_id, project_name=project_name).run()
    # print(summary_llm_answer)

    # 06. Saving the data in pdf-file.
    pdf.CreatePdf(project_name=project_name, pdf_type="summary", text=summary_llm_answer).run()
    pdf.CreatePdf(project_name=project_name, pdf_type="interviews", text=all_llm_answer_interviews).run()


if __name__ == "__main__":
    name = "test_real_estate_02"
    main(project_name=name, save_files=False, process_interviews=False, process_project=False)
