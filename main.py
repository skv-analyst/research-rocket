from dotenv import load_dotenv
from loguru import logger
from src.paths import PATH_TO_LOG, PATH_TO_DATA
from src.data.working_db import sav_interview_files_to_database, CreateSTR2PDF
from src.llm.prompt_templates import INTERVIEW_QUESTIONS, SUMMARY_QUESTIONS
from src.llm.working_llm import ProcessAllInterviewsProject, ProcessResultsAllInterviews
from src.output.working_pdf import save_string_to_pdf

load_dotenv()
logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")


def main(project_name: str = None, folder_path: str = None, full_pipeline: bool = False) -> None:
    if full_pipeline:
        cnt_files_save = sav_interview_files_to_database(project_name=project_name, folder_path=folder_path)
        print(f"{cnt_files_save} interview files have been added to the database")

        try:
            print(f"Started processing the interview")
            ProcessAllInterviewsProject(project_name, questions=INTERVIEW_QUESTIONS).run()
        except Exception as e:
            logger.error(e)

    try:
        print(f"The start of summarization")
        ProcessResultsAllInterviews(project_name=project_name, questions=SUMMARY_QUESTIONS).run()
    except Exception as e:
        logger.error(e)

    try:
        print("Saving the results to a file")
        str_merged, str_summarize = CreateSTR2PDF(project_name=project_name).run()
        save_string_to_pdf(text=str_summarize, path_to_save=folder_path, filename="ouput_summary", line_length=70)
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    name = "test_real_estate_3"
    main(project_name=name, folder_path=f"{PATH_TO_DATA}/raw/{name}", full_pipeline=False)
