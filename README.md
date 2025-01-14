# FileScan-敏感信息扫描工具

## 一、项目概述
该脚本是一个用于检测代码文件中敏感信息泄露的工具。它能够扫描指定目录下的文件，识别并报告诸如内网IP、邮箱、公民身份信息、各种Key等多种敏感信息。


## 二、功能特点
1. **多类型敏感信息检测**：支持检测多种常见的敏感信息，如数据库连接信息、云服务凭证、加密密钥、第三方API密钥等，具体可检测的信息类型及对应的正则表达式在代码中定义。
2. **可配置性**：通过 `rules.yml` 和 `config.yml` 配置文件，用户可以灵活定义检测规则和排除的文件后缀等配置项。
3. **进度展示**：使用 `tqdm` 库展示扫描进度，让用户实时了解扫描进展。
4. **结果输出**：扫描结果按照规则名分类输出，每个匹配结果包含规则名、文件相对路径、行号以及匹配到的内容，输出到指定的日志文件中。

## 三、使用方法
1. **准备配置文件**：
    - 在项目根目录下准备 `rules.yml` 文件，定义敏感信息的检测规则，每个规则由规则名和对应的正则表达式组成。
    - 准备 `config.yml` 文件，可在其中配置需要排除扫描的文件后缀，格式为以 `|` 分隔的字符串。
2. **运行脚本**：
    - 确保已经安装了脚本所需的依赖库，如 `yaml`、`tqdm` 等。可以使用 `pip install -r requirements.txt` 安装。
    - 运行命令：`python filescan.py -d <directory> -o <output_file>`
    - `-d` 参数指定要扫描的目录，绝对路径。
    - `-o` 参数指定输出日志文件的路径。

示例：

运行命令：
```bash
python filescan.py -d target_directory -o scan_results.log
```
扫描完成后，`scan_results.log` 文件将包含按规则分类的敏感信息匹配结果。

## 四、项目结构
1. **脚本文件**：`filescan.py` 是主脚本文件，包含加载配置、扫描文件、结果输出等主要功能。
2. **配置文件**：
    - `rules.yml`：定义敏感信息检测规则。
    - `config.yml`：配置排除扫描的文件后缀等项目。

## 五、贡献指南
1. **问题反馈**：如果在使用过程中发现任何问题或有任何建议，欢迎在项目的Issues页面提交。
