# 测试正则文件加载功能
import yaml

try:
    with open('test-rules.yml', 'r', encoding='utf-8') as f:
        rules = yaml.safe_load(f)
        print('成功加载rules.yml文件，共', len(rules), '条规则')
        for rule_name, rule_pattern in rules.items():
            print(f'规则名: {rule_name}')
            print(f'规则模式: {rule_pattern}')
            print('-' * 50)
except Exception as e:
    print(f'加载rules.yml文件失败: {type(e).__name__}: {e}')