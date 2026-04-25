-- Schema do banco de dados gestor-ml360

CREATE SEQUENCE IF NOT EXISTS seq_historico_ratings START 1;
CREATE SEQUENCE IF NOT EXISTS seq_jogadores_reais START 1;
CREATE SEQUENCE IF NOT EXISTS seq_analises_scouting START 1;

CREATE TABLE IF NOT EXISTS jogadores_jogo (
    sofifa_id       VARCHAR PRIMARY KEY,
    nome            VARCHAR NOT NULL,
    idade           INTEGER,
    overall         INTEGER,
    potencial       INTEGER,
    posicao         VARCHAR,
    posicoes_alt    VARCHAR,
    time            VARCHAR,
    liga            VARCHAR,
    nacionalidade   VARCHAR,
    valor_eur       BIGINT,
    salario_eur     INTEGER,
    altura_cm       INTEGER,
    peso_kg         INTEGER,
    pe_preferido    VARCHAR,
    skill_moves     INTEGER,
    weak_foot       INTEGER,
    ritmo           INTEGER,
    finalizacao     INTEGER,
    passe           INTEGER,
    drible          INTEGER,
    defesa          INTEGER,
    fisico          INTEGER,
    versao_jogo     VARCHAR,
    data_coleta     TIMESTAMP DEFAULT current_timestamp,
    patch_versao    VARCHAR
);

CREATE TABLE IF NOT EXISTS historico_ratings (
    id              INTEGER DEFAULT nextval('seq_historico_ratings') PRIMARY KEY,
    sofifa_id       VARCHAR NOT NULL,
    overall         INTEGER,
    potencial       INTEGER,
    versao_jogo     VARCHAR,
    data_registro   TIMESTAMP DEFAULT current_timestamp,
    variacao        INTEGER
);

CREATE TABLE IF NOT EXISTS jogadores_reais (
    id              INTEGER DEFAULT nextval('seq_jogadores_reais') PRIMARY KEY,
    nome            VARCHAR NOT NULL,
    nome_normalizado VARCHAR,
    time            VARCHAR,
    liga            VARCHAR,
    temporada       VARCHAR,
    partidas        INTEGER,
    minutos         INTEGER,
    gols            INTEGER,
    assistencias    INTEGER,
    xg              DOUBLE,
    xa              DOUBLE,
    xg_por_90       DOUBLE,
    xa_por_90       DOUBLE,
    progressive_carries INTEGER,
    progressive_passes  INTEGER,
    data_coleta     TIMESTAMP DEFAULT current_timestamp,
    fonte           VARCHAR DEFAULT 'fbref'
);

CREATE TABLE IF NOT EXISTS mapeamento_jogadores (
    sofifa_id       VARCHAR PRIMARY KEY,
    nome_jogo       VARCHAR,
    nome_real       VARCHAR,
    fbref_id        VARCHAR,
    similaridade    DOUBLE,
    verificado      BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS analises_scouting (
    id              INTEGER DEFAULT nextval('seq_analises_scouting') PRIMARY KEY,
    sofifa_id       VARCHAR,
    tipo_analise    VARCHAR,
    score           DOUBLE,
    justificativa   VARCHAR,
    data_analise    TIMESTAMP DEFAULT current_timestamp
);
