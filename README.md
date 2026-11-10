# NVIDIA A40 & Ubuntu Server Monitor

منصة مراقبة خفيفة ضمن خدمة Python واحدة: NVIDIA NVML وموارد Ubuntu، وواجهة عربية/إنجليزية، وبث WebSocket، وتاريخ SQLite وتنبيهات قابلة للتكوين. جميع قراءات نسخة التشغيل من العتاد والنظام؛ البيانات الاصطناعية محصورة في `tests/`.

## تشغيل محلي

المسار المتحقق منه: Ubuntu 24.04 وPython 3.12. التعريف الموجود يبقى كما هو؛ لا يعيد المشروع تثبيت NVIDIA أو CUDA.

```bash
cd /root/gpu-monitor
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

افتح **http://127.0.0.1:5000**. الاستماع على loopback فقط، والعامل واحد. لا تشغّل عدة Uvicorn workers: سيكرر ذلك جمع العتاد. تحتفظ بيئة `venv/` القديمة بتبعياتها السابقة؛ النسخة المطورة تستخدم `.venv/`.

لإعدادات مخصصة، انسخ `config.example.toml` إلى ملف محلي وعدّل مسار قاعدة البيانات ثم عيّن `GPU_MONITOR_CONFIG=/path/to/config.toml`. عند استخدام منفذ مختلف، أضف أصل المتصفح الدقيق إلى `allowed_origins`. الإعداد الافتراضي دون ملف يحفظ التاريخ داخل `data/history.sqlite3`.

إذا لم تتوفر NVIDIA، يبدأ التطبيق ويستمر رصد السيرفر، وتظهر حالة GPU غير متاحة. لا تُستبدل القيم المفقودة بصفر. نجاح API لا يثبت نجاح كل حساس؛ افحص حالة المصدر وحداثة القراءة.

## ما تعرضه المنصة

- جميع بطاقات GPU مع UUID وNVML: الاستخدام ونشاط الذاكرة وVRAM والحرارة والطاقة والترددات وECC وPCIe وأسباب خفض التردد، حسب الدعم الفعلي.
- A40 ذات تبريد سلبي؛ قراءة fan ليست قياساً لمراوح السيرفر. الحدود الحرارية تُقرأ من العتاد، مع إمكانية ضبط حدود الموقع.
- CPU والأنوية وRAM وSwap والأقراص ومعدلات I/O والشبكات ووقت التشغيل ومعلومات النظام.
- عمليات GPU: PID ووقت البدء والاسم وVRAM وRAM وCPU ونوع العملية. الاستخدام لكل عملية يبقى N/A عند غياب الدعم؛ لا نوزّع الاستخدام الكلي تخمينياً.
- تحليل النشاط والذروة والمتوسط وتغطية العينات وتغير VRAM. لا تعادل نسبة GPU جودة الاستدلال أو Tokens/s.
- تكامل LM Studio اختياري ومعطل افتراضياً، يقرأ قائمة النماذج الرسمية فقط؛ لا يقرأ المحادثات أو ينفذ طلبات استدلال.
- تاريخ خمس دقائق في الذاكرة بدقة الجمع، وتجميعات دقيقة محفوظة سبعة أيام افتراضياً. رسوم آخر ساعة و24 ساعة وأسبوع بحد 600 نقطة. يستخدم الأسبوع فواصل 30 دقيقة افتراضياً لاحتواء كامل الأيام السبعة؛ الحد الأدنى لتجميعه 15 دقيقة.
- تنبيهات باستمرار زمني وhysteresis وتعافٍ مستقر، دون رسائل خارجية.

## API

| المسار | المحتوى |
|---|---|
| `GET /api/health` | جاهزية المجمع وحالات المصادر؛ 503 عند التقادم، و200 مع degraded عند فشل مصدر |
| `GET /api/metrics` | Snapshot بإصدار مخطط 1، وكل البطاقات والنظام والتنبيهات وصحة المراقب |
| `GET /api/system` | آخر قراءة موارد السيرفر |
| `GET /api/gpu` | توافق حقول البطاقة الأولى ووحدات MiB السابقة؛ المفقود null |
| `GET /api/processes` | عمليات البطاقة الأولى، مع توافق وحدات MiB السابقة |
| `GET /api/history?window=5m` | `5m / 1h / 24h / 7d`؛ `max_points` بين 1 و600 |
| `WebSocket /ws/metrics` | آخر Snapshot ثم بث مشترك؛ لا ينشئ مجمعاً لكل اتصال |

الوحدات في المخطط الجديد: bytes وseconds وwatts و°C وMHz، والنسب من 0 إلى 100 ما لم يُذكر غير ذلك. CPU للعملية يمكن أن يتجاوز 100% بسبب تعدد الأنوية. `published_at` لتقدير زمن التسليم عند تزامن ساعات العميل والخادم. [الترحيل والتوافق](docs/operations/migration.md).

## النشر والوصول الآمن

[دليل Ubuntu وsystemd وHTTPS](docs/deployment/ubuntu.md) يجهز مستخدماً مخصصاً، ومسارات `/opt` و`/etc` و`/var/lib`، وNginx مع شهادة موثوقة وBasic Auth. التثبيت والتفعيل الإداريان يحتاجان الموافقة؛ لا يُفتح جدار الحماية تلقائياً. للحماية الكاملة يجب أن تشمل المصادقة REST وWebSocket والملفات الثابتة.

```bash
sudo systemctl start gpu-monitor
sudo systemctl stop gpu-monitor
sudo systemctl restart gpu-monitor
systemctl status gpu-monitor --no-pager
journalctl -u gpu-monitor -f
```

[النسخ الاحتياطي والاستعادة والتحديث والتراجع](docs/operations/recovery.md). لا تنسخ ملف SQLite منفرداً أثناء WAL؛ استخدم أداة backup المرفقة. لا حذف تلقائي لقواعد البيانات أو تعديل للطاقة أو التبريد أو التعريف.

## التطوير والتحقق

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy monitor app.py gpu.py
npm ci --ignore-scripts
npm run typecheck
npm run format:check
npx playwright install chromium
npm run test:browser
.venv/bin/python -m build --no-isolation
```

Node 22 مطلوب لأدوات التطوير فقط؛ Chart.js محفوظ محلياً. الاختبارات العامة تستخدم mocks. اختبار العتاد اختياري للقراءة فقط:
`GPU_MONITOR_REAL_GPU=1 .venv/bin/pytest tests/test_hardware.py`.

[CONTRIBUTING](CONTRIBUTING.md) يتضمن فحوص الأمان الكاملة. [خطة العمل](docs/roadmap.md) تربط المهام بالفروع وIssues. لا Push أو Merge أو Release أو تغيير حماية دون موافقة. [القرارات المعمارية](docs/adr/001-technology.md) تشرح اختيار Python بدلاً من إعادة الكتابة.

راجع [تقرير التحقق والجاهزية](docs/validation.md) لمعرفة ما تحقق فعلياً وما ينتظر إعداد الإنتاج. الإصدار الأول `0.0.1` متاح عبر [GitHub Releases](https://github.com/buruj7722-wq/gpu-monitor/releases/tag/v0.0.1)؛ متطلبات التحقق من النشر الإنتاجي موضّحة في التقرير. اختيار ترخيص المشروع مؤجل؛ ترخيص Chart.js المرفق يخص المكتبة وحدها.

[قائمة الملفات المنشأة والمعدلة](docs/file-inventory.md).

[نتائج النشر وطلبات الدمج وCI](docs/publication.md).
