# پیش‌بینی ریزش مشتری (Customer Churn Prediction)

پروژه‌ی کامل یادگیری ماشین از **شناخت داده** تا **ارزیابی نهایی مدل روی Test Set** — با تمرکز بر اینکه *چرا* هر تصمیمی گرفته شده، نه فقط اینکه چه کدی نوشته شده است.

---

## خلاصه‌ی سریع

| | |
|---|---|
| **مسئله** | کدام مشتریان احتمالاً سرویس را ترک می‌کنند؟ (Classification) |
| **داده** | IBM Telco Customer Churn — ۷٬۰۴۳ سطر، نرخ ریزش ۲۶.۵٪ |
| **مدل‌ها** | Baseline (Dummy) · Logistic Regression · KNN · SVM |
| **روش** | Pipeline + ColumnTransformer · Stratified 5-Fold CV · GridSearchCV · بدون Data Leakage |
| **مدل نهایی** | **Logistic Regression** (C=100) — انتخاب‌شده بر اساس ROC-AUC/F1/سادگی، **نه فقط Accuracy** |
| **نتیجه‌ی Test** | Accuracy 0.805 · Precision 0.654 · Recall 0.561 · F1 0.604 · **ROC-AUC 0.841** |

نتیجه‌ی کسب‌وکاری: مدل می‌تواند ~۵۶٪ از ریزش‌های واقعی را **قبل از وقوع** شناسایی کند (در تست: ۲۱۰ از ۳۷۴ نفر) و با پایین آوردن آستانه‌ی تصمیم تا 0.3 این پوشش به ~۷۷٪ می‌رسد.

---

## ساختار پروژه

```
customer-churn-ml/
│
├── data/
│   ├── README.md                      # منبع دیتاست + لینک دانلود مستقیم
│   └── Telco-Customer-Churn.csv       # خود دیتاست
│
├── notebooks/
│   └── customer_churn_analysis.ipynb  # ★ نوت‌بوک کامل و اجراشده (۱۲۰ سلول)
│
├── src/
│   ├── preprocessing.py               # پاک‌سازی + مهندسی ویژگی + ColumnTransformer
│   ├── train.py                       # pipeline مدل‌ها، Stratified CV، GridSearch
│   ├── evaluate.py                    # معیارها و توابع رسم نمودار
│   └── utils.py                       # seed، لود داده، ذخیره/بارگذاری مدل
│
├── models/
│   └── README.md                      # نحوه‌ی ذخیره‌ی مدل برای Production
│
├── requirements.txt
└── README.md                          # همین فایل
```

## اجرا

```bash
# 1) نصب وابستگی‌ها
pip install -r requirements.txt

# 2) باز کردن نوت‌بوک
jupyter notebook notebooks/customer_churn_analysis.ipynb
# یا در VS Code / JupyterLab مستقیم باز کنید
```

نوت‌بوک **از قبل کامل اجرا شده** و خروجی‌ها (جدول‌ها و نمودارها) داخل همان فایل ذخیره‌اند — بدون اجرا هم قابل مطالعه است. همه‌ی نتایج با `random_state = 42` reproducible هستند.

اجرای مجدد کل نوت‌بوک حدود ۳ دقیقه طول می‌کشد.

## منبع دیتاست

**IBM Telco Customer Churn**

* مخزن رسمی: <https://github.com/IBM/telco-customer-churn-on-icp4d>
* دانلود مستقیم CSV: <https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv>
* نسخه Kaggle (جایگزین): <https://www.kaggle.com/datasets/blastchar/telco-customer-churn>

جزئیات بیشتر در [`data/README.md`](data/README.md).

---

## نقشه‌ی نوت‌بوک (۲۳ بخش)

1. مرور پروژه — مسئله، هدف، ورودی/خروجی، چرا Classification
2. واژه‌نامه‌ی مفاهیم کلیدی (Classification تا Margin/Kernel — ۳۲ مفهوم)
3. آشنایی با Dataset — ابعاد، typeها، missing، duplicate، مقادیر غیرمنطقی، توزیع target
4. EDA — هشت نمودار با هدف مشخص + تفسیر «از این نمودار چه فهمیدیم؟»
5. Data Cleaning — تصمیم + دلیل برای هر مشکل
6. Feature Engineering — `AvgMonthlyCharge`، `ServicesCount` + بررسی Leakage
7. Preprocessing — Encoding، Scaling (و چرا برای KNN/SVM حیاتی)، Pipeline/ColumnTransformer
8. Train/Test Split — چرا test فقط آخر، نقش Stratify
9. Baseline — چرا و با چه عددی
10. سه مدل با intuition و پیاده‌سازی (LR، KNN، SVM)
11. Cross Validation — Stratified K-Fold، مفهوم K
12. Hyperparameter Tuning — Parameter در برابر Hyperparameter + GridSearchCV
13. Model Evaluation — Accuracy/Precision/Recall/F1/ROC-AUC + Confusion Matrix + ROC/PR
14. جدول مقایسه قبل/بعد از Tuning + تحلیل تفاوت‌ها
15. انتخاب مدل نهایی با معیارهای چندگانه
16. ارزیابی نهایی روی Test Set (تنها یک بار)
17. تفسیر مدل — coefficientها و بررسی منطقی بودن
18. تفسیر کسب‌وکاری — هزینه‌ی FP در برابر FN + جدول Trade-off آستانه
19. محدودیت‌ها (صادقانه)
20. بهبودهای آینده
21. جمع‌بندی نهایی
22. **«اگر استاد ازم سؤال بپرسد»** — ۲۴ سؤال با جواب کوتاه
23. **«چیزهایی که باید خودم بتوانم توضیح بدهم»** — چک‌لیست نهایی

---

## نتایج کلیدی

### مقایسه‌ی مدل‌ها (CV روی Train)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Baseline (Dummy) | 0.735 | 0.000 | 0.000 | 0.000 | 0.500 |
| **Logistic Regression (tuned)** | **0.803** | 0.653 | **0.551** | **0.597** | **0.846** |
| KNN (tuned) | 0.781 | 0.593 | 0.555 | 0.573 | 0.816 |
| SVM (tuned) | 0.796 | 0.677 | 0.442 | 0.534 | 0.837 |

### مدل نهایی روی Test Set

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| 0.805 | 0.654 | 0.561 | 0.604 | **0.841** |

### بهترین فراپارامترها

* **Logistic Regression:** `C=100`
* **KNN:** `n_neighbors=11`, `weights=uniform`, `p=2`
* **SVM:** `C=0.1`, `gamma=0.01`, `kernel=rbf`

### مهم‌ترین ویژگی‌ها (از coefficientهای LR)

* **ریزش:** `InternetService_Fiber optic`، `Contract_Month-to-month`، `ServicesCount`، `TotalCharges`
* **ماندگاری:** `tenure`، `Contract_Two year`، `InternetService_DSL`

---

## نکات methodology (چیزی که پروژه را «درست» می‌کند)

* هیچ **Data Leakage**: همه‌ی impute/scale/encode داخل `Pipeline` و فقط با `fit` روی train هر fold
* **Test Set تا بخش ۱۶ دست‌نخورده** و تصمیم انتخاب مدل قبل از دیدن آن گرفته شده
* **Stratified K-Fold** برای حفظ نسبت کلاس‌ها در هر fold
* ارزیابی فقط با Accuracy **نیست** — چون کلاس‌ها نامتوازن و هزینه‌های FP/FN متفاوت‌اند
* `random_state=42` در همه‌جا → نتایج reproducible
