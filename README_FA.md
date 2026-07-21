# 🚀 اپیزوکدکس (EpisoCodex) — فریم‌ورک مهندسی نرم‌افزار خودگردان

<div align="center">

![الهام گرفته از Grok-Build](https://img.shields.io/badge/%D9%87%D8%A7%D9%85%20%DA%AF%D8%B1%D9%81%D8%AA%D9%87%20%D8%A7%D8%B2-xAI%20grok--build-red?style=for-the-badge&logo=github)
![نسخه](https://img.shields.io/badge/%D9%86%D8%B3%D8%AE%D9%87-2.0-blue?style=for-the-badge)
![پایتون](https://img.shields.io/badge/%D9%BE%D8%A7%DB%8C%D8%AA%D9%88%D9%86-3.11+-green?style=for-the-badge&logo=python)
![لایسنس](https://img.shields.io/badge/%D9%84%D8%A7%DB%8C%D8%B3%D9%86%D8%B3-Apache%202.0-orange?style=for-the-badge)
![بهینه‌سازی توکن](https://img.shields.io/badge/%D8%A8%D9%87%DB%8C%D9%86%D9%87%E2%80%8C%D8%B3%D8%A7%D8%B2%DB%8C%20%D8%AA%D9%88%DA%A9%D9%86-%D8%A8%D9%84%D9%87-brightgreen?style=for-the-badge)

<br/>

### 💡 **فریم‌ورک هوشمند توسعه نرم‌افزار، الهام گرفته شده و برگرفته از معماری کدهای [grok-build](https://github.com/xai-org/grok-build) شرکت xAI.**

*دستیار برنامه‌نویسی خود را به یک مهندس نرم‌افزار خود‌درمان، خودآموز و فوق‌العاده بهینه تبدیل کنید.*

[شروع سریع](#-شروع-سریع) • [ویژگی‌ها](#-ویژگی‌های-کلیدی) • [معماری سیستم](#-معماری-سیستم) • [دستورات CLI](#-مرجع-دستورات-cli) • [ادغام با IDE](#-ادغام-با-ادیتورها) • [لایسنس](#-لایسنس)

---

</div>

> [!NOTE]
> ℹ️ **یادداشت شفافیت / Attribution Notice:**  
> این پروژه بر اساس معماری، الگوهای اجرایی و کدهای پایه پروژه متن‌باز **[grok-build](https://github.com/xai-org/grok-build)** توسعه یافته است.

---

## ⚡ تفاوت اصلی اپیزوکدکس چیست؟

ابزارهای معمولی برنامه‌نویسی فقط دستورالعمل‌های متنی (System Prompt) هستند، اما **EpisoCodex** با بهره‌گیری از مفاهیم **grok-build**، یک سیستم‌عامل شناختی کامل برای دستیار هوش مصنوعی شما ارائه می‌دهد.

| ویژگی | ابزارهای معمولی هوش مصنوعی | اپیزوکدکس (معماری Grok-Build) |
|---|---|---|
| 🔀 **انتخاب مهارت‌ها** | دستی و پرامپت ثابت | **مسیریابی معنایی** فقط ابزارهای مورد نیاز را بارگذاری می‌کند |
| 🧠 **یادگیری از اشتباهات** | تکرار مداوم باگ‌ها | **حلقه RLHF** مانع تکرار اشتباهات گذشته می‌شود |
| 🛡️ **مدیریت مصرف توکن** | مصرف بی‌رویه و گران | **سپر فشرده‌ساز توکن** جلوی خواندن فایل‌های سنگین را می‌گیرد |
| 🏖️ **تست و ایمنی** | اعمال مستقیم روی کد | **سندباکس شبیه‌سازی** کد را قبل از اعمال نهایی تست می‌کند |
| 📝 **پایداری حافظه** | پاک شدن بعد از هر نشست | **حافظه اپیزودیک** تجربیات را در نشست‌های بعدی حفظ می‌کند |
| 🔧 **بهبود کیفیت کد** | نیازمند بازبینی دستی | **موتور خود‌بازنویسی** کدهای مرده و بهینه‌سازی‌ها را کشف می‌کند |

---

## 🚀 شروع سریع

### ۱. دریافت و راه‌اندازی
```bash
# دریافت مخزن
git clone https://github.com/cleverboy01/EpisoCodex.git
cd EpisoCodex

# اجرای نصب‌کننده خودکار
python setup.py
```

### ۲. اجرای محیط کاری
```bash
# روش اول: اجرای داشبورد دسکتاپ گرافیکی
python gui/guicli.py

# روش دوم: اجرای داشبورد زنده ترمینال
python agicli.py
```

### ۳. اجرای یک وظیفه
```bash
python agicli.py run "refactor the auth module to use JWT"
```

> 💡 **بدون نیاز به کلید API مجزا:** همه چیز به صورت محلی با دستیار ادیتور فعلی شما (Cursor, Windsurf, Antigravity IDE) کار می‌کند.

---

## 🏗️ معماری سیستم

### چرخه شناختی (Cognitive Execution Loop)

```mermaid
flowchart TD
    A([🖥️ SessionStart Hook]) --> B[📚 Skill Indexer\nBuilds skill-index.json]
    B --> C{User Task}
    C --> D[🧠 RLHF Preflight\nCheck past errors]
    D --> E[🔀 Skill Router\nSemantic skill selection]
    E --> F[🎯 Task Execution\nWith selected skills]
    F --> G{Result OK?}
    G -->|Yes| H[📝 Episodic Memory\nStore experience]
    G -->|No| I[🏥 Self-Heal Loop\nSandbox → Fix → Retry]
    I --> J{3 retries\nexhausted?}
    J -->|No| F
    J -->|Yes| K[🚨 Critic Agent\nAdversarial review]
    K --> H
    H --> L[🔧 Self-Rewrite Engine\nPrioritize improvements]
    L --> M[🔑 Token Guard\nUpdate token ledger]
    M --> N([💾 SessionEnd Hook\nFlush memory to disk])
    
    style A fill:#1a1a2e,color:#e94560
    style N fill:#1a1a2e,color:#e94560
    style I fill:#16213e,color:#f5a623
    style K fill:#16213e,color:#e94560
    style E fill:#0f3460,color:#53d8fb
    style D fill:#0f3460,color:#53d8fb
```

---

## 🖥️ محیط گرافیکی دسکتاپ (CustomTkinter)

در مسیر `gui/guicli.py` یک برنامه مدرن دسکتاپ قرار دارد که امکانات زیر را ارائه می‌دهد:
* 📡 **داشبورد سینک زنده:** نمایش ابزارهای فعال و وضعیت لحظه‌ای ادیتور.
* 🚀 **مدیریت بصری توکن:** نمایش نوارهای پیشرفت مصرف توکن روزانه و نشست جاری.
* 🛡️ **همگام‌سازی پروفایل:** هماهنگی اطلاعات و حافظه با پروفایل محلی.
* 🎯 **اجراکننده تعاملی:** امکان تایپ وظایف و مشاهده لایو لوگ‌های هوش مصنوعی.

---

## 🔀 فازهای شناختی ۵ گانه

1. **بازیابی پویای مهارت‌ها:** بارگذاری هوشمند لایبرری‌ها بر اساس نیاز تسک.
2. **تکامل خودکار:** ساخت مهارت‌های جدید در صورت نبود ابزار مناسب.
3. **حافظه اپیزودیک:** چک کردن خطاهای قبلی پروژه قبل از نوشتن کد جدید.
4. **تفکر سیستم-۲:** بررسی تغییرات پرریسک در سندباکس ایزوله.
5. **عاملیت کنش‌گرا:** اسکن خودکار پروژه برای یافتن بدهی‌های فنی در زمان بیکاری.

---

## 📖 مرجع دستورات CLI

| دستور | توضیحات |
|---|---|
| `python agicli.py` | باز کردن داشبورد متنی زنده |
| `python agicli.py run "<task>"` | اجرای کامل تسک در چرخه شناختی |
| `python agicli.py loop [--iterations N]` | اجرای لوپ خود‌اصلاحی مداوم |
| `python agicli.py tokens` | مشاهده و مدیریت بودجه توکن‌ها |
| `python agicli.py scan` | اسکن کل پروژه برای یافتن نقاط قابل بهبود |
| `python agicli.py memory "<task>"` | بررسی خطاهای گذشته پیش از شروع کار |

---

## 🛠️ ادغام با ادیتورها

* **Cursor / Windsurf:** پوشه `agents/` را در ریشه پروژه کپی کرده و فایل `agents/.cursorrules` را اضافه کنید.
* **Antigravity IDE:** شناسایی خودکار هوک‌ها از طریق `agents/hooks/agent-hooks.json`.

---

## 📜 قدردانی و لایسنس

این پروژه با الهام از الگوی فریم‌ورک متن‌باز **[grok-build](https://github.com/xai-org/grok-build)** توسعه یافته است.

تحت لایسنس **Apache 2.0** منتشر شده و استفاده از آن کاملاً آزاد است.

---

<div align="center">

**توسعه یافته با 🧠 EpisoCodex (الهام گرفته از grok-build شرکت xAI)**  
⭐ اگر این پروژه برایتان مفید بود، به آن ستاره دهید!

</div>
