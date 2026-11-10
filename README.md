# NVIDIA GPU Monitor

لوحة ويب لمراقبة بطاقة NVIDIA باستخدام Flask. تعرض درجة الحرارة، استخدام المعالج والذاكرة، استهلاك الطاقة، سرعة المروحة، والعمليات التي تستخدم البطاقة. تتحدث البيانات كل ثانية.

## المتطلبات

- Python 3 و `pip` و `venv`.
- بطاقة NVIDIA وتعريفاتها مثبتة على الجهاز الذي يشغّل التطبيق، مع توفر مكتبة NVML.

## التشغيل

```bash
git clone https://github.com/buruj7722-wq/gpu-monitor.git
cd gpu-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

افتح http://localhost:5000 في المتصفح. على Windows، فعّل البيئة بالأمر `venv\Scripts\activate`.

التطبيق يراقب أول بطاقة NVIDIA (الفهرس `0`). يحتاج إلى الوصول إلى البطاقة على الجهاز الذي يشغّله؛ رفع الكود إلى GitHub لا يشغّل المراقبة تلقائيًا.

## واجهات البيانات

- `GET /api/gpu`: إحصاءات البطاقة.
- `GET /api/processes`: عمليات الحوسبة التي تستخدم البطاقة واستهلاكها للذاكرة.

إعداد التشغيل الحالي مخصص للتطوير، مع تفعيل `debug` والاستماع على جميع واجهات الشبكة. شغّله في بيئة محلية موثوقة.
