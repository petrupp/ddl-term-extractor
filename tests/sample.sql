CREATE TABLE resources (
    resource_id   VARCHAR(50)  NOT NULL,
    group_id      INTEGER      NOT NULL,
    parent_id     VARCHAR(50),
    resource_type VARCHAR(20)  NOT NULL,
    resource_name VARCHAR(100) NOT NULL,
    description   TEXT,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (resource_id, group_id)
);
COMMENT ON TABLE resources IS '그룹별자원마스터';
COMMENT ON COLUMN resources.resource_id IS '자원ID(그룹내유일)';
COMMENT ON COLUMN resources.group_id IS '권한그룹ID';
COMMENT ON COLUMN resources.parent_id IS '상위자원ID';
COMMENT ON COLUMN resources.resource_type IS '자원유형코드';
COMMENT ON COLUMN resources.resource_name IS '자원명';
COMMENT ON COLUMN resources.description IS '자원설명';
COMMENT ON COLUMN resources.created_at IS '생성일시';

CREATE TABLE groups (
    group_id    SERIAL       PRIMARY KEY,
    group_name  VARCHAR(100) NOT NULL,
    group_desc  TEXT,
    use_yn      CHAR(1)      DEFAULT 'Y' NOT NULL,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE groups IS '권한그룹마스터';
COMMENT ON COLUMN groups.group_id IS '그룹ID';
COMMENT ON COLUMN groups.group_name IS '그룹명';
COMMENT ON COLUMN groups.group_desc IS '그룹설명';
COMMENT ON COLUMN groups.use_yn IS '사용여부';
COMMENT ON COLUMN groups.created_at IS '생성일시';
COMMENT ON COLUMN groups.updated_at IS '수정일시';
