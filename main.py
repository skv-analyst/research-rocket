from src.data import working_db_2 as DATABASE




def main(project_name: str = None, full_pipeline: bool = False) -> None:
    if full_pipeline:
        DATABASE.save_to_db(table_name="projects", name=project_name)
        DATABASE.save_files_to_db(project_name=project_name)

    # print(f"Started processing the interview")
    # ProcessAllInterviewsProject(project_name, questions=INTERVIEW_QUESTIONS).run()
    # print(f"The start of summarization")
    # ProcessResultsAllInterviews(project_name=project_name, questions=SUMMARY_QUESTIONS).run()
    # print("Saving the results to a file")
    # str_merged, str_summarize = CreateSTR2PDF(project_name=project_name).run()
    # save_string_to_pdf(text=str_summarize, path_to_save=folder_path, filename="ouput_summary", line_length=70)


if __name__ == "__main__":
    name = "test_real_estate_4"
    main(project_name=name, full_pipeline=False)
