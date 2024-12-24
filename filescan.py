import os
import re
import yaml
import time
from tqdm import tqdm


def load_rules():
    with open('rules.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_config():
    with open('config.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def should_skip_file(file_path, exclude_suffixes):
    file_extension = os.path.splitext(file_path)[1].lstrip('.')
    return file_extension in exclude_suffixes


def scan_file(file_path, rules):
    rule_results = {rule_name: [] for rule_name in rules}
    with open(file_path, 'r', encoding='utf-8', errors='ignore', buffering=8192) as f:
        for line_num, line in enumerate(f, 1):
            for rule_name, rule_pattern in rules.items():
                matches = rule_pattern.finditer(line)
                for match in matches:
                    rule_results[rule_name].append((file_path, line_num, match.group()))
    return rule_results


def scan_directory(directory, rules, exclude_suffixes):
    all_rule_results = {rule_name: [] for rule_name in rules}
    file_count = sum([len(files) for _, _, files in os.walk(directory)])

    terminal_width = os.get_terminal_size().columns
    threshold_width = 100  
    ncols = min(terminal_width, threshold_width)

    with tqdm(total=file_count, desc='Scanning files', ncols=ncols) as pbar:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if should_skip_file(file_path, exclude_suffixes):
                    pbar.update(1)
                    continue
                file_rule_results = scan_file(file_path, rules)
                for rule_name in rules:
                    all_rule_results[rule_name].extend(file_rule_results[rule_name])
                pbar.update(1)
    return all_rule_results

def write_results_to_file(results, output_file, base_dir):
    print(f"结果输出到目标文件：{output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for rule_name in results:
            f.write(f"规则名：{rule_name}\n")
            for file_path, line_num, match_content in results[rule_name]:
                relative_path = os.path.relpath(file_path, base_dir)
                f.write(f"{rule_name}:文件路径：{relative_path}  行号：{line_num}  匹配到的内容：{match_content}\n")
            f.write("\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='文件内容敏感信息扫描工具')
    parser.add_argument('-d', '--directory', required=True, help='指定要扫描的目录')
    parser.add_argument('-o', '--output_file', required=True, help='指定输出日志文件')
    args = parser.parse_args()

    start_time = time.time()
    print("程序开始运行...")

    rules = load_rules()
    compiled_rules = {rule_name: re.compile(rule_pattern) for rule_name, rule_pattern in rules.items()}
    config = load_config()
    exclude_suffixes = config.get('excludeSuffix', '').split('|')

    results = scan_directory(args.directory, compiled_rules, exclude_suffixes)
    write_results_to_file(results, args.output_file, args.directory)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"程序运行结束，总运行时间: {total_time:.2f} 秒")

if __name__ == "__main__":
    main()