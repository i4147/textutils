# database to text

数据库结构等导出到文本的工具。

可以用来对数据库结构进行比较，检查变更，做版本控制等工作。

也可以用来根据数据库结构自动生成文档，自动更新源代码等。

# 使用方法

## 安装

使用pip install db2text即可安装执行。注意这个工具在linux下开发调试，在windows使用如果有异常，请告知我。

## 使用

在命令行执行dbt即可。可以带参数指定命令文件，如果未指定，则使用当前目录下的dbt.txt文件。

如果dbt跟系统内其它软件冲突，可以使用db2text，效果是相同的。

详细的使用手册请参考

https://gitee.com/chenc224/dbt/blob/master/database2text/datafile/dbtmanual.md
