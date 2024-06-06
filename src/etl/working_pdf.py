from loguru import logger
from src.paths import PATH_TO_LOG, PATH_TO_FONT, PATH_TO_DATA
from fpdf import FPDF

logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")


class CreatePdf:
    def __init__(self, project_name, text: str):
        self.project_name = project_name
        self.text = text
        self.file = f"{PATH_TO_DATA}/raw/{self.project_name}/{self.project_name}.pdf"
        self.font = f"{PATH_TO_FONT}/DejaVuSans.ttf"

    def run(self):
        pdf = FPDF()

        pdf.add_page()
        pdf.add_font('DejaVuSans', '', self.font, uni=True)
        pdf.set_font("DejaVuSans", size=10)

        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.set_top_margin(10)
        pdf.set_auto_page_break(auto=True, margin=10)

        pdf.multi_cell(0, 5, self.text)

        pdf.output(self.file)


if __name__ == '__main__':
    ...
