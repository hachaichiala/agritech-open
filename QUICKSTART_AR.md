# دليل التشغيل السريع بالعربية

## الهدف

توفّر الدالة `design_drip_irrigation_system` مساراً موحداً لتحليل قطاع ري بالتنقيط، وبناء منحنى النظام، ثم تحديد نقطة تقاطع منحنى المضخة مع منحنى النظام وحساب القدرة.

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

1. يفترض تحليل القطاع خطوطاً متساوية الطول وعدد النقاطات والتدفق، ومجمعاً أفقياً ذا تفرعات متساوية.
2. يمثل منحنى النظام أنبوباً رئيسياً واحداً ومعامل فاقد موضعياً إجمالياً.
3. أدخل منحنى المضخة وكفاءة المضخة من بيانات الشركة المصنّعة.
4. أدخل مجال ضغط النقاطة من بيانات المنتج. المجال الافتراضي 1 إلى 4 bar ليس مواصفة عامة.
5. أضف فواقد المرشح والصمامات والعدادات وخط السحب وفروق المناسيب عندما تكون مؤثرة.
6. لا تعتمد النتائج للتنفيذ قبل مراجعة الموقع وبيانات المعدات والتحقق الميداني.

## تشغيل الاختبارات

```bash
python -m pytest irrigation/tests -v
```
