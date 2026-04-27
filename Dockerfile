FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 🚀 تفعيل وضع الديباج عشان بايثون يفضح أي خطأ صامت
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONASYNCIODEBUG=1 \
    UV_SYSTEM_PYTHON=1 \
    DENO_INSTALL="/root/.deno" \
    PATH="/root/.deno/bin:/usr/local/bin:/usr/bin:${PATH}"

WORKDIR /app

RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    build-essential cmake git curl wget unzip \
    ffmpeg aria2 libffi-dev libxml2-dev libxslt-dev zlib1g-dev libssl-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && curl -fsSL https://deno.land/install.sh | sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN uv pip install --upgrade setuptools wheel

COPY pytgcalls /app/pytgcalls

COPY requirements.txt .

RUN grep -v -E -i '^(py-tgcalls|pytgcalls|deepai|numba|llvmlite|quimb)' requirements.txt > filtered.txt && \
    uv pip install --no-cache -r filtered.txt

RUN uv pip install --no-cache \
    g4f \
    curl_cffi

RUN mkdir -p /etc/yt-dlp && \
    echo "--remote-components ejs:github" > /etc/yt-dlp.conf

RUN yt-dlp "ytsearch1:test" --dump-json > /dev/null 2>&1 || true

COPY . .

# 🚀 كشف الملف اللي بيخفي الخطأ الحقيقي وإجباره على طباعة مكان الخطأ بالظبط
RUN find . -type f -name "*.py" -exec sed -i 's/Fatal Error Occurred/Fatal Error Occurred\\n" + __import__("traceback").format_exc() + "/g' {} + || true

# 🚀 أمر التشغيل الذكي: هيشغل البوت، ولو البوت عمل كراش السيرفر مش هيقفل
# هيفضل شغال عشان تدخل تشوف الخطأ براحتك
CMD ["sh", "-c", "python3 -m AnnieXMedia ; echo '\n\n🚨 البوت توقف عن العمل! السيرفر لن يغلق لتمكينك من فحص الأخطاء... 🚨\n\n' ; tail -f /dev/null"]
