-- SmartPlan 时间规划助手 - 数据库建表语句
-- 数据库名: smart_plan

CREATE DATABASE IF NOT EXISTS smart_plan
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE smart_plan;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL COMMENT 'PBKDF2-SHA256 格式: pbkdf2_sha256$iterations$salt$hash',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL COMMENT '任务标题',
    description TEXT COMMENT '任务描述',
    task_date DATE NOT NULL COMMENT '任务日期',
    planned_start_time TIME COMMENT '预计开始时间',
    planned_end_time TIME COMMENT '预计结束时间',
    status ENUM('TODO', 'IN_PROGRESS', 'DONE', 'UNDONE', 'CANCELLED') NOT NULL DEFAULT 'TODO',
    -- SMART 法则字段
    smart_specific VARCHAR(500) NOT NULL COMMENT 'S: 具体要完成什么',
    smart_measurable VARCHAR(500) NOT NULL COMMENT 'M: 通过什么标准判断完成',
    smart_achievable VARCHAR(500) COMMENT 'A: 今天是否具备完成条件',
    smart_relevant VARCHAR(500) COMMENT 'R: 和目标、工作或学习有什么关系',
    smart_time_bound VARCHAR(500) NOT NULL COMMENT 'T: 需要在什么时间前完成',
    -- 四象限
    important TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否重要',
    urgent TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否紧急',
    quadrant ENUM('IMPORTANT_URGENT', 'IMPORTANT_NOT_URGENT', 'NOT_IMPORTANT_URGENT', 'NOT_IMPORTANT_NOT_URGENT') NOT NULL COMMENT '四象限(自动计算)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, task_date),
    INDEX idx_user_status (user_id, status),
    INDEX idx_user_quadrant (user_id, quadrant)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 任务复盘表
CREATE TABLE IF NOT EXISTS task_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL UNIQUE COMMENT '一个任务最多一条复盘',
    user_id INT NOT NULL,
    actual_start_time TIME COMMENT '实际开始时间',
    actual_end_time TIME COMMENT '实际结束时间',
    is_completed TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否完成',
    completion_note VARCHAR(1000) COMMENT '完成情况说明',
    unfinished_reason VARCHAR(500) COMMENT '未完成原因',
    problems VARCHAR(1000) COMMENT '遇到的问题',
    learnings VARCHAR(1000) COMMENT '收获',
    improvement VARCHAR(1000) COMMENT '下次改进',
    self_rating TINYINT COMMENT '自我评分 1-5',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    CONSTRAINT chk_rating CHECK (self_rating >= 1 AND self_rating <= 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 每日复盘表
CREATE TABLE IF NOT EXISTS daily_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    review_date DATE NOT NULL COMMENT '复盘日期',
    total_tasks INT NOT NULL DEFAULT 0,
    completed_tasks INT NOT NULL DEFAULT 0,
    unfinished_tasks INT NOT NULL DEFAULT 0,
    cancelled_tasks INT NOT NULL DEFAULT 0,
    quadrant_summary JSON COMMENT '四象限任务数量统计',
    ai_summary TEXT COMMENT 'AI 生成的今日小结 (markdown)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_date (user_id, review_date),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
