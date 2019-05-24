# -*- coding:utf8 -*-
"""
Author : Myth
Date   : 2019/5/13
Email  : email4myth at gmail.com
"""

from __future__ import unicode_literals, absolute_import

import sys

# 使用 utf-8 作为默认的字符编码, 取代默认的 ASCII
reload(sys)
sys.setdefaultencoding('utf-8')

# 从 fabric 导入我们需要用到的 API
from fabric.api import env, run, execute, hide, settings

# 使用内置的 argparse 模块来定义命令行参数
import argparse
import os

# 使用内置的 multiprocessing 提供的 Pool 对象来管理进程组
# 因为我们用进程并发模型来实现同时在多机上执行命令并回显
from multiprocessing import Pool

'''
一个简单的命令行工具, 读取一个配置文件, 获取目标IP地址及其账号密码, ssh 端口等信息, 然后进行登录并执行命令, 然后回显
'''


class ArgumentDefaultsHelpFormatter(argparse.HelpFormatter):
    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    if action.default is not None:
                        help += ' (default: %(default)s)'
        return help


def define_and_parse_args(args=None):
    '''
    定义一些命令行参数, 让该工具可以友好的交互使用
    :param args:
    :return:
    '''
    parser = argparse.ArgumentParser(prog="PROG", formatter_class=ArgumentDefaultsHelpFormatter)

    ############### Target
    target_group = parser.add_argument_group('Target')
    target_group.add_argument('-t', '--targets', action='append', help='目标机器 IP 列表')
    target_group.add_argument('-u', '--user', default='root', help='ssh 用户名')
    target_group.add_argument('-p', '--password', help='ssh 用户密码')
    target_group.add_argument('-P', '--port', type=int, default=22, help='ssh 端口')
    target_group.add_argument('-c', '--concurrency', type=int, default=8, help='目标机器并发执行数量')
    target_group.add_argument('-S', '--no-self', action='store_true', help='不在当前机器执行给定的命令')

    command_group = parser.add_argument_group('Command')
    command_group.add_argument('command', help='要执行的命令')

    options = parser.parse_args(args)

    if os.path.isfile('/etc/bky/target'):
        options.myip = open('/etc/bky/target').read().strip()
    else:
        options.myip = ''

    if not options.targets:
        if os.path.exists('/etc/ambot/targets'):
            options.targets = [t.strip() for t in open('/etc/ambot/targets').readlines() if t.strip()]
        else:
            parser.error('targets must be provide')
    elif len(options.targets) == 1 and os.path.isfile(os.path.realpath(options.targets[0])):
        options.targets = [t.strip() for t in open(os.path.realpath(options.targets[0])).readlines() if
                           t.strip() and not t.strip().startswith('#')]
    else:
        targets = []
        for ts in options.targets:
            for target in ts.split(','):
                target = target.strip()
                if not target:
                    continue
                if target.startswith('#'):
                    continue
                targets.append(target)
        options.targets = targets
    return options


def parallel_execute_function(target, command):
    try:
        # format command use target
        command = command % {'target': target}

        with settings(warn_only=True), hide('stdout', 'stderr', 'warnings', 'running', 'aborts'):
            run.return_value = ''
            rs = execute(run, host=target, command=command)

        return rs[target]
    except SystemExit:  # fabric api 出错的时候会使用 sys.exit 调用来退出当前进程, 因此可以通过捕获 SystemExit 错误来判定错误是否来自 fabric
        raise Exception('connection timeout')
    except KeyboardInterrupt: # 用户按了 CTRL+C
        raise Exception('user canceled')
    except Exception as e:  # 其他未知的异常
        raise Exception('error: %s' % e)


def main():
    options = define_and_parse_args()

    env.user = options.user
    if options.password:
        env.password = options.password
    env.port = options.port
    env.disable_known_hosts = True

    pool = Pool(options.concurrency)
    results = []

    for target in options.targets:
        if options.no_self and (options.myip and options.myip == target):
            continue
        try:
            results.append((target, pool.apply_async(parallel_execute_function, args=(target, options.command))))
        except KeyboardInterrupt:
            pass
        except Exception:
            pass

    try:
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print '\x1b[31muser canceled\x1b[0m'
        try:
            pool.terminate()
        except KeyboardInterrupt:
            pass
        except Exception:
            pass
        return
    except Exception as e:
        print '\x1b[31Error: %s\x1b[0m' % e
        return

    def get_result(async_ret):
        try:
            ret = async_ret.get()
            if ret.succeeded:
                return True, ret.stdout
            else:
                return False, ret.stderr or ret.stdout
        except KeyboardInterrupt:
            return False, 'action cancel by user'
        except Exception as e:
            return False, str(e)

    max_target_len = max([len(t) for t in options.targets])

    for target, async_ret in results:
        success, output = get_result(async_ret)
        multi_lines = len(output.splitlines()) > 1
        if success:
            print '[\x1b[32m%s\x1b[0m]%s%s' % (target.ljust(max_target_len), os.linesep if multi_lines else ' ', output)
        else:
            print '[\x1b[31m%s\x1b[0m]%s%s' % (target.ljust(max_target_len), os.linesep if multi_lines else ' ', output)


if __name__ == '__main__':
    main()
