# models/

پوشه‌ی خروجی مدل‌های ذخیره‌شده.

## چه چیزی اینجا ذخیره می‌شود؟

مدل نهایی (Pipeline کامل: `ColumnTransformer` + `LogisticRegression`) با فراپارامترهای انتخاب‌شده، به کمک `joblib`:

```python
from src.utils import save_model, load_model

save_model(final_model, "churn_final")     # -> models/churn_final.joblib
model = load_model("churn_final")          # بارگذاری مجدد
```

> نکته‌ی مهم: چون preprocessing داخل خود Pipeline است، فایل ذخیره‌شده **به‌تنهایی** قابل استفاده در API/Production است —
> نیازی نیست scaling و encoding را جداگانه کنار مدل نگه داریم.

## وضعیت فعلی

فایل `.joblib` عمداً در مخزن commit نمی‌شود (معمولاً در `.gitignore`)؛
با اجرای بخش‌های پایانی نوت‌بوک قابل بازتولید است.
