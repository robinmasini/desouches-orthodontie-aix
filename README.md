# Site du Dr Renaud Desouches — Orthodontiste à Aix-en-Provence

Version 1, statique (HTML/CSS/JS, aucune dépendance, aucun build front).

## Lancer en local

```bash
cd site
python3 -m http.server 8000
```

Puis ouvrir <http://localhost:8000>.

Testé sans framework : n'importe quel serveur statique convient (`npx serve`, Live Server, Nginx…).
Ouvrir les fichiers en `file://` fonctionne aussi, mais les polices Google et les chemins relatifs
sont plus fiables via un serveur.

## Structure

```
index.html                 Accueil — maquette Claude Design, autonome
_partiels.html             En-tête et pied des pages intérieures
build.py                   Génère les 27 pages intérieures
assets/css/site.css        Système de design des pages intérieures
assets/js/site.js          Arcade interactive, navigation, séquences, FAQ, comparateurs
assets/img/                Visuels
sitemap.xml, robots.txt    Générés par build.py
```

**L'accueil est la maquette Claude Design reprise telle quelle** : styles en ligne,
animations liées au défilement, aucune dépendance à `site.css`. On l'édite directement.

**Les 27 pages intérieures** partagent l'en-tête et le pied de `_partiels.html`.
Pour modifier le menu ou le footer : éditer `_partiels.html`, puis relancer
`python3 build.py`.

Pour modifier le contenu d'une page intérieure : éditer le bloc correspondant dans `build.py`
(les pages sont dans l'ordre de l'arborescence fournie), puis relancer le script.
Toute modification directe d'un `.html` généré sera écrasée au prochain build.

## Pages livrées

Les 25 pages de l'arborescence sont en place, plus les pages légales :
accueil, aligneurs, déroulement du traitement, conception et fabrication, Dental Monitoring,
aligneurs ou bagues, Invisalign, orthodontie de l'enfant, bilan 6–7 ans, adolescent,
aligneurs enfant/ado, orthodontie adulte, aligneurs adulte, Ortho Mind, avant/après,
problèmes orthodontiques, Dr Desouches, notre approche, technologie, Casper Dental,
tarifs, FAQ, cabinet, rendez-vous, mentions légales, confidentialité, cookies, données de santé.

## À renseigner avant mise en ligne

| Élément | Où |
|---|---|
| Adresse, téléphone, horaires | `cabinet-aix-en-provence.html`, `rendez-vous.html`, JSON-LD de `index.html` |
| Lien Doctolib | `rendez-vous.html`, boutons « Prendre rendez-vous » |
| Lien vers le site Casper Dental | `casper-dental.html` |
| Parcours, formation, titres du Dr Desouches | `dr-renaud-desouches.html` |
| Grille tarifaire | `tarifs.html` |
| Photos cliniques avant/après | `avant-apres.html` — schémas SVG en attendant |
| Mentions légales, RGPD, hébergeur HDS | pages légales |
| Domaine réel | constante `DOMAINE` dans `build.py` + `<link rel="canonical">` de `index.html` |
| Bandeau cookies | à intégrer avant la carte Google Maps et tout script tiers |

Les zones concernées sont signalées dans les pages par un encart à filet rouge.

## Design

| Rôle | Valeur |
|---|---|
| Fond | Porcelaine `#F0F3F7` |
| Plans | Blanc verre `#FFFFFF` |
| Texte et sections sombres | Bleu marine `#10233F` |
| Structure secondaire | Vert d'eau `#C3D3E6` / `#DFE7F2` |
| Accent unique | Azur `#1F6FE0` |

Typographie : **Barlow Condensed** (titres) sur **Barlow** (texte courant), via Google Fonts.

Le parti-pris : marine dominant, un seul azur pour les éléments cliquables et les états
actifs, filets fins et motif d'arcade. Sur fond marine le bouton principal passe en clair,
le contraste azur/marine étant insuffisant pour du texte.

## Interactions

- **Arcade du hero** : SVG généré en JS, interpolé entre encombrement et alignement.
  S'anime une fois au chargement, puis passe la main au curseur. Compteur d'aligneurs synchronisé.
- **Comparateurs avant/après** : glissière au pointeur, même moteur SVG.
- **Séquences numérotées** : jauge de progression liée au défilement.
- **Filtres de la galerie**, **FAQ**, **menus** : accessibles au clavier, `aria-expanded` géré.
- **Mouvement lié au défilement** (section 19 du CSS) : jauge de lecture, parallaxe,
  révélations et pivot 3D du hero, en `animation-timeline: scroll()` / `view()`.
  Aucune bibliothèque, aucun JavaScript.
- `prefers-reduced-motion` respecté : toutes les animations sont neutralisées.

### Support des animations liées au défilement

`animation-timeline` fonctionne sur Chrome, Edge et Safari 26+. Ailleurs (Firefox,
Safari plus ancien), le bloc `@supports` n'est pas appliqué et les révélations
`IntersectionObserver` de `site.js` prennent le relais ; la scène du hero garde une
inclinaison fixe. Le site reste complet dans les deux cas.

### Ajouter du mouvement à un élément

| Attribut | Effet |
|---|---|
| `data-reveler` (+ `data-reveler-delai="1..3"`) | Apparition par le bas, décalée |
| `data-derive` / `data-derive="bas"` / `data-derive="incline"` | Parallaxe |
| `data-balayage` | Révélation par balayage horizontal |
| `.scene-3d` sur un parent | Perspective + pivot 3D au défilement |

## SEO en place

URL propres · un seul H1 par page · hiérarchie H2/H3 · title et meta description calibrés
(vérifiés < 68 et < 166 caractères) · canonical · Open Graph · JSON-LD
(`Dentist`, `Physician`, `FAQPage`, `WebPage`) · maillage interne · fil d'Ariane ·
`sitemap.xml` · `robots.txt` · attributs `alt` · dimensions d'images ·
aucune dépendance JS bloquante.

Requêtes visées, une page par intention : orthodontiste Aix-en-Provence · aligneurs
Aix-en-Provence · Invisalign Aix · orthodontiste enfant / adulte Aix · gouttières
orthodontiques Aix · prix orthodontiste Aix · bilan 6–7 ans.

## Points d'attention

- La photo du praticien fait 1 Mo. À convertir en WebP/AVIF et à décliner en plusieurs
  tailles avant la mise en production.
- Les polices sont chargées depuis Google Fonts. Pour la performance et le RGPD,
  les auto-héberger.
- Aucune image de patient ne doit être publiée sans autorisation écrite.
