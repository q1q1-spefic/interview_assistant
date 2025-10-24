#!/bin/bash
# setup_fixed.sh - 修复版AI面试助手系统安装脚本

echo "🚀 AI面试助手系统 - 修复版安装脚本"
echo "========================================="

# 检查Python版本
echo "📋 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python 3.8+"
    exit 1
fi

python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要3.8+，当前版本: $python_version"
    exit 1
fi
echo "✅ Python版本: $python_version"

# 检查pip
echo "📦 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3未安装，请先安装pip"
    exit 1
fi
echo "✅ pip3可用"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip和setuptools
echo "⬆️ 升级pip和setuptools..."
pip install --upgrade pip setuptools wheel

# 安装核心依赖（分步安装，避免冲突）
echo "📦 安装核心依赖..."

echo "  🔧 安装Flask..."
pip install flask==2.3.3

echo "  🤖 安装OpenAI..."
pip install openai==1.35.0

echo "  📝 安装日志库..."
pip install loguru==0.7.2

echo "  🔍 安装向量数据库..."
pip install chromadb==0.4.15

echo "  📄 安装文档处理..."
pip install PyPDF2==3.0.1 python-docx==0.8.11

echo "  🌐 安装网络库..."
pip install beautifulsoup4==4.12.2 requests==2.31.0

echo "  🛠️ 安装工具库..."
pip install python-dateutil==2.8.2 python-dotenv==1.0.0 aiofiles==23.2.1

echo "  🔢 安装数值计算..."
pip install numpy==1.24.3

echo "  ⚙️ 安装Web工具..."
pip install Werkzeug==2.3.7

echo "  📊 安装进度条..."
pip install tqdm==4.66.1

# 验证关键包安装
echo "🧪 验证关键包安装..."
python3 -c "
import sys
import importlib

packages = [
    'flask', 'openai', 'loguru', 'chromadb', 
    'PyPDF2', 'docx', 'bs4', 'requests', 
    'numpy', 'tqdm'
]

failed = []
for pkg in packages:
    try:
        if pkg == 'docx':
            importlib.import_module('docx')
        elif pkg == 'bs4':
            importlib.import_module('bs4')
        elif pkg == 'PyPDF2':
            importlib.import_module('PyPDF2')
        else:
            importlib.import_module(pkg)
        print(f'✅ {pkg} 导入成功')
    except ImportError as e:
        print(f'❌ {pkg} 导入失败: {e}')
        failed.append(pkg)

if failed:
    print(f'\\n❌ 以下包安装失败: {failed}')
    sys.exit(1)
else:
    print('\\n🎉 所有关键包安装成功！')
"

if [ $? -ne 0 ]; then
    echo "❌ 依赖包安装验证失败"
    exit 1
fi

# 创建必要目录
echo "📁 创建项目目录..."
mkdir -p data
mkdir -p data/chroma_templates
mkdir -p uploads
mkdir -p templates
mkdir -p logs

# 设置目录权限
chmod 755 data uploads templates logs
chmod 755 data/chroma_templates

# 检查环境变量
echo "🔑 检查环境变量..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY 未设置"
    
    # 创建.env文件模板
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# AI面试助手环境变量配置
OPENAI_API_KEY=your_openai_api_key_here

# 可选配置
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_region

# 日志级别
LOG_LEVEL=INFO
EOF
        echo "📝 已创建.env文件模板，请编辑并填入你的API密钥"
        echo "   编辑命令: nano .env"
    fi
    
    echo ""
    echo "🔑 请设置OpenAI API密钥："
    echo "   方法1: export OPENAI_API_KEY=your_key"
    echo "   方法2: 编辑.env文件填入密钥"
    echo ""
else
    echo "✅ OPENAI_API_KEY 已设置"
fi

# 运行最终测试
echo "🧪 运行最终系统测试..."
python3 -c "
print('🔄 测试系统组件...')

# 测试OpenAI导入
try:
    import openai
    print('✅ OpenAI导入成功')
except Exception as e:
    print(f'❌ OpenAI导入失败: {e}')
    exit(1)

# 测试ChromaDB
try:
    import chromadb
    print('✅ ChromaDB导入成功')
except Exception as e:
    print(f'❌ ChromaDB导入失败: {e}')
    exit(1)

# 测试Flask
try:
    import flask
    print('✅ Flask导入成功')
except Exception as e:
    print(f'❌ Flask导入失败: {e}')
    exit(1)

# 测试文档处理
try:
    import PyPDF2
    import docx
    print('✅ 文档处理库导入成功')
except Exception as e:
    print(f'❌ 文档处理库导入失败: {e}')
    exit(1)

print('🎉 所有组件测试通过！')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 安装完成！"
    echo ""
    echo "📋 下一步操作:"
    echo "1. 设置API密钥:"
    echo "   export OPENAI_API_KEY=your_openai_key"
    echo ""
    echo "2. 启动系统:"
    echo "   python interview_assistant_system.py"
    echo ""
    echo "3. 访问界面:"
    echo "   http://localhost:5000"
    echo ""
    echo "💡 如果遇到问题："
    echo "   - 检查Python版本: python3 --version"
    echo "   - 检查虚拟环境: source venv/bin/activate"
    echo "   - 查看日志: tail -f logs/system.log"
    echo ""
else
    echo "❌ 安装过程中出现错误"
    echo ""
    echo "🔧 常见解决方案："
    echo "1. 重新创建虚拟环境:"
    echo "   rm -rf venv"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install --upgrade pip"
    echo ""
    echo "2. 手动安装依赖:"
    echo "   pip install openai==1.35.0"
    echo "   pip install flask==2.3.3"
    echo "   pip install chromadb==0.4.15"
    echo ""
    echo "3. 检查网络连接和权限"
    exit 1
fi

# 创建简化的测试脚本
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
"""
安装验证测试脚本
"""

def test_imports():
    """测试所有必要的导入"""
    print("🧪 测试导入...")
    
    try:
        import openai
        print("✅ openai")
    except Exception as e:
        print(f"❌ openai: {e}")
        return False
    
    try:
        import flask
        print("✅ flask")
    except Exception as e:
        print(f"❌ flask: {e}")
        return False
    
    try:
        import chromadb
        print("✅ chromadb")
    except Exception as e:
        print(f"❌ chromadb: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2")
    except Exception as e:
        print(f"❌ PyPDF2: {e}")
        return False
        
    try:
        import docx
        print("✅ python-docx")
    except Exception as e:
        print(f"❌ python-docx: {e}")
        return False
    
    return True

def test_openai_connection():
    """测试OpenAI连接"""
    import os
    import openai
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OPENAI_API_KEY未设置，跳过连接测试")
        return True
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # 这里不做实际API调用，只测试客户端创建
        print("✅ OpenAI客户端创建成功")
        return True
    except Exception as e:
        print(f"❌ OpenAI客户端创建失败: {e}")
        return False

def test_directories():
    """测试目录创建"""
    import os
    
    dirs = ['data', 'uploads', 'templates', 'logs']
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/ 目录存在")
        else:
            print(f"❌ {dir_name}/ 目录不存在")
            return False
    
    return True

if __name__ == "__main__":
    print("🔍 安装验证测试")
    print("=" * 30)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_openai_connection()
    all_passed &= test_directories()
    
    print("\n" + "=" * 30)
    if all_passed:
        print("🎉 所有测试通过！系统可以正常使用")
        print("\n📋 启动系统:")
        print("   python interview_assistant_system.py")
    else:
        print("❌ 部分测试失败，请检查安装")
        exit(1)
EOF

echo "📝 已创建安装验证脚本: test_installation.py"
echo "运行验证: python test_installation.py"