import os
import re
import yaml
import time
from tqdm import tqdm

#configPath=os.path.expanduser('~/.config/filescan/')
configPath=os.path.dirname(os.path.abspath(__file__))+'/'
print('配置文件路径:',configPath)

def load_rules():
    with open(configPath+'rules.yml', 'r', encoding='utf-8') as f:
        rules = yaml.safe_load(f)
        compiled_rules = {}
        
        for rule_name, rule_content in rules.items():
            if isinstance(rule_content, list):
                compiled_rules[rule_name] = [re.compile(pattern) for pattern in rule_content]
            else:
                compiled_rules[rule_name] = re.compile(rule_content)
                
        return compiled_rules


def load_config():
    with open(configPath+'config.yml', 'r', encoding='utf-8') as f:
        raw_config = yaml.safe_load(f)

    # 处理排除的后缀
    exclude_config = raw_config.get('excludeSuffix', [])
    exclude_suffixes = []
    if isinstance(exclude_config, str):
        exclude_suffixes = exclude_config.split('|') if exclude_config else []
    elif isinstance(exclude_config, list):
        for item in exclude_config:
            if isinstance(item, str):
                exclude_suffixes.extend(item.split('|'))
    #print('exclude_suffixes:',exclude_suffixes)
    
    # 处理包含的后缀
    include_config = raw_config.get('includeSuffix', [])
    include_suffixes = []
    if isinstance(include_config, str):
        include_suffixes = include_config.split('|') if include_config else []
    elif isinstance(include_config, list):
        # 处理列表中的每个元素，每个元素可能包含用|分隔的多个后缀
        for item in include_config:
            if isinstance(item, str):
                include_suffixes.extend(item.split('|'))
    #print('include_suffixes:',include_suffixes)
    return {
        'exclude_suffixes': exclude_suffixes,
        'include_suffixes': include_suffixes
    }


def should_skip_file(file_path, exclude_suffixes, include_suffixes):
    file_extension = os.path.splitext(file_path)[1].lstrip('.')
    if include_suffixes and file_extension in include_suffixes:
        return False
    return file_extension in exclude_suffixes


def scan_file(file_path, rules):
    rule_results = {rule_name: [] for rule_name in rules}
    with open(file_path, 'r', encoding='utf-8', errors='ignore', buffering=8192) as f:
        for line_num, line in enumerate(f, 1):
            for rule_name, rule_pattern in rules.items():
                if isinstance(rule_pattern, list):
                    # 处理正则组
                    for pattern in rule_pattern:
                        matches = pattern.finditer(line)
                        for match in matches:
                            rule_results[rule_name].append((file_path, line_num, match.group()))
                else:
                    matches = rule_pattern.finditer(line)
                    for match in matches:
                        rule_results[rule_name].append((file_path, line_num, match.group()))
    return rule_results


def scan_directory(directory, rules, exclude_suffixes, include_suffixes):
    all_rule_results = {rule_name: [] for rule_name in rules}
    file_count = sum([len(files) for _, _, files in os.walk(directory)])

    terminal_width = os.get_terminal_size().columns
    threshold_width = 100  
    ncols = min(terminal_width, threshold_width)

    with tqdm(total=file_count, desc='Scanning files', ncols=ncols) as pbar:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if should_skip_file(file_path, exclude_suffixes, include_suffixes):
                    pbar.update(1)
                    continue
                file_rule_results = scan_file(file_path, rules)
                for rule_name in rules:
                    all_rule_results[rule_name].extend(file_rule_results[rule_name])
                pbar.update(1)
    return all_rule_results

def process_special_rules(results, compiled_rules):
    processed_results = {rule_name: matches.copy() for rule_name, matches in results.items()}
    
    # 处理Linkfinder规则，过滤条件：
    # 1. 过滤与 All URL重叠部分
    # 2. 移除匹配内容中最外层的单双引号
    if "Linkfinder" in processed_results:
        original_count = len(processed_results["Linkfinder"])
        
        
        filtered_matches = []
        for match in processed_results["Linkfinder"]:
            file_path = match[0]
            match_content = match[2]
            
            # 检查是否包含URL - 处理可能是规则组的情况
            contains_url = False
            if 'All URL' in compiled_rules:
                all_url_rule = compiled_rules['All URL']
                if isinstance(all_url_rule, list):
                    # 处理规则组
                    for pattern in all_url_rule:
                        if re.search(pattern, match_content):
                            contains_url = True
                            break
                else:
                    contains_url = bool(re.search(all_url_rule, match_content))
            
            if not contains_url :
                # 移除最外层的单双引号
                if (match_content.startswith('"') and match_content.endswith('"')) or (match_content.startswith("'") and match_content.endswith("'")):
                    match_content = match_content[1:-1]  
                    match = (file_path, match[1], match_content)
                    filtered_matches.append(match)
        
        processed_results["Linkfinder"] = filtered_matches
        filtered_count = len(filtered_matches)
        
    return processed_results

def write_results_to_file(results, output_file, level='simple'):
    switch = {
        '1': 'simple',
        '2': 'standard',
        '3': 'detailed'
    }
    level = switch.get(level, 'simple')

    print(f"结果输出到目标文件：{output_file}，输出级别：{level}")
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入统计信息
        total_matches = 0
        rule_stats = {}
        
        for rule_name in results:
            match_count = len(results[rule_name])
            rule_stats[rule_name] = match_count
            total_matches += match_count
            
        f.write(f"扫描统计信息：\n")
        f.write(f"总匹配数：{total_matches}\n")
        # for rule_name, count in rule_stats.items():
        #     f.write(f"{rule_name}：{count}个匹配\n")
        f.write("\n")
        
        if level == 'simple':
            output_lines = []
            for rule_name in results:
                if not results[rule_name]:
                    continue
                matches = results[rule_name]
                unique_contents = sorted({match[2] for match in matches})  # 去重+排序
                
                output_lines.append(f"规则名：{rule_name}")
                output_lines.extend(unique_contents)  
                output_lines.append("")  

            f.write('\n'.join(output_lines) + '\n')

        elif level == 'standard':
            for rule_name in results:
                f.write(f"\n规则名: {rule_name} 匹配结果：\n")
                for match in results[rule_name]:
                    f.write(f"{rule_name}: 文件路径：{match[0]}    行号：{match[1]}    匹配内容：{match[2]}\n")
        else:
            for rule_name in results:
                f.write(f"\n规则名: {rule_name} 匹配结果：\n")
                for match in results[rule_name]:
                    f.write(f"  {rule_name}:\n")
                    f.write(f"  文件路径：{match[0]}\n")
                    f.write(f"  行号：{match[1]}\n")
                    f.write(f"  匹配内容：{match[2]}\n")
                    f.write("\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='文件内容敏感信息扫描工具')
    parser.add_argument('-d', '--directory', required=True, help='指定要扫描的目录')
    parser.add_argument('-o', '--output_file', required=True, help='指定输出日志文件')
    parser.add_argument('-l', '--level', default='1', choices=['1', '2','3'], 
                        help='控制输出内容的丰富程度：1-simple(简单信息)、2-standard(标准信息)、3-detailed(详细信息)')
    args = parser.parse_args()

    try:
        start_time = time.time()
        print("程序开始运行...")

        compiled_rules = load_rules()
        config = load_config()
        exclude_suffixes = config['exclude_suffixes']
        include_suffixes = config['include_suffixes']
        #print(include_suffixes)

        results = scan_directory(args.directory, compiled_rules, exclude_suffixes, include_suffixes)
        # 对特定规则进行二次处理
        results = process_special_rules(results, compiled_rules)
        write_results_to_file(results, args.output_file, args.level)

        end_time = time.time()
        total_time = end_time - start_time
        print(f"程序运行结束，总运行时间: {total_time:.2f} 秒")
    except KeyboardInterrupt:
        print("\n程序已被用户中断 (Ctrl+C)")
        print("扫描过程已提前终止，部分结果可能未保存")
    except Exception as e:
        print(f"程序运行出错: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()