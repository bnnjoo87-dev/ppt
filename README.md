# academic-ppt-ai

استوديو عروض أكاديمية يعتمد على نماذج NVIDIA NIM، بفصل واضح بين الواجهة والـ Backend:

- **Nemotron 3.5 Parse** (Cloud API) — المحرك الأساسي: استخراج النص + الجداول + الـ layout من صورة صفحة واحدة.
- **Nemotron OCR v2** (NIM محلي) — خطة بديلة **يدوية فقط**، يتطلب GPU ولا يُستدعى تلقائيًا.

لا توجد أي مفاتيح داخل الواجهة (HTML) — كل المفاتيح تعيش في الـ Backend فقط.

## الهيكل

```
academic-ppt-ai/
├── backend/
│   ├── app.py            # Flask API: /health ، /api/parse ، /api/ocr + خدمة الواجهة
│   ├── nvidia_parse.py   # Nemotron 3.5 Parse (Cloud)
│   └── nvidia_ocr.py     # Nemotron OCR v2 (NIM محلي — fallback)
├── frontend/
│   └── index.html        # استوديو الشرائح (Beast Mode v5.0) — يستدعي الـ Backend فقط
├── .github/workflows/
│   └── deploy.yml        # نشر تلقائي إلى Fly.io عند كل push إلى main
├── Dockerfile            # صورة الإنتاج (python:3.12-slim + gunicorn)
├── fly.toml              # إعداد النشر على Fly.io (internal_port 8000)
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
└── run_ocr_nim.sh        # تشغيل حاوية OCR v2 على المنفذ 8001 (اختياري، يتطلب GPU)
```

## التشغيل

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # على ويندوز: .venv\Scripts\activate
pip install -r ../requirements.txt
python app.py
```

ثم افتح المتصفح على: **http://localhost:8000** (الـ Flask يخدم الواجهة مباشرة من `frontend/`).

اختبار التدفق الأساسي: **توليد العرض بالـ AI → اختر صورة صفحة → يظهر النص المستخرج في حقل "نص البحث"**.

> إن كنت تفتح `index.html` بطريقة أخرى (Live Server مثلًا)، اضبط "رابط الـ Backend" في النافذة على `http://localhost:8000` واضغط "فحص الاتصال" (CORS مُفعّل في الـ Backend).

## النشر: GitHub + Fly.io

### 1) ارفع المشروع إلى GitHub

```bash
git init
git add .
git commit -m "academic-ppt-ai: Nemotron Parse + OCR fallback"
git branch -M main
git remote add origin https://github.com/<اسم-حسابك>/academic-ppt-ai.git
git push -u origin main
```

### 2) انشر على Fly.io

```bash
# ثبّت flyctl أولًا: https://fly.io/docs/flyctl/install/
fly auth login

# ⚠️ اسم التطبيق فريد عالميًا — إذا كان "academic-ppt-ai" محجوزًا اختر اسمًا آخر
#    وحدّث سطر app = "..." في fly.toml ليطابقه.
fly apps create academic-ppt-ai

# اختياري لكن مُستحسن: ضع مفتاح Parse كـ secret (يتجاوز المفتاح المضمّن في الكود)
fly secrets set NVIDIA_PARSE_API_KEY=nvapi-xxxx

fly deploy          # يبني Dockerfile وينشر
fly open            # يفتح https://academic-ppt-ai.fly.dev
```

الواجهة والـ API معًا على نفس الرابط: `https://<اسم-التطبيق>.fly.dev` —
في الواجهة اضبط "رابط الـ Backend" على نفس الرابط (بدون مسار) واضغط "فحص الاتصال".

> ملاحظة: بروكسي Fly.io يقطع الاستجابات التي تتجاوز ~60 ثانية بدون بث. استخراج
> Parse المُختبَر يستغرق ~8 ثوانٍ، لكن إن واجهت صفحة ثقيلة جدًا قد تحتاج إعادة المحاولة.

### 3) نشر تلقائي من GitHub (اختياري)

```bash
# أنشئ توكن نشر طويل الأجل ثم ضعه كسرّ في المستودع
fly tokens create deploy -a academic-ppt-ai -x 999999h
```

- في GitHub: **Settings → Secrets and variables → Actions → New repository secret**
  بالاسم `FLY_API_TOKEN` والقيمة هي التوكِن.
- بعدها كل `git push` إلى `main` ينشر تلقائيًا عبر `.github/workflows/deploy.yml`.

## تفعيل Nemotron OCR v2 (اختياري — يتطلب NVIDIA GPU)

```bash
./run_ocr_nim.sh     # يسحب nvcr.io/nim/nvidia/nemotron-ocr-v2 ويشغّله على المنفذ 8001
```

المنفذ **8001** على الجهاز المضيف (داخل الحاوية 8000) لتفادي التعارض مع Flask على 8000.
عند فشل Parse ستظهر في الواجهة نافذة تقترح تجربة OCR كخطة بديلة.

## المفاتيح

- مفتاح Parse مضمّن كقيمة افتراضية داخل `backend/nvidia_parse.py`، ويمكن تجاوزه عبر `NVIDIA_PARSE_API_KEY` في ملف `.env` (انسخ `.env.example`).
- مفتاح NGC مضمّن في `run_ocr_nim.sh` لتسجيل الدخول إلى nvcr.io وسحب الحاوية، ويمكن تجاوزه عبر `NGC_API_KEY`.
- ⚠️ **تنبيه أمني**: كلا المفتاحين ورد داخل محادثات نصية، لذا يجب **تدويرهما (revoke + إنشاء مفتاح جديد) قبل جعل المستودع عامًا على GitHub**. ملف `.env` مستثنى من Git عبر `.gitignore`.

## خارطة الطريق

1. ✅ المرحلة الحالية: رفع صورة → Nemotron 3.5 Parse → ظهور النص/الجداول في التطبيق (OCR v2 كـ fallback يدوي).
2. تحويل نتيجة Parse إلى `ResearchDocument` (pages / sections / paragraphs / tables / figures / headings / metadata).
3. إدخال النموذج الثالث **Nemotron 3 Nano Omni 30B A3B Reasoning** لتحويل `ResearchDocument` إلى Presentation Design JSON.
