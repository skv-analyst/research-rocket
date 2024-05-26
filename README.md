## Refactoring:
- __src.data.working_db__ 
  - [ ] Единая функция сохранения данных в БД. Принимает: класс таблицы в которую сохранять и {key:value} с данными для сохранения.
  - [ ] Единая функция запроса данных из БД. Принимает: SQL-запрос
  - [ ] Модуль только для работы с БД проекта (запись/чтение данных)
- __src.llm.working_llm__
  - [ ] Единая функция создания шаблона prompt
  - [ ] Единый класс обращений к llm с циклом обхода всех вопросов по списку
  - [ ] Единая функция распаковки json. Не достаточно обернуть ответ в json, надо пройтись и по вложенным структурам.
- __src.output.working_pdf__
  - [ ] Класс сбора и подготовки данных для формирования pdf

## Future features
- [ ] Сохранять в БД object, чтобы была возможность получить его из БД и иметь доступ ко всем свойствам этого объекта. 