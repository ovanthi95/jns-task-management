-- JNS Task Management Platform
-- Data Tier - Lookup Seed Data
-- Exported from AWS RDS MySQL

-- roles
INSERT IGNORE INTO `roles` (`role_id`, `role_name`, `description`, `is_active`, `created_at`, `updated_at`) VALUES (1, 'Admin', 'System and organisation administration', 1, '2026-09-16 19:56:30.511854', '2026-09-16 19:56:30.511892');
INSERT IGNORE INTO `roles` (`role_id`, `role_name`, `description`, `is_active`, `created_at`, `updated_at`) VALUES (2, 'Manager', 'Project and task management', 1, '2026-09-16 19:56:30.523844', '2026-09-16 19:56:30.523874');
INSERT IGNORE INTO `roles` (`role_id`, `role_name`, `description`, `is_active`, `created_at`, `updated_at`) VALUES (3, 'Employee', 'Standard employee access', 1, '2026-09-16 19:56:30.535532', '2026-09-16 19:56:30.535571');
INSERT IGNORE INTO `roles` (`role_id`, `role_name`, `description`, `is_active`, `created_at`, `updated_at`) VALUES (4, 'Intern', 'Intern access', 1, '2026-09-16 19:56:30.547086', '2026-09-16 19:56:30.547114');
INSERT IGNORE INTO `roles` (`role_id`, `role_name`, `description`, `is_active`, `created_at`, `updated_at`) VALUES (5, 'Volunteer', 'Volunteer access', 1, '2026-09-16 19:56:30.558957', '2026-09-16 19:56:30.558986');

-- task_types
INSERT IGNORE INTO `task_types` (`task_type_id`, `type_name`, `description`, `is_active`, `display_order`, `created_at`, `updated_at`) VALUES (1, 'Accounting', 'Accounting-related work', 1, 1, '2026-09-16 19:56:30.571449', '2026-09-16 19:56:30.571477');
INSERT IGNORE INTO `task_types` (`task_type_id`, `type_name`, `description`, `is_active`, `display_order`, `created_at`, `updated_at`) VALUES (2, 'Taxation', 'Tax-related work', 1, 2, '2026-09-16 19:56:30.585390', '2026-09-16 19:56:30.585418');
INSERT IGNORE INTO `task_types` (`task_type_id`, `type_name`, `description`, `is_active`, `display_order`, `created_at`, `updated_at`) VALUES (3, 'Funding Application', 'Funding application work', 1, 3, '2026-09-16 19:56:30.596903', '2026-09-16 19:56:30.596932');

-- task_statuses
INSERT IGNORE INTO `task_statuses` (`status_id`, `status_name`, `description`, `is_active`, `is_terminal`, `display_order`, `created_at`, `updated_at`) VALUES (1, 'New', NULL, 1, 0, 1, '2026-09-16 19:56:30.608833', '2026-09-16 19:56:30.608861');
INSERT IGNORE INTO `task_statuses` (`status_id`, `status_name`, `description`, `is_active`, `is_terminal`, `display_order`, `created_at`, `updated_at`) VALUES (2, 'Assigned', NULL, 1, 0, 2, '2026-09-16 19:56:30.620501', '2026-09-16 19:56:30.620534');
INSERT IGNORE INTO `task_statuses` (`status_id`, `status_name`, `description`, `is_active`, `is_terminal`, `display_order`, `created_at`, `updated_at`) VALUES (3, 'In Progress', NULL, 1, 0, 3, '2026-09-16 19:56:30.633224', '2026-09-16 19:56:30.633253');
INSERT IGNORE INTO `task_statuses` (`status_id`, `status_name`, `description`, `is_active`, `is_terminal`, `display_order`, `created_at`, `updated_at`) VALUES (4, 'Waiting for Information', NULL, 1, 0, 4, '2026-09-16 19:56:30.645986', '2026-09-16 19:56:30.646014');
INSERT IGNORE INTO `task_statuses` (`status_id`, `status_name`, `description`, `is_active`, `is_terminal`, `display_order`, `created_at`, `updated_at`) VALUES (5, 'Under Review', NULL, 1, 0, 5, '2026-09-16 19:56:30.658688', '2026-09-16 19:56:30.658720');
INSERT IGNORE INTO `task_statuses` (`status_id`, `status_name`, `description`, `is_active`, `is_terminal`, `display_order`, `created_at`, `updated_at`) VALUES (6, 'Completed', NULL, 1, 1, 6, '2026-09-16 19:56:30.671234', '2026-09-16 19:56:30.671264');

-- priorities
INSERT IGNORE INTO `priorities` (`priority_id`, `priority_name`, `priority_level`, `display_order`, `colour`, `is_active`, `created_at`, `updated_at`) VALUES (1, 'Low', 1, 1, NULL, 1, '2026-09-16 19:56:30.683693', '2026-09-16 19:56:30.683721');
INSERT IGNORE INTO `priorities` (`priority_id`, `priority_name`, `priority_level`, `display_order`, `colour`, `is_active`, `created_at`, `updated_at`) VALUES (2, 'Medium', 2, 2, NULL, 1, '2026-09-16 19:56:30.696503', '2026-09-16 19:56:30.696530');
INSERT IGNORE INTO `priorities` (`priority_id`, `priority_name`, `priority_level`, `display_order`, `colour`, `is_active`, `created_at`, `updated_at`) VALUES (3, 'High', 3, 3, NULL, 1, '2026-09-16 19:56:30.708693', '2026-09-16 19:56:30.708720');
INSERT IGNORE INTO `priorities` (`priority_id`, `priority_name`, `priority_level`, `display_order`, `colour`, `is_active`, `created_at`, `updated_at`) VALUES (4, 'Urgent', 4, 4, NULL, 1, '2026-09-16 19:56:30.720131', '2026-09-16 19:56:30.720160');

