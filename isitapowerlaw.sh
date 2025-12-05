#!/bin/bash

# 检查是否提供了仓库路径
if [ $# -ne 1 ]; then
    echo "Usage: $0 <python_repo_path>"
    exit 1
fi

REPO_PATH="$1"

# 检查目录是否存在
if [ ! -d "$REPO_PATH" ]; then
    echo "Error: Directory $REPO_PATH does not exist"
    exit 1
fi

# 临时文件用于存储函数长度
TEMP_FILE=$(mktemp)

# 查找所有Python文件并统计函数长度
find "$REPO_PATH" -name "*.py" -type f | while read -r pyfile; do
    # 使用awk解析Python文件，统计函数长度
    # 注意：这个解析器假设标准缩进为4个空格，且函数定义没有装饰器等复杂情况
    awk '
    BEGIN {
        in_function = 0
        function_lines = 0
        bracket_count = 0
        prev_indent = 0
        current_indent = 0
    }
    
    /^[[:space:]]*def[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(/ {
        # 如果已经在函数中，保存前一个函数的长度
        if (in_function && function_lines > 0) {
            print function_lines
        }
        
        # 开始新函数
        in_function = 1
        function_lines = 1  # 包括def这一行
        
        # 计算当前行的缩进
        match($0, /^[[:space:]]*/)
        prev_indent = RLENGTH
        bracket_count = 0
        
        # 检查def行是否以冒号结束
        if (/:\s*$/) {
            # 简单情况：def行以冒号结束
            next
        } else {
            # 处理括号可能跨行的情况
            bracket_count = gsub(/\(/, "&") - gsub(/\)/, "&")
            if (bracket_count > 0) {
                # 括号未闭合，继续读取直到找到冒号
                while (getline next_line > 0) {
                    function_lines++
                    bracket_count += gsub(/\(/, "&", next_line) - gsub(/\)/, "&", next_line)
                    if (/:\s*$/ && bracket_count == 0) {
                        break
                    }
                }
            }
        }
        next
    }
    
    in_function {
        # 计算当前行的缩进
        match($0, /^[[:space:]]*/)
        current_indent = RLENGTH
        
        # 空行不增加函数行数（可选，根据需求调整）
        # if ($0 ~ /^[[:space:]]*$/) {
        #     next
        # }
        
        # 检查是否仍在同一函数内
        if (current_indent > prev_indent) {
            function_lines++
        } else {
            # 缩进回到def行或更少，函数结束
            if (function_lines > 0) {
                print function_lines
            }
            in_function = 0
            function_lines = 0
            
            # 检查当前行是否是新的函数定义
            if (/^[[:space:]]*def[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(/) {
                in_function = 1
                function_lines = 1
                prev_indent = current_indent
                bracket_count = 0
                
                # 检查def行是否以冒号结束
                if (!/:\s*$/) {
                    bracket_count = gsub(/\(/, "&") - gsub(/\)/, "&")
                }
            }
        }
    }
    
    END {
        # 处理最后一个函数
        if (in_function && function_lines > 0) {
            print function_lines
        }
    }
    ' "$pyfile"
done > "$TEMP_FILE"

# 统计分布并排序输出
echo "Function length distribution:"
sort -n "$TEMP_FILE" | uniq -c | awk '{print $2, $1}' | sort -n

# 可选：显示总计函数数量
TOTAL_FUNCTIONS=$(wc -l < "$TEMP_FILE")
echo "Total functions: $TOTAL_FUNCTIONS"

# 清理临时文件
rm -f "$TEMP_FILE"