import json
from loguru import logger
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from src.paths import PATH_TO_LOG, PATH_TO_FONT, PATH_TO_DATA
from src.data import working_db_2 as db

logger.add(f"{PATH_TO_LOG}/project.log", level="DEBUG", rotation="100 MB", retention="7 days",
           format="{time} | {level} | file: {file} | module: {module} | func: {function} | {message}")


def get_project_id(project_name):
    id = db.read_db("SELECT DISTINCT id FROM projects WHERE name = $name", {"name": project_name})
    return id[0]


class CreatePdf:
    def __init__(self, project_name):
        self.project_name = project_name
        self.project_id = get_project_id(self.project_name)
        self.replace = {
            "step_01": "Основные разделы",
            "step_02": "Кодирование интервью",
            "step_03": "Категории кодов в интервью",
            "step_04": "Проблемы обозначенные респондентом в интервью",
            "step_05": "Сгруппированные проблемы",
            "step_06": "Итоговые выводы по интервью"}

    def get_data(self):
        data = db.read_db("""SELECT answer_clear, answer_content
            FROM llm_answers_merged
            WHERE project == $id
            ORDER BY created DESC
            LIMIT 1""", {"id": self.project_id})

        if 'ERROR":"Something went wrong and the response was not parsed in json.' not in data[0][0]:
            result = data[0][0]
        else:
            result = data[0][1]

        try:
            result_json = json.loads(result)
            file = f"{PATH_TO_DATA}/raw/{self.project_name}/{self.project_name}.json"
            with open(file, "w", encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=4)

        except Exception as e:
            logger.error(e)

    def create_pdf(self):
        file = f"{PATH_TO_DATA}/raw/{self.project_name}/{self.project_name}.json"
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        doc = SimpleDocTemplate(f"{PATH_TO_DATA}/raw/{self.project_name}/{self.project_name}.pdf", pagesize=A4)
        pdfmetrics.registerFont(TTFont("DejaVuSans", f"{PATH_TO_FONT}/DejaVuSans.ttf"))

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='heading', fontName='DejaVuSans', fontSize=16, spaceAfter=10, spaceBefore=10))
        styles.add(ParagraphStyle(name='text_1', fontName='DejaVuSans', fontSize=12, spaceAfter=10, spaceBefore=10))
        styles.add(ParagraphStyle(name='text_2', fontName='DejaVuSans', fontSize=12, spaceAfter=10, spaceBefore=10,
                                  leftIndent=20))

        elements = []
        for key, val in data.items():
            elements.append(Paragraph(self.replace[key], styles["heading"]))
            if type(val) != "str": # !!!
                for val, inner_val in val.items():
                    elements.append(Paragraph(str(val), styles["text_1"]))
                    elements.append(Paragraph(str(inner_val), styles["text_2"]))
            else: # !!!
                elements.append(Paragraph(str(val), styles["text_1"])) # !!!
            elements.append(Spacer(1, 0.2 * inch))

        doc.build(elements)

    def run(self):
        self.get_data()
        self.create_pdf()


if __name__ == '__main__':
    ...
