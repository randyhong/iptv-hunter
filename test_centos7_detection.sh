#!/bin/sh

# 测试CentOS 7检测逻辑

echo "测试CentOS 7检测逻辑..."

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME="$ID"
    OS_VERSION="$VERSION_ID"
    OS_PRETTY="$PRETTY_NAME"
elif [ -f /etc/redhat-release ]; then
    OS_NAME="rhel"
    OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
    OS_PRETTY=$(cat /etc/redhat-release)
else
    OS_NAME="unknown"
    OS_VERSION="unknown"
    OS_PRETTY="Unknown OS"
fi

echo "检测到的系统信息:"
echo "  OS_NAME: $OS_NAME"
echo "  OS_VERSION: $OS_VERSION"
echo "  OS_PRETTY: $OS_PRETTY"

# 测试CentOS 7检测
if [ "$OS_NAME" = "centos" ] && [ -n "$OS_VERSION" ] && [ "$(echo "$OS_VERSION < 8" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    echo "✅ 检测到CentOS 7"
    if [ -f "requirements-centos7.txt" ]; then
        echo "✅ 找到兼容的requirements文件"
    else
        echo "❌ 未找到requirements-centos7.txt文件"
    fi
else
    echo "❌ 未检测到CentOS 7"
fi 