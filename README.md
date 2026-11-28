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

- Flow and emitter discharge calculations.
- Hazen-Williams pipe and dripline head losses.
- Emitter pressure analysis for compensating and non-compensating emitters.
- Manifold and irrigation-sector hydraulic analysis.
- Pipe sizing, velocity, pressure rating, and economic comparisons.
- Pump curves, operating point, system curve, HMT, and power.
- Integrated sector-to-pump workflow.
- JSON command-line interface.
- Daily crop-water demand and sequential sector runtime planning from ET₀, Kc, planted area, and application efficiency.
- FAO-56 soil-water storage, irrigation trigger interval, refill volume, and sector runtime estimates.

## Hydraulic Methodology

See [HYDRAULIC_METHODS.md](HYDRAULIC_METHODS.md) for equations, assumptions, reference sources, and model limitations.

## Quick Start

Install the package and development tools:

```bash
python -m pip install -e ".[dev]"
```

Run the example design:

```bash
agritech-irrigation design examples/drip_irrigation_design.json --output report.json
```

The example uses illustrative values only. Replace pump curves, emitter pressure limits, pipe dimensions, and site data with verified project information.

See [QUICKSTART_AR.md](QUICKSTART_AR.md) for the complete Arabic guide.

## Testing

Run the suite:

```bash
python -m pytest irrigation/tests -v
```

GitHub Actions installs the package and runs the test suite on pushes to `main` and pull requests targeting `main`.

## Development Status

The irrigation calculation package and command-line workflow are implemented for the documented scope. Further engineering validation and additional network configurations remain under active development. Review model assumptions and manufacturer data before field deployment.

Version: 0.1.0
