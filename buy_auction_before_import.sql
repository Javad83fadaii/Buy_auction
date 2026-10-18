-- MySQL dump 10.13  Distrib 8.0.30, for Win64 (x86_64)
--
-- Host: localhost    Database: buy_auction
-- ------------------------------------------------------
-- Server version	8.0.30

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts_user`
--

DROP TABLE IF EXISTS `accounts_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `phone_number` varchar(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user`
--

LOCK TABLES `accounts_user` WRITE;
/*!40000 ALTER TABLE `accounts_user` DISABLE KEYS */;
INSERT INTO `accounts_user` VALUES (1,'pbkdf2_sha256$870000$HmmaeIO8d34hlRnEq0Mg15$RDsvG94mug1j2mINOL9mIiq1m3YGxcyfPzqL2aKdnX0=','2026-10-15 09:38:06.749047',0,'admin','','','',1,1,'2026-10-15 09:30:25.213831','','2026-10-15 09:30:25.750678','2026-10-15 09:36:57.736839'),(2,'pbkdf2_sha256$870000$YRl6Ef6WOR0YWEWCTUqFEC$5Zl6uSKocX9C3RRqlnIdQCBe5ErlLhzpnR2FM/+l1oA=','2026-10-15 09:36:13.783867',1,'javad','','','',1,1,'2026-10-15 09:31:27.740630','','2026-10-15 09:31:28.276217','2026-10-15 09:37:08.381939'),(3,'pbkdf2_sha256$870000$Yr98XBR3hXwtWzhFaIXmBq$INc02BmX/26OA9VpdUWgPF1ycFnWXOB+igDhot32oQA=',NULL,0,'operator','','','',0,1,'2026-10-15 09:31:47.674989','','2026-10-15 09:31:48.187405','2026-10-15 09:37:15.006396');
/*!40000 ALTER TABLE `accounts_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_groups`
--

DROP TABLE IF EXISTS `accounts_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_groups_user_id_group_id_59c0b32f_uniq` (`user_id`,`group_id`),
  KEY `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_user_groups_group_id_bd11a704_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `accounts_user_groups_user_id_52b62117_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_groups`
--

LOCK TABLES `accounts_user_groups` WRITE;
/*!40000 ALTER TABLE `accounts_user_groups` DISABLE KEYS */;
INSERT INTO `accounts_user_groups` VALUES (1,1,1),(2,2,2),(3,3,3);
/*!40000 ALTER TABLE `accounts_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq` (`user_id`,`permission_id`),
  KEY `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_user_p_permission_id_113bb443_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `accounts_user_user_p_user_id_e4f0a161_fk_accounts_` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_user_permissions`
--

LOCK TABLES `accounts_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'ADMIN'),(4,'EXPERT'),(2,'MANAGER'),(3,'OPERATOR');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
INSERT INTO `auth_group_permissions` VALUES (1,1,9),(2,1,10),(3,1,11),(4,1,12),(5,1,21),(6,1,22),(7,1,23),(8,1,24),(9,1,25),(10,1,26),(22,1,27),(23,1,28),(24,1,29),(25,1,30),(26,1,31),(14,1,32),(15,1,33),(16,1,34),(17,1,35),(18,1,36),(19,1,37),(20,1,38),(21,1,39),(11,2,25),(30,2,27),(31,2,28),(32,2,30),(33,2,31),(27,2,36),(28,2,37),(29,2,39),(12,3,25),(13,3,26),(37,3,27),(38,3,28),(39,3,30),(34,3,36),(35,3,37),(36,3,39),(40,4,30),(41,4,39);
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add کاربر',6,'add_user'),(22,'Can change کاربر',6,'change_user'),(23,'Can delete کاربر',6,'delete_user'),(24,'Can view کاربر',6,'view_user'),(25,'Can view dashboard',6,'view_dashboard'),(26,'Can view operator dashboard',6,'view_operator_dashboard'),(27,'Can add محصول',7,'add_product'),(28,'Can change محصول',7,'change_product'),(29,'Can delete محصول',7,'delete_product'),(30,'Can view محصول',7,'view_product'),(31,'Can review product',7,'review_product'),(32,'Can add تصویر محصول',8,'add_productimage'),(33,'Can change تصویر محصول',8,'change_productimage'),(34,'Can delete تصویر محصول',8,'delete_productimage'),(35,'Can view تصویر محصول',8,'view_productimage'),(36,'Can add حراجی',9,'add_auction'),(37,'Can change حراجی',9,'change_auction'),(38,'Can delete حراجی',9,'delete_auction'),(39,'Can view حراجی',9,'view_auction');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_user_id` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-10-15 09:36:57.738354','1','admin',2,'[{\"changed\": {\"fields\": [\"\\u0646\\u0642\\u0634\"]}}]',6,2),(2,'2026-10-15 09:37:08.391847','2','javad',2,'[{\"changed\": {\"fields\": [\"\\u0646\\u0642\\u0634\"]}}]',6,2),(3,'2026-10-15 09:37:15.013712','3','operator',2,'[{\"changed\": {\"fields\": [\"\\u0646\\u0642\\u0634\"]}}]',6,2);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (6,'accounts','user'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(9,'products','auction'),(7,'products','product'),(8,'products','productimage'),(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-15 09:29:38.896965'),(2,'contenttypes','0002_remove_content_type_name','2026-10-15 09:29:38.956687'),(3,'auth','0001_initial','2026-10-15 09:29:39.203518'),(4,'auth','0002_alter_permission_name_max_length','2026-10-15 09:29:39.258937'),(5,'auth','0003_alter_user_email_max_length','2026-10-15 09:29:39.264984'),(6,'auth','0004_alter_user_username_opts','2026-10-15 09:29:39.270653'),(7,'auth','0005_alter_user_last_login_null','2026-10-15 09:29:39.277403'),(8,'auth','0006_require_contenttypes_0002','2026-10-15 09:29:39.279460'),(9,'auth','0007_alter_validators_add_error_messages','2026-10-15 09:29:39.285591'),(10,'auth','0008_alter_user_username_max_length','2026-10-15 09:29:39.291583'),(11,'auth','0009_alter_user_last_name_max_length','2026-10-15 09:29:39.297065'),(12,'auth','0010_alter_group_name_max_length','2026-10-15 09:29:39.353163'),(13,'auth','0011_update_proxy_permissions','2026-10-15 09:29:39.361356'),(14,'auth','0012_alter_user_first_name_max_length','2026-10-15 09:29:39.368219'),(15,'accounts','0001_initial','2026-10-15 09:29:39.653156'),(16,'accounts','0002_remove_viewer_dashboard_permission','2026-10-15 09:29:39.660354'),(17,'admin','0001_initial','2026-10-15 09:29:39.791564'),(18,'admin','0002_logentry_remove_auto_add','2026-10-15 09:29:39.798891'),(19,'admin','0003_logentry_add_action_flag_choices','2026-10-15 09:29:39.808549'),(20,'products','0001_initial','2026-10-15 09:29:40.589814'),(21,'products','0002_alter_product_options','2026-10-15 09:29:40.601665'),(22,'products','0003_product_assigned_expert','2026-10-15 09:29:40.706257'),(23,'products','0004_product_final_inspection_done_product_has_all_prices_and_more','2026-10-15 09:29:41.454691'),(24,'sessions','0001_initial','2026-10-15 09:29:41.492470'),(25,'products','0005_auction_auction_number_productimage_thumbnail','2026-10-18 04:57:49.777302');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('zxy3olbnd3ucunwl9zbjtjlbr1m2ksst','.eJxVjEEOwiAQRe_C2pAZaBFcuu8ZCDOAVA0kpV0Z765NutDtf-_9l_BhW4vfelr8HMVFoDj9bhT4keoO4j3UW5Pc6rrMJHdFHrTLqcX0vB7u30EJvXxrq_LgBkJAZcgAJ4MabM4pYxw1WhWcJiLjKDODOUMiisSMEMYM0Yj3B9y6OHQ:1xHHuY:0ekRK1Ed-a0UG2TYK14QWXtdGtAxqMeo_5jSzcKvZP4','2026-10-29 09:38:06.753211');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products_auction`
--

DROP TABLE IF EXISTS `products_auction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products_auction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `source_house` varchar(32) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date DEFAULT NULL,
  `location` varchar(255) NOT NULL,
  `currency` varchar(16) NOT NULL,
  `commission_rate` decimal(5,2) NOT NULL,
  `status` varchar(32) NOT NULL,
  `total_lots` int unsigned NOT NULL,
  `entered_lots_count` int unsigned NOT NULL,
  `cancelled_lots_count` int unsigned NOT NULL,
  `expert_lots_count` int unsigned NOT NULL,
  `notable_lots_count` int unsigned NOT NULL,
  `to_buy_count` int unsigned NOT NULL,
  `initial_info_count` int unsigned NOT NULL,
  `all_prices_count` int unsigned NOT NULL,
  `final_inspection_count` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `updated_by_id` bigint DEFAULT NULL,
  `auction_number` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auction_status_date_idx` (`status`,`start_date`),
  KEY `auction_house_status_idx` (`source_house`,`status`),
  KEY `products_auction_created_by_id_c233c649_fk_accounts_user_id` (`created_by_id`),
  KEY `products_auction_updated_by_id_dfaef642_fk_accounts_user_id` (`updated_by_id`),
  KEY `products_auction_name_a0c3fec1` (`name`),
  KEY `products_auction_source_house_e73bb1e5` (`source_house`),
  KEY `products_auction_start_date_ab1d2b62` (`start_date`),
  KEY `products_auction_status_f7a1ca35` (`status`),
  KEY `products_auction_auction_number_396d1e6c` (`auction_number`),
  CONSTRAINT `products_auction_created_by_id_c233c649_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `products_auction_updated_by_id_dfaef642_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `products_auction_chk_1` CHECK ((`total_lots` >= 0)),
  CONSTRAINT `products_auction_chk_2` CHECK ((`entered_lots_count` >= 0)),
  CONSTRAINT `products_auction_chk_3` CHECK ((`cancelled_lots_count` >= 0)),
  CONSTRAINT `products_auction_chk_4` CHECK ((`expert_lots_count` >= 0)),
  CONSTRAINT `products_auction_chk_5` CHECK ((`notable_lots_count` >= 0)),
  CONSTRAINT `products_auction_chk_6` CHECK ((`to_buy_count` >= 0)),
  CONSTRAINT `products_auction_chk_7` CHECK ((`initial_info_count` >= 0)),
  CONSTRAINT `products_auction_chk_8` CHECK ((`all_prices_count` >= 0)),
  CONSTRAINT `products_auction_chk_9` CHECK ((`final_inspection_count` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products_auction`
--

LOCK TABLES `products_auction` WRITE;
/*!40000 ALTER TABLE `products_auction` DISABLE KEYS */;
/*!40000 ALTER TABLE `products_auction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products_product`
--

DROP TABLE IF EXISTS `products_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `product_code` varchar(64) DEFAULT NULL,
  `description` longtext NOT NULL,
  `suggested_price` decimal(18,2) DEFAULT NULL,
  `suitable_price` decimal(18,2) DEFAULT NULL,
  `suggestion_date` date NOT NULL,
  `production_date` date DEFAULT NULL,
  `production_location` varchar(255) NOT NULL,
  `artist` varchar(255) NOT NULL,
  `material` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `usage` varchar(255) NOT NULL,
  `art_type` varchar(255) NOT NULL,
  `suggested_by` varchar(255) NOT NULL,
  `contact_method` varchar(32) NOT NULL,
  `is_cancelled` tinyint(1) NOT NULL,
  `is_notable` tinyint(1) NOT NULL,
  `needs_expert_review` tinyint(1) NOT NULL,
  `source_type` varchar(32) NOT NULL,
  `source_name` varchar(255) NOT NULL,
  `source_url` varchar(1000) NOT NULL,
  `status` varchar(32) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by_id` bigint DEFAULT NULL,
  `updated_by_id` bigint DEFAULT NULL,
  `assigned_expert_id` bigint DEFAULT NULL,
  `final_inspection_done` tinyint(1) NOT NULL,
  `has_all_prices` tinyint(1) NOT NULL,
  `has_initial_info` tinyint(1) NOT NULL,
  `to_buy` tinyint(1) NOT NULL,
  `auction_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `products_product_source_type_product_code_key` (`source_type`,`product_code`),
  KEY `products_src_status_idx` (`source_type`,`status`),
  KEY `products_product_created_by_id_dd4af40e_fk_accounts_user_id` (`created_by_id`),
  KEY `products_product_updated_by_id_33940c75_fk_accounts_user_id` (`updated_by_id`),
  KEY `products_product_title_659cf449` (`title`),
  KEY `products_product_product_code_9b97c0ac` (`product_code`),
  KEY `products_product_suggestion_date_28da4aff` (`suggestion_date`),
  KEY `products_product_artist_99203a5d` (`artist`),
  KEY `products_product_status_5c2da276` (`status`),
  KEY `products_product_assigned_expert_id_0f850a0c_fk_accounts_user_id` (`assigned_expert_id`),
  KEY `products_product_auction_id_2b527b3c_fk_products_auction_id` (`auction_id`),
  KEY `products_product_final_inspection_done_df71ab47` (`final_inspection_done`),
  KEY `products_product_to_buy_63be4441` (`to_buy`),
  CONSTRAINT `products_product_assigned_expert_id_0f850a0c_fk_accounts_user_id` FOREIGN KEY (`assigned_expert_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `products_product_auction_id_2b527b3c_fk_products_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `products_auction` (`id`),
  CONSTRAINT `products_product_created_by_id_dd4af40e_fk_accounts_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `products_product_updated_by_id_33940c75_fk_accounts_user_id` FOREIGN KEY (`updated_by_id`) REFERENCES `accounts_user` (`id`),
  CONSTRAINT `products_product_suggested_price_gte_0` CHECK (((`suggested_price` >= 0) or (`suggested_price` is null))),
  CONSTRAINT `products_product_suitable_price_gte_0` CHECK (((`suitable_price` >= 0) or (`suitable_price` is null)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products_product`
--

LOCK TABLES `products_product` WRITE;
/*!40000 ALTER TABLE `products_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `products_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products_productimage`
--

DROP TABLE IF EXISTS `products_productimage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products_productimage` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `image` varchar(100) NOT NULL,
  `is_primary` tinyint(1) NOT NULL,
  `sort_order` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `product_id` bigint NOT NULL,
  `thumbnail` varchar(500) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `products_productimage_product_id_e747596a_fk_products_product_id` (`product_id`),
  CONSTRAINT `products_productimage_product_id_e747596a_fk_products_product_id` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`),
  CONSTRAINT `products_productimage_chk_1` CHECK ((`sort_order` >= 0)),
  CONSTRAINT `products_productimage_sort_order_gte_0` CHECK ((`sort_order` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products_productimage`
--

LOCK TABLES `products_productimage` WRITE;
/*!40000 ALTER TABLE `products_productimage` DISABLE KEYS */;
/*!40000 ALTER TABLE `products_productimage` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-18  9:41:42
