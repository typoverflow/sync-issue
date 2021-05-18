# issue-sync
用于同步NJU.Git仓库的issue至Github仓库的脚本，使用Github Action定时运行

目前仅用作同步[LUG Joke Collection](https://git.nju.edu.cn/nju-lug/lug-joke-collection)仓库（需校园网）中的issues，路过的话不妨去原仓库看看。

## Usage
待填坑

## Update
+ 2021-05-19 00:45
  + 重写了代码结构，使用Issue类管理Issue相关的资源
  + 添加了同步图片的功能，目前使用的解决方案是上传到仓库里
  + 修正了issue顺序紊乱的问题

## TODO
+ [x] 修正issue的顺序
+ [x] 添加图片同步功能
+ [ ] 支持gitee