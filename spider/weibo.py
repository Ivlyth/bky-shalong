# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 2019/5/13
Email  : email4myth at gmail.com
"""

from __future__ import unicode_literals

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import time

# 导入 splinter 的 Browser 对象
from splinter import Browser

# 导入 bs4 模块, 用于 html 文档结构化解析
import bs4

# 同目录下放置一个名为  weibo.password 的文件
# 第一行为登录用户名
# 第二行为登录密码
auth = open('weibo.password').readlines()
WEIBO_USERNAME = auth[0].strip()
WEIBO_PASSWORD = auth[1].strip()

# 想要监控的 ID
MONITOR_USER_ID = 'wflanker'
MONITOR_USER_ID = '314264602'
MONITOR_USER_ID = 'IoT141'

# 仔细研究一个指定用户的主页 URL
# weibo.com 域名后跟 用户 ID 即可访问其主页
# 会发现如果要查看其全部微博, 对应参数 is_all=1
MONITOR_USER_URL = 'https://weibo.com/%(user_id)s?is_all=1'


def login():
    '''
    该函数实现打开浏览器并模拟登录, 然后返回浏览器对象
    '''

    # 实例化一个浏览器对象
    browser = Browser('chrome')

    # 访问 weibo 主页
    browser.visit('https://weibo.com/')

    # 访问之后, 页面异步加载渲染, 我们要等待页面渲染完毕后开始操作
    # 这里我们通过检查 登录按钮是否存在来进行判断
    # 为了防止异常, 我们每秒检查1次, 最多检查10次
    for i in range(10):
        login_button = browser.find_by_css('#pl_login_form > div > div:nth-child(3) > div.info_list.login_btn > a')
        if not login_button.is_empty():
            print u'微博登录页面加载成功'
            break
        time.sleep(1)
    else:
        print u'访问微博页面超时'
        sys.exit(1)

    # 输入账户密码
    print u'输入账户中 ...'
    for _ in browser.type('username', WEIBO_USERNAME, slowly=True):
        time.sleep(0.05)

    print u'输入密码中 ...'
    for _ in browser.type('password', WEIBO_PASSWORD, slowly=True):
        time.sleep(0.05)

    # 点击登录按钮
    print u'点击登录 ...'
    login_button.first.click()

    # 等待登录完成
    # 这里我们通过循环等待 页面标题 变化来实现这个效果
    for i in range(10):
        t = browser.title
        # 仔细观察, 登录后进入到个人主页, 页面标题会改变
        # 因此我们可以以这个特征来判定是否登录成功
        if t.strip().startswith(u'我的首页'):
            print u'登录成功'
            break
        time.sleep(1)
    else:
        print u'登录超时'
        sys.exit(3)

    return browser


def start_monitor_user(browser):
    if not MONITOR_USER_ID:
        while True:
            user_id = raw_input('please type user id you want to monitor: ')
            if not user_id:
                continue
            break
    else:
        user_id = MONITOR_USER_ID

    # 根据给定的 用户 ID, 直接访问其主页对应的 URL
    browser.visit(MONITOR_USER_URL % {'user_id': user_id})

    # 通过 css 选择器选中好友元素, 查看其好友(关注)数
    frients_element = browser.find_by_css('#Pl_Core_T8CustomTriColumn__3 > div > div > div > table > tbody > tr > td:nth-child(1) > a > strong')
    # 选中元素后, 通常先判断选中元素是否为空
    # 防止因对方网站结构变化导致的 css 元素选择器失效而产生的异常
    if not frients_element.is_empty():
        frients_count = frients_element.first.text
        print '%s has %s friends' % (user_id, frients_count)

    # 通过 css 选择器选中粉丝元素, 查看其粉丝数
    followers_element = browser.find_by_css('#Pl_Core_T8CustomTriColumn__3 > div > div > div > table > tbody > tr > td:nth-child(2) > a > strong')
    if not followers_element.is_empty():
        followers_count = followers_element.first.text
        print '%s has %s followers' % (user_id, followers_count)

    # 通过 css 选择器选中 微博数 元素, 查看其微博数量
    weibo_elements = browser.find_by_css('#Pl_Core_T8CustomTriColumn__3 > div > div > div > table > tbody > tr > td:nth-child(3) > a > strong')
    if not weibo_elements.is_empty():
        weibo_count = weibo_elements.first.text
        print '%s has %s weibo' % (user_id, weibo_count)
        try:
            weibo_count = int(weibo_count)
        except:
            weibo_count = 0
    else:
        weibo_count = 0

    # 如果微博数 > 0, 则进一步获取其最近一个的微博 ID
    if weibo_count > 0:
        for i in range(3):
            # 通过 css 选择器定位最近一条微博 (微博信息流的第一个)
            latest_weibo = browser.find_by_xpath('//*[@class="WB_feed WB_feed_v3 WB_feed_v4"]/div[2]')
            print 'current weibo content is: '
            print latest_weibo.first.find_by_css('.WB_text.W_f14').first.text
            s = bs4.BeautifulSoup(latest_weibo.first.outer_html, 'lxml')
            latest_mid = s.div.attrs.get('mid')  # 最新的微博 ID?
            break
        else:
            print u'获取用户最新微博失败 ...'
            latest_mid = None
    else:
        latest_mid = None

    print 'start to monitor user - %s' % user_id

    monitor_count = 0
    while True:
        # 刷新当前页面
        browser.reload()
        # 并等待 10s 中, 等待页面加载完毕
        time.sleep(10)

        # 使用 css 元素选择器来定位最上边的一条微博
        new_weibo = browser.find_by_xpath('//*[@class="WB_feed WB_feed_v3 WB_feed_v4"]/div[2]')
        if new_weibo.is_empty():
            continue

        # 使用 bs4 来结构化解析微博元素块的内容
        s = bs4.BeautifulSoup(new_weibo.first.outer_html, 'lxml')

        # 经过仔细观察, mid 属性类似于一个 微博ID, 唯一
        new_mid = s.div.attrs.get('mid')

        # 通过比较最新的 mid 于 上一次的 mid 是否相同来判断是否发了新微博
        if new_mid != latest_mid:
            print ''
            print 'find a new weibo for user %s' % user_id
            print new_weibo.first.find_by_css('.WB_text.W_f14').first.text
            latest_mid = new_mid
            monitor_count += 1
            if monitor_count >= 3:
                print 'shutdown the monitor ...'
                break
            else:
                print 'continue to monitor ...'


def main():
    browser = login()
    start_monitor_user(browser)
    browser.quit()


if __name__ == '__main__':
    sys.exit(main())
