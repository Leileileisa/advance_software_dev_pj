# advance_software_dev_pj
高级软件开发微服务项目

运行微服务命令,在代码主目录的cmd里输入docker-compose up -d
演示之前先正常开启微服务，然后运行以下命令：
     curl "localhost:6001/register?department=coder&name=leisa1"
     curl "localhost:6001/register?department=coder&name=leisa2"
这里主要是为了生成db文件。
然后杀掉所有微服务，把三个app.py里最下面的init_db()注释掉，之后重新运行docker-compose up -d，开始演示


## 测试场景
### 场景1: （70%）
1. 在【员工管理系统】中注册新员工
2. 使用新员工的ID和初始密码可以在【用户管理系统】成功认证（调用login返回success或fail即可）
3. 使用新员工ID可以从【任务管理系统】中获取员工的任务，含状态。此时应该有一条处于未完成状态的初始化密码的任务。
4. 通过【用户管理系统】可以更新用户密码。
5. 成功更新密码后，【任务管理系统】中相应的任务状态变为完成

### 场景2:（20%）
1. 将【用户管理系统】和【任务管理系统】服务停止
2. 在【员工管理系统】中注册新员工
3. 启动【用户管理系统】和【任务管理系统】服务
4. 验证场景1中2至5的步骤

### 场景3: （10%）
1. 可以通过【某个服务】查询获取部门任务完成情况统计报表：例如部门1:10件; 部门2:5。
2. 员工可以更换部门，完成跟换部门操作后，上诉报表需要能够正确反映结果。


如果觉得使用微服务架构难度过大，三个子系统可以使用同一个数据库，只需要完成场景1，基准分为70%。

## 提交内容
1. 源程序，含Dockerfile, docker-compose.yml等。
2. 10分钟演示上述场景的视频，对于场景3，需简单解释一下实现的方法。

下面为演示内容，按照顺序输入即可
## 场景1
##### 查看员工，用户，任务系统数据
     curl "localhost:6001/see"
     curl "localhost:6002/see"
     curl "localhost:6003/see"
##### 注册用户
     curl "localhost:6001/register?department=finance&name=Linda"
     curl "localhost:6001/register?department=finance&name=刘敏"
     curl "localhost:6001/register?department=test&name=王红"
     curl "localhost:6001/register?department=test&name=周知"
     curl "localhost:6001/register?department=product&name=吴三"
     curl "localhost:6001/register?department=product&name=张敏"
     curl "localhost:6001/register?department=product&name=李三"
     curl "localhost:6001/register?department=product&name=金敏"
     curl "localhost:6001/register?department=design&name=赵思"
     curl "localhost:6001/register?department=design&name=沈斯"
     curl "localhost:6001/register?department=design&name=刘月"
## 场景2
##### 在docker-desktop中停止task_management和user_management
     curl "localhost:6002/see"
     curl "localhost:6003/see"
     curl "localhost:6001/register?department=test&name=李四"
     curl "localhost:6001/see"
##### 在docker-desktop中恢复task_management和user_management
     curl "localhost:6002/see"
     curl "localhost:6003/see"
     curl "localhost:6002/login?id=4&password=wrong"
     curl "localhost:6002/login?id=4&password=123456"
     curl "localhost:6003/see"
     curl "localhost:6002/new_password?id=4&password=123456&new_password=leisa234"
     curl "localhost:6002/see"
     curl "localhost:6003/see"
## 场景3
     curl "localhost:6003/report"
     curl "localhost:6001/modify/Linda/design"
     curl "localhost:6003/report"