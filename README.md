# advance_software_dev_pj
高级软件开发微服务项目

运行微服务命令,在代码主目录的cmd里输入docker-compose up -d
演示之前先正常开启微服务，然后运行以下命令：
     curl "localhost:6001/register?department=coder&name=leisa1"
     curl "localhost:6001/register?department=coder&name=leisa2"
这里主要是为了生成db文件。
然后杀掉所有微服务，把三个app.py里最下面的init_db()注释掉，之后重新运行docker-compose up -d，开始演示

下面为演示内容，按照顺序输入即可
## 场景1
     curl "localhost:6001/see"
     curl "localhost:6002/see"
     curl "localhost:6003/see"
     curl "localhost:6001/register?department=coder&name=leisa3"
     curl "localhost:6001/see"
     curl "localhost:6002/login?id=3&password=wrong"
     curl "localhost:6002/login?id=3&password=123456"
     curl "localhost:6003/see"
     curl "localhost:6002/new_password?id=3&password=123456&new_password=leisa123"
     curl "localhost:6002/see"
     curl "localhost:6003/see"
## 场景2
     在docker-desktop中停止task_management和user_management
     curl "localhost:6001/register?department=coder&name=leisa4"
     curl "localhost:6001/see"
     在docker-desktop中恢复task_management和user_management
     curl "localhost:6002/see"
     curl "localhost:6003/see"
     curl "localhost:6002/login?id=4&password=wrong"
     curl "localhost:6002/login?id=4&password=123456"
     curl "localhost:6003/see"
     curl "localhost:6002/new_password?id=4&password=123456&new_password=leisa234"
     curl "localhost:6002/see"
     curl "localhost:6003/see"
## 场景3
     curl "localhost:6003/report?department=coder"
     curl "localhost:6003/report?department=leader"
     curl "localhost:6001/transfer?id=3&department=leader"
     curl "localhost:6003/report?department=coder"
     curl "localhost:6003/report?department=leader"