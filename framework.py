"""web框架：专门处理动态资源请求"""
import time
import pymysql
import json
import logging

# 路由列表，每一条记录都一是一个路由，请求的资源与处理函数之间的映射
# 可以手动添加，但比较麻烦，利用装饰器添加后续比较简单
route_list = [
    # ("/index.html", index),
    # ("/center.html", center),
]


# 利用装饰器方式给路由列表添加路由
def add_route(path):
    def decorator(func):
        # 执行装饰器的时候添加路由，装饰器只会执行一次
        route_list.append((path, func))

        def inner():
            result = func()
            return result
        return inner
    return decorator


@add_route("/index.html")
def index():
    # 获取首页数据
    status = '200 OK'
    # 一个元组代表一行响应头信息，后面可以拓展多个信息，往列表继续添加即可
    header = [("Server", "PWS/1.1")]
    # 1.打开指定的模板文件，读取模板文件里的数据
    with open("template/index.html", 'r', encoding='utf-8') as file:
        file_data = file.read()

    # 2.查询数据库，把模板文件里的变量替换成数据库里查询的数
    conn = pymysql.connect(host="192.168.117.128",
                           port=3306,
                           user="root",
                           passwd="123456",
                           database="stock_db",
                           charset="utf8")
    cursor = conn.cursor()
    sql = "SELECT * FROM info;"
    cursor.execute(sql)
    result = cursor.fetchall()
    # print(result)

    cursor.close()
    conn.close()

    data = ""

    # 下面的操作应该是前端人员的操作，这种响应方式是前后端不分离，后端人员进行拼接
    # 前后端分离：前端人员使用ajax，利用后端人员提供的数据接口进行刷新网页数据
    for row in result:
        data += """<tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td><input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="000007"></td>
                </tr>""" % row

    response_body = file_data.replace("{%content%}", data)

    # 默认多返回值返回的是一个元组
    return status, header, response_body


# 个人中心数据接口，供其他开发人员使用
@add_route("/center_data.html")
def center_data():
    # 把数据库里的数据查询出来，然后转成json数据
    conn = pymysql.connect(host="192.168.117.128",
                           port=3306,
                           user="root",
                           passwd="123456",
                           database="stock_db",
                           charset="utf8")
    cursor = conn.cursor()
    sql = """
            select i.code, i.short, i.chg, i.turnover, i.price, i.highs, f.note_info 
            from info i inner join focus f on i.id = f.info_id;
            """

    cursor.execute(sql)
    result = cursor.fetchall()
    # 把result元组转化为列表字典
    center_data_list = [{
        "code": row[0],
        "short": row[1],
        "chg": row[2],
        "turnover": row[3],
        "price": str(row[4]),
        "highs": str(row[5]),
        "note_info": row[6]
      } for row in result]

    # ensure_ascii 如果想让在控制台正常显示中文，就指定false
    json_str = json.dumps(center_data_list, ensure_ascii=False)
    # print(json_str)
    # print(type(json_str))

    cursor.close()
    conn.close()

    status = '200 OK'
    # 一个元组代表一行响应头信息，后面可以拓展多个信息，往列表继续添加即可
    # 因为返回给浏览器的json数据没有模板，没有指定内容格式，所以为了在浏览器上能正常显示，需要在响应头里指定相应格式
    header = [("Server", "PWS/1.1"), ("Content-Type", "text/html;charset=utf-8")]
    return status, header, json_str


@add_route("/center.html")
def center():
    # 获取首页数据
    status = '200 OK'
    # 一个元组代表一行响应头信息，后面可以拓展多个信息，往列表继续添加即可
    header = [("Server", "PWS/1.1")]
    # 1.打开指定的模板文件，读取模板文件里的数据
    with open("template/center.html", 'r', encoding='utf-8') as file:
        file_data = file.read()

    # 前后端分离方式：
    # 后端直接返回空模板给浏览器，前端再使用ajax请求刷新网页数据
    response_body = file_data.replace("{%content%}","")

    # 默认多返回值返回的是一个元组
    return status, header, response_body


def not_found():
    # 获取首页数据
    status = '404 Not Found'
    # 一个元组代表一行响应头信息，后面可以拓展多个信息，往列表继续添加即可
    header = [("Server", "PWS/1.1")]
    data = "not found"

    # 默认多返回值返回的是一个元组
    return status, header, data


def handle_request(env):
    # 获取动态资源请求路径
    request_path = env["request_path"]
    # print(request_path)

    for path, func in route_list:
        if request_path == path:
            # 找到了指定的路由
            result = func()
            return result
    else:
        logging.error("没有配置相应的路由信息：" + request_path)
        result = not_found()
        return result

    # if request_path == '/index.html':
    #     result = index()
    #     return result
    # elif request_path == '/center.html':
    #     result = center()
    #     return result
    # else:
    #     # 没有动态资源数据
    #     result = not_found()
    #     return result