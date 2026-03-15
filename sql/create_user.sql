-- Active: 1773024750352@@127.0.0.1@3306@car1_db
# 새로운 계정 생성 (User: car1_user / PW: Team3Car1)
CREATE DATABASE IF NOT EXISTS car1_db
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

CREATE USER 'car1_user'@'%' IDENTIFIED BY 'Team3Car1';

GRANT ALL PRIVILEGES ON car1_db.* TO 'car1_user'@'%';

FLUSH PRIVILEGES;

# 계정 생성 확인
SELECT user, host
FROM mysql.user
WHERE user = 'car1_user';

# 권한 확인
SHOW GRANTS FOR 'car1_user'@'%';