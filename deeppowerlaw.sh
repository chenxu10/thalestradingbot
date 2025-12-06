#!/bin/bash

# 检查参数
if [ $# -ne 2 ]; then
    echo "Usage: $0 <python_repo_path> <function_length>"
    echo "Example: $0 ./my_project 74"
    exit 1
fi

REPO_PATH="$1"
TARGET_LENGTH="$2"

# 检查目录是否存在
if [ ! -d "$REPO_PATH" ]; then
    echo "Error: Directory $REPO_PATH does not exist"
    exit 1
fi

echo "Searching for functions with exactly $TARGET_LENGTH lines in: $REPO_PATH"
echo "================================================================================"
echo ""

# 创建一个Python脚本来解析Python文件
PYTHON_PARSER=$(mktemp)
cat > "$PYTHON_PARSER" << 'EOF'
#!/usr/bin/env python3
import ast
import sys
import os

def analyze_file(filepath, target_length):
    """分析单个Python文件，查找指定长度的函数"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        tree = ast.parse(content)
        
        # 读取所有行以便计算行号
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 获取函数起始行号（AST行号从1开始）
                start_line = node.lineno - 1  # 转换为0-based索引
                
                # 获取函数体结束行号
                if node.body:
                    # 找到函数体最后一行
                    last_body_node = node.body[-1]
                    
                    # 如果是嵌套的复合语句，需要找到最深的行号
                    def get_last_line(node):
                        if hasattr(node, 'lineno'):
                            return node.lineno
                        elif hasattr(node, 'body') and node.body:
                            return get_last_line(node.body[-1])
                        elif hasattr(node, 'orelse') and node.orelse:
                            return get_last_line(node.orelse[-1])
                        elif hasattr(node, 'finalbody') and node.finalbody:
                            return get_last_line(node.finalbody[-1])
                        else:
                            return node.lineno if hasattr(node, 'lineno') else start_line + 1
                    
                    end_line = get_last_line(last_body_node) - 1  # 转换为0-based
                else:
                    # 空函数体
                    end_line = start_line
                
                # 计算函数长度（包括def行）
                function_length = end_line - start_line + 1
                
                if function_length == target_length:
                    # 获取相对路径
                    rel_path = os.path.relpath(filepath, sys.argv[1])
                    print(f"{function_length:6d} {rel_path:60s} {node.name} (lines {start_line+1}-{end_line+1})")
    
    except (SyntaxError, UnicodeDecodeError) as e:
        # 忽略语法错误或编码问题的文件
        pass
    except Exception as e:
        # 其他错误也忽略
        pass

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python_parser.py <repo_path> <filepath> <target_length>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    filepath = sys.argv[2]
    target_length = int(sys.argv[3])
    
    analyze_file(filepath, target_length)
EOF

# 使Python脚本可执行
chmod +x "$PYTHON_PARSER"

# 查找所有Python文件并分析
find "$REPO_PATH" -name "*.py" -type f | while read -r pyfile; do
    python3 "$PYTHON_PARSER" "$REPO_PATH" "$pyfile" "$TARGET_LENGTH"
done

# 清理临时文件
rm -f "$PYTHON_PARSER"

echo ""
echo "================================================================================"
echo "Note: Used Python's AST parser for accurate function detection"
echo "================================================================================"