# Telco Customer Churn Dataset

این پوشه دیتاست اصلی پروژه را نگه می‌دارد.

## فایل

| فایل | توضیح |
|---|---|
| `Telco-Customer-Churn.csv` | ۷٬۰۴۳ سطر، ۲۱ ستون — دیتاست استاندارد ریزش مشتریان مخابراتی/سرویس اشتراکی |

## منبع (Source)

* **عنوان:** IBM Telco Customer Churn
* **مخزن رسمی GitHub (منبع دانلود این فایل):**
  <https://github.com/IBM/telco-customer-churn-on-icp4d>
  (مسیر فایل: `data/Telco-Customer-Churn.csv`)
* **لینک دانلود مستقیم (raw):**
  <https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv>
* **نسخه Kaggle (جایگزین):**
  <https://www.kaggle.com/datasets/blastchar/telco-customer-churn>
* **صفحه معرفی توسط IBM Community:**
  <https://community.ibm.com/communitydata/business/customer-churn>

## بازتولید دانلود

```bash
curl -L -o data/Telco-Customer-Churn.csv \
  "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
```

## خلاصه‌ی خواص

* **تعداد سطر:** ۷٬۰۴۳
* **ستون هدف:** `Churn` (Yes/No) — نرخ ریزش ≈ ۲۶.۵٪
* **مشکل شناخته‌شده:** ۱۱ مقدار خالی رشته‌ای در `TotalCharges` (همه با `tenure=0`) — در بخش Data Cleaning نوت‌بوک حل می‌شود
* **لایسنس/نحوه استفاده:** دیتاست نمونه‌ی عمومی منتشرشده توسط IBM برای آموزش و تحلیل

> نکته: در این مخزن یک نسخه از CSV کنار پروژه قرار دارد تا نوت‌بوک بدون نیاز به اینترنت هم اجرا شود.
