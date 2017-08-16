DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `Id` int(11) NOT NULL,
  `Amount` int(11) NOT NULL,
  `AuctionType` varchar(20) NOT NULL,
  `EnchantmentLevel` int(11) NOT NULL,
  `Expires` timestamp NOT NULL,
  `ItemTypeId` varchar(50) NOT NULL,
  `LocationId` int(11) NOT NULL,
  `QualityLevel` int(11) NOT NULL,
  `UnitPriceSilver` int(11) NOT NULL,
  `Inserted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
  ON CONFLICT REPLACE
);
