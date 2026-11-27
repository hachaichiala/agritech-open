AgriTech Open


Open-source agricultural tools for water management and irrigation design.


العربية | Français | English



العربية


من نحن؟


AgriTech Open مشروع مفتوح المصدر يهدف إلى تطوير أدوات تقنية وعلمية تخدم الفلاحين والمهندسين والفنيين في المجال الزراعي.


نركز على إدارة المياه وتصميم أنظمة الري، مع مراعاة ظروف المناطق الجافة وشبه الجافة.


الأداة الأولى: تصميم شبكات الري بالتنقيط


نعمل على تطوير محرك حساب هيدروليكي يساعد على:




حساب التدفق المائي المطلوب.


تحديد أقطار الأنابيب المناسبة.


حساب فواقد الضغط.


تقسيم شبكة الري إلى قطاعات.


تقدير ضغط التشغيل وارتفاع الضخ الإجمالي (HMT).


تقييم أداء شبكة الري.




مبادئ المشروع




مصادر مفتوحة وشفافة.


حسابات علمية قابلة للتحقق.


توثيق واضح ومتعدد اللغات.


أدوات عملية مستقلة عن الشركات المصنعة للمعدات.




المساهمة


نرحب بمساهمات المطورين والمهندسين والفلاحين والباحثين.



Français


À propos


AgriTech Open est un projet open source dédié au développement d'outils techniques et scientifiques pour les agriculteurs, les ingénieurs et les techniciens agricoles.


Le projet se concentre sur la gestion de l'eau et la conception des systèmes d'irrigation, notamment dans les régions arides et semi-arides.


Premier outil : conception des réseaux goutte-à-goutte


Nous développons un moteur de calcul hydraulique permettant de :




Calculer les débits nécessaires.


Déterminer les diamètres des conduites.


Calculer les pertes de charge.


Organiser le réseau en secteurs d'irrigation.


Estimer la pression de fonctionnement et la hauteur manométrique totale (HMT).


Évaluer les performances du réseau.




Nos principes




Code source ouvert et transparent.


Calculs scientifiques vérifiables.


Documentation multilingue.


Outils indépendants des fabricants de matériel.




Contribution


Les contributions des développeurs, ingénieurs, agriculteurs et chercheurs sont les bienvenues.



English


About


AgriTech Open is an open-source project focused on developing practical and scientific tools for farmers, agricultural engineers, and irrigation technicians.


The project focuses on water management and irrigation system design, especially in arid and semi-arid regions.


First tool: Drip Irrigation Design


We are developing a hydraulic calculation engine to support:




Water flow calculations.


Pipe diameter selection.


Hydraulic head loss calculations.


Irrigation sector planning.


Operating pressure and Total Dynamic Head (TDH) estimation.


Irrigation network performance evaluation.




Project principles




Open and transparent source code.


Verifiable scientific calculations.


Multilingual documentation.


Tools independent of equipment manufacturers.




Contributing


Contributions from developers, engineers, farmers, and researchers are welcome.



License


This project is licensed under the MIT License. See the LICENSE file for details.


Project status


Active development of the irrigation calculation engine.

## Current Features

- Total irrigation flow calculation.
- Emitter quantity and tree-zone flow calculation.
- Hazen-Williams pressure loss calculation.
- Hydraulic unit conversions.
- Initial dripline friction loss estimation.

## Hydraulic Methodology

See [HYDRAULIC_METHODS.md](HYDRAULIC_METHODS.md) for the equations, assumptions, reference sources, and current model limitations.

## Quick Start

Use the integrated sector-to-pump workflow with the [Arabic quick-start guide](QUICKSTART_AR.md). The public function `design_drip_irrigation_system` combines sector pressure analysis, system-curve construction, pump operating-point analysis, and power estimation using the existing calculation modules.

## Testing

The project uses pytest for automated testing.

Run the full irrigation test suite locally with:

```bash
python -m pytest irrigation/tests -v
```

GitHub Actions runs this test suite automatically on pushes to `main`
and on pull requests targeting `main`.

## Development Status

### Pressure-Compensating Emitters

The irrigation engine includes preliminary pressure
validation for pressure-compensating (PC) emitters.

Features:
- Configurable emitter operating pressure range.
- Inlet and outlet pressure calculations.
- Dripline friction loss integration.
- Automatic pressure compensation range checks.

The default pressure range (1 to 4 bar) is temporary
and must be replaced with manufacturer specifications.


Version: 0.1.0

The irrigation calculation engine is under active development.
All hydraulic models require further validation before field deployment.

