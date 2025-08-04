#!/bin/sh

# IPTV Hunter 一键启动脚本
# 作者: IPTV Hunter Team
# 版本: 1.0

set -e  # 遇到错误时退出

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_PATH="$PROJECT_ROOT/venv"
PYTHON_CMD="$VENV_PATH/bin/python"
MAIN_SCRIPT="$PROJECT_ROOT/src/main.py"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    printf "${GREEN}[INFO]${NC} %s\n" "$1"
}

log_warn() {
    printf "${YELLOW}[WARN]${NC} %s\n" "$1"
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}

log_success() {
    printf "${CYAN}[SUCCESS]${NC} %s\n" "$1"
}

# 显示帮助信息
show_help() {
    cat << EOF
${BLUE}IPTV Hunter 一键启动脚本${NC}

${YELLOW}用法:${NC}
    $0 [选项]

${YELLOW}选项:${NC}
    ${GREEN}模式选择:${NC}
    --mode <模式>           运行模式 (collect|check|generate|full|stats)
                            默认: full (完整流程)

    ${GREEN}频道选择:${NC}
    --channel <频道名>      指定单个频道 (如: CCTV1, 湖南卫视)
    --category <分类>       指定频道分类 (如: 央视, 卫视, 体育)

    ${GREEN}链接检测:${NC}
    --max-links <数量>      限制检测的链接数量 (默认: 不限制)
    --min-quality <分数>    最低质量评分 (0-100, 默认: 0)

    ${GREEN}输出设置:${NC}
    --output <路径>         自定义输出文件路径
    --format <格式>         输出格式 (m3u|json, 默认: m3u)

    ${GREEN}其他选项:${NC}
    --help, -h              显示此帮助信息
    --version, -v           显示版本信息
    --debug                 启用调试模式
    --force                 强制执行 (跳过确认)

${YELLOW}运行模式说明:${NC}
    ${CYAN}collect${NC}     仅收集频道链接
    ${CYAN}check${NC}       仅检测链接可用性
    ${CYAN}generate${NC}    仅生成播放列表
    ${CYAN}full${NC}        完整流程: 同步频道 -> 收集链接 -> 检测可用性 -> 生成播放列表
    ${CYAN}stats${NC}       显示统计信息

${YELLOW}示例:${NC}
    ${GREEN}# 完整流程 (默认)${NC}
    $0

    ${GREEN}# 仅收集央视频道链接${NC}
    $0 --mode collect --category 央视

    ${GREEN}# 检测特定频道并限制链接数量${NC}
    $0 --mode check --channel CCTV1 --max-links 50

    ${GREEN}# 生成JSON格式播放列表${NC}
    $0 --mode generate --format json --output ./my_playlist.json

    ${GREEN}# 调试模式运行完整流程${NC}
    $0 --debug

${YELLOW}支持的频道分类:${NC}
    央视, 卫视, 体育, 新闻, 电影, 音乐, 少儿, 纪录片等

${YELLOW}注意事项:${NC}
    - 首次运行请确保已安装依赖: pip install -r requirements.txt
    - 虚拟环境路径: $VENV_PATH
    - 配置文件: $PROJECT_ROOT/config/channels.yaml
    - 输出目录: $PROJECT_ROOT/output/

EOF
}

# 显示版本信息
show_version() {
    echo "IPTV Hunter 启动脚本 v1.0"
}

# 显示启动界面
show_banner() {
    cat << EOF
${BLUE}
╔═══════════════════════════════════════╗
║          IPTV Hunter 启动器           ║
║       一键管理IPTV频道列表           ║
╚═══════════════════════════════════════╝
${NC}
EOF
}

# 检查运行环境
check_environment() {
    log_info "检查运行环境..."
    
    # 检查Python3
    if ! command -v python3 > /dev/null 2>&1; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查虚拟环境
    if [ ! -f "$PYTHON_CMD" ]; then
        log_error "虚拟环境不存在: $VENV_PATH"
        log_warn "请运行以下命令创建虚拟环境:"
        echo "  python3 -m venv venv"
        echo "  . venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi

    # 检查主脚本
    if [ ! -f "$MAIN_SCRIPT" ]; then
        log_error "主脚本不存在: $MAIN_SCRIPT"
        exit 1
    fi

    # 创建必要目录
    mkdir -p "$PROJECT_ROOT/data" "$PROJECT_ROOT/logs" "$PROJECT_ROOT/output"

    log_success "环境检查通过"
}

# 构建命令
build_command() {
    local cmd="$PYTHON_CMD $MAIN_SCRIPT"
    
    case "$MODE" in
        "collect")
            cmd="$cmd collect"
            if [ -n "$CHANNEL" ]; then
                cmd="$cmd --channel $CHANNEL"
            fi
            if [ -n "$CATEGORY" ]; then
                cmd="$cmd --category $CATEGORY"
            fi
            ;;
        "check")
            cmd="$cmd check"
            if [ -n "$CHANNEL" ]; then
                cmd="$cmd --channel $CHANNEL"
            fi
            if [ -n "$CATEGORY" ]; then
                cmd="$cmd --category $CATEGORY"
            fi
            if [ -n "$MAX_LINKS" ]; then
                cmd="$cmd --max-links $MAX_LINKS"
            fi
            ;;
        "generate")
            cmd="$cmd generate"
            if [ -n "$OUTPUT" ]; then
                cmd="$cmd --output $OUTPUT"
            fi
            if [ -n "$CATEGORY" ]; then
                cmd="$cmd --category $CATEGORY"
            fi
            if [ -n "$MIN_QUALITY" ]; then
                cmd="$cmd --min-quality $MIN_QUALITY"
            fi
            if [ -n "$FORMAT" ]; then
                cmd="$cmd --format $FORMAT"
            fi
            ;;
        "stats")
            cmd="$cmd stats"
            ;;
        "full")
            cmd="$cmd run"
            ;;
        *)
            log_error "未知的运行模式: $MODE"
            exit 1
            ;;
    esac

    echo "$cmd"
}

# 执行命令
run_command() {
    local cmd
    cmd=$(build_command)
    
    log_info "执行命令: $cmd"
    
    if [ "$DEBUG" = "true" ]; then
        export LOG_LEVEL=DEBUG
        log_info "调试模式已启用"
    fi

    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT"
    
    # 执行命令
    if [ "$FORCE" = "true" ] || confirm_execution; then
        log_info "开始执行..."
        eval "$cmd"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            log_success "执行完成!"
            show_results
        else
            log_error "执行失败，退出代码: $exit_code"
            exit $exit_code
        fi
    else
        log_warn "用户取消执行"
        exit 0
    fi
}

# 确认执行
confirm_execution() {
    if [ "$MODE" = "full" ] && [ -z "$FORCE" ]; then
        echo
        log_warn "将执行完整更新流程，这可能需要较长时间："
        echo "  1. 同步频道配置"
        echo "  2. 收集所有频道链接"
        echo "  3. 检测链接可用性"
        echo "  4. 生成播放列表"
        echo
        printf "确定继续吗? [y/N]: "
        read -r reply
        echo
        case "$reply" in
            [Yy]*)
                return 0
                ;;
            *)
                return 1
                ;;
        esac
    else
        return 0
    fi
}

# 显示结果
show_results() {
    log_info "查看结果文件:"
    
    local output_dir="$PROJECT_ROOT/output"
    if [ -d "$output_dir" ]; then
        echo
        echo "📁 输出文件:"
        ls -la "$output_dir" 2>/dev/null || echo "  无输出文件"
    fi
}

# 显示运行信息
show_run_info() {
    echo
    log_info "运行信息:"
    echo "  模式: $MODE"
    echo "  项目路径: $PROJECT_ROOT"
    echo "  虚拟环境: $VENV_PATH"
    echo "  Python: $PYTHON_CMD"
    
    if [ -n "$CHANNEL" ]; then
        echo "  频道: $CHANNEL"
    fi
    
    if [ -n "$CATEGORY" ]; then
        echo "  分类: $CATEGORY"
    fi
    
    if [ -n "$MAX_LINKS" ]; then
        echo "  最大链接: $MAX_LINKS"
    fi
    
    if [ -n "$MIN_QUALITY" ]; then
        echo "  最低质量: $MIN_QUALITY"
    fi
    
    if [ -n "$OUTPUT" ]; then
        echo "  输出文件: $OUTPUT"
    fi
    
    if [ -n "$FORMAT" ]; then
        echo "  输出格式: $FORMAT"
    fi
    
    if [ "$DEBUG" = "true" ]; then
        echo "  调试模式: 启用"
    fi
    
    if [ "$FORCE" = "true" ]; then
        echo "  强制执行: 启用"
    fi
}

# 验证参数
validate_parameters() {
    # 验证MAX_LINKS
    if [ -n "$MAX_LINKS" ]; then
        case "$MAX_LINKS" in
            *[!0-9]*)
                log_error "MAX_LINKS 必须是数字: $MAX_LINKS"
                exit 1
                ;;
        esac
    fi
    
    # 验证MIN_QUALITY
    if [ -n "$MIN_QUALITY" ]; then
        case "$MIN_QUALITY" in
            *[!0-9]*)
                log_error "MIN_QUALITY 必须是数字: $MIN_QUALITY"
                exit 1
                ;;
        esac
    fi
}

# 主函数
main() {
    # 默认值
    MODE="full"
    CHANNEL=""
    CATEGORY=""
    MAX_LINKS=""
    MIN_QUALITY=""
    OUTPUT=""
    FORMAT=""
    DEBUG="false"
    FORCE="false"
    
    # 解析命令行参数
    while [ $# -gt 0 ]; do
        case "$1" in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --channel)
                CHANNEL="$2"
                shift 2
                ;;
            --category)
                CATEGORY="$2"
                shift 2
                ;;
            --max-links)
                MAX_LINKS="$2"
                shift 2
                ;;
            --min-quality)
                MIN_QUALITY="$2"
                shift 2
                ;;
            --output)
                OUTPUT="$2"
                shift 2
                ;;
            --format)
                FORMAT="$2"
                shift 2
                ;;
            --debug)
                DEBUG="true"
                shift
                ;;
            --force)
                FORCE="true"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --version|-v)
                show_version
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 显示启动界面
    show_banner
    
    # 验证参数
    validate_parameters
    
    # 显示运行信息
    if [ "$DEBUG" = "true" ]; then
        show_run_info
    fi
    
    # 检查环境
    check_environment
    
    # 执行命令
    run_command
}

# 运行主函数
main "$@"