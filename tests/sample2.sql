-- [1. 메뉴] 그룹별로 리소스를 따로 관리하는 고속 구조
CREATE TABLE resources (
    resource_id   VARCHAR(50)  NOT NULL, -- 'PG_NOTICE' 등이 중복될 수 있음
    group_id      INTEGER      NOT NULL, -- 소유 그룹 ID
    parent_id     VARCHAR(50),           -- 상위 자원
    resource_type VARCHAR(20)  NOT NULL, 
    resource_name VARCHAR(100) NOT NULL,
    description   TEXT,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    
    -- [핵심] 리소스ID와 그룹ID를 묶어서 PK로 지정 (중복 생성 가능)
    PRIMARY KEY (resource_id, group_id)
);
COMMENT ON TABLE resources IS '그룹별자원마스터';
COMMENT ON COLUMN resources.resource_id IS '자원ID(그룹내유일)';
COMMENT ON COLUMN resources.group_id IS '권한그룹ID';

-- [3. 권한 그룹]
CREATE TABLE biz_auth_groups (
    group_id     INTEGER      PRIMARY KEY,
    group_name   VARCHAR(100) NOT NULL,
    description  TEXT,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE biz_auth_groups IS '권한그룹';

-- [5. 사용자 마스터]
CREATE TABLE users (
    user_id      BIGINT       PRIMARY KEY,
    user_name    VARCHAR(50)  NOT NULL,
    email        VARCHAR(100) UNIQUE NOT NULL,
    status       VARCHAR(10)  DEFAULT 'ACTIVE',
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE users IS '사용자마스터';
