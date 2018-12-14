#!/usr/bin/python3
# -*- coding: utf-8 -*-
import scrapy
import sys, os
import re
from scrapy.http import Request
from datascraper.items import InstagramItem
from w3lib.html import replace_escape_chars
import time
from hashlib import md5
import datetime
import logging
import json
import requests
from random import shuffle
from hashlib import md5
from w3lib.http import basic_auth_header
import html

import pymysql
from pymysql.cursors import DictCursor


def unescapeHtml(value):
    if value is not None:
        return html.unescape(value.strip())
    else:
        return value

    
#  scrapy crawl instagram_spd -a hastag=macbookpro
class InstagramSpdSpider(scrapy.Spider):
    name = "instagram_spd"
    #allowed_domains = ['buyzoxs.de', 'rebuy.de', 'momox.de']
    auth = {'Proxy-Authorization' : basic_auth_header('luketych', '3rzdbpixv9')}
    
    custom_settings = {
        'IS_STOP_REPORT'   : False,
        'MYSQL_TABLE'   : 'Scraping_Content',
        'DOWNLOAD_TIMEOUT'   : 180,
        'ROTATING_PROXY_PAGE_RETRY_TIMES'   : 5,
        'RETRY_TIMES'   : 3,
        'HTTPERROR_ALLOWED_CODES': [],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 543,
            'datascraper.middlewares.MySpiderMiddleware': 100,
            'datascraper.middlewares.RandomUserAgentMiddleware': 400,
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
            'scrapy.downloadermiddlewares.cookies.CookiesMiddleware':543,
        },
        # 'ROTATING_PROXY_BAN_POLICY':'datascraper.middlewares.MyDetectionPolicy',
        'ITEM_PIPELINES': {
            # 'datascraper.pipelines.PrintPipeline': 100,
            'datascraper.pipelines.MySQLPipeline': 600,
            'datascraper.pipelines.AnotherCsvPipeline': 500,
        },
    }

    def inputHashtag(self, hash_name):
        db_args = {
            'host': self.settings.get('MYSQL_HOST', 'localhost'),
            'port': self.settings.get('MYSQL_PORT', 3306),
            'user': self.settings.get('MYSQL_USER', None),
            'password': self.settings.get('MYSQL_PASSWORD', ''),
            'db': self.settings.get('MYSQL_DB', None),
            'charset': 'utf8',
            'cursorclass': DictCursor
        }
        # Select data by hashtag name
        sqlconnect = pymysql.connect(**db_args)
        
        try:
            with sqlconnect.cursor() as cursor:
                # Select hashtag id from db
                sql = """SELECT `id` FROM `Hash_Tag` WHERE name='{}'""".format(hash_name)
                logging.info('1. select sql: %s', sql)
                cursor.execute(sql)
                item = cursor.fetchone()
                logging.info(item)
                if item:
                    logging.info('Hash tag exist id: {}'.format(item['id']))
                    return item['id']
                else:
                    # Insert the recorst
                    logging.info('Hash tag does not exist')
                    hashid = md5((hash_name).lower().encode('utf-8')).hexdigest()
                    sql = """INSERT INTO `Hash_Tag`(`id`, `name`) VALUES ('{}','{}')""".format(hashid, hash_name)
                    logging.info('2. Inser sql: {}'.format(sql))
                    cursor.execute(sql)
                    sqlconnect.commit()
                    return hashid
        except Exception as ex:
            logging.error('==> Cant insert new hashtag')
            logging.info(ex)
            return None
        finally:
            sqlconnect.close()

    def __init__(self, hashtag=None, *args, **kwargs):
        super(InstagramSpdSpider, self).__init__(*args, **kwargs)

        if hashtag is None:
            self.hashtag = "macbookpro"
            print(self.hashtag)
        else:
            self.hashtag = hashtag.strip()

    def start_requests(self):
        # Insert or get hastag id from db
        id = self.inputHashtag(self.hashtag)
        if not id:
            sys.exit("Stop because cant make hastagid")
        
        self.hashtagid = id

        # Get list project from ebay
        logging.info("--- hashtag: %s ---", self.hashtag)
        url = "https://www.instagram.com/explore/tags/{}/?__a=1".format(self.hashtag)

        
        yield Request(
            url,
            headers = self.auth,
            callback=self.parse_post,
        )

    def canculateColor(self, img_url):
        image_name = md5(img_url.lower().encode('utf-8')).hexdigest()
        ext = img_url.split(".")   
        if ext:
            ext = ext[-1]
        else:
            ext='jpg'

        img_filepath = image_name + "." + ext
        logging.info("Downloading image...")
        with open(img_filepath, 'wb') as f:
            f.write(requests.get(img_url).content)

        logging.info("Analyse image color...")
        import extcolors
        if os.path.isfile(img_filepath):
            colors, pixel_count = extcolors.extract(img_filepath)
            os.remove(img_filepath)
            
            return ','.join(str(color) for color in colors[:5])
            
        return ''

    def getPostData(self, edges):
        data_list = []
        for post in edges:
            data_item = {
                'image_location': '',
                'image_caption': '',
                'image_comment_count': '',
                'image_liked_count': '',
                'image_date_posted': '',
                'thumbnail_src150': '',
                'shortcode': '',
            }
            try:
                data_item['image_location'] = post['node']['location']['name']
            except Exception as ex:
                data_item['image_location'] = ''
                pass
            
            try:
                data_item['image_caption'] = replace_escape_chars(post['node']['edge_media_to_caption']['edges'][0]['node']['text'])
            except Exception as ex:
                data_item['image_caption'] = ''
                pass

            try:
                data_item['image_comment_count'] = post['node']['edge_media_to_comment']['count']
            except Exception as ex:
                data_item['image_comment_count'] = ''
                pass
            
            try:
                data_item['image_liked_count'] = post['node']['edge_liked_by']['count']
            except Exception as ex:
                data_item['image_comment_count'] =''
                pass

            try:
                data_item['image_date_posted'] = datetime.datetime.fromtimestamp(post['node']['taken_at_timestamp']).isoformat()
            except Exception as ex:
                data_item['image_date_posted'] = ''
                pass
            
            try:
                data_item['thumbnail_src150'] = post['node']['thumbnail_resources'][0]['src']
            except Exception as ex:
                data_item['thumbnail_src150'] = ''
                pass
            
            try:
                data_item['shortcode'] = post['node']['shortcode']
            except Exception as ex:
                data_item['shortcode'] = ''
                
            
            # yield data_item  
            data_list.append(data_item)
        
        return data_list

    def scrambled(self, data):
        if not data:
            return ""

        data = data.replace("|", " ")
        data = re.sub(" +", " ", data)
        list_item = re.split(" ", data)
        shuffle(list_item)
        return re.sub(" +", " ", " ".join(list_item)).replace("\n", "")

    def parse_owner(self, response):
        data_item = response.meta
        data_item['owner_follow_count'] = ''
        data_item['owner_engagement_rate'] =''
        data_item['owner_bio']= ''
        # Get follower count
        page_source = html.unescape(response.text)
        

        temp = re.findall(r'"edge_followed_by":{"count":(\d+)},', page_source, re.MULTILINE)
        if temp:
            data_item['owner_follow_count'] = temp[0]
            # Find 4 recent post counter
            
            temp = re.findall(r'shortcode":".[^\}]*","edge_media_to_comment":{"count":(\d+)', page_source)
            
            if len(temp)>4: 
                
                avarage_comment = (int(temp[0]) + int(temp[1]) + int(temp[2]) + int(temp[3]))/4
                
                data_item['owner_engagement_rate'] = (avarage_comment/float(data_item['owner_follow_count']))*100
                
        # Get user bio
        page_source = re.sub(r'\\u.{4}', '  ', page_source)
        temp = re.findall(r'"graphql":{"user":{"biography":"(.*)","blocked_by_viewer"', page_source, re.MULTILINE)
        if temp:
            data_item['owner_bio'] = temp[0]
        
        
        # Canculate color
        if data_item['thumbnail_src150']:
            data_item['image_top_color'] = self.canculateColor(data_item['thumbnail_src150'])
        
        

        result = InstagramItem()
        result["id"] = md5((response.url).lower().encode('utf-8')).hexdigest()
        result['image_location'] =  str(data_item['image_location'])
        result['image_caption'] =  str(self.scrambled(data_item['image_caption']))
        result['image_comment_count'] =  str(data_item['image_comment_count'])
        result['image_liked_count'] =  str(data_item['image_liked_count'])
        result['image_date_posted'] =  str(data_item['image_date_posted'])
        result['image_top_color'] =  str(data_item['image_top_color'])
        result['owner_follow_count'] =  str(data_item['owner_follow_count'])
        result['owner_bio'] =  str(self.scrambled(data_item['owner_bio']))
        result['owner_engagement_rate'] =  str(data_item['owner_engagement_rate'])
        result['hashtagid'] =  self.hashtagid
        
        yield result

    def parse_post_owner(self, response):
        data_item = response.meta
        temp = re.findall(r'owner.*"username":"(.[^\"]*)', response.text, re.MULTILINE)
        if temp:
            owner_url = 'https://www.instagram.com/{}/'.format(temp[0])
            yield Request(
                owner_url,
                headers = self.auth,
                callback= self.parse_owner,
                meta = data_item
            )

    def parse_post(self, response):
        # jdata = json.loads(response.text.encode('utf8'))
        jdata = json.loads(response.text)
        # Get next infomation
        try:
            has_next_page = jdata['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['has_next_page']
            logging.info("Print has_next_page = {}".format(has_next_page))
        except Exception as ex:
            has_next_page = None
            
        
        try:
            max_id = jdata['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor']
            
        except Exception as ex:
            max_id = None
        
        # If has next page and max_id then request next page
        if has_next_page and max_id:
            url = "https://www.instagram.com/explore/tags/{}/?__a=1&max_id={}".format(self.hashtag, max_id)
            yield Request(
                url,
                headers = self.auth,
                callback=self.parse_post,
            )
        
        data_list = self.getPostData(jdata['graphql']['hashtag']['edge_hashtag_to_media']['edges'])
        for data_item in data_list:
            if data_item['shortcode']:    
                post_url = 'https://www.instagram.com/p/{}/'.format(data_item['shortcode'])
                yield Request(
                    post_url,
                    headers = self.auth,
                    callback= self.parse_post_owner,
                    meta = data_item
                )
            
