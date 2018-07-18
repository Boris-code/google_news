import sys
sys.path.append('..')
import init

import base.base_parser as base_parser
from magic_google.magic_google import MagicGoogle
import utils.tools as tools
from utils.log import log
from extractor.article_extractor import ArticleExtractor
import base.constance as Constance
import parsers.base_parser as self_base_parser
import random

SITE_ID = 1712150002
NAME = 'google新闻'

mg = MagicGoogle()
MIN_SLEEP_TIME = 30 # 请求google的睡眠时间
MAX_SLEEP_TIME = 60


# 必须定义 添加网站信息
@tools.run_safe_model(__name__)
def add_site_info():
    log.debug('添加网站信息')

    table = 'google_news_site_info'
    url = 'http://news.baidu.com'

    base_parser.add_website_info(table, site_id=SITE_ID, url=url, name=NAME)


# 必须定义 添加根url
@tools.run_safe_model(__name__)
def add_root_url(keywords):
    log.debug('''
        添加根url
        parser_params : %s
        ''' % str(keywords))
    for keyword in keywords:
        log.debug('添加关键词' + keyword)
        base_parser.add_url('google_news_urls', SITE_ID, keyword)


# 必须定义 解析网址
def parser(url_info):
    url_info['_id'] = str(url_info['_id'])
    log.debug('处理 \n' + tools.dumps_json(url_info))

    root_url = url_info['url']
    depth = url_info['depth']
    site_id = url_info['site_id']

    # 获取搜索词比配到的url
    start = 0
    while True:
        urls = mg.search_url(query=root_url, num=50, start=start, pause=random.randint(MIN_SLEEP_TIME, MAX_SLEEP_TIME))
        if not urls:
            break

        for url in urls:
            url = url.replace('amp;', '')

            article_extractor = ArticleExtractor(url)
            content = title = release_time = author = website_domain =''
            content = article_extractor.get_content()
            if content:
                title = article_extractor.get_title()
                release_time = article_extractor.get_release_time()
                author = article_extractor.get_author()
                website_domain = tools.get_domain(url)
                uuid = tools.get_uuid(title, website_domain)
                website_name = ''
                website_position = 35 # 境外

                log.debug('''
                    uuid         %s
                    title        %s
                    author       %s
                    release_time %s
                    domain       %s
                    url          %s
                    content      %s
                    '''%(uuid, title, author, release_time, website_domain, url, '...'))

                # 入库
                if tools.is_have_chinese(content):
                    is_continue = self_base_parser.add_news_acticle(uuid, title, author, release_time, website_name , website_domain, website_position, url, content)

                    if not is_continue:
                        break
        else:
            # 循环正常结束 该页均正常入库， 继续爬取下页
            start += 50

    base_parser.update_url('google_news_urls', root_url, Constance.DONE)