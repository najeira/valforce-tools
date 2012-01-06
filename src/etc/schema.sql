-- phpMyAdmin SQL Dump
-- version 3.3.9.2
-- http://www.phpmyadmin.net
--
-- ホスト: localhost
-- 生成時間: 2011 年 3 月 08 日 15:53
-- サーバのバージョン: 5.1.55
-- PHP のバージョン: 5.3.5

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT=0;
START TRANSACTION;

--
-- データベース: `valforce_dev`
--

-- --------------------------------------------------------

--
-- テーブルの構造 `match`
--

DROP TABLE IF EXISTS `match`;
CREATE TABLE IF NOT EXISTS `match` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `home` varchar(20) DEFAULT NULL,
  `away` varchar(20) DEFAULT NULL,
  `home_player` varchar(20) DEFAULT NULL,
  `away_player` varchar(20) DEFAULT NULL,
  `stage` varchar(100) DEFAULT NULL,
  `result` tinyint(4) DEFAULT NULL,
  `version` varchar(20) DEFAULT NULL,
  `etag` varchar(100) DEFAULT NULL,
  `author` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `uploaded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `etag` (`etag`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- テーブルの構造 `match_data`
--

DROP TABLE IF EXISTS `match_data`;
CREATE TABLE IF NOT EXISTS `match_data` (
  `match_id` int(11) NOT NULL,
  `data` mediumblob DEFAULT NULL,
  PRIMARY KEY (`match_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

SET FOREIGN_KEY_CHECKS=1;
COMMIT;
