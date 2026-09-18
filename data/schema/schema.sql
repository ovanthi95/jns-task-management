-- JNS Task Management Platform
-- Data Tier - MySQL Schema
-- Exported from AWS RDS MySQL

SET FOREIGN_KEY_CHECKS = 0;

-- organisations
DROP TABLE IF EXISTS `organisations`;
CREATE TABLE `organisations` (
  `organisation_id` int NOT NULL AUTO_INCREMENT,
  `organisation_name` varchar(150) NOT NULL,
  `organisation_type` varchar(50) NOT NULL,
  `email` varchar(150) NOT NULL,
  `phone` varchar(30) NOT NULL,
  `address` varchar(255) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`organisation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- roles
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `role_id` int NOT NULL AUTO_INCREMENT,
  `role_name` varchar(50) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `role_name` (`role_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- users
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(80) NOT NULL,
  `last_name` varchar(80) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `availability` varchar(30) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `organisation_id` int NOT NULL,
  `role_id` int NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `unique_organisation_email` (`organisation_id`,`email`),
  KEY `users_role_id_1900a745_fk_roles_role_id` (`role_id`),
  CONSTRAINT `users_organisation_id_5768f0e1_fk_organisations_organisation_id` FOREIGN KEY (`organisation_id`) REFERENCES `organisations` (`organisation_id`),
  CONSTRAINT `users_role_id_1900a745_fk_roles_role_id` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- projects
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `project_id` int NOT NULL AUTO_INCREMENT,
  `project_name` varchar(150) NOT NULL,
  `description` longtext,
  `status` varchar(30) NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by` int NOT NULL,
  `organisation_id` int NOT NULL,
  PRIMARY KEY (`project_id`),
  KEY `projects_created_by_a99c4979_fk_users_user_id` (`created_by`),
  KEY `projects_organisation_id_92f61849_fk_organisat` (`organisation_id`),
  CONSTRAINT `projects_created_by_a99c4979_fk_users_user_id` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `projects_organisation_id_92f61849_fk_organisat` FOREIGN KEY (`organisation_id`) REFERENCES `organisations` (`organisation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- project_members
DROP TABLE IF EXISTS `project_members`;
CREATE TABLE `project_members` (
  `project_member_id` int NOT NULL AUTO_INCREMENT,
  `project_role` varchar(50) DEFAULT NULL,
  `joined_at` datetime(6) NOT NULL,
  `project_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`project_member_id`),
  UNIQUE KEY `unique_project_user` (`project_id`,`user_id`),
  KEY `project_members_user_id_2e9d44b1_fk_users_user_id` (`user_id`),
  CONSTRAINT `project_members_project_id_bf2e42ec_fk_projects_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`),
  CONSTRAINT `project_members_user_id_2e9d44b1_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- task_types
DROP TABLE IF EXISTS `task_types`;
CREATE TABLE `task_types` (
  `task_type_id` int NOT NULL AUTO_INCREMENT,
  `type_name` varchar(50) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `display_order` smallint unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`task_type_id`),
  UNIQUE KEY `type_name` (`type_name`),
  CONSTRAINT `task_types_chk_1` CHECK ((`display_order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- task_statuses
DROP TABLE IF EXISTS `task_statuses`;
CREATE TABLE `task_statuses` (
  `status_id` int NOT NULL AUTO_INCREMENT,
  `status_name` varchar(50) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_terminal` tinyint(1) NOT NULL,
  `display_order` smallint unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`status_id`),
  UNIQUE KEY `status_name` (`status_name`),
  CONSTRAINT `task_statuses_chk_1` CHECK ((`display_order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- priorities
DROP TABLE IF EXISTS `priorities`;
CREATE TABLE `priorities` (
  `priority_id` int NOT NULL AUTO_INCREMENT,
  `priority_name` varchar(30) NOT NULL,
  `priority_level` smallint unsigned NOT NULL,
  `display_order` smallint unsigned NOT NULL,
  `colour` varchar(20) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`priority_id`),
  UNIQUE KEY `priority_name` (`priority_name`),
  CONSTRAINT `priorities_chk_1` CHECK ((`priority_level` >= 0)),
  CONSTRAINT `priorities_chk_2` CHECK ((`display_order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tasks
DROP TABLE IF EXISTS `tasks`;
CREATE TABLE `tasks` (
  `task_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `description` longtext,
  `start_date` date DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `estimated_hours` decimal(6,2) DEFAULT NULL,
  `actual_hours` decimal(6,2) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by` int NOT NULL,
  `priority_id` int NOT NULL,
  `project_id` int NOT NULL,
  `status_id` int NOT NULL,
  `task_type_id` int NOT NULL,
  PRIMARY KEY (`task_id`),
  KEY `tasks_created_by_c7787c8a_fk_users_user_id` (`created_by`),
  KEY `tasks_priority_id_a8d06c60_fk_priorities_priority_id` (`priority_id`),
  KEY `tasks_project_id_288f49d9_fk_projects_project_id` (`project_id`),
  KEY `tasks_status_id_741f7b54_fk_task_statuses_status_id` (`status_id`),
  KEY `tasks_task_type_id_c63f994a_fk_task_types_task_type_id` (`task_type_id`),
  CONSTRAINT `tasks_created_by_c7787c8a_fk_users_user_id` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `tasks_priority_id_a8d06c60_fk_priorities_priority_id` FOREIGN KEY (`priority_id`) REFERENCES `priorities` (`priority_id`),
  CONSTRAINT `tasks_project_id_288f49d9_fk_projects_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`),
  CONSTRAINT `tasks_status_id_741f7b54_fk_task_statuses_status_id` FOREIGN KEY (`status_id`) REFERENCES `task_statuses` (`status_id`),
  CONSTRAINT `tasks_task_type_id_c63f994a_fk_task_types_task_type_id` FOREIGN KEY (`task_type_id`) REFERENCES `task_types` (`task_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- task_assignees
DROP TABLE IF EXISTS `task_assignees`;
CREATE TABLE `task_assignees` (
  `task_assignee_id` int NOT NULL AUTO_INCREMENT,
  `assignment_role` varchar(50) DEFAULT NULL,
  `assigned_at` datetime(6) NOT NULL,
  `assigned_by` int NOT NULL,
  `task_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`task_assignee_id`),
  UNIQUE KEY `unique_task_user` (`task_id`,`user_id`),
  KEY `task_assignees_assigned_by_7403ca6f_fk_users_user_id` (`assigned_by`),
  KEY `task_assignees_user_id_6b1c6501_fk_users_user_id` (`user_id`),
  CONSTRAINT `task_assignees_assigned_by_7403ca6f_fk_users_user_id` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `task_assignees_task_id_dfd06a60_fk_tasks_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`),
  CONSTRAINT `task_assignees_user_id_6b1c6501_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- comments
DROP TABLE IF EXISTS `comments`;
CREATE TABLE `comments` (
  `comment_id` int NOT NULL AUTO_INCREMENT,
  `comment_text` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  `task_id` int NOT NULL,
  PRIMARY KEY (`comment_id`),
  KEY `comments_user_id_b8fd0b64_fk_users_user_id` (`user_id`),
  KEY `comments_task_id_10ef8fe2_fk_tasks_task_id` (`task_id`),
  CONSTRAINT `comments_task_id_10ef8fe2_fk_tasks_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`),
  CONSTRAINT `comments_user_id_b8fd0b64_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- attachments
DROP TABLE IF EXISTS `attachments`;
CREATE TABLE `attachments` (
  `attachment_id` int NOT NULL AUTO_INCREMENT,
  `file_name` varchar(255) NOT NULL,
  `file_type` varchar(100) DEFAULT NULL,
  `file_size` bigint unsigned DEFAULT NULL,
  `s3_key` varchar(500) NOT NULL,
  `uploaded_at` datetime(6) NOT NULL,
  `uploaded_by` int NOT NULL,
  `task_id` int NOT NULL,
  PRIMARY KEY (`attachment_id`),
  KEY `attachments_uploaded_by_df0e9261_fk_users_user_id` (`uploaded_by`),
  KEY `attachments_task_id_e16e8b13_fk_tasks_task_id` (`task_id`),
  CONSTRAINT `attachments_task_id_e16e8b13_fk_tasks_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`),
  CONSTRAINT `attachments_uploaded_by_df0e9261_fk_users_user_id` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `attachments_chk_1` CHECK ((`file_size` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- task_history
DROP TABLE IF EXISTS `task_history`;
CREATE TABLE `task_history` (
  `history_id` int NOT NULL AUTO_INCREMENT,
  `field_name` varchar(100) NOT NULL,
  `old_value` json DEFAULT NULL,
  `new_value` json DEFAULT NULL,
  `changed_at` datetime(6) NOT NULL,
  `changed_by` int NOT NULL,
  `task_id` int NOT NULL,
  PRIMARY KEY (`history_id`),
  KEY `task_history_changed_by_b8ff1939_fk_users_user_id` (`changed_by`),
  KEY `task_history_task_id_118b5d3f_fk_tasks_task_id` (`task_id`),
  CONSTRAINT `task_history_changed_by_b8ff1939_fk_users_user_id` FOREIGN KEY (`changed_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `task_history_task_id_118b5d3f_fk_tasks_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- audit_logs
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `audit_log_id` int NOT NULL AUTO_INCREMENT,
  `action` varchar(50) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` int DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `old_value` json DEFAULT NULL,
  `new_value` json DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `organisation_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`audit_log_id`),
  KEY `audit_logs_organisation_id_3111dee5_fk_organisat` (`organisation_id`),
  KEY `audit_logs_user_id_752b0e2b_fk_users_user_id` (`user_id`),
  CONSTRAINT `audit_logs_organisation_id_3111dee5_fk_organisat` FOREIGN KEY (`organisation_id`) REFERENCES `organisations` (`organisation_id`),
  CONSTRAINT `audit_logs_user_id_752b0e2b_fk_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
