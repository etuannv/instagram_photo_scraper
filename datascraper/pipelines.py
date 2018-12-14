# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

"""
MIT License

scrapy_mysql_pipeline: Asynchronous mysql Scrapy item pipeline

Copyright (c) 2017 Iaroslav Russkykh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Requirements:
- scrapy>=1.4.0
- pymysql>=0.7.11

"""

import logging
import pprint
from scrapy.exceptions import DropItem
from pymysql.cursors import DictCursor
from pymysql import OperationalError
from pymysql.constants.CR import CR_SERVER_GONE_ERROR,  CR_SERVER_LOST, CR_CONNECTION_ERROR
from twisted.internet import defer
from twisted.enterprise import adbapi
from scrapy.exporters import CsvItemExporter
import csv

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class MySQLPipeline(object):  #
    """
    Defaults:
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = None
    MYSQL_PASSWORD = ''
    MYSQL_DB = None
    MYSQL_TABLE = None
    MYSQL_MARK_SCRAPED_TABLE   : None
    MYSQL_MARK_SCRAPED_KEY   : None
    MYSQL_MARK_SCRAPED_VALUE   : None
    MYSQL_UPSERT = False
    MYSQL_RETRIES = 3
    MYSQL_CLOSE_ON_ERROR = True
    Pipeline:
    ITEM_PIPELINES = {
       'scrapy_mysql_pipeline.MySQLPipeline': 300,
    }
    """
    stats_name = 'mysql_pipeline'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.stats = crawler.stats
        self.stats.set_value('done', 0)
        self.settings = crawler.settings
        db_args = {
            'host': self.settings.get('MYSQL_HOST', 'localhost'),
            'port': self.settings.get('MYSQL_PORT', 3306),
            'user': self.settings.get('MYSQL_USER', None),
            'password': self.settings.get('MYSQL_PASSWORD', ''),
            'db': self.settings.get('MYSQL_DB', None),
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'cp_reconnect': True,
        }
        self.retries = self.settings.get('MYSQL_RETRIES', 3)
        self.close_on_error = self.settings.get('MYSQL_CLOSE_ON_ERROR', True)
        self.upsert = self.settings.get('MYSQL_UPSERT', False)
        self.table = self.settings.get('MYSQL_TABLE', None)
        self.db = adbapi.ConnectionPool('pymysql', **db_args)

    def close_spider(self, spider):
        self.db.close()

    @staticmethod
    def preprocess_item(item):
        """Can be useful with extremly straight-line spiders design without item loaders or items at all
        CAVEAT: On my opinion if you want to write something here - you must read
        http://scrapy.readthedocs.io/en/latest/topics/loaders.html before
        """
        return item

    def postprocess_item(self, *args):
        """Can be useful if you need to update query tables depends of mysql query result"""
        if len(args) > 1:
            if 'dummy' not in args[0]['id']:
                self.stats.inc_value('done')

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        # Start process insert db
        retries = self.retries
        status = False
        while retries:
            try:
                item = self.preprocess_item(item)
                yield self.db.runInteraction(self._process_item, item)
            except OperationalError as e:
                if e.args[0] in (
                        CR_SERVER_GONE_ERROR,
                        CR_SERVER_LOST,
                        CR_CONNECTION_ERROR,
                ):
                    retries -= 1
                    logger.info('%s %s attempts to reconnect left', e, retries)
                    self.stats.inc_value('{}/reconnects'.format(self.stats_name))
                    continue
                logger.exception('%s', pprint.pformat(item))
                self.stats.inc_value('{}/errors'.format(self.stats_name))
            except Exception:
                logger.exception('%s', pprint.pformat(item))
                self.stats.inc_value('{}/errors'.format(self.stats_name))
            else:
                status = True  # executed without errors
            break
        else:
            if self.close_on_error:  # Close spider if connection error happened and MYSQL_CLOSE_ON_ERROR = True
                spider.crawler.engine.close_spider(spider, '{}_fatal_error'.format(self.stats_name))
        self.postprocess_item(item, status)
        
        if self.stats.get_value('done') % 10 == 0:
            logger.info("--> Done %s/ %s", self.stats.get_value('done'), self.stats.get_value('total'))
        yield item

    def _generate_sql(self, data):
        columns = lambda d: ', '.join(['`{}`'.format(k) for k in d])
        values = lambda d: [v for v in d.values()]
        placeholders = lambda d: ', '.join(['%s'] * len(d))
        if self.upsert:
            sql_template = 'INSERT INTO `{}` ( {} ) VALUES ( {} ) ON DUPLICATE KEY UPDATE {}'
            on_duplicate_placeholders = lambda d: ', '.join(['`{}` = %s'.format(k) for k in d])
            return (
                sql_template.format(
                    self.table, columns(data),
                    placeholders(data), on_duplicate_placeholders(data)
                ),
                values(data) + values(data)
            )
        else:
            sql_template = 'INSERT INTO `{}` ( {} ) VALUES ( {} )'
            return (
                sql_template.format(self.table, columns(data), placeholders(data)),
                values(data)
            )

    def _process_item(self, tx, row):
        if row['id'] == 'dummy':
            try:
                # Mark parent done
                tx.execute(row['mark_parent_done_sql'], [])
                return
            except Exception:
                logger.error("Mark done SQL: %s", row['mark_parent_done_sql'])
                raise
        
        # Insert or update data in database
        sql, data = self._generate_sql(row)
        try:
            tx.execute(sql, data)

        except Exception:
            logger.error("SQL: %s", sql)
            # logger.error("SQL: %s", upsql)
            raise
        self.stats.inc_value('{}/saved'.format(self.stats_name))


class PrintPipeline(object):
    def process_item(self, item, spider):
        print("+++++++++++++++++++++++")
        print("hello world")
        print(item['image_location'])
        print(item['image_caption'])
        print(item['image_comment_count'])
        print(item['image_liked_count'])
        print(item['image_date_posted'])
        print(item['image_top_color'])
        print(item['owner_follow_count'])
        print(item['owner_bio'])
        print(item['owner_engagement_rate'])
        return item
  

class CsvPipeline(object):
    def __init__(self):
        self.file = open("result.csv", 'wb')
        self.exporter = CsvItemExporter(self.file)
        EXPORT_FIELDS = [
            'image_location',
            'image_caption',
            'image_comment_count',
            'image_liked_count',
            'image_date_posted',
            'image_top_color',
            'owner_follow_count',
            'owner_bio',
            'owner_engagement_rate',
        ]
                
        self.exporter.fields_to_export = EXPORT_FIELDS
        self.exporter.start_exporting()
 
    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()
 
    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

class AnotherCsvPipeline(object):
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.stats = crawler.stats
        self.stats.set_value('done', 0)
        self.file = open('scraped_items.csv', 'w', encoding='utf-8')
        self.csvwriter = csv.writer(self.file)
        self.csvwriter.writerow(
            [
                'Post Caption',
                'Post Comments',
                'Time Taken',
                'Post Likes',
                'Main Color',
                'Location',
                'Poster Follwer Count',
                'Poster Bio',
                'Average Engagement Rate of Posters Last Four Post',
            ]
        )
    
    def close_spider(self, spider):
        self.file.close()
 
    def process_item(self, item, spider):
        self.stats.inc_value('done')
        logging.info("Got {} results".format(self.stats.get_value('done')))
        self.csvwriter.writerow(
            [
                item['image_caption'],
                item['image_comment_count'],
                item['image_date_posted'],
                item['image_liked_count'],
                item['image_top_color'],
                item['image_location'],
                item['owner_follow_count'],
                item['owner_bio'],
                item['owner_engagement_rate'],
            ]
        )
        return item