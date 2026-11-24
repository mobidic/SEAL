# Releases

## v1.2.0 - 2026-11-24

This release features significant improvements, as well as a few fixes.

### 🚨 Breaking Changes

- **DataBase model**: the model of database was update to integrate some new features

### ✨ New Features

- **GRCh38 support**: SEAL now runs on both GRCh37 and GRCh38, with GRCh38 as the default genome build (need 2 different instancies)
- **Multi variant-caller support** : import several VCFs for the same sample, one per caller (GATK-hc, DeepVariant, FreeBayes, ...) (#55)
- **HPO**: HPO terms for samples (#31)
- **Tag system**: add tags to samples (#42)
- **IGV.js**: fully local visualization of BAM, BED and VCF files
- **CovReport**: new dedicated coverage report view
- **Utilities**: add some utilities

### 🛠️ Improvements

- **Artefact**: the old hidden feature is now an artefact tag system
- **ClinVar filtering**: filter on ClinVar classification and confidence stars (#77)
- **Family info**: improved family data to prepare de novo / family filtering
- **Runs management**: run edition backend, run occurrences and per-run variant occurrence counts (#44)
- **Index / Affected status**: status added to the sample table, with dedicated filtering options
- **Static cache busting**: assets URL now carry a version parameter to force browser reload after each deployment
- **Highest missense score**: the highest missense mean score is now available 
- **Add some links** : Mutalyzer3, spliceAI lookup, UCSC (#78)

### ⚡️ Performance

- **Optimization**: some code and requests optimization


### 🐛 Fixes

- Reported depth / VCF AD mismatch on import: correct DP and AD extraction (#84)
- DefGen export (class names, sample name, AF for family samples)
- Prediction scores returned in filter and export columns; MaxEntScan origin-data
- Sorting on the Gene column, allele frequency formatted to two decimals
- Scheduler issues when importing another VCF or a new sample
- ClinVar auto-upload: new method (urllib instead of deprecated ftplib), no more threading
- API token ordering + second token for adding callers
- Session cookie naming to avoid conflicts when running multiple instances
- Minor UI fixes: sidebar, DataTables footer alignment, swal messages, artefact opacity

### 🔒 Dependencies

- Add pyyaml (#65)
- Upgrade jQuery-UI, SweetAlert, FontAwesome

## v1.1.9 - 2024-02-21

This minor version mainly fix some bugs.

### Fixes

* Fix some typo
* Fix locker when ftp of ncbi not reached
* Update Links for GnomAD

### Known Issues

* **Initialisation of database** (#26)

## v1.1.8 - 2023-11-08

This minor version mainly fix some bugs.

### Fixes

* **ClinVar stats and conf** when import a new variant
* Cron ID
* Default filter
* **FontAwesome**: path and webfonts

### Known Issues

* **Initialisation of database** (#26)


## v1.1.7 - 2023-11-07

This minor version mainly fix some bugs and improve performances.

### New Features

* **Auto-update ClinVar**  source file

### Fixes

* **Export column ClinVar**
* **Export to DefGen**
* **Some fixes**

### Known Issues

* **Initialisation of database** (#26)

## v1.1.6 - 2023-10-11

This minor version mainly enhances fix some bugs and add new features.

### New Features

* **Update ClinVar VCF in VEP** 
  - replace plugins ClinVar and use VCF from ClinVar
  - add ClinVar into models
  - create a filter for ClinVar
  - add page to update ClinVar
* **Export for DefGen** : Add a button to export in DefGen compatible format
* **Variants into the family** : add genotype informations for all samples of the same family for all variants

### Fixes

* **Sort HGVSc**
* **Rename Family**
* **Some fixes**

### Other Changes

* **Update FontAwesome** -> 6.4.2
* **Exon or Intron**: Use font weight to distinguish exons or introns prosition into main variant info.

### Known Issues

*   **Initialisation of database** (#26)

## v1.1.5 - 2023-07-05

This minor version mainly enhances fix some bugs and improve performances.

### New Features

*   **Modal population**: representation of gnomAD on a barplot  (#47, 96155d2d6b67499c679b90b55d63e409f3ad14b5)
*   **Add the possibility of modifying the family** (#17, 91073efd2b1d4453fbdb647d62fd9246fae9f9d6)
*   **Better export**: add phenotype on export (eb16c76daf94daab464dcca6a17127602993356b)
*   Other minor front-end and back-ends enhancements 

### Fixes

*   **Flask Admin Template**: use lower case for bootswatch theme (671fd4385a5b34d95f3040157724c14de6dc2fe2)
*   **Header for variant view**: call this method once (#50, 7c4a8e8d157c0bcfec8955999791126f2035a782)
*   **Sample status 0**: fixed a bug where the sample status was set to 0. It should have appeared in the "import" status and not in the "error" status. (b583e86b0f06a8e3114580edf61a3ffdb4e1a27b)
*   **Annotations**: an error on a variable name results in the annotation not being imported. (b583e86b0f06a8e3114580edf61a3ffdb4e1a27b)

### Other Changes

*   **Performance optimisation**: use sqlalchemy request to replace python len() function (14d1151f2f00ea881a78a0dc82e1f9a5cde68b9b)
* **Add license GNU GPLv3 or later** (5d7a61f44f7cc3f600da00a71430be852c8d9034)
*   **Documentation**

### Known Issues

*   **Initialisation of database** (#26)

## v1.1.4 - 2023-06-30

This minor version mainly enhances the interface to improve the user and administrator experience.

### New Features

*   **Add Hide variant in database**: keep variant hidden when reload page  (9d7ecda9cb5eef3127e49b72a2eb747774f31694, 01172c71a65cb961c096adb7e54f62dd7e3491cd)
*   **New Admin Interface** (5f41bd2a3463b666ef730bef48a3718c105b0869, cbba08477c6b73b03d04878d48934ae6470b69c4)
*   **Redraw cell** when changes are made (e94baab0abf63f92ca851e842a6a0b29e512e9ff, 5170e2982f9722798ce6c59e6fc9e288d014340b)
*   **Add Last Action** for samples : sorts the sample table by modification date (141a243e89354e99db79a20b638839a6b7b3265d, 700fe0241445630f0f631b3bff080ce101990509)
*   **Add Releases Note** in about page (49b118c09e778c2b99a6e2f5ee11a615b1753f94)
*   Other minor front-end and back-ends enhancements 

### Fixes

*   **AjaxSetup**: call this method once (b3f81c763519da79692fe2bf8af2134f187c6b79)
*   **Add default date**: for tables History, Comment\_sample and Comment\_variant (13255682dd7e04c49cdecaf07bcb01d86d7dfc32)

### Other Changes

*   **Occurences**: hits now come from the entire database (#43, 22d642048119e8864332eae235fc51bc1b66668b)
*   **Documentation** (08993dd70335a7e8f6e778a2ec03a9bf1894bc5d)

### Known Issues

*   **Initialisation of database** (#26)

## v1.1.3 - 2023-06-13

This minor version mainly enhances the interface to improve the user experience.

### New Features

- **Add new status : *Archived*** (89613ac58b8cdce9335b617e7f86d91a2fff5eb1, 7dea7e619b0b5b9cacffa14081e9e1f7e087d869)
- **Better table variant**
  - Add subheader (46824d861ebc979d6c431454836d19f73b53eea4)
  - Reorder, delete and merge columns (c4f8c1c35e9c296877d59e4a7e54cbc3390a364f, 759ad7b045730a9182fa68a1acae0efb6c4450a3)
  - Add some extra links (Franklin & GnomAD) (3a4d7c8aead6e8fb03eeae94fa89f3be66dfd910)
  - Add SweetAlert (15ce8dbd2f1fd35a6348507b60eee7710ba10fda, 2513532e9f318b53785cbbd3222576d5ba2b19ae)
  - Add possibility to hide some rows (d8f185fc42ee4f9c15b3d958fb44885aac2d4bb9)
  - Add possibility to edit filter (#13, 1203f10562d928b592f1916c664abc60314edce0)
- Other minor front-end enhancements

### Fixes

- **Fix security issues** (1f5d2c60cb9c79ca40d9da0d23fc50c0fc3b9197, 16cd244488bc3b77328aa63d8d6a0ea75a10698f, 33fec8d294341e28cae4b162d77de96713d0eafe, 5ce5d09df9b7441855f5e087b41801def482b9fa, a1c8583d4cad05b2b749e69172e22e0b0333de94)
- **Fix status on sidebar** (1b6006eaf6acddc5c864901284774ded03ee4cc3

### Known Issues

- **Initialisation of database** (#26)

## v1.1.2 - 2023-03-01

This minor release features significant documentation improvements, as well as a few front-end tweaks to enhance usability and user experience.

### New Features

- **Frequency of variant calculate from "visible" sample (SEAL count)** (795a640c495df75db1d7c676f5c4bbe3e2247d4b)
- **Add warnings (banner) if not production version** (976d61e1a035e1dcd5193e43d65289fffec42dd3, 3596e624887e2c96710d29b37d282f5d072f0544)
- **Add ability to edit some sample fields** (bc6657ef89e6dbac1accaae8e3bb6e291f3c5496, 23f3637ba9fda840c0a7b1ff68a6c2c2d2590abd)
- **Use a config file to launch the app** (3596e624887e2c96710d29b37d282f5d072f0544)

### Bug Fixes

- **JSON Variant : Check if a sample id is provided** (#38)

### Other Changes

- **Upgrade DataTable** (9288adcfaa58ed073e9aa36395c3315905abb7a0, 210e5a959195efbda3b3db668cc6355f4dd7ba90)
- **Improve handling exception in scheduler** (5d96e6a2dc968242326361554a868e2f337806c3)
- **Documentation**

### Known Issues

- **Initialisation of database** (#26)

## v1.1.1 - 2023-02-15

This minor update brings a number of front-end improvements that are designed to enhance the user experience.

### Bug Fixes

- **MobiDetails API key check**
- **CSRF error redirection on login**
- **Fixed Header of variant table** (#35)

### Other Changes

- **Upgrade DataTable** (d2f70204f9190ca9493fa6fc4fcdb4dfa0b65496)
- **Add labels for update account view** (cf1f0a69e02e3a4d58529e4a284f0c65076ae1a1)
- **Some Style**

### Known Issues

- **Initialisation of database** (#26)


## v1.1.0 - 2023-02-06

We are excited to announce the new release of SEAL 🎉 .
This update cames with a range of new features, bug fixes and improvements for better maintanability.
Read on for full details!

### New Features 

- **History of samples** (e9243df652af1e65d091673e0b0602cb2cf24040, a5f6d0407abcbebe84edf49241ec0b790d23c93c)
- **Use of personal MobiDetails API key** (620b470404829a002bf6a08b4474b2529b910a66)
- **Comments on samples** (0fce09265c514ef64be68bac6d931b5630ee8468, e32984c12d59146d6096667654fb0f21ad42b6db)
- **Filter and bed in sample form** (6a0af55eae7ae49584b294db22144a2483327af9)
- **Export only reported variants** (12e158297946acd69c2d518a9e8a2a9730787437)
- **Maintenance mode** (599aa56ac060deb604960e95965becb5a4b0be5b)
- **Ability to check panels** (#19, 1e4e780d0928e90b3bade350c6cc635724162fc1)

### Bug Fixes

- **Filter variants on class and report** (#21)
- **Password bug in admin interface** (#29)
- **Exportation of datatables** (#34)
- **Filter on clinsig** (#36)
- **CSS fixes**

### Other Changes

- **Upgrade dependencies** (4088a6d58a5c024c739fdee5997d1e7a11c8a586)
- **Better maintainability** (4ae94ab2e7d2f07bef371a17903888df0dbb58a8)
- **Select2 replacement** (c610a477f06d6fce5e6abf9971c8cdb8dfbbc6c0)
- **Auto-refresh** (ecd7518aa48473f73749cb65bd1ea1b840579d7b)

### Known Issues

- **Initialisation of database** (#26)
- **Fixed header of datatables when scrolling** (#35)

### How to Upgrade

It can be a bit tricky to update the database (see #33).


## v1.0.0 - 

We are proud to announce the first official release of SEAL, a web application for analyzing and annotating genetic variants.

In this initial release, SEAL includes the following key features:

- An intuitive interface for uploading and managing VCF files
- Annotation of variants using the Ensembl Variant Effect Predictor (VEP)
- Sample and family management tools for tracking variant inheritance patterns
- A rich set of visualizations and reports to help interpret variant data

---

**/!\ Please note that this is a minimum viable product and there may be some known issues or limitations.
We encourage users to report any bugs or suggestions for improvement through our issue tracker.**

---

To get started with SEAL, simply follow the installation instructions in the [README](https://github.com/mobidic/SEAL) for more information.

We would like to extend a special thank you to all of the contributors who helped make this release possible. We are excited to continue developing and improving SEAL in the future.