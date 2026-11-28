# دليل التشغيل السريع بالعربية

## الهدف

توفّر الدالة `design_drip_irrigation_system` مساراً موحداً لتحليل قطاع ري بالتنقيط، وبناء منحنى النظام، ثم تحديد نقطة تقاطع منحنى المضخة مع منحنى النظام وحساب القدرة. وتوفّر `design_irrigation_sectors` تحليلاً مستقلاً لعدة قطاعات تعمل بالتتابع.

الدالة تنسّق الحسابات الموجودة. لا تضيف معادلات هيدروليكية جديدة.

## المتطلبات

- Python 3.10 أو أحدث.
- بيانات هندسية فعلية للأنابيب والقطاعات.
- منحنى المضخة من ورقة الشركة المصنّعة.
- مجال ضغط النقاطات من ورقة الشركة المصنّعة.

## مثال الاستخدام

```python
from irrigation.calculations import (
    EmitterPressureRange,
    design_drip_irrigation_system,
)

result = design_drip_irrigation_system(
    sector_parameters={
        "number_of_laterals": 10,
        "emitters_per_lateral": 20,
        "emitter_flow_lph": 4.0,
        "lateral_length_m": 40.0,
        "lateral_diameter_m": 0.016,
        "manifold_length_m": 20.0,
        "manifold_diameter_m": 0.040,
        "inlet_pressure_bar": 1.5,
        "hazen_williams_c": 150,
        # Optional elevations in meters, relative to the manifold inlet.
        # Positive values indicate uphill takeoffs.
        "lateral_takeoff_elevations_m": [0.0] * 10,
        # Optional emitter elevations in meters, relative to each lateral inlet.
        "emitter_elevations_m": [0.0] * 20,
    },
    pressure_range=EmitterPressureRange(
        minimum_bar=1.0,
        maximum_bar=4.0,
    ),
    upstream_system_parameters={
        "static_elevation_difference_m": 3.0,
        "upstream_pipe_length_m": 30.0,
        "upstream_pipe_diameter_m": 0.040,
        "hazen_williams_c": 150,
        "local_loss_coefficient": 2.0,
        "flow_rates_m3_s": [
            0.0002,
            0.0005,
            0.0010,
            0.0015,
        ],
    },
    pump_data={
        "manufacturer": "Example manufacturer",
        "model": "Example pump",
        "pump_curve": [
            (0.0001, 25.0),
            (0.0005, 19.0),
            (0.0010, 12.0),
            (0.0015, 5.0),
        ],
        "efficiency_curve": [
            (0.0001, 30.0),
            (0.0005, 45.0),
            (0.0010, 40.0),
            (0.0015, 25.0),
        ],
    },
    motor_efficiency_percent=80.0,
)

print(result["sector_analysis"]["total_flow_lph"])
print(result["design_duty"])
print(result["pump_system_analysis"]["pump_analysis"])
```

القيم أعلاه للتوضيح البرمجي فقط. لا تمثل توصية لاختيار مضخة أو أنبوب.

## تحليل عدة قطاعات بالتتابع

```python
from irrigation.calculations import design_irrigation_sectors

result = design_irrigation_sectors(
    sectors=[
        {"name": "قطاع الأشجار", "sector_parameters": tree_sector_parameters},
        {"name": "قطاع الخضروات", "sector_parameters": vegetable_sector_parameters},
    ],
    upstream_system_parameters=upstream_parameters,
    pump_data=pump_data,
    pressure_range=pressure_range,
    motor_efficiency_percent=80.0,
)

for sector in result["sectors"]:
    print(sector["name"], sector["analysis"]["design_duty"])
```

يعيد هذا المسار نتيجة مستقلة لكل قطاع باستخدام بيانات المضخة والأنبوب الرئيسي المشتركة. يفترض التشغيل بالتتابع، ولا يحسب تشغيل عدة قطاعات في الوقت نفسه أو التدفق المشترك في رأس توزيع واحد.

## حساب ET₀ اليومي من بيانات الطقس

```python
from irrigation.calculations import calculate_fao56_et0

weather = calculate_fao56_et0(
    tmin_c=18.0,
    tmax_c=31.0,
    wind_speed_2m_m_s=2.0,
    solar_radiation_mj_m2_day=20.0,
    elevation_m=10.0,
    latitude_degrees=33.78,
    day_of_year=180,
    relative_humidity_min_percent=35.0,
    relative_humidity_max_percent=85.0,
)

et0 = weather["et0_mm_day"]
```

تحسب الدالة ET₀ اليومية بمعادلة FAO-56 Penman-Monteith. أدخل قياسات اليوم للموقع. سرعة الرياح يجب أن تكون على ارتفاع مترين. أدخل ضغط البخار الفعلي مباشرة بدلاً من الرطوبة النسبية، أو أدخل الرطوبة الدنيا والعليا معاً. خط العرض موجب شمالاً وسالب جنوباً. رقم اليوم من 1 إلى 366. يفترض الحساب أن تدفق حرارة التربة اليومي يساوي صفراً.

## حساب الاحتياجات المائية للمحاصيل

```python
from irrigation.calculations import calculate_crop_water_requirements

water = calculate_crop_water_requirements(
    crops=[
        {"name": "أشجار", "kc": 0.8, "area_m2": 100.0},
        {"name": "خضروات", "kc": 1.2, "area_m2": 50.0},
    ],
    et0_mm_day=5.0,
    application_efficiency_percent=80.0,
)

daily_volume_l = water["summary"]["gross_irrigation_requirement_l_day"]
daily_volume_m3 = water["summary"]["gross_irrigation_requirement_m3_day"]
```

تعتمد المعادلة على:

- الاحتياج الصافي (لتر/يوم) = ET₀ (مم/يوم) × Kc × المساحة (م²).
- الاحتياج الإجمالي (لتر/يوم) = الاحتياج الصافي ÷ (كفاءة التطبيق ÷ 100).
- كل 1 مم من الماء فوق 1 م² يساوي 1 لتر.

أدخل ET₀ اليومي للموقع، واختر Kc حسب المحصول ومرحلة نموه. كفاءة التطبيق تقدير يعكس حالة شبكة الري. لا تحسب الوحدة ET₀ من بيانات الطقس، ولا تخصم المطر أو تضيف احتياجات الغسيل ومعالجة الملوحة. يمكن تمرير الحجم الإجمالي لكل قطاع إلى `schedule_irrigation_sectors` لحساب مدة تشغيله.


## ربط احتياجات المحاصيل بجدولة القطاعات

بعد إنشاء تصميم القطاعات عبر `design_irrigation_sectors`، استخدم الدالة التالية لحساب الاحتياج اليومي لكل قطاع ثم مدة تشغيله:

```python
from irrigation.calculations import plan_daily_irrigation_from_crops

plan = plan_daily_irrigation_from_crops(
    sector_design=sector_design,
    crops_by_sector={
        "قطاع الأشجار": [
            {"name": "أشجار مثمرة", "kc": 0.8, "area_m2": 500.0},
        ],
        "قطاع الخضروات": [
            {"name": "خضروات", "kc": 1.1, "area_m2": 300.0},
        ],
    },
    et0_mm_day=5.0,
    application_efficiency_percent=90.0,
    available_runtime_hours_per_day=8.0,
)

print(plan["daily_irrigation_requirements_l"])
print(plan["schedule"]["sectors"])
print(plan["schedule"]["summary"]["fits_available_runtime"])
```

يجب أن تطابق أسماء المفاتيح في `crops_by_sector` أسماء القطاعات في التصميم. أدخل Kc والمساحة وفق المحاصيل ومراحل نموها الفعلية. تعرض النتيجة حجم الري الإجمالي اليومي لكل قطاع وزمن تشغيله، ثم توضح ما إذا كان مجموع الأزمنة يتناسب مع ساعات التشغيل المتاحة. لا تخصم الدالة المطر ولا تضيف احتياجات الغسيل أو تعديلات الملوحة.


## تقدير فاصل الري من خصائص التربة

استخدم `calculate_irrigation_trigger` لتقدير عدد الأيام بين الريات وكمية إعادة الملء وزمن التشغيل:

```python
from irrigation.calculations import calculate_irrigation_trigger

trigger = calculate_irrigation_trigger(
    field_capacity_vwc=0.30,
    wilting_point_vwc=0.15,
    root_depth_m=0.60,
    depletion_fraction=0.50,
    crop_et_mm_day=5.0,
    irrigated_area_m2=100.0,
    application_efficiency_percent=90.0,
    sector_flow_lph=1000.0,
)

print(trigger["soil_water"]["total_available_water_mm"])
print(trigger["soil_water"]["readily_available_water_mm"])
print(trigger["irrigation"]["estimated_interval_days"])
print(trigger["irrigation"]["gross_application_volume_l"])
print(trigger["irrigation"]["estimated_runtime_hours"])
```

في هذا المثال، TAW يساوي 90 مم، وRAW يساوي 45 مم، وفاصل الري التقديري 9 أيام. حجم إعادة الملء الإجمالي 5000 لتر، وزمن التشغيل 5 ساعات عند تدفق 1000 لتر/ساعة.

أدخل FC وWP ككسور حجمية، مثل 0.30 لا 30. استخدم عمق الجذور الفعال وقيمة p الملائمة للمحصول ومرحلة النمو. هذا تقدير تخطيطي يفترض تجانس التربة وإعادة الملء عند استنزاف RAW. لا يأخذ في الحسبان المطر أو الجزء المبتل تحت النقاطات أو الملوحة. راقب رطوبة التربة لتعديل موعد الري وكمية الماء.

## الوحدات

- التدفق في بيانات المضخة ومنحنى النظام: متر مكعب في الثانية.
- التدفق داخل القطاع: لتر في الساعة.
- الضغط: bar.
- الارتفاع والفواقد: متر من عمود الماء.
- أقطار الأنابيب: متر، ويجب إدخال القطر الداخلي الفعلي.

## قراءة النتائج

- `sector_analysis`: التدفق الكلي، ضغوط مداخل الخطوط والنقاطات، ونسبة النقاطات ضمن مجال الضغط.
- `pump_system_analysis.system`: نقاط منحنى النظام وفواقد الأنبوب.
- `pump_system_analysis.pump_analysis.operating_point`: التدفق والارتفاع عند نقطة تشغيل المضخة.
- `pump_system_analysis.pump_analysis.power`: القدرة الهيدروليكية وقدرة عمود المضخة، والقدرة الكهربائية عند إدخال كفاءة المحرك.
- `design_duty.operating_flow_matches_sector_design`: مقارنة تدفق نقطة التشغيل بتدفق القطاع التصميمي ضمن هامش تحدده أنت.

## حدود النموذج

1. يفترض تحليل القطاع خطوطاً متساوية الطول وعدد النقاطات والتدفق، وتفرعات متساوية التباعد. يدعم النموذج إدخال مناسيب مخارج المجمع ومناسيب النقاطات اختيارياً.
2. يمثل منحنى النظام أنبوباً رئيسياً واحداً ومعامل فاقد موضعياً إجمالياً.
3. أدخل منحنى المضخة وكفاءة المضخة من بيانات الشركة المصنّعة.
4. أدخل مجال ضغط النقاطة من بيانات المنتج. المجال الافتراضي 1 إلى 4 bar ليس مواصفة عامة.
5. أدخل مناسيب مخارج المجمع في `lateral_takeoff_elevations_m` ومناسيب النقاطات في `emitter_elevations_m`. القيم موجبة عند الصعود، وتقاس كل مجموعة نسبةً إلى مدخلها. أدخل فرق المنسوب بين مصدر الماء ومدخل القطاع ضمن `static_elevation_difference_m`. أضف فواقد المرشح والصمامات والعدادات وخط السحب أيضاً.
6. لا تعتمد النتائج للتنفيذ قبل مراجعة الموقع وبيانات المعدات والتحقق الميداني.

## تشغيل الاختبارات

```bash
python -m pytest irrigation/tests -v
```

## التشغيل من سطر الأوامر

يوفر المشروع واجهة JSON لتشغيل التحليل دون كتابة برنامج Python:

```bash
python -m irrigation design examples/drip_irrigation_design.json --output report.json
```

يمكن تمرير البيانات عبر الإدخال القياسي أيضاً:

```bash
cat examples/drip_irrigation_design.json | python -m irrigation design -
```

الملف الموجود في `examples/drip_irrigation_design.json` مثال تعليمي ببيانات افتراضية. استبدل منحنى المضخة وكفاءتها وأبعاد الأنابيب وضغوط النقاطات ببيانات المعدات والموقع قبل أي استخدام هندسي.


## تقدير الغسيل للحد من تراكم الأملاح في الري بالتنقيط

```python
from irrigation.calculations import calculate_drip_leaching_requirement

leaching = calculate_drip_leaching_requirement(
    irrigation_water_ec_ds_m=1.2,
    crop_max_soil_ec_ds_m=3.0,
    net_irrigation_depth_mm=5.0,
    irrigated_area_m2=100.0,
    application_efficiency_percent=90.0,
    sector_flow_lph=1000.0,
)

print(leaching["leaching"]["required_leaching_percent"])
print(leaching["leaching"]["additional_net_leaching_depth_mm"])
print(leaching["application"]["gross_application_volume_l"])
print(leaching["application"]["estimated_runtime_hours"])
```

تستخدم الدالة معادلة الري بالتنقيط عالي التواتر: LR = ECw ÷ (2 × ECe_max). في المثال، ECw يساوي 1.2 dS/m وECe_max يساوي 3 dS/m، فتكون نسبة الغسيل التقديرية 20%. يرتفع عمق الاحتياج الصافي من 5 إلى 6.25 مم قبل تصحيح كفاءة التطبيق. أدخل ملوحة الماء من تحليل مخبري، واختر ECe_max وفق المحصول ومستوى الإنتاج المقبول.

هذا تقدير أولي. يشترط صرف فعال لإخراج الأملاح من منطقة الجذور. لا تضف ماء الغسيل إلى برنامج الري دون فحص الصرف وملوحة التربة وماء الري. لا تستخدم هذه المعادلة المخصصة للري بالتنقيط لحساب الغسيل بالري السطحي.
