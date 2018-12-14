from scrapy import signals
import random
from rotating_proxies.policy import BanDetectionPolicy
from scrapy.core.downloader.handlers.http11 import TunnelError
import gzip
from w3lib.http import basic_auth_header
import logging
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class ProxyMiddleware(object):
    def process_request(self, request, spider):
        request.meta['proxy'] = spider.crawler.settings.get('HTTP_PROXY')
        # proxy_user_pass = "luketych:3rzdbpixv9"
        # encoded_user_pass = base64.encodestring(proxy_user_pass).replace('\n', '')
        # headers = {'Proxy-Authorization': 'Basic ' + encoded_user_pass}
        # request.headers['Proxy-Authorization'] 

class MyDetectionPolicy(BanDetectionPolicy):
    def response_is_ban(self, request, response):
        # use default rules, but also consider HTTP 200 responses
        # a ban if there is 'captcha' word in response body.
        ban = super(MyDetectionPolicy, self).response_is_ban(request, response)
        ban = ban or b'My public IP address is' in response.body\
                    or b'Forbidden' in response.body\
                    or b"Service Unavailable" in response.body
        if ban:
            logger.info("Proxy %s is ban by %s", request.meta.get('proxy', None), response.url)
            
        return ban

    def exception_is_ban(self, request, exception):
        # override method completely: don't take exceptions in account
        # print "Proxy %s on url %s result: %s" % ( request.meta.get('proxy', None), request.url, exception)
        # print "Retry %s" % request.url

        return None

# class ForceUTF8Response(object):
#     """A downloader middleware to force UTF-8 encoding for all responses."""
#     encoding = 'utf-8'

#     def process_response(self, request, response, spider):
#         # Note: Use response.body_as_unicode() instead of response.text in in Scrapy <1.0.
#         return response.replace(encoding='UTF-8')
        

class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua = random.choice(spider.crawler.settings.get('USER_AGENT_LIST'))
        if ua:
            request.headers.setdefault('User-Agent', ua)




class MySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s
    
    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.
        
        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        # if ( isinstance(exception, self.EXCEPTIONS_TO_RETRY) or isinstance(exception, TunnelError) ) \
        #         and 'dont_retry' not in request.meta:
        #     print("=========== hehehe")
        #     print (response.status)
        #     return self._retry(request, exception, spider)

        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesnt have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    
    def spider_closed(self, spider):
        # second param is instance of spder about to be closed.
        spider.logger.info('Spider closed: %s' % spider.name)
        if spider.crawler.settings.get('IS_STOP_REPORT'):
            msg = spider.name+ " stopp..."
            self.notifyEmail('Spider notify', msg, 'etuannv@gmail.com')

    def notifyEmail(self, subject, message, toaddr):
        EMAIL_SENDER_USER = 'naitce@gmail.com'
        EMAIL_SENDER_PWD = 'chaoem12@'
        fromaddr = EMAIL_SENDER_USER
        password = EMAIL_SENDER_PWD
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = subject
        body = message
        msg.attach(MIMEText(body, 'HTML'))
        try:
            logging.info('sending mail to %s on %s', toaddr, subject)
            mailServer = smtplib.SMTP('smtp.gmail.com', 587)
            mailServer.ehlo()
            mailServer.starttls()
            mailServer.ehlo()
            mailServer.login(fromaddr, password)
            mailServer.sendmail(fromaddr, toaddr, msg.as_string())
            mailServer.close()
        except Exception as e:
            logging.info(str(e))

