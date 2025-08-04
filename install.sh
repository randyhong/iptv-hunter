#!/bin/sh

# 跨平台安装脚本
# 支持 Ubuntu/CentOS/macOS 等系统
# 自动检测并安装依赖，然后调用 install.py

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
${BLUE}IPTV Hunter 跨平台安装脚本${NC}

${YELLOW}用法:${NC}
    $0 [选项]

${YELLOW}选项:${NC}
    --help, -h              显示此帮助信息
    --force                 强制重新安装
    --skip-deps             跳过依赖安装
    --python-version <版本> 指定Python版本 (如: 3.8, 3.9, 3.10, 3.11, 3.12)

${YELLOW}支持的系统:${NC}
    - Ubuntu/Debian
    - CentOS/RHEL/Fedora
    - macOS
    - Alpine Linux
    - 其他基于Linux的系统

${YELLOW}示例:${NC}
    $0                    # 自动检测并安装
    $0 --force           # 强制重新安装
    $0 --python-version 3.11  # 指定Python版本

EOF
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="$ID"
        OS_VERSION="$VERSION_ID"
        OS_PRETTY="$PRETTY_NAME"
    elif [ -f /etc/redhat-release ]; then
        OS_NAME="rhel"
        OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
        OS_PRETTY=$(cat /etc/redhat-release)
    elif [ "$(uname)" = "Darwin" ]; then
        OS_NAME="macos"
        OS_VERSION=$(sw_vers -productVersion)
        OS_PRETTY="macOS $OS_VERSION"
    else
        OS_NAME="unknown"
        OS_VERSION="unknown"
        OS_PRETTY="Unknown OS"
    fi
    
    log_info "检测到系统: $OS_PRETTY"
}

# 检测Python版本
detect_python() {
    if command -v python3 > /dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
        log_info "检测到Python: $PYTHON_VERSION"
        return 0
    else
        log_error "未检测到Python3"
        return 1
    fi
}

# 检查是否需要安装Python
check_python() {
    if ! detect_python; then
        log_warn "需要安装Python3"
        install_python
    fi
}

# 安装Python (Ubuntu/Debian)
install_python_ubuntu() {
    log_info "在Ubuntu/Debian上安装Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv python3-dev
    
    # 如果指定了特定版本
    if [ -n "$PYTHON_VERSION_SPECIFIED" ]; then
        sudo apt install -y "python$PYTHON_VERSION_SPECIFIED" "python$PYTHON_VERSION_SPECIFIED-venv"
    fi
}

# 安装Python (CentOS/RHEL/Fedora)
install_python_centos() {
    log_info "在CentOS/RHEL/Fedora上安装Python3..."
    
    # 检查是否为CentOS 8+ 或 RHEL 8+
    if [ "$OS_NAME" = "rhel" ] || [ "$OS_NAME" = "centos" ]; then
        if [ -n "$OS_VERSION" ] && [ "$(echo "$OS_VERSION >= 8" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
            # CentOS 8+ 使用 dnf
            sudo dnf install -y python3 python3-pip python3-devel
        else
            # 较老版本使用 yum
            sudo yum install -y python3 python3-pip python3-devel
        fi
    else
        # Fedora 使用 dnf
        sudo dnf install -y python3 python3-pip python3-devel
    fi
}

# 安装Python (macOS)
install_python_macos() {
    log_info "在macOS上安装Python3..."
    
    if command -v brew > /dev/null 2>&1; then
        log_info "使用Homebrew安装Python3..."
        brew install python@3.11
    else
        log_warn "未检测到Homebrew，建议安装Homebrew:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "然后重新运行此脚本"
        exit 1
    fi
}

# 安装Python (Alpine)
install_python_alpine() {
    log_info "在Alpine Linux上安装Python3..."
    sudo apk add --no-cache python3 py3-pip python3-dev
}

# 安装Python
install_python() {
    case "$OS_NAME" in
        "ubuntu"|"debian")
            install_python_ubuntu
            ;;
        "centos"|"rhel"|"fedora"|"rocky"|"alma")
            install_python_centos
            ;;
        "macos")
            install_python_macos
            ;;
        "alpine")
            install_python_alpine
            ;;
        *)
            log_error "不支持的操作系统: $OS_NAME"
            log_info "请手动安装Python3"
            exit 1
            ;;
    esac
}

# 检查并安装系统依赖
install_system_deps() {
    log_info "检查系统依赖..."
    
    case "$OS_NAME" in
        "ubuntu"|"debian")
            log_info "安装Ubuntu/Debian依赖..."
            sudo apt update
            sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
            
            # 安装特定版本的venv包
            if [ -n "$PYTHON_VERSION_SPECIFIED" ]; then
                sudo apt install -y "python$PYTHON_VERSION_SPECIFIED-venv"
            else
                sudo apt install -y python3-venv
            fi
            ;;
        "centos"|"rhel"|"fedora"|"rocky"|"alma")
            log_info "安装CentOS/RHEL/Fedora依赖..."
            if [ -n "$OS_VERSION" ] && [ "$(echo "$OS_VERSION >= 8" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
                sudo dnf groupinstall -y "Development Tools"
                sudo dnf install -y openssl-devel libffi-devel python3-devel
            else
                sudo yum groupinstall -y "Development Tools"
                sudo yum install -y openssl-devel libffi-devel python3-devel
            fi
            ;;
        "macos")
            log_info "安装macOS依赖..."
            if command -v brew > /dev/null 2>&1; then
                brew install openssl libffi
            fi
            ;;
        "alpine")
            log_info "安装Alpine依赖..."
            sudo apk add --no-cache build-base openssl-dev libffi-dev
            ;;
    esac
}

# 检查虚拟环境
check_venv() {
    if [ -d "venv" ]; then
        if [ "$FORCE" = "true" ]; then
            log_warn "删除现有虚拟环境..."
            rm -rf venv
        else
            log_info "虚拟环境已存在"
            # 检查虚拟环境是否有效
            if [ -f "venv/bin/python" ] && [ -f "venv/bin/pip" ]; then
                log_info "虚拟环境有效"
                return 0
            else
                log_warn "虚拟环境可能损坏，重新创建..."
                rm -rf venv
            fi
        fi
    fi
    
    log_info "创建虚拟环境..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        log_error "创建虚拟环境失败"
        log_info "尝试安装venv包..."
        case "$OS_NAME" in
            "ubuntu"|"debian")
                sudo apt install -y python3-venv
                ;;
            "centos"|"rhel"|"fedora"|"rocky"|"alma")
                if [ -n "$OS_VERSION" ] && [ "$(echo "$OS_VERSION >= 8" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
                    sudo dnf install -y python3-venv
                else
                    sudo yum install -y python3-venv
                fi
                ;;
            "macos")
                if command -v brew > /dev/null 2>&1; then
                    brew install python@3.11
                fi
                ;;
        esac
        
        # 重试创建虚拟环境
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            log_error "创建虚拟环境失败，请手动安装python3-venv包"
            exit 1
        fi
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    # 激活虚拟环境
    . venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        log_warn "未找到requirements.txt文件"
    fi
}

# 运行install.py
run_install_py() {
    log_info "运行install.py..."
    
    if [ -f "install.py" ]; then
        . venv/bin/activate
        python install.py
    else
        log_warn "未找到install.py文件"
    fi
}

# 显示安装完成信息
show_completion() {
    log_success "安装完成!"
    echo
    echo "🎉 IPTV Hunter 已成功安装"
    echo
    echo "📋 下一步操作:"
    echo "  1. 运行程序: ./start.sh"
    echo "  2. 查看帮助: ./start.sh --help"
    echo "  3. 激活虚拟环境: . venv/bin/activate"
    echo "  4. 运行Python脚本: python run.py --help"
    echo
    echo "📁 重要文件:"
    echo "  - 配置文件: config/channels.yaml"
    echo "  - 输出目录: output/"
    echo "  - 日志目录: logs/"
    echo
    echo "🔧 如果遇到问题，请查看:"
    echo "  - README.md - 使用指南"
    echo "  - docs/USAGE.md - 详细文档"
}

# 主函数
main() {
    # 默认值
    FORCE="false"
    SKIP_DEPS="false"
    PYTHON_VERSION_SPECIFIED=""
    
    # 解析命令行参数
    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --force)
                FORCE="true"
                shift
                ;;
            --skip-deps)
                SKIP_DEPS="true"
                shift
                ;;
            --python-version)
                PYTHON_VERSION_SPECIFIED="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║        IPTV Hunter 安装脚本           ║"
    echo "║        跨平台自动安装工具             ║"
    echo "╚═══════════════════════════════════════╝"
    echo "${NC}"
    
    # 检测操作系统
    detect_os
    
    # 检查Python
    if [ "$SKIP_DEPS" != "true" ]; then
        check_python
        install_system_deps
    fi
    
    # 检查虚拟环境
    check_venv
    
    # 安装Python依赖
    install_python_deps
    
    # 运行install.py
    run_install_py
    
    # 显示完成信息
    show_completion
}

# 运行主函数
main "$@" 