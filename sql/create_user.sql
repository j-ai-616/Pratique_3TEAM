-- ============================================
-- create_user.sql
-- 데이터베이스 및 전용 사용자 계정을 생성하는 초기 설정 스크립트
-- 목적:
-- 1) 프로젝트 전용 DB 생성
-- 2) 프로젝트 전용 사용자 생성
-- 3) 해당 사용자에게 car1_db에 대한 권한 부여
-- 4) 계정/권한이 정상 생성되었는지 검증
-- ============================================

-- 1. 프로젝트에서 사용할 데이터베이스 생성
-- IF NOT EXISTS를 사용하여 이미 DB가 있어도 에러 없이 통과하도록 설계
CREATE DATABASE IF NOT EXISTS car1_db
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

-- 2. 프로젝트 전용 사용자 생성
-- '%' 호스트를 사용했기 때문에 원격 접속도 허용 가능
-- (발표 때는 "개발 편의를 위한 설정"이라고 설명 가능)
CREATE USER 'car1_user'@'%' IDENTIFIED BY 'Team3Car1';

-- 3. car1_db 데이터베이스에 대한 모든 권한 부여
-- 실제 프로젝트에서는 테이블 생성/조회/삽입/수정 등을 모두 수행할 수 있어야 하므로 ALL PRIVILEGES 부여
GRANT ALL PRIVILEGES ON car1_db.* TO 'car1_user'@'%';

-- 4. 권한 변경 사항을 즉시 반영
FLUSH PRIVILEGES;

-- 5. 계정 생성 확인
SELECT user, host
FROM mysql.user
WHERE user = 'car1_user';

-- 6. 권한 부여 확인
SHOW GRANTS FOR 'car1_user'@'%';