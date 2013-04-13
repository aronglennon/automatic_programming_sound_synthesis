CREATE DATABASE  IF NOT EXISTS `automatic_programming_sound_synthesis` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `automatic_programming_sound_synthesis`;
-- MySQL dump 10.13  Distrib 5.5.16, for osx10.5 (i386)
--
-- Host: localhost    Database: automatic_programming_sound_synthesis
-- ------------------------------------------------------
-- Server version	5.5.8

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `testdata_similarity_repinsert`
--

DROP TABLE IF EXISTS `testdata_similarity_repinsert`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_repinsert` (
  `id` int(11) NOT NULL,
  `testrun_id` int(11) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `num_unique_reps` int(11) DEFAULT NULL,
  `max_reps_for_unique` int(11) DEFAULT NULL,
  `min_reps_for_unique` int(11) DEFAULT NULL,
  `total_reps` int(11) DEFAULT NULL,
  `avg_reps` float DEFAULT NULL,
  `total_length_reps` int(11) DEFAULT NULL,
  `total_length_deletes` int(11) DEFAULT NULL,
  `num_seg_deletes` int(11) DEFAULT NULL,
  `max_del` int(11) DEFAULT NULL,
  `min_del` int(11) DEFAULT NULL,
  `max_rep` int(11) DEFAULT NULL,
  `min_rep` int(11) DEFAULT NULL,
  `avg_rep` float DEFAULT NULL,
  `avg_del` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_repinsert`
--

LOCK TABLES `testdata_similarity_repinsert` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_repinsert` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_repinsert` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `parameters`
--

DROP TABLE IF EXISTS `parameters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `parameters` (
  `parameter_set_id` int(11) NOT NULL,
  `test_type` varchar(45) NOT NULL,
  `init_method` varchar(45) DEFAULT NULL,
  `resource_lim_type` varchar(45) DEFAULT NULL,
  `genops1` varchar(45) DEFAULT NULL,
  `genops1_prob` double DEFAULT NULL,
  `genops2` varchar(45) DEFAULT NULL,
  `genops2_prob` double DEFAULT NULL,
  `genops3` varchar(45) DEFAULT NULL,
  `genops3_prob` double DEFAULT NULL,
  `genops4` varchar(45) DEFAULT NULL,
  `genops4_prob` double DEFAULT NULL,
  `tree_depth_type` varchar(45) DEFAULT NULL,
  `features` varchar(45) DEFAULT NULL,
  `similarity` varchar(45) DEFAULT NULL,
  `selection` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`parameter_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parameters`
--

LOCK TABLES `parameters` WRITE;
/*!40000 ALTER TABLE `parameters` DISABLE KEYS */;
INSERT INTO `parameters` VALUES (0,'similarity_measure',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'mfcc','dtw',NULL),(1,'similarity_measure',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'mfcc','seq_matching',NULL),(2,'similarity_measure',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'nlse','dtw',NULL),(3,'similarity_measure',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'nlse','seq_matching',NULL),(4,'gen_ops',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'nlse','seq_matching',NULL),(5,'gen_ops',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'nlse','seq_matching',NULL),(6,'full',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `parameters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata_similarity_reorder`
--

DROP TABLE IF EXISTS `testdata_similarity_reorder`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_reorder` (
  `id` int(11) NOT NULL,
  `testrun_id` int(11) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `num_swaps` int(11) DEFAULT NULL,
  `max_size` int(11) DEFAULT NULL,
  `min_size` int(11) DEFAULT NULL,
  `total_size` int(11) DEFAULT NULL,
  `avg_size` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_reorder`
--

LOCK TABLES `testdata_similarity_reorder` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_reorder` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_reorder` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata_similarity_sampdel`
--

DROP TABLE IF EXISTS `testdata_similarity_sampdel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_sampdel` (
  `id` int(11) NOT NULL,
  `testrun_id` int(11) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `num_segments` int(11) DEFAULT NULL,
  `max_segment_length` int(11) DEFAULT NULL,
  `min_segment_length` int(11) DEFAULT NULL,
  `average_segment_length` float DEFAULT NULL,
  `total_deleted_content` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_sampdel`
--

LOCK TABLES `testdata_similarity_sampdel` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_sampdel` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_sampdel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata_similarity_stableextension`
--

DROP TABLE IF EXISTS `testdata_similarity_stableextension`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_stableextension` (
  `id` int(11) NOT NULL,
  `testrun_id` int(11) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `num_segments` int(11) DEFAULT NULL,
  `max_segment` int(11) DEFAULT NULL,
  `min_segment` int(11) DEFAULT NULL,
  `avg_segment` float DEFAULT NULL,
  `total_content_extended` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_stableextension`
--

LOCK TABLES `testdata_similarity_stableextension` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_stableextension` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_stableextension` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testrun`
--

DROP TABLE IF EXISTS `testrun`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testrun` (
  `testrun_id` int(11) NOT NULL AUTO_INCREMENT,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  PRIMARY KEY (`testrun_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testrun`
--

LOCK TABLES `testrun` WRITE;
/*!40000 ALTER TABLE `testrun` DISABLE KEYS */;
/*!40000 ALTER TABLE `testrun` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata_similarity_tsts`
--

DROP TABLE IF EXISTS `testdata_similarity_tsts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_tsts` (
  `id` int(11) NOT NULL,
  `testrun_id` int(11) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `scale_percent` float DEFAULT NULL,
  `shift_amount` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_tsts`
--

LOCK TABLES `testdata_similarity_tsts` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_tsts` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_tsts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata_similarity_contentintro`
--

DROP TABLE IF EXISTS `testdata_similarity_contentintro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_contentintro` (
  `id` int(11) NOT NULL,
  `testrun_id` varchar(45) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `intro_filename` varchar(45) DEFAULT NULL,
  `total_percent_introduction` float DEFAULT NULL,
  `total_percent_deletion` float DEFAULT NULL,
  `num_intro` int(11) DEFAULT NULL,
  `max_intro` int(11) DEFAULT NULL,
  `min_intro` int(11) DEFAULT NULL,
  `avg_intro` float DEFAULT NULL,
  `num_delete` int(11) DEFAULT NULL,
  `max_delete` int(11) DEFAULT NULL,
  `min_delete` int(11) DEFAULT NULL,
  `avg_delete` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_contentintro`
--

LOCK TABLES `testdata_similarity_contentintro` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_contentintro` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_contentintro` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata_similarity_tw`
--

DROP TABLE IF EXISTS `testdata_similarity_tw`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata_similarity_tw` (
  `id` int(11) NOT NULL,
  `testrun_id` int(11) DEFAULT NULL,
  `filename` varchar(45) DEFAULT NULL,
  `min_warping_threshold` int(11) DEFAULT NULL,
  `max_warping_threshold` int(11) DEFAULT NULL,
  `warping_path` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata_similarity_tw`
--

LOCK TABLES `testdata_similarity_tw` WRITE;
/*!40000 ALTER TABLE `testdata_similarity_tw` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata_similarity_tw` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `testdata`
--

DROP TABLE IF EXISTS `testdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `testdata` (
  `testdata_id` int(11) NOT NULL AUTO_INCREMENT,
  `testrun_id` int(11) NOT NULL,
  `generation` int(11) DEFAULT NULL,
  `individual` longtext,
  `fitness` float DEFAULT NULL,
  PRIMARY KEY (`testdata_id`),
  KEY `testrun_id_key` (`testrun_id`),
  KEY `testrun_fk` (`testrun_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `testdata`
--

LOCK TABLES `testdata` WRITE;
/*!40000 ALTER TABLE `testdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `testdata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `similarity_testdata`
--

DROP TABLE IF EXISTS `similarity_testdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `similarity_testdata` (
  `testdata_id` int(11) NOT NULL AUTO_INCREMENT,
  `testrun_id` int(11) DEFAULT NULL,
  `file_name` varchar(45) DEFAULT NULL,
  `distortion_type` varchar(45) DEFAULT NULL,
  `distortion_severity` varchar(45) DEFAULT NULL,
  `similarity_measure` varchar(45) DEFAULT NULL,
  `similarity_score` float DEFAULT NULL,
  PRIMARY KEY (`testdata_id`),
  KEY `testrun_id_fk` (`testrun_id`),
  CONSTRAINT `testrun_id_fk` FOREIGN KEY (`testrun_id`) REFERENCES `testrun` (`testrun_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `similarity_testdata`
--

LOCK TABLES `similarity_testdata` WRITE;
/*!40000 ALTER TABLE `similarity_testdata` DISABLE KEYS */;
/*!40000 ALTER TABLE `similarity_testdata` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-04-12 20:45:43
