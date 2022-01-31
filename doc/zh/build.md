# 构建JDKMGR

## 在Windows上构建

### 准备工作

先决条件：GCC>=12.1.0,Python3>=3.8,[7zip](https://www.7-zip.org/download.html)。

### 安装依赖库

推荐独立的虚拟环境，否者编译产生的文件可能会比较大

```bash
pip install -r requirements.txt
```

### 编译程序

```bash
python build.py
```

编译完成后，可以在artifact目录下找到打包完后的文件。

### 打包程序（可选）

打包程序需要安装[NSIS>=3.0](https://nsis.sourceforge.io/Download)。

并且需要安装[EnVar](https://github.com/GsNSIS/EnVar/)插件。

```bash
# 如果makensis在PATH中
python build.py --pack
# 如果makensis在其他目录中
python build.py --pack --makensis /path/to/makensis
```