##### bky-share



注意️: 本教程代码使用 python2.7 开发


1. fabric demo

1.1 安装, 仅依赖 fabric, 小于 2.0 的版本均可

```sh
pip install 'fabric<2'
```

1.2 使用

```python
# 简单用法
python fabrun.py -t 1.1.1.1,2.2.2.2 -u USER -p PASS command

# 命令可以带参数
python fabrun.py -t 1.1.1.1,2.2.2.2 -u USER -p PASS 'command with args'

# 指定一个文件, 一行一个 IP
python fabrun.py -t FILE -u USER -p PASS 'command with args'
```

2. splinter demo

2.1 安装

首先需要使用 splinter 库

```sh
pip install splinter
```

然后需要安装 chromedriver, chromedriver 的版本号于 Chrome 浏览器对应,
因此先查看本机的 chrome 版本, 然后访问:

http://chromedriver.chromium.org/downloads

下载对应的 chromedriver, 下载的可执行文件放入到 PATH 环境变量包含的路径下即可使用

2.2 使用

```
# 1. 在 spider 目录下创建文件  weibo.password, 第一行为自己的微博账号, 第二行为密码

# 2. 修改代码中的 MONITOR_USER_ID 为自己想要监控的账号, 或者自己的用来测试

# 3. 运行脚本

python weibo.py

```