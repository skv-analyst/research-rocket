CREATE TABLE IF NOT EXISTS projects
(
    id          INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    descript    TEXT    NOT NULL,
    part        INT     NOT NULL,
    cnt_symbols INT     NOT NULL,
    raw_data    TEXT    NOT NULL
);


CREATE TABLE IF NOT EXISTS llm_results
(
    project_id       INTEGER NOT NULL,
    project_name     TEXT    NOT NULL,
    project_part     INT     NOT NULL,
    created          DATETIME,
    model            TEXT,
    input_tokens     INT,
    output_tokens    INT,
    prompt           TEXT,
    answer           TEXT,
    answer_clear     TEXT,
    FOREIGN KEY (project_id, project_name, project_part) REFERENCES projects (id, name, part)
);





