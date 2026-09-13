# chartflow —— 确定性产图引擎的容器镜像
#
# 为什么要容器:渲染依赖 Graphviz 的 dot 可执行文件与中文字体,
# 这两样恰是"在我机器上跑不起来"的头号原因。镜像把它们钉死,
# 让「同输入必同输出」在别人机器上也成立 —— 否则那句话只对本机成立。
#
#   docker build -t chartflow .
#   docker run --rm chartflow                                  # 默认:环境自检
#   docker run --rm chartflow build.py samples/library/plan.json
#
# 跑自己的论文数据(挂载进容器):
#   docker run --rm -v "$PWD/我的论文:/data" chartflow build.py /data/plan.json

FROM python:3.12-slim

# 容器里 LANG 默认是 POSIX,Python 的 stdout 会退化成 ASCII ——
# 而本项目的输出满是中文,一 print 就 UnicodeEncodeError。
# C.UTF-8 是 glibc 内置 locale,不需要 locale-gen,也不会有 perl 告警。
ENV LANG=C.UTF-8 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONDONTWRITEBYTECODE=1

# graphviz        → dot 可执行文件(graphviz 这个 python 包只是个调用壳)
# fontconfig      → fc-list,doctor.py 靠它检查字体
# fonts-noto-cjk  → 中文字体。⚠ 别换成更小的 fonts-wqy-zenhei:
#                   它的字体族名里没有 "CJK" 字样,doctor.py 会误报 FAIL
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        graphviz \
        fontconfig \
        fonts-noto-cjk \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先只拷依赖清单 —— 改代码时这一层仍能命中缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 1000 chartflow

# --chown 一步到位,省掉一条会把整个仓库复制一遍的 RUN chown 层
COPY --chown=chartflow:chartflow . .

# uid 1000 与多数 Linux/WSL 宿主用户一致,挂载目录写入不会变成 root 属主
USER chartflow

# ENTRYPOINT 固定成 python,于是 `docker run chartflow <脚本> <参数>`
# 与 README 里的 `python3 <脚本> <参数>` 命令形状完全一致
ENTRYPOINT ["python"]
CMD ["doctor.py"]
