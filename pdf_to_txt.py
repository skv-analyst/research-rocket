import fitz  # PyMuPDF

def pdf_to_text(pdf_path, txt_path):
    document = fitz.open(pdf_path)

    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text = page.get_text("text")
            txt_file.write(text)

    print(f"Текст успешно сохранен в {txt_path}")

if __name__ == "__main__":
    file = 9
    pdf_path = f'data/raw/sociology/{file}.pdf'
    txt_path = f'data/raw/sociology/{file}.txt'

    pdf_to_text(pdf_path, txt_path)