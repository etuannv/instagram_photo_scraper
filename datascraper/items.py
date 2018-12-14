# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class InstagramItem(scrapy.Item):
    id = scrapy.Field()
    image_location = scrapy.Field()
    image_caption = scrapy.Field()
    image_comment_count = scrapy.Field()
    image_liked_count = scrapy.Field()
    image_date_posted = scrapy.Field()
    image_top_color = scrapy.Field()
    owner_follow_count = scrapy.Field()
    owner_bio = scrapy.Field()
    owner_engagement_rate = scrapy.Field()
    hashtagid = scrapy.Field()
    
