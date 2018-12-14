-- phpMyAdmin SQL Dump
-- version 4.7.7
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Oct 12, 2018 at 08:03 AM
-- Server version: 5.6.38
-- PHP Version: 7.2.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `instagram_data`
--

-- --------------------------------------------------------

--
-- Table structure for table `Hash_Tag`
--

CREATE TABLE `Hash_Tag` (
  `id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(225) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Scraping_Content`
--

CREATE TABLE `Scraping_Content` (
  `id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_caption` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `image_comment_count` int(11) NOT NULL DEFAULT '0',
  `image_date_posted` varchar(125) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `image_liked_count` int(11) NOT NULL DEFAULT '0',
  `image_top_color` varchar(75) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `image_location` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `owner_follow_count` int(11) NOT NULL DEFAULT '0',
  `owner_bio` varchar(1000) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `owner_engagement_rate` float NOT NULL DEFAULT '0',
  `hashtagid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Hash_Tag`
--
ALTER TABLE `Hash_Tag`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `Scraping_Content`
--
ALTER TABLE `Scraping_Content`
  ADD PRIMARY KEY (`id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
