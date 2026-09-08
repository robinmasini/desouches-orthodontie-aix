#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les pages intérieures du site du Dr Renaud Desouches.
L'en-tête et le pied de page sont extraits de index.html : une seule source.

Usage :  python3 build.py
"""
import os, re, json, hashlib, datetime

RACINE = os.path.dirname(os.path.abspath(__file__))
DOMAINE = "https://desouches-orthodontie-aix.com"


def empreinte(chemin):
    """Hachage court du contenu d'un asset.

    Vercel sert /assets/ en Cache-Control immutable pendant un an. Sans cette
    empreinte dans l'URL, un visiteur déjà venu garderait l'ancien CSS ou JS
    et ne verrait jamais les corrections."""
    with open(os.path.join(RACINE, chemin), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:8]

# --------------------------------------------------------------------------
# 1. Extraction de l'en-tête et du pied depuis l'accueil
# --------------------------------------------------------------------------
PARTIELS = os.path.join(RACINE, "_partiels.html")
with open(PARTIELS, encoding="utf-8") as f:
    _P = f.read()

ENTETE = _P.split("<!-- ENTETE -->")[1].split("<!-- /ENTETE -->")[0].strip()
PIED   = _P.split("<!-- PIED -->")[1].split("<!-- /PIED -->")[0].strip()


def marquer_actif(html, slug):
    """Ajoute aria-current sur le lien de navigation correspondant."""
    return html.replace('href="%s"' % slug, 'href="%s" aria-current="page"' % slug, 1)


# --------------------------------------------------------------------------
# 2. Briques de contenu
# --------------------------------------------------------------------------
FLECHE = ('<span class="puce" aria-hidden="true"><svg viewBox="0 0 12 12">'
          '<path d="M1 6h10M7 2l4 4-4 4" fill="none" stroke="currentColor" '
          'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span>')


def btn(texte, href, style="fantome", fleche=False):
    cls = "btn btn--primaire" if style == "primaire" else "btn btn--fantome"
    ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
    # L'évaluation en ligne n'est pas encore ouverte : le CTA ouvre une modale.
    # Le href reste le repli si JavaScript est indisponible.
    marque = ' data-eval' if "Évaluation Orthodontique" in texte else ""
    return '<a class="%s" href="%s"%s%s>%s%s</a>' % (cls, href, ext, marque, texte, FLECHE if fleche else "")


def visuel(fichier, alt, legende=None, ratio="3/2", variante="", largeur=None, hauteur=None):
    """Figure illustrée. variante : "" (photo recadrée), "detoure", "logo"."""
    cls = "visuel" + ((" visuel--" + variante) if variante else "")
    dims = ' width="%s" height="%s"' % (largeur, hauteur) if largeur else ""
    cap = '<figcaption class="legende">%s</figcaption>' % legende if legende else ""
    return ('<figure class="visuel-bloc" data-reveler>'
            '<div class="%s" style="aspect-ratio:%s">'
            '<img src="assets/img/%s" alt="%s" loading="lazy" decoding="async"%s></div>%s</figure>'
            % (cls, ratio, fichier, alt, dims, cap))


# Visuels injectés dans les pages intérieures, juste avant l'appel final.
# Chaque entrée : (fichier, alt, légende, ratio, variante, bande)
VISUELS = {
    "aligneurs.html": ("aligneur.webp",
        "Aligneur orthodontique transparent vu de trois quarts",
        "Un aligneur : une coque transparente moulée sur la forme exacte de l’arcade.",
        "16/9", "detoure", "verre"),
    "conception-fabrication.html": ("gouttiere.webp",
        "Gouttière orthodontique transparente équipée de son dispositif",
        "Chaque gouttière est contrôlée avant d’être remise au patient.",
        "16/9", "detoure", "marine"),
    "aligneurs-ou-bagues.html": ("multi-attaches.webp",
        "Sourire portant un appareil orthodontique multibague en métal",
        "Les appareils fixes conservent des indications précises.",
        "16/9", "", "verre"),
    "cabinet-aix-en-provence.html": ("cabinet-2.webp",
        "Salle de soins du cabinet d’orthodontie, fauteuil et écrans muraux",
        "Une salle de soins du cabinet.",
        "3/2", "", "verre"),
    "technologie.html": ("cabinet.webp",
        "Poste de travail équipé d’un écran et d’un scanner intra-oral",
        "L’empreinte optique remplace les pâtes à empreinte.",
        "3/2", "", "verre"),
    "ortho-mind.html": ("orthomind-lockup.webp",
        "Logotype OrthoMind",
        None, "5/2", "logo", "verre"),
    "casper-dental.html": ("casper.webp",
        "Logotype Casper Dental",
        None, "5/2", "logo", "verre"),
    "dr-renaud-desouches.html": ("team.webp",
        "L’équipe du cabinet du Dr Renaud Desouches réunie en tenue professionnelle",
        "Le Dr Desouches et son équipe : Sandrine, Magali et Emeline, assistantes dentaires qualifiées, Fiona et Samantha, prothésistes dentaires.",
        "16/9", "", "verre"),
    "aligneurs-adulte.html": ("enfants.webp",
        "Personne souriante en extérieur",
        None, "3/2", "", "verre"),
}


def boutons(*items):
    return '<div class="groupe-btn">%s</div>' % "".join(items)


def liste(items):
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items)


def sequence(etapes):
    out = ['<div class="sequence" data-reveler>',
           '<span class="sequence__rail" aria-hidden="true"><span class="sequence__jauge"></span></span>']
    for i, (titre, texte) in enumerate(etapes, 1):
        out.append('<div class="etape"><span class="etape__puce">%02d</span>'
                   '<h3>%s</h3><p>%s</p></div>' % (i, titre, texte))
    out.append("</div>")
    return "".join(out)


def faq(items, titre=None):
    out = []
    if titre:
        out.append('<h2 style="margin-bottom:.4rem">%s</h2>' % titre)
    out.append('<div class="faq" data-reveler>')
    for q, r in items:
        out.append(
            '<div class="faq__item">'
            '<button class="faq__q" aria-expanded="false">%s'
            '<span class="faq__croix" aria-hidden="true"></span></button>'
            '<div class="faq__r"><div><p>%s</p></div></div></div>' % (q, r))
    out.append("</div>")
    return "".join(out)


def bande(contenu, variante="", serree=False, reveler=True):
    cls = "bande"
    if variante:
        cls += " bande--" + variante
    if serree:
        cls += " bande--serree"
    return '<section class="%s"><div class="enveloppe">%s</div></section>' % (cls, contenu)


def duo(gauche, droite, modif="", collant=False):
    cls = "duo"
    if modif:
        cls += " duo--" + modif
    if collant:
        cls += " duo--collant"
    return ('<div class="%s"><div data-reveler>%s</div>'
            '<div data-reveler data-reveler-delai="1">%s</div></div>' % (cls, gauche, droite))


def titre_bloc(sur, h2, chapo=None):
    out = '<p class="sur-titre">%s</p><h2>%s</h2>' % (sur, h2)
    if chapo:
        out += '<p class="chapo" style="margin-top:1.4rem">%s</p>' % chapo
    return out


def prose(html):
    return '<div class="prose">%s</div>' % html


def avis(texte):
    return '<p class="avis"><span>%s</span></p>' % texte


def chiffres(items):
    cells = "".join('<div class="chiffre"><span class="chiffre__valeur">%s</span>'
                    '<span class="chiffre__legende">%s</span></div>' % (v, l) for v, l in items)
    return '<div class="chiffres" data-reveler>%s</div>' % cells


APPEL = bande(
    '<div data-reveler><p class="sur-titre">Prendre rendez-vous</p>'
    '<h2>Deux façons de commencer.</h2></div>'
    '<div class="appel__voies" data-reveler data-reveler-delai="1">'
    '<a class="voie" href="rendez-vous.html"><h3>Je veux consulter au cabinet</h3>'
    '<p>Première consultation, bilan orthodontique, examen clinique. Pour un enfant, '
    'un adolescent ou un adulte.</p>'
    '<span class="btn btn--primaire">Prendre rendez-vous%s</span></a>'
    '<a class="voie" data-eval href="ortho-mind.html"><h3>Je veux d’abord une évaluation en ligne</h3>'
    '<p>Quelques photos depuis votre téléphone, une première orientation avant de vous '
    'déplacer.</p><span class="btn btn--fantome">Démarrer mon Évaluation Orthodontique</span></a></div>' % FLECHE,
    variante="marine") .replace('<section class="bande bande--marine">',
                               '<section class="bande bande--marine appel">')


# --------------------------------------------------------------------------
# 3. Gabarit
# --------------------------------------------------------------------------
GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{domaine}/{slug}">
<meta property="og:type" content="article">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{domaine}/{slug}">
<meta name="theme-color" content="#FBFCFD">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="favicon-16.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/site.css?v={v_css}">
</head>
<body>
<a class="saut-contenu" href="#contenu">Aller au contenu</a>
<div class="jauge-page" aria-hidden="true"></div>
{entete}
<main id="contenu" class="contenu">
  <section class="tete-page">
    <div class="enveloppe">
      <nav class="fil" aria-label="Fil d’Ariane">
        <a href="index.html">Accueil</a><span>/</span>{rubrique}<span aria-current="page">{fil}</span>
      </nav>
      <h1>{h1}</h1>
      <p class="chapo">{chapo}</p>
      {actions}
    </div>
  </section>
{corps}
{appel}
</main>
{pied}
<script type="application/ld+json">
{schema}
</script>
<div class="modale" id="modale-eval" hidden role="dialog" aria-modal="true" aria-labelledby="modale-eval-titre">
  <div class="modale__voile" data-fermer></div>
  <div class="modale__carte">
    <button class="modale__fermer" type="button" data-fermer aria-label="Fermer">&times;</button>
    <img class="modale__logo" src="assets/img/orthomind-lockup.webp" alt="OrthoMind" width="315" height="444" loading="lazy" decoding="async">
    <h2 class="modale__titre" id="modale-eval-titre">Bientôt disponible</h2>
    <p class="modale__texte">L’évaluation orthodontique en ligne est en cours de finalisation. En attendant, le cabinet reste joignable pour un premier avis.</p>
    <div class="modale__actions">
      <a class="btn btn--primaire" href="rendez-vous.html">Prendre rendez-vous</a>
      <a class="modale__lien" href="ortho-mind.html">En savoir plus sur OrthoMind &rarr;</a>
    </div>
  </div>
</div>
<script src="assets/js/site.js?v={v_js}" defer></script>
</body>
</html>
"""


def fil_ariane(fil, url=None):
    if url:
        return '<a href="%s">%s</a><span>/</span>' % (url, fil)
    return ""


def schema_page(nom, slug, description, extra=None):
    base = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": nom,
        "description": description,
        "url": "%s/%s" % (DOMAINE, slug),
        "inLanguage": "fr-FR",
        "isPartOf": {"@type": "WebSite", "name": "Dr Renaud Desouches — Orthodontiste à Aix-en-Provence",
                     "url": DOMAINE + "/"},
        "about": {"@type": "MedicalSpecialty", "name": "Orthodontic"},
        "provider": {"@id": DOMAINE + "/#cabinet"}
    }
    if extra:
        base.update(extra)
    return json.dumps(base, ensure_ascii=False, indent=2)


def schema_faq(items):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", r)}}
                       for q, r in items]
    }, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------
# 4. Contenu des pages
# --------------------------------------------------------------------------
PAGES = []


def page(slug, title, description, h1, chapo, corps, fil, rubrique="", actions=None, schema=None):
    PAGES.append(dict(slug=slug, title=title, description=description, h1=h1, chapo=chapo,
                      corps=corps, fil=fil, rubrique=rubrique,
                      actions=actions if actions is not None else boutons(
                          btn("Prendre rendez-vous", "rendez-vous.html", "primaire", True),
                          btn("Démarrer mon Évaluation Orthodontique", "ortho-mind.html")),
                      schema=schema or schema_page(h1, slug, description)))


RUB_ALIGNEURS = fil_ariane("Aligneurs", "aligneurs.html")
RUB_ENFANTS = fil_ariane("Enfants &amp; ados", "orthodontie-enfant.html")
RUB_ADULTES = fil_ariane("Adultes", "orthodontie-adulte.html")
RUB_CABINET = fil_ariane("Le cabinet", "dr-renaud-desouches.html")

# ---- PAGE 2 : Aligneurs -----------------------------------------------------
faq_aligneurs = [
    ("Combien de temps dure un traitement par aligneurs ?",
     "Cela dépend entièrement de la situation de départ et de l’objectif. Une correction limitée peut se compter en quelques mois, une réorganisation complète des arcades en un an et demi à deux ans, parfois davantage. La durée annoncée en début de traitement repose sur la planification et suppose que le temps de port soit respecté."),
    ("Faut-il porter les gouttières la nuit ?",
     "Oui. Le port est continu, jour et nuit, en dehors des repas et du brossage. C’est même la nuit qui apporte les heures les plus faciles à tenir."),
    ("Peut-on boire avec ses aligneurs ?",
     "De l’eau, oui. Les boissons chaudes, sucrées ou colorées se prennent gouttières retirées : la chaleur peut déformer le matériau et le sucre reste piégé contre l’émail."),
    ("Que se passe-t-il si je perds un aligneur ?",
     "Il faut prévenir le cabinet sans attendre et remettre en place le précédent en attendant les instructions. Ne pas sauter d’étape : la série est une progression, pas une collection."),
    ("Les aligneurs suffisent-ils dans tous les cas ?",
     "Non. Certaines situations relèvent d’un appareil fixe, d’un dispositif complémentaire ou d’une prise en charge multidisciplinaire. C’est le rôle du bilan de le déterminer avant de s’engager."),
]
page(
    "aligneurs.html",
    "Aligneurs transparents à Aix-en-Provence | Dr Desouches",
    "Traitement par aligneurs transparents à Aix-en-Provence : principe, indications, durée, temps de port, suivi, contention, prix et remboursement.",
    "Traitement orthodontique par aligneurs à Aix-en-Provence",
    "Une série de gouttières transparentes, calculée à l’avance, qui déplace les dents par étapes successives. C’est le traitement que nous pratiquons le plus, chez l’enfant, l’adolescent et l’adulte.",
    bande(duo(
        titre_bloc("Le principe", "Une gouttière ne pousse pas une dent. Elle en contient le déplacement."),
        prose(
            "<p>Un aligneur est une coque en matériau transparent, fabriquée à partir de la forme exacte de vos arcades, mais dessinée pour une position légèrement différente de la position actuelle. En la mettant en bouche, vous appliquez une force douce et permanente qui amène progressivement la dent vers cette nouvelle position.</p>"
            "<p>Une fois le déplacement obtenu, la gouttière suivante prend le relais avec l’étape d’après. Le résultat final n’est jamais l’œuvre d’un aligneur : c’est celui d’une série entière, planifiée dent par dent avant même que la première gouttière ne soit fabriquée.</p>"
            "<h3>Des attachements, parfois</h3>"
            "<p>Certains mouvements — redresser une racine, faire tourner une prémolaire, extruder une dent — ne s’obtiennent pas avec une simple coque lisse. On colle alors de petits reliefs de la couleur de la dent, appelés attachements, qui donnent à l’aligneur une prise. Ils sont retirés en fin de traitement.</p>"
        ), collant=True)) +
    bande(duo(
        titre_bloc("Indications", "Ce que l’on traite couramment par aligneurs."),
        prose(
            liste([
                "Un <strong>encombrement</strong> : des dents qui se chevauchent par manque de place.",
                "Des <strong>espaces</strong> entre les dents, dont le diastème médian.",
                "Des <strong>incisives projetées vers l’avant</strong>.",
                "Une <strong>supraclusion</strong> : les dents du haut recouvrent trop celles du bas.",
                "Une <strong>béance</strong> : les dents ne se touchent pas à la fermeture.",
                "Un <strong>articulé croisé</strong> localisé.",
                "Une <strong>récidive</strong> après un traitement orthodontique ancien.",
                "Une préparation avant <strong>prothèse, implant ou soin parodontal</strong>.",
            ]) +
            "<h3>Et ce qui demande autre chose</h3>"
            "<p>Les décalages squelettiques importants, certaines dents incluses, certaines situations chirurgicales ou de croissance relèvent d’un dispositif fixe, d’un appareil complémentaire, ou d’une prise en charge coordonnée avec un autre praticien. Le rôle du bilan est de trancher ce point avant que vous ne vous engagiez.</p>"
        ), modif="inverse"), variante="verre") +
    bande(
        '<div data-reveler>' + titre_bloc("Au quotidien", "Ce que ça change, concrètement.") + '</div>' +
        '<div style="margin-top:2.5rem">' + chiffres([
            ("~22 h", "de port par jour, repas et brossage exclus"),
            ("7–14 j", "de port par aligneur, selon le protocole"),
            ("~10 j", "l’intervalle courant entre deux scans de suivi"),
            ("0", "restriction alimentaire : la gouttière se retire pour manger"),
        ]) + '</div>' +
        '<div class="duo" style="margin-top:3.5rem"><div data-reveler>' +
        prose(
            "<h3>Les avantages</h3>" +
            liste([
                "Le brossage et le fil dentaire restent normaux, gouttières retirées.",
                "Aucune restriction alimentaire, contrairement aux appareils fixes.",
                "Pas de fil ni de bague susceptible de blesser la joue.",
                "Une discrétion réelle en situation professionnelle ou scolaire.",
                "Un plan de traitement visible et discutable avant de commencer.",
            ])) +
        '</div><div data-reveler data-reveler-delai="1">' +
        prose(
            "<h3>Les contraintes, dites franchement</h3>" +
            liste([
                "Tout repose sur le temps de port. Un aligneur dans sa boîte ne déplace rien.",
                "Il faut le retirer à chaque repas et le remettre ensuite, sans exception.",
                "Une sensation de pression accompagne souvent les premiers jours d’une nouvelle gouttière.",
                "La contention en fin de traitement n’est pas facultative.",
            ])) +
        '</div></div>', variante="") +
    bande(duo(
        titre_bloc("Le déroulé", "Dix étapes, du premier rendez-vous à la contention.",
                   "Chaque étape a une raison d’être clinique. Aucune n’est un passage administratif."),
        sequence([
            ("Consultation", "On écoute la demande et on explique ce qui est envisageable."),
            ("Bilan orthodontique", "Examen clinique, radiographies, photographies."),
            ("Empreinte numérique", "Un scanner intra-oral relève la forme exacte des arcades."),
            ("Diagnostic", "Les déplacements nécessaires sont définis dent par dent."),
            ("Planification 3D", "La séquence complète est calculée puis validée."),
            ("Fabrication", "La série d’aligneurs est produite à partir du plan validé."),
            ("Mise en place", "Attachements si besoin, essayage, consignes de port."),
            ("Suivi Dental Monitoring", "Des scans réguliers entre les rendez-vous."),
            ("Contrôles au cabinet", "L’examen clinique reste indispensable."),
            ("Contention", "La phase qui stabilise le résultat dans la durée."),
        ])), variante="marine") +
    bande(duo(
        titre_bloc("Prix et remboursement", "Ce que coûte un traitement, et ce qui est pris en charge."),
        prose(
            "<p>Un traitement orthodontique fait toujours l’objet d’un devis écrit et détaillé, remis après le bilan. Il n’existe pas de tarif unique : le montant dépend de l’étendue de la correction, du nombre d’aligneurs, de la durée du suivi et de la contention prévue.</p>"
            "<p>En France, l’Assurance Maladie prend en charge les traitements orthodontiques débutés <strong>avant le 16<sup>e</sup> anniversaire</strong>, sous condition d’entente préalable. Au-delà de cet âge, le traitement n’est pas remboursé par la Sécurité sociale, mais de nombreuses complémentaires santé prévoient un forfait pour l’orthodontie adulte.</p>" +
            boutons(btn("Le détail des tarifs", "tarifs.html"))
        ), modif="inverse"), variante="glace") +
    bande('<div class="duo"><div data-reveler>' +
          titre_bloc("Questions fréquentes", "Sur le traitement par aligneurs.") +
          boutons(btn("Toutes les questions", "faq.html")) +
          '</div><div data-reveler data-reveler-delai="1">' + faq(faq_aligneurs) + '</div></div>',
          variante="verre"),
    "Aligneurs transparents", RUB_ALIGNEURS,
    actions=boutons(btn("Savoir si les aligneurs sont adaptés à mon cas", "rendez-vous.html", "primaire", True),
                    btn("Démarrer mon Évaluation Orthodontique", "ortho-mind.html")),
    schema=schema_faq(faq_aligneurs))

# ---- PAGE 3 : Déroulement ---------------------------------------------------
page(
    "deroulement-traitement.html",
    "Déroulé d’un traitement par aligneurs | Aix-en-Provence",
    "Les dix étapes d’un traitement par aligneurs à Aix-en-Provence : consultation, bilan, empreinte numérique, planification 3D, suivi et contention.",
    "Comment se déroule un traitement par aligneurs ?",
    "Un traitement par gouttières suit un protocole précis. Le voici en entier, sans étape sautée, pour que vous sachiez exactement ce qui vous attend et pourquoi.",
    bande(
        '<div data-reveler style="max-width:44rem">' +
        prose("<p>La question qui revient le plus souvent en consultation n’est pas « est-ce que ça marche ». "
              "C’est « qu’est-ce qu’on va me faire, et quand ». Voici la réponse, étape par étape.</p>") +
        '</div><div style="margin-top:1rem">' +
        sequence([
            ("Consultation", "Un premier échange : ce qui vous gêne, ce que vous attendez, ce qui est réalisable. On regarde, on explique, et vous repartez avec une idée claire des options — sans engagement."),
            ("Bilan orthodontique", "L’examen complet : radiographies panoramique et de profil, photographies, analyse de l’occlusion et des fonctions. C’est ce qui transforme une impression en diagnostic."),
            ("Empreinte numérique", "Une caméra intra-orale relève la forme exacte de vos arcades en quelques minutes. Pas de pâte, pas de haut-le-cœur, et un modèle exploitable immédiatement."),
            ("Diagnostic", "Les données sont réunies et analysées. On détermine ce qui doit bouger, dans quel sens, et ce qui ne doit surtout pas bouger."),
            ("Planification 3D", "Chaque déplacement est décidé et simulé, étape par étape, jusqu’au résultat visé. Le plan vous est présenté et expliqué avant toute fabrication."),
            ("Fabrication des aligneurs", "La série est produite à partir du plan validé, avec un contrôle des pièces avant remise."),
            ("Mise en place", "Pose des attachements si le plan en prévoit, essayage du premier aligneur, consignes de port et d’entretien."),
            ("Suivi Dental Monitoring", "Vous scannez vos arcades avec votre smartphone selon le rythme prescrit. Les images sont analysées et relues au cabinet."),
            ("Contrôles au cabinet", "À intervalles réguliers : vérification de l’occlusion, des attachements, de l’état des dents et des gencives. Le suivi à distance ne remplace jamais cet examen."),
            ("Contention", "Une fois les dents en place, un dispositif de contention stabilise le résultat. Cette phase fait partie du traitement, pas de l’après-traitement."),
        ]) + '</div>') +
    bande(duo(
        titre_bloc("Ce qu’il faut retenir", "Le suivi à distance ne remplace pas la consultation."),
        prose("<p>La technologie sert à voir plus souvent, pas à voir moins bien. Un scan permet de repérer entre deux "
              "rendez-vous qu’une dent ne suit pas la trajectoire prévue, et donc de réagir plus tôt. Il ne permet ni "
              "de palper, ni de vérifier une occlusion en bouche, ni de contrôler l’état parodontal.</p>"
              "<p>C’est pour cette raison que les contrôles au cabinet restent programmés tout au long du traitement.</p>") +
        avis("Les informations de cette page décrivent un déroulé habituel. Le protocole exact est adapté à chaque "
             "patient au moment du bilan.")), variante="verre"),
    "Déroulement d’un traitement", RUB_ALIGNEURS)

# ---- PAGE 4 : Conception et fabrication ------------------------------------
page(
    "conception-fabrication.html",
    "Conception et fabrication de nos aligneurs | Aix-en-Provence",
    "Des aligneurs conçus avec une expertise d’orthodontiste à Aix-en-Provence : planification numérique, matériaux, contrôle qualité, personnalisation.",
    "Des aligneurs conçus avec une expertise d’orthodontiste",
    "Entre le plan de traitement et la gouttière que vous mettez en bouche, il y a une chaîne de décisions techniques. Nous la maîtrisons de bout en bout.",
    bande(duo(
        titre_bloc("Pourquoi cela compte", "Concevoir soi-même, c’est pouvoir corriger soi-même."),
        prose(
            "<p>Dans un schéma classique, l’orthodontiste envoie une empreinte et reçoit une série de gouttières. "
            "Entre les deux, une part importante des décisions lui échappe : la répartition des déplacements, "
            "l’épaisseur du matériau, la forme des reliefs, la stratégie de rattrapage lorsqu’une dent résiste.</p>"
            "<p>Nous avons fait le choix inverse. La planification et la conception sont menées au cabinet, "
            "ce qui permet d’ajuster un plan en cours de traitement plutôt que de le recommencer, et d’adapter "
            "la mécanique à la situation clinique plutôt que l’inverse.</p>"), collant=True)) +
    bande(duo(
        titre_bloc("La chaîne", "Du scanner à la gouttière."),
        sequence([
            ("Empreinte optique", "Le scanner intra-oral produit un modèle numérique fidèle des deux arcades."),
            ("Analyse et diagnostic", "Les objectifs de déplacement sont définis à partir du bilan complet, pas du seul modèle."),
            ("Planification des déplacements", "Chaque dent reçoit une trajectoire et un rythme. Les ancrages sont décidés à ce moment."),
            ("Conception des aligneurs", "Forme, découpe, reliefs et attachements sont dessinés étape par étape."),
            ("Production", "Les gouttières sont fabriquées à partir des modèles validés."),
            ("Contrôle qualité", "Chaque série est vérifiée avant d’être remise au patient."),
            ("Ajustements en cours de route", "Si une dent ne suit pas, la suite de la série est reprise sans repartir de zéro."),
        ])), variante="marine") +
    bande(duo(
        titre_bloc("De la clinique à l’industrie", "Casper Dental."),
        prose(
            "<p>Cette expérience clinique et cette maîtrise de la conception ont conduit à la création de "
            "<strong>Casper Dental</strong>, une activité destinée aux orthodontistes et chirurgiens-dentistes.</p>"
            "<p>Sur ce site, nous n’en disons volontairement que l’essentiel : ce qui vous concerne en tant que "
            "patient, c’est que votre traitement est conçu par un praticien qui connaît l’objet qu’il prescrit.</p>" +
            boutons(btn("En savoir plus sur Casper Dental", "casper-dental.html"))), modif="inverse"),
        variante="verre"),
    "Conception et fabrication", RUB_ALIGNEURS)

# ---- PAGE 5 : Dental Monitoring --------------------------------------------
faq_dm = [
    ("Combien de temps prend un scan ?",
     "Quelques minutes. Vous placez l’écarteur fourni, vous suivez les indications de l’application, et les images partent automatiquement."),
    ("Faut-il un téléphone récent ?",
     "Un smartphone courant suffit. L’application indique les prérequis lors de l’installation."),
    ("Est-ce que cela remplace mes rendez-vous ?",
     "Non. Le suivi à distance s’ajoute aux consultations, il ne les remplace pas. Il permet en revanche d’espacer certains contrôles quand tout se déroule comme prévu, et de vous faire venir plus tôt quand ce n’est pas le cas."),
    ("Qui regarde mes scans ?",
     "Les images sont analysées par la technologie Dental Monitoring, puis relues dans le cadre du suivi orthodontique défini par le praticien. Les décisions cliniques restent prises au cabinet."),
    ("Que se passe-t-il si je saute un scan ?",
     "Vous perdez un point de contrôle. Ce n’est pas grave une fois, cela le devient si cela se répète : c’est précisément la régularité qui donne sa valeur au suivi."),
]
page(
    "dental-monitoring.html",
    "Dental Monitoring — Suivi orthodontique à Aix-en-Provence",
    "Suivi orthodontique à distance à Aix-en-Provence : scan au smartphone tous les dix jours environ, analyse, contrôle par l’orthodontiste, rôle et limites.",
    "Votre traitement orthodontique suivi à distance",
    "Un scan réalisé chez vous avec votre smartphone, transmis au cabinet, analysé, puis relu dans le cadre de votre suivi. Environ tous les dix jours, selon le protocole prescrit.",
    bande(duo(
        titre_bloc("Le cycle", "Ce qui se passe entre deux rendez-vous."),
        sequence([
            ("Notification", "L’application vous prévient qu’un scan est attendu."),
            ("Scan au smartphone", "Quelques minutes, chez vous, avec l’écarteur fourni."),
            ("Transmission des images", "Les prises de vue partent directement vers le cabinet."),
            ("Analyse", "La technologie Dental Monitoring compare l’évolution observée au plan de traitement."),
            ("Contrôle orthodontique", "La lecture s’effectue dans le cadre du suivi défini par le praticien."),
            ("Instructions", "Poursuivre, prolonger l’aligneur en cours, ou venir au cabinet."),
        ]))) +
    bande(duo(
        titre_bloc("L’intérêt", "Voir plus tôt qu’une dent ne suit pas."),
        prose(
            "<p>Le principal risque d’un traitement par aligneurs n’est pas l’erreur de planification : c’est le "
            "décalage silencieux entre ce qui était prévu et ce qui se passe réellement. Une dent qui ne suit pas, "
            "un aligneur qui ne s’assoit plus complètement, un temps de port insuffisant.</p>"
            "<p>Sans suivi intermédiaire, ce décalage se découvre au rendez-vous suivant — parfois plusieurs semaines "
            "plus tard, avec des étapes déjà franchies. Avec un contrôle régulier, il se repère au moment où il "
            "apparaît, et la correction reste simple.</p>"
            "<h3>Ce que le suivi connecté permet</h3>" +
            liste([
                "Repérer tôt un retard de déplacement.",
                "Adapter la durée de port d’un aligneur plutôt que de subir la suite de la série.",
                "Espacer certains rendez-vous quand tout se déroule normalement.",
                "Vous faire venir plus tôt lorsque c’est nécessaire.",
                "Suivre l’hygiène et l’état des tissus au fil du traitement.",
            ])), modif="inverse"), variante="verre") +
    bande(duo(
        titre_bloc("Les limites", "Ce qu’un scan ne fait pas."),
        prose(
            "<p>Un suivi à distance reste un suivi par l’image. Il ne permet ni de palper, ni de tester une occlusion "
            "en bouche, ni d’examiner l’état parodontal avec la même précision qu’en consultation, ni de recoller un "
            "attachement.</p>"
            "<p>L’intelligence artificielle intervient dans l’analyse des images, pas dans la décision de traitement. "
            "Les orientations thérapeutiques relèvent de l’orthodontiste, sur la base de votre dossier complet.</p>" +
            avis("Les consultations au cabinet restent programmées pendant toute la durée du traitement. Le suivi "
                 "connecté vient s’y ajouter, jamais s’y substituer.")), collant=True), variante="marine") +
    bande('<div class="duo"><div data-reveler>' +
          titre_bloc("Questions fréquentes", "Sur le suivi connecté.") +
          '</div><div data-reveler data-reveler-delai="1">' + faq(faq_dm) + '</div></div>'),
    "Dental Monitoring", RUB_ALIGNEURS, schema=schema_faq(faq_dm))

# ---- PAGE 6 : Aligneurs ou bagues ------------------------------------------
COMP = """
<table class="comparatif">
<thead><tr><th>Critère</th><th>Aligneurs</th><th>Appareil multibague</th></tr></thead>
<tbody>
<tr><th>Discrétion</th><td data-col="Aligneurs">Gouttières transparentes, très peu visibles.</td><td data-col="Bagues">Visible, même avec des attaches céramiques.</td></tr>
<tr><th>Hygiène</th><td data-col="Aligneurs">Brossage et fil normaux, appareil retiré.</td><td data-col="Bagues">Brossage plus long, matériel spécifique nécessaire.</td></tr>
<tr><th>Alimentation</th><td data-col="Aligneurs">Aucune restriction : on retire pour manger.</td><td data-col="Bagues">Aliments durs ou collants à éviter.</td></tr>
<tr><th>Confort</th><td data-col="Aligneurs">Pas de fil ni de bague contre la joue.</td><td data-col="Bagues">Irritations possibles, surtout au début.</td></tr>
<tr><th>Coopération</th><td data-col="Aligneurs">Déterminante : tout dépend du temps de port.</td><td data-col="Bagues">L’appareil travaille en continu, sans intervention du patient.</td></tr>
<tr><th>Indications</th><td data-col="Aligneurs">Large, mais pas universelle.</td><td data-col="Bagues">Reste indiqué dans certaines situations complexes.</td></tr>
<tr><th>Urgences</th><td data-col="Aligneurs">Rares : une gouttière fêlée se remplace.</td><td data-col="Bagues">Décollements et fils blessants possibles.</td></tr>
<tr><th>Sport</th><td data-col="Aligneurs">Gouttière retirable, protège-dents compatible.</td><td data-col="Bagues">Protection recommandée pour les sports de contact.</td></tr>
</tbody></table>
"""
page(
    "aligneurs-ou-bagues.html",
    "Aligneurs ou bagues : que choisir ? | Aix-en-Provence",
    "Aligneurs transparents ou appareil multibague à Aix-en-Provence : esthétique, hygiène, alimentation, confort, coopération, indications et durée.",
    "Aligneurs ou bagues : quel traitement orthodontique choisir ?",
    "Les deux fonctionnent. Ils ne fonctionnent simplement pas de la même manière, ni dans les mêmes situations. Voici de quoi comparer honnêtement.",
    bande('<div data-reveler style="max-width:44rem">' +
          prose("<p>La bonne question n’est pas « lequel est le meilleur » mais « lequel est adapté à ce cas, pour ce "
                "patient ». Un appareil parfaitement indiqué mais mal porté donne un moins bon résultat qu’un "
                "dispositif un peu moins puissant porté correctement.</p>") + '</div>' + COMP) +
    bande(duo(
        titre_bloc("Notre position", "Nous privilégions les aligneurs — quand c’est justifié."),
        prose(
            "<p>La très grande majorité des traitements du cabinet est menée par aligneurs. Ce n’est pas une position "
            "de principe : c’est la conséquence de la planification numérique et de la maîtrise de la fabrication, "
            "qui ont considérablement élargi ce que l’on sait faire avec une gouttière depuis dix ans.</p>"
            "<p>Cela ne veut pas dire que les appareils fixes ont disparu. Certaines situations les rendent plus "
            "sûrs ou plus rapides, et il serait malhonnête de les écarter pour des raisons d’image. Quand c’est "
            "le cas, nous le disons, et nous expliquons pourquoi.</p>"), modif="inverse"), variante="verre"),
    "Aligneurs ou bagues ?", RUB_ALIGNEURS)

# ---- PAGE 7 : Invisalign ---------------------------------------------------
page(
    "invisalign-aix-en-provence.html",
    "Invisalign et aligneurs à Aix-en-Provence | Dr Desouches",
    "Invisalign, gouttières, aligneurs à Aix-en-Provence : ce que recouvrent ces termes, et pourquoi le diagnostic compte plus que la marque.",
    "Invisalign et aligneurs orthodontiques à Aix-en-Provence",
    "Invisalign est une marque d’aligneurs, largement connue. Ce n’est pas un synonyme de traitement orthodontique — et cette nuance change beaucoup de choses.",
    bande(duo(
        titre_bloc("La confusion la plus fréquente", "La marque n’est pas le traitement."),
        prose(
            "<p>Beaucoup de patients arrivent en demandant « un Invisalign », comme on demanderait une marque de "
            "médicament. C’est légitime : le nom est devenu synonyme de gouttière transparente dans le langage courant.</p>"
            "<p>Mais Invisalign désigne un système d’aligneurs commercialisé par un fabricant, parmi plusieurs "
            "solutions existantes. Ce qui détermine votre résultat n’est pas la marque imprimée sur la boîte, "
            "c’est ce qui a été décidé avant : le diagnostic, les déplacements planifiés, les ancrages, la séquence, "
            "et le suivi qui accompagne le tout.</p>"
            "<h3>Ce qui fait vraiment la différence</h3>" +
            liste([
                "Un <strong>diagnostic complet</strong>, appuyé sur un examen clinique et des radiographies.",
                "Une <strong>planification</strong> pensée par l’orthodontiste, pas seulement acceptée par lui.",
                "La <strong>qualité des ancrages</strong> et la stratégie de déplacement.",
                "Un <strong>suivi régulier</strong>, capable de corriger la trajectoire en cours de route.",
                "Une <strong>contention</strong> adaptée et expliquée.",
            ])), collant=True)) +
    bande(duo(
        titre_bloc("Au cabinet", "Nos aligneurs sont conçus ici."),
        prose(
            "<p>Le cabinet planifie et conçoit ses propres aligneurs, ce qui permet d’ajuster un plan en cours de "
            "traitement sans repartir de zéro. Cette maîtrise est d’ailleurs à l’origine de "
            "<a class=\"lien-souligne\" href=\"casper-dental.html\">Casper Dental</a>.</p>"
            "<p>Si vous êtes venu chercher « Invisalign à Aix-en-Provence », vous cherchez en réalité un traitement "
            "par gouttières transparentes bien conduit. C’est exactement ce dont nous parlons sur ce site.</p>" +
            boutons(btn("Comprendre le traitement par aligneurs", "aligneurs.html"),
                    btn("Aligneurs ou bagues ?", "aligneurs-ou-bagues.html"))), modif="inverse"),
        variante="verre"),
    "Invisalign et aligneurs", RUB_ALIGNEURS)

# ---- PAGE 8 : Orthodontie de l'enfant --------------------------------------
page(
    "orthodontie-enfant.html",
    "Orthodontiste pour enfant à Aix-en-Provence | Dr Renaud Desouches",
    "Orthodontie de l’enfant à Aix-en-Provence : quand consulter, croissance des mâchoires, manque de place, articulé croisé, surveillance ou traitement.",
    "Orthodontiste pour enfant à Aix-en-Provence",
    "Chez l’enfant, l’orthodontie ne consiste pas d’abord à aligner des dents. Elle consiste à accompagner une croissance pendant qu’elle est encore en cours.",
    bande(duo(
        titre_bloc("Quand consulter", "Le repère est 6–7 ans, pas « quand toutes les dents sont là »."),
        prose(
            "<p>Attendre que la denture définitive soit complète, c’est attendre que la croissance des mâchoires soit "
            "en grande partie terminée. Or c’est précisément sur cette croissance que l’on peut agir chez l’enfant, "
            "et seulement pendant qu’elle a lieu.</p>"
            "<p>Vers 6–7 ans apparaissent les premières molaires et les incisives définitives. Ce moment permet un "
            "premier regard utile — et, dans une majorité de cas, il débouche sur une simple surveillance.</p>" +
            boutons(btn("Pourquoi un bilan vers 6–7 ans ?", "bilan-6-7-ans.html", "primaire", True))), collant=True)) +
    bande(duo(
        titre_bloc("Ce que l’on recherche", "Les signes qui méritent un avis."),
        prose(
            liste([
                "Un <strong>manque de place</strong> visible sur les incisives qui viennent de sortir.",
                "Des <strong>dents en avant</strong>, exposées en cas de chute.",
                "Une <strong>mâchoire étroite</strong> ou un <strong>articulé croisé</strong>.",
                "Un <strong>décalage entre les mâchoires</strong>, du haut ou du bas.",
                "Une <strong>respiration à bouche ouverte</strong> persistante.",
                "Une <strong>déglutition atypique</strong>, la langue venant buter contre les dents.",
                "La <strong>succion du pouce</strong> ou de la tétine au-delà de l’âge habituel.",
                "Une <strong>dent définitive qui tarde</strong> ou qui sort de travers.",
            ]) +
            "<h3>Surveiller ou traiter</h3>"
            "<p>Ces observations n’entraînent pas automatiquement un appareil. Elles déterminent la conduite : "
            "surveiller l’évolution à intervalle régulier, agir sur une fonction, ou entreprendre un traitement "
            "court à un moment précis de la croissance.</p>"), modif="inverse"), variante="verre") +
    bande(duo(
        titre_bloc("Et les aligneurs", "Chez l’enfant aussi, dans certaines situations."),
        prose("<p>Les gouttières transparentes ne sont pas réservées à l’adulte. Elles peuvent être indiquées en "
              "denture mixte, à condition que l’objectif soit adapté et que l’enfant soit capable de les porter "
              "le temps nécessaire. Cette évaluation se fait au bilan, jamais par principe.</p>" +
              boutons(btn("Aligneurs chez l’enfant et l’adolescent", "aligneurs-enfant-adolescent.html")))),
        variante="glace"),
    "Orthodontie de l’enfant", RUB_ENFANTS)

# ---- PAGE 9 : Bilan 6-7 ans ------------------------------------------------
faq_bilan = [
    ("Mon enfant a encore toutes ses dents de lait, est-ce trop tôt ?",
     "Le repère est l’apparition des premières dents définitives, généralement vers 6–7 ans. S’il n’en a encore aucune, le bilan peut attendre quelques mois."),
    ("Le bilan débouche-t-il forcément sur un appareil ?",
     "Non, et c’est même le contraire dans une majorité de cas. Le bilan sert à décider s’il faut agir, et surtout quand. Beaucoup d’enfants sont simplement revus à intervalle régulier."),
    ("Est-ce douloureux ou impressionnant pour un enfant ?",
     "Le bilan est un examen : on regarde, on photographie, on réalise des radiographies. Rien n’est invasif et l’enfant reste avec vous."),
    ("Faut-il une ordonnance de mon dentiste ?",
     "Vous pouvez consulter directement un orthodontiste. Le suivi habituel chez le chirurgien-dentiste reste par ailleurs nécessaire."),
    ("Un traitement précoce évite-t-il un traitement plus tard ?",
     "Pas toujours. Un traitement précoce vise généralement un objectif précis — créer de la place, corriger un articulé croisé, arrêter une habitude. Une seconde phase peut rester nécessaire à l’adolescence."),
]
page(
    "bilan-6-7-ans.html",
    "Pourquoi consulter un orthodontiste vers 6–7 ans ? | Aix-en-Provence",
    "Bilan orthodontique de l’enfant vers 6–7 ans à Aix-en-Provence : ce que l’on recherche, et pourquoi consulter tôt ne signifie pas traiter tôt.",
    "Pourquoi consulter un orthodontiste vers 6–7 ans ?",
    "Parce que c’est le moment où les premières dents définitives arrivent, et où l’on peut encore accompagner la croissance des mâchoires plutôt que de la rattraper.",
    bande(duo(
        titre_bloc("Ce qui change à cet âge", "Deux événements, la même année."),
        prose(
            "<h3>Les premières molaires définitives</h3>"
            "<p>Elles apparaissent au fond, sans qu’aucune dent de lait ne tombe — ce qui explique qu’elles passent "
            "souvent inaperçues. Elles fixent pourtant la manière dont les deux arcades vont s’engrener pour les "
            "années suivantes.</p>"
            "<h3>Les incisives définitives</h3>"
            "<p>Plus grandes que les dents de lait qu’elles remplacent, elles révèlent immédiatement si la place "
            "disponible est suffisante, et dans quel sens les choses s’orientent.</p>"), collant=True)) +
    bande(duo(
        titre_bloc("Ce que l’on recherche", "Six points examinés au bilan."),
        prose(liste([
            "Un <strong>manque de place</strong> pour les dents définitives à venir.",
            "Un <strong>problème de largeur</strong> des mâchoires.",
            "Un <strong>articulé croisé</strong>, d’un côté ou des deux.",
            "Un <strong>décalage squelettique</strong> entre le haut et le bas.",
            "Des <strong>incisives très en avant</strong>, plus exposées aux chocs.",
            "Un <strong>trouble fonctionnel</strong> : respiration, déglutition, succion.",
        ])), modif="inverse"), variante="verre") +
    bande(
        '<div data-reveler style="max-width:46rem">'
        '<p class="sur-titre">Le message essentiel</p>'
        '<h2>Consulter tôt ne signifie pas forcément traiter tôt.</h2>'
        '<div class="prose" style="margin-top:1.6rem">'
        '<p>C’est la crainte la plus courante des parents, et elle est légitime : venir consulter, est-ce s’engager '
        'dans un appareil ?</p>'
        '<p>Non. Dans une large part des cas, le bilan de 6–7 ans aboutit à une simple surveillance de la croissance '
        'et de l’évolution de la dentition, avec un rendez-vous de contrôle programmé. Consulter à cet âge sert '
        'd’abord à ne pas passer à côté des rares situations où le moment d’agir ne se représentera pas.</p>'
        '</div>' +
        boutons(btn("Prendre rendez-vous pour un premier bilan", "rendez-vous.html", "primaire", True)) +
        '</div>', variante="marine") +
    bande('<div class="duo"><div data-reveler>' +
          titre_bloc("Questions de parents", "Ce que l’on nous demande le plus souvent.") +
          '</div><div data-reveler data-reveler-delai="1">' + faq(faq_bilan) + '</div></div>'),
    "Bilan 6–7 ans", RUB_ENFANTS,
    actions=boutons(btn("Prendre rendez-vous pour un premier bilan", "rendez-vous.html", "primaire", True)),
    schema=schema_faq(faq_bilan))

# ---- PAGE 10 : Adolescent ---------------------------------------------------
page(
    "orthodontie-adolescent.html",
    "Orthodontie de l’adolescent à Aix-en-Provence | Dr Renaud Desouches",
    "Orthodontie de l’adolescent à Aix-en-Provence : aligneurs ou appareil fixe, esthétique, hygiène, sport, coopération, suivi connecté et contention.",
    "Orthodontie de l’adolescent à Aix-en-Provence",
    "C’est l’âge où la denture définitive est en place et où la croissance n’est pas terminée. Une fenêtre confortable — à condition que le traitement tienne dans la vie de l’adolescent.",
    bande(duo(
        titre_bloc("Le vrai sujet", "L’appareil qui marche est celui qui est porté."),
        prose(
            "<p>À cet âge, la réussite d’un traitement tient rarement à la difficulté technique du cas. Elle tient à "
            "la place que l’appareil prend dans le quotidien : l’image de soi, les repas au lycée, le sport, l’oubli.</p>"
            "<p>C’est pourquoi le choix entre aligneurs et appareil fixe se discute avec l’adolescent lui-même, et "
            "pas seulement avec ses parents. Les aligneurs offrent une discrétion réelle et aucune restriction "
            "alimentaire, mais reposent entièrement sur le temps de port. Un appareil fixe travaille en continu "
            "sans rien demander, au prix d’une hygiène plus exigeante.</p>"), collant=True)) +
    bande(duo(
        titre_bloc("Au quotidien", "Les points qui reviennent."),
        prose(liste([
            "<strong>Esthétique</strong> : gouttières transparentes ou attaches, y compris céramiques.",
            "<strong>Hygiène</strong> : brossage normal avec des aligneurs, plus technique avec un appareil fixe.",
            "<strong>Sport</strong> : gouttière retirable et compatible avec un protège-dents.",
            "<strong>Alimentation</strong> : aucune restriction avec des aligneurs.",
            "<strong>Suivi</strong> : Dental Monitoring permet de vérifier régulièrement sans multiplier les rendez-vous manqués.",
            "<strong>Contention</strong> : indispensable en fin de traitement, expliquée dès le départ.",
        ])), modif="inverse"), variante="verre") +
    bande(duo(
        titre_bloc("Remboursement", "L’âge compte."),
        prose("<p>L’Assurance Maladie prend en charge les traitements orthodontiques débutés avant le "
              "16<sup>e</sup> anniversaire, sous réserve d’une entente préalable. C’est un élément à intégrer dans "
              "le calendrier lorsque le traitement peut attendre.</p>" +
              boutons(btn("Tarifs et remboursement", "tarifs.html")))), variante="glace"),
    "Orthodontie de l’adolescent", RUB_ENFANTS)

# ---- PAGE 11 : Aligneurs enfant/ado ----------------------------------------
page(
    "aligneurs-enfant-adolescent.html",
    "Aligneurs chez l’enfant et l’adolescent | Aix-en-Provence",
    "Aligneurs transparents chez l’enfant et l’adolescent à Aix-en-Provence : indications, denture mixte, croissance, coopération, avantages, limites et suivi numérique.",
    "Peut-on traiter les enfants et adolescents avec des aligneurs ?",
    "Oui, dans un nombre croissant de situations. Mais la réponse dépend moins de l’âge que du stade de la dentition et de la capacité à porter les gouttières.",
    bande(duo(
        titre_bloc("Les conditions", "Trois questions avant de dire oui."),
        prose(
            "<h3>Où en est la dentition ?</h3>"
            "<p>En denture mixte, des dents de lait cohabitent avec des dents définitives et de nouvelles dents "
            "sont attendues. Les aligneurs peuvent en tenir compte, à condition que la planification anticipe ces "
            "évolutions.</p>"
            "<h3>Où en est la croissance ?</h3>"
            "<p>Certains objectifs — élargir une mâchoire étroite, corriger un décalage — dépendent de la croissance "
            "et peuvent demander un dispositif complémentaire.</p>"
            "<h3>L’enfant portera-t-il les gouttières ?</h3>"
            "<p>C’est le point décisif. Un aligneur retiré ne fait rien. Le suivi connecté aide beaucoup à "
            "objectiver le port réel, sans transformer chaque soir en négociation.</p>"), collant=True)) +
    bande(duo(
        titre_bloc("Ce que ça apporte", "Et ce que ça n’apporte pas."),
        prose(
            liste([
                "Pas d’aliment interdit, ce qui compte beaucoup à la cantine.",
                "Un brossage normal, donc un moindre risque de taches autour des attaches.",
                "Aucune urgence de fil blessant ou de bague décollée.",
                "Une acceptation souvent bien meilleure à l’adolescence.",
            ]) +
            "<p>En revanche, les aligneurs ne compensent pas un port insuffisant, et certaines situations restent "
            "mieux traitées par un appareil fixe ou un dispositif de croissance. Le bilan tranche.</p>" +
            boutons(btn("Le bilan de 6–7 ans", "bilan-6-7-ans.html"),
                    btn("Orthodontie de l’adolescent", "orthodontie-adolescent.html"))), modif="inverse"),
        variante="verre"),
    "Aligneurs chez l’enfant et l’adolescent", RUB_ENFANTS)

# ---- PAGE 12 : Adulte -------------------------------------------------------
page(
    "orthodontie-adulte.html",
    "Orthodontiste pour adulte à Aix-en-Provence | Dr Renaud Desouches",
    "Orthodontie adulte à Aix-en-Provence : aligneurs transparents, encombrement, espaces, dents qui ont rebougé, occlusion et contexte parodontal.",
    "Orthodontiste pour adulte à Aix-en-Provence",
    "Il n’y a pas d’âge limite pour déplacer des dents. Il y a en revanche des précautions supplémentaires, et c’est ce qui distingue un traitement adulte d’un traitement adolescent.",
    bande(duo(
        titre_bloc("Ce qui change à l’âge adulte", "La croissance est terminée. Le reste ne l’est pas."),
        prose(
            "<p>Chez l’adulte, on ne peut plus compter sur la croissance pour modifier la forme des mâchoires. "
            "Les déplacements sont purement dentaires, et les objectifs se définissent dans ce cadre — quitte à "
            "envisager une prise en charge coordonnée lorsque le décalage est important.</p>"
            "<p>En contrepartie, l’adulte porte généralement ses aligneurs beaucoup mieux qu’un adolescent, ce qui "
            "compense largement.</p>"
            "<h3>Les motifs de consultation les plus courants</h3>" +
            liste([
                "Un <strong>encombrement</strong> qui s’est aggravé avec les années.",
                "Des <strong>espaces</strong> apparus ou élargis.",
                "Des <strong>dents qui ont rebougé</strong> après un traitement d’adolescence.",
                "Une <strong>usure</strong> ou une gêne liée à l’occlusion.",
                "Une <strong>préparation</strong> avant implant, couronne ou soin parodontal.",
            ])), collant=True)) +
    bande(duo(
        titre_bloc("Le point parodontal", "Une précaution qui n’est pas une formalité."),
        prose(
            "<p>Déplacer une dent, c’est solliciter l’os et la gencive qui la soutiennent. Chez l’adulte, ce support "
            "peut avoir été fragilisé par une maladie parodontale, parfois ancienne et silencieuse.</p>"
            "<p>Un traitement orthodontique ne se commence donc pas sans avoir évalué cet état, et le cas échéant "
            "sans l’avoir stabilisé au préalable, en coordination avec votre chirurgien-dentiste ou un parodontiste. "
            "Ce n’est pas un retard : c’est ce qui rend le résultat durable.</p>" +
            avis("Un bilan complet précède tout traitement adulte. Certaines situations nécessitent une prise en "
                 "charge multidisciplinaire, coordonnée avec les autres praticiens qui vous suivent.")),
        modif="inverse"), variante="verre") +
    bande(duo(
        titre_bloc("Et après", "La contention, surtout chez l’adulte."),
        prose("<p>Les dents conservent toute la vie une tendance à se déplacer. Après un traitement adulte, la "
              "contention n’est pas une précaution optionnelle : c’est la condition pour que le résultat obtenu "
              "reste celui que vous voyez le jour de la dépose.</p>" +
              boutons(btn("Aligneurs chez l’adulte", "aligneurs-adulte.html")))), variante="glace"),
    "Orthodontie adulte", RUB_ADULTES)

# ---- PAGE 13 : Aligneurs adulte --------------------------------------------
faq_adulte = [
    ("Suis-je trop âgé pour un traitement orthodontique ?",
     "Non. Un déplacement dentaire reste possible à tout âge dès lors que l’os et la gencive sont sains. Ce qui compte n’est pas l’année de naissance mais l’état parodontal."),
    ("Combien de temps cela va-t-il durer ?",
     "De quelques mois pour une correction limitée à un an et demi ou deux ans pour une réorganisation complète. La durée est estimée après le bilan, pas avant."),
    ("Est-ce que ça se voit au travail ?",
     "Très peu. Les gouttières sont transparentes. Les attachements, quand il y en a, sont de la couleur de la dent."),
    ("Est-ce que c’est douloureux ?",
     "Une pression est fréquente pendant un à deux jours après chaque changement d’aligneur, puis elle s’estompe. Ce n’est pas une douleur aiguë."),
    ("Puis-je parler normalement ?",
     "Une gêne d’élocution est possible les premiers jours, le temps que la langue s’habitue. Elle disparaît rapidement."),
    ("Combien d’heures par jour dois-je les porter ?",
     "Environ 22 heures. Concrètement : tout le temps, sauf pour manger et se brosser les dents."),
]
page(
    "aligneurs-adulte.html",
    "Aligneurs transparents pour adulte à Aix-en-Provence | Dr Desouches",
    "Aligneurs transparents pour adulte à Aix-en-Provence : discrétion, durée, temps de port, douleur, vie professionnelle, prix et suivi.",
    "Aligneurs transparents pour adulte à Aix-en-Provence",
    "La demande la plus fréquente au cabinet : corriger ce qui gêne, sans que cela se voie et sans mettre sa vie professionnelle entre parenthèses.",
    bande('<div class="duo"><div data-reveler>' +
          titre_bloc("Vos questions", "Répondues sans détour.") +
          boutons(btn("Prendre rendez-vous", "rendez-vous.html", "primaire", True)) +
          '</div><div data-reveler data-reveler-delai="1">' + faq(faq_adulte) + '</div></div>') +
    bande(duo(
        titre_bloc("Ce que l’on corrige le plus", "Chez l’adulte, en pratique."),
        prose(liste([
            "Un encombrement des incisives, souvent aggravé depuis l’adolescence.",
            "Des espaces entre les dents.",
            "Une récidive après un ancien traitement, faute de contention maintenue.",
            "Une préparation avant prothèse ou implant, pour redonner de la place.",
            "Un ajustement de l’occlusion en coordination avec d’autres soins.",
        ]) + boutons(btn("Voir la galerie avant / après", "avant-apres.html"),
                     btn("Orthodontie adulte", "orthodontie-adulte.html"))), modif="inverse"), variante="verre"),
    "Aligneurs chez l’adulte", RUB_ADULTES, schema=schema_faq(faq_adulte))

# ---- PAGE 14 : Ortho Mind ---------------------------------------------------
page(
    "ortho-mind.html",
    "Ortho Mind — Analysez votre sourire | Aix-en-Provence",
    "Ortho Mind : une première analyse de votre sourire à partir de photos, vérifiée selon le protocole défini par le Dr Desouches, à Aix-en-Provence.",
    "Analysez votre sourire en ligne avec Ortho Mind",
    "Quelques photos prises avec votre téléphone, une première lecture des éléments orthodontiques visibles, et une orientation avant même de vous déplacer.",
    bande(duo(
        titre_bloc("Le parcours", "Cinq étapes, une dizaine de minutes."),
        sequence([
            ("Je prends mes photos", "Face, sourire, profil et vues des arcades, en suivant les repères affichés."),
            ("Ortho Mind analyse mon sourire", "Les images sont traitées pour en extraire les éléments observables."),
            ("Les principaux éléments sont identifiés", "Encombrement, espaces, décalages, recouvrement : ce qui se voit sur des photos."),
            ("L’analyse est vérifiée", "La lecture s’effectue dans le cadre du protocole défini par le Dr Desouches."),
            ("Je reçois une première orientation", "Une réponse claire sur la pertinence d’un bilan et sur les options envisageables."),
        ]))) +
    bande(duo(
        titre_bloc("Ce que c’est — et ce que ce n’est pas", "Une orientation, pas un diagnostic."),
        prose(
            "<p>Ortho Mind répond à une question simple : « est-ce que ma situation relève de l’orthodontie, et à "
            "quoi ressemblerait la suite ? » C’est utile pour décider de prendre rendez-vous, ou pour comprendre "
            "ce qui vous gêne sans encore vous engager.</p>"
            "<p>Ce n’est pas un diagnostic. Un diagnostic orthodontique s’appuie sur un examen clinique, des "
            "radiographies, une analyse de l’occlusion et des fonctions — autant d’éléments qu’aucune photographie "
            "ne remplace.</p>" +
            avis("Cet outil ne remplace ni un examen clinique, ni un diagnostic orthodontique complet. Aucune "
                 "décision de traitement n’est prise sur la seule base des photographies.")), modif="inverse"),
        variante="verre") +
    bande(
        '<div data-reveler style="max-width:44rem">' +
        titre_bloc("Vos données", "Des photographies de santé, traitées comme telles.") +
        prose("<p>Les images que vous transmettez sont des données de santé. Elles sont traitées dans le cadre "
              "prévu par la réglementation applicable, conservées de manière sécurisée et utilisées uniquement "
              "pour répondre à votre demande.</p>" +
              boutons(btn("Notre politique sur les données de santé", "donnees-de-sante.html"))) +
        '</div>', variante="glace") +
    bande('<div data-reveler style="max-width:40rem">'
          '<h2>Prêt à commencer ?</h2>'
          '<p class="chapo" style="margin-top:1.2rem">L’analyse est gratuite et sans engagement. '
          'Si un bilan s’avère pertinent, nous vous le dirons — et si ce n’est pas le cas, nous vous le dirons aussi.</p>' +
          boutons(btn("Démarrer mon Évaluation Orthodontique", "rendez-vous.html", "primaire", True),
                  btn("Prendre rendez-vous au cabinet", "rendez-vous.html")) + '</div>'),
    "Ortho Mind",
    actions=boutons(btn("Démarrer mon Évaluation Orthodontique", "rendez-vous.html", "primaire", True)))

# ---- PAGE 15 : Avant / après ------------------------------------------------
CAS = [
    ("encombrement", "Encombrement antérieur", "aligneurs adultes encombrement",
     "Manque de place au niveau des incisives, avec chevauchement.",
     [("Situation initiale", "Encombrement marqué du bloc incisif"),
      ("Objectif", "Créer de la place et réaligner sans extraction"),
      ("Traitement", "Aligneurs transparents"),
      ("Résultat", "Arcade alignée, contention posée")]),
    ("diasteme", "Dents écartées", "aligneurs adultes ecartees",
     "Espaces entre les dents, dont un diastème médian.",
     [("Situation initiale", "Diastème médian et espaces latéraux"),
      ("Objectif", "Fermer les espaces en préservant l’occlusion"),
      ("Traitement", "Aligneurs transparents"),
      ("Résultat", "Points de contact rétablis")]),
    ("proalveolie", "Dents en avant", "aligneurs adolescents classe2",
     "Incisives projetées vers l’avant, fréquemment associées à un décalage.",
     [("Situation initiale", "Incisives supérieures très inclinées"),
      ("Objectif", "Réduire la projection et protéger les incisives"),
      ("Traitement", "Aligneurs, avec dispositif complémentaire si besoin"),
      ("Résultat", "Recouvrement normalisé")]),
    ("croise", "Articulé croisé", "enfants croise",
     "Les dents du bas recouvrent celles du haut d’un côté.",
     [("Situation initiale", "Articulé croisé unilatéral"),
      ("Objectif", "Rétablir un engrènement correct"),
      ("Traitement", "Prise en charge adaptée à l’âge et à la croissance"),
      ("Résultat", "Croisement corrigé")]),
    ("encombrement", "Récidive après orthodontie", "aligneurs adultes recidive",
     "Dents ayant rebougé plusieurs années après un premier traitement.",
     [("Situation initiale", "Récidive du bloc incisif inférieur"),
      ("Objectif", "Réaligner et sécuriser par une contention durable"),
      ("Traitement", "Aligneurs transparents"),
      ("Résultat", "Alignement retrouvé, contention collée")]),
    ("diasteme", "Supraclusion", "aligneurs adolescents supraclusion",
     "Les incisives du haut recouvrent excessivement celles du bas.",
     [("Situation initiale", "Recouvrement incisif important"),
      ("Objectif", "Réduire le recouvrement"),
      ("Traitement", "Aligneurs avec mécanique d’ingression"),
      ("Résultat", "Recouvrement ramené à une valeur physiologique")]),
]

def carte_cas(c):
    typ, titre, cats, desc, details = c
    dl = "".join("<dt>%s</dt><dd>%s</dd>" % (k, v) for k, v in details)
    return ('<article class="cas" data-cat="%s" data-reveler>'
            '<div class="duel" data-duel="%s">'
            '<div class="duel__face"><svg data-duel-avant></svg></div>'
            '<div class="duel__face duel__face--apres"><svg data-duel-apres></svg></div>'
            '<span class="duel__poignee" aria-hidden="true"></span>'
            '<span class="duel__balise duel__balise--g">Avant</span>'
            '<span class="duel__balise duel__balise--d">Après</span></div>'
            '<div class="cas__texte"><h3>%s</h3>'
            '<p style="font-size:.875rem;color:var(--marine-60);margin:0">%s</p>'
            '<dl>%s</dl></div></article>' % (cats, typ, titre, desc, dl))

FILTRES = [("tous", "Tous les cas"), ("aligneurs", "Aligneurs"), ("enfants", "Enfants"),
           ("adolescents", "Adolescents"), ("adultes", "Adultes"), ("encombrement", "Encombrement"),
           ("ecartees", "Dents écartées"), ("classe2", "Classe II"), ("supraclusion", "Supraclusion"),
           ("croise", "Articulé croisé"), ("recidive", "Récidive")]

page(
    "avant-apres.html",
    "Avant / après — Résultats orthodontiques | Aix-en-Provence",
    "Résultats de traitements par aligneurs à Aix-en-Provence : encombrement, dents écartées, supraclusion, articulé croisé, récidive après orthodontie.",
    "Résultats de traitements orthodontiques",
    "Chaque cas est présenté avec sa situation de départ, l’objectif poursuivi, le type de traitement engagé et le résultat obtenu. Faites glisser pour comparer.",
    bande(
        '<div class="filtres" role="group" aria-label="Filtrer les cas">' +
        "".join('<button class="filtre" data-filtre="%s" aria-pressed="%s">%s</button>'
                % (k, "true" if k == "tous" else "false", v) for k, v in FILTRES) +
        '</div><p class="legende" id="galerie-compte" style="margin-top:1rem">%d cas affichés</p>'
        '<div class="galerie">%s</div>'
        '<p class="legende" style="margin-top:2rem;max-width:46rem">Les visuels présentés ici sont des schémas '
        'destinés à illustrer les situations traitées. Les photographies cliniques du cabinet seront publiées '
        'uniquement pour les cas dont les autorisations écrites ont été recueillies, conformément à la '
        'réglementation applicable à la communication des professionnels de santé.</p>'
        % (len(CAS), "".join(carte_cas(c) for c in CAS))),
    "Avant / après")

# ---- PAGE 16 : Problèmes orthodontiques ------------------------------------
PROBLEMES = [
    ("Dents qui se chevauchent", "Les dents se recouvrent partiellement, faute de place sur l’arcade. C’est le motif de consultation le plus fréquent, à tout âge."),
    ("Manque de place", "L’arcade est trop courte pour accueillir toutes les dents. Chez l’enfant, on peut parfois agir sur la largeur des mâchoires pendant la croissance."),
    ("Dents écartées, diastème", "Des espaces subsistent entre les dents, en particulier entre les deux incisives centrales. Les causes sont variées : taille des dents, frein, langue."),
    ("Dents en avant", "Les incisives supérieures sont projetées vers l’avant. Au-delà de l’aspect, elles sont beaucoup plus exposées en cas de chute ou de choc."),
    ("Supraclusion", "Les dents du haut recouvrent excessivement celles du bas, jusqu’à parfois masquer complètement les incisives inférieures."),
    ("Béance", "Les dents ne se touchent pas à la fermeture, souvent au niveau antérieur. La fonction de la langue joue fréquemment un rôle."),
    ("Classe II", "La mâchoire inférieure est en retrait par rapport à la supérieure, ce qui décale l’engrènement des arcades."),
    ("Classe III", "La mâchoire inférieure est en avance par rapport à la supérieure. Chez l’enfant, l’interception précoce a tout son intérêt."),
    ("Articulé croisé", "Les dents du bas recouvrent celles du haut, d’un côté ou des deux. Non corrigé, il peut entraîner une déviation à la fermeture."),
    ("Mâchoire étroite", "L’arcade supérieure est trop étroite. C’est une situation où la croissance de l’enfant offre des possibilités qui disparaissent ensuite."),
    ("Dents incluses", "Une dent définitive reste bloquée dans l’os et n’apparaît pas sur l’arcade. La canine est particulièrement concernée."),
    ("Récidive après orthodontie", "Les dents ont repris leur position ancienne après un traitement, généralement faute de contention maintenue dans la durée."),
]
page(
    "problemes-orthodontiques.html",
    "Que peut corriger l’orthodontie ? | Aix-en-Provence",
    "Encombrement, diastème, supraclusion, béance, classe II, classe III, articulé croisé, dents incluses : ce que traite l’orthodontie à Aix-en-Provence.",
    "Quels problèmes peut corriger l’orthodontie ?",
    "Un tour d’horizon des situations que nous prenons en charge, de l’enfant à l’adulte. Chacune a ses signes, son moment favorable et ses options de traitement.",
    bande('<div class="duo" style="align-items:start"><div data-reveler>' +
          prose("".join("<h3>%s</h3><p>%s</p>" % (t, d) for t, d in PROBLEMES[:6])) +
          '</div><div data-reveler data-reveler-delai="1">' +
          prose("".join("<h3>%s</h3><p>%s</p>" % (t, d) for t, d in PROBLEMES[6:])) +
          '</div></div>') +
    bande('<div data-reveler style="max-width:42rem">' +
          titre_bloc("La suite logique", "Identifier n’est pas diagnostiquer.") +
          prose("<p>Reconnaître sa situation dans cette liste est utile pour comprendre. Cela ne dit ni la cause, "
                "ni la sévérité, ni le bon moment pour agir — trois éléments qui déterminent pourtant entièrement "
                "le traitement. C’est l’objet du bilan.</p>" +
                boutons(btn("Prendre rendez-vous pour un bilan", "rendez-vous.html", "primaire", True),
                        btn("Voir des résultats", "avant-apres.html"))) + '</div>', variante="verre"),
    "Problèmes orthodontiques")

# ---- PAGE 17 : Dr Desouches ------------------------------------------------
page(
    "dr-renaud-desouches.html",
    "Dr Renaud Desouches — Orthodontiste à Aix-en-Provence",
    "Le Dr Renaud Desouches, orthodontiste à Aix-en-Provence : parcours, orthodontie par aligneurs, orthodontie numérique, conception et fabrication.",
    "Dr Renaud Desouches — Orthodontiste à Aix-en-Provence",
    "Une pratique orientée depuis plusieurs années vers l’orthodontie numérique : diagnostic, planification en trois dimensions, conception des aligneurs et suivi connecté.",
    bande('<div class="duo duo--inverse"><div data-reveler>' +
          prose(
              "<p>Installé à Aix-en-Provence, le Dr Renaud Desouches consacre l’essentiel de son activité aux "
              "traitements par aligneurs transparents, chez l’enfant, l’adolescent et l’adulte.</p>"
              "<p>Sa pratique s’est construite autour d’une conviction simple : la technologie n’a d’intérêt que "
              "si elle sert le diagnostic et le suivi. Une planification en trois dimensions ne vaut rien sans "
              "l’examen clinique qui la précède, et un suivi connecté ne remplace pas une consultation — il permet "
              "d’en tirer davantage.</p>"
              "<h3>Une chaîne maîtrisée de bout en bout</h3>"
              "<p>Empreinte optique, analyse, planification des déplacements, conception des aligneurs, contrôle "
              "qualité, suivi : chacune de ces étapes est menée avec la même exigence, et la plupart le sont "
              "directement au cabinet. Cette maîtrise permet d’ajuster un plan de traitement en cours de route "
              "plutôt que de le recommencer.</p>"
              "<h3>Deux prolongements</h3>"
              "<p>Cette expertise a donné naissance à <a class=\"lien-souligne\" href=\"casper-dental.html\">Casper "
              "Dental</a>, destiné aux orthodontistes et chirurgiens-dentistes, et à l’usage de "
              "<a class=\"lien-souligne\" href=\"ortho-mind.html\">Ortho Mind</a> pour la première analyse du "
              "sourire des patients.</p>" +
              avis("Parcours détaillé, diplômes, titres et activités professionnelles : cette section sera "
                   "complétée avec les éléments fournis par le cabinet, dans le respect des règles déontologiques "
                   "encadrant la communication des chirurgiens-dentistes.")) +
          '</div><div data-reveler data-reveler-delai="1">'
          '<figure style="margin:0"><div class="portrait">'
          '<img src="assets/img/dr-desouches-1200.webp" '
          'alt="Portrait du Dr Renaud Desouches, orthodontiste à Aix-en-Provence"></div>'
          '<figcaption class="legende">Dr Renaud Desouches, au cabinet d’Aix-en-Provence.</figcaption>'
          '</figure></div></div>') +
    bande(duo(
        titre_bloc("Ce qui structure la pratique", "Huit principes, dans cet ordre."),
        sequence([
            ("Diagnostic", "Rien ne commence avant que la situation ne soit comprise."),
            ("Numérique", "L’empreinte optique et la 3D remplacent l’approximation."),
            ("Aligneurs", "Le traitement de référence du cabinet, quand il est indiqué."),
            ("Personnalisation", "Chaque plan est dessiné pour un patient, pas décliné d’un modèle."),
            ("Fabrication", "Concevoir soi-même, c’est pouvoir corriger soi-même."),
            ("Suivi connecté", "Voir plus souvent, pour réagir plus tôt."),
            ("Contrôle orthodontique", "L’examen clinique reste la décision finale."),
            ("Contention", "Le résultat n’est acquis que s’il est stabilisé."),
        ])), variante="marine"),
    "Dr Renaud Desouches", RUB_CABINET,
    schema=json.dumps({
        "@context": "https://schema.org", "@type": "Physician",
        "name": "Dr Renaud Desouches", "jobTitle": "Orthodontiste",
        "medicalSpecialty": "Orthodontic",
        "url": DOMAINE + "/dr-renaud-desouches.html",
        "image": DOMAINE + "/assets/img/dr-desouches-1200.webp",
        "worksFor": {"@id": DOMAINE + "/#cabinet"},
        "address": {"@type": "PostalAddress", "addressLocality": "Aix-en-Provence",
                    "postalCode": "13090", "addressCountry": "FR"}
    }, ensure_ascii=False, indent=2))

# ---- PAGE 18 : Notre approche ----------------------------------------------
page(
    "notre-approche.html",
    "Notre approche de l’orthodontie | Dr Desouches, Aix-en-Provence",
    "L’approche du cabinet d’orthodontie du Dr Desouches à Aix-en-Provence : diagnostic, numérique, aligneurs, fabrication, suivi connecté et contention.",
    "Notre approche de l’orthodontie",
    "La technologie est un outil au service du diagnostic et du suivi clinique. Jamais l’inverse. C’est la seule ligne directrice de ce cabinet.",
    bande(duo(
        titre_bloc("Le fil conducteur", "Un cabinet numérique reste un cabinet médical."),
        prose(
            "<p>Il est facile aujourd’hui de confondre modernité et qualité de soin. Un scanner, une simulation 3D "
            "et une application ne font pas un bon traitement : ils rendent possible un bon traitement, à condition "
            "qu’un diagnostic solide précède et qu’un praticien décide.</p>"
            "<p>C’est la raison pour laquelle nous n’avons jamais présenté les aligneurs comme un produit. Ce sont "
            "des dispositifs médicaux, prescrits après examen, dont la série est calculée, contrôlée et corrigée "
            "au fil du traitement.</p>"), collant=True)) +
    bande(duo(
        titre_bloc("En pratique", "Huit étapes qui reviennent dans chaque dossier."),
        sequence([
            ("Diagnostic", "Examen clinique, radiographies, analyse de l’occlusion et des fonctions."),
            ("Numérique", "Empreinte optique, modèles 3D, photographies standardisées."),
            ("Aligneurs", "Le traitement de référence lorsqu’il est indiqué."),
            ("Personnalisation", "Un plan dessiné pour une bouche précise."),
            ("Fabrication", "Conception et contrôle des séries d’aligneurs."),
            ("Suivi connecté", "Des scans réguliers entre les rendez-vous."),
            ("Contrôle orthodontique", "L’examen clinique tranche toujours."),
            ("Contention", "La stabilisation fait partie du traitement."),
        ])), variante="marine"),
    "Notre approche", RUB_CABINET)

# ---- PAGE 19 : Technologie --------------------------------------------------
page(
    "technologie.html",
    "Technologie et orthodontie numérique | Dr Desouches, Aix-en-Provence",
    "Scanner intra-oral, empreintes numériques, planification et simulation 3D, fabrication numérique, Dental Monitoring et Ortho Mind, à Aix-en-Provence.",
    "Technologie et orthodontie numérique",
    "Ce que nous utilisons, et à quoi cela sert précisément. Sans emballement, parce qu’un outil n’a de valeur que par ce qu’il permet de mieux faire.",
    bande('<div class="duo" style="align-items:start"><div data-reveler>' +
          prose(
              "<h3>Scanner intra-oral</h3><p>Une caméra qui relève la forme exacte des arcades en quelques minutes. "
              "Fini les pâtes à empreinte, et surtout : un modèle numérique immédiatement exploitable et reproductible.</p>"
              "<h3>Empreintes numériques</h3><p>Elles servent de base à toute la planification et permettent de comparer "
              "l’évolution d’un rendez-vous à l’autre avec précision.</p>"
              "<h3>Photographies standardisées</h3><p>Des vues codifiées, prises dans les mêmes conditions à chaque étape. "
              "C’est ce qui rend une comparaison honnête.</p>"
              "<h3>Logiciels de planification</h3><p>Ils permettent de définir les déplacements dent par dent, de "
              "vérifier les collisions et de calculer la séquence des aligneurs.</p>") +
          '</div><div data-reveler data-reveler-delai="1">' +
          prose(
              "<h3>Simulation 3D</h3><p>Une projection du résultat attendu, utile pour expliquer et pour valider un "
              "plan. C’est une projection, pas une promesse : la biologie garde son mot à dire.</p>"
              "<h3>Fabrication numérique</h3><p>La production des aligneurs à partir des modèles validés, avec un "
              "contrôle des pièces avant remise.</p>"
              "<h3>Dental Monitoring</h3><p>Le suivi entre les rendez-vous, à partir de scans réalisés au smartphone.</p>"
              "<h3>Ortho Mind</h3><p>La première analyse du sourire à partir de photographies, en amont du bilan.</p>"
              "<h3>Intelligence artificielle</h3><p>Elle intervient dans l’analyse d’images : détecter, mesurer, comparer. "
              "Elle ne pose pas de diagnostic et ne décide d’aucun traitement. Ces décisions relèvent de l’orthodontiste.</p>") +
          '</div></div>') +
    bande('<div data-reveler style="max-width:42rem">' + avis(
        "Les outils numériques complètent l’examen clinique et le dossier radiographique. Ils ne s’y substituent pas.")
        + boutons(btn("Notre approche", "notre-approche.html"), btn("Le suivi connecté", "dental-monitoring.html")) +
        '</div>', variante="verre"),
    "Technologie", RUB_CABINET)

# ---- PAGE 20 : Casper Dental ------------------------------------------------
page(
    "casper-dental.html",
    "Casper Dental — Nos aligneurs pour les professionnels",
    "Casper Dental, né de l’expérience clinique et de la maîtrise de la conception et de la fabrication des aligneurs au cabinet du Dr Renaud Desouches à Aix-en-Provence.",
    "Casper Dental : notre expertise des aligneurs au service des professionnels",
    "Ce que nous avons appris en concevant nos propres aligneurs, nous le mettons aujourd’hui à disposition des orthodontistes et chirurgiens-dentistes.",
    bande(duo(
        titre_bloc("L’origine", "Une réponse à un besoin de cabinet."),
        prose(
            "<p>Casper Dental est né d’un constat de terrain : entre le plan de traitement pensé par l’orthodontiste "
            "et la gouttière effectivement produite, trop de décisions échappaient au praticien.</p>"
            "<p>L’expérience clinique accumulée au cabinet et la maîtrise de la conception et de la fabrication des "
            "aligneurs ont conduit à structurer cette activité pour d’autres professionnels.</p>"
            "<p>Pour vous, patient, cela signifie une chose : votre traitement est conçu par un praticien qui "
            "connaît intimement le dispositif qu’il vous prescrit.</p>"), collant=True)) +
    bande(
        '<div data-reveler style="max-width:40rem">'
        '<h2>Vous êtes orthodontiste ou chirurgien-dentiste ?</h2>'
        '<p class="chapo" style="margin-top:1.2rem">L’ensemble de l’offre professionnelle, les modalités de '
        'collaboration et la documentation technique sont présentés sur le site dédié.</p>' +
        boutons(btn("Découvrir Casper Dental", "https://casperdental.fr/", "primaire", True)) +
        ''
        '</div>', variante="marine"),
    "Casper Dental", RUB_CABINET)

# ---- PAGE 21 : Tarifs -------------------------------------------------------
page(
    "tarifs.html",
    "Prix d’un traitement orthodontique à Aix-en-Provence | Dr Desouches",
    "Prix d’un traitement orthodontique à Aix-en-Provence : devis, bilan, aligneurs, contention, Sécurité sociale, mutuelles et modalités de paiement.",
    "Prix d’un traitement orthodontique à Aix-en-Provence",
    "Un traitement orthodontique n’a pas de prix unique. Il a en revanche un devis écrit, remis avant tout engagement, et des règles de remboursement claires.",
    bande(duo(
        titre_bloc("Comment se construit un devis", "Quatre éléments, pas un seul."),
        prose(
            liste([
                "L’<strong>étendue de la correction</strong> et le nombre d’aligneurs nécessaires.",
                "La <strong>durée prévue</strong> du traitement et du suivi.",
                "Les <strong>dispositifs complémentaires</strong> éventuels.",
                "La <strong>contention</strong> et son suivi dans le temps.",
            ]) +
            "<p>Le devis vous est remis après le bilan, détaillé poste par poste, et vous repartez avec. Aucun "
            "traitement ne débute sans qu’il ait été signé.</p>"), collant=True)) +
    bande(duo(
        titre_bloc("Remboursement", "Ce que prend en charge l’Assurance Maladie."),
        prose(
            "<h3>Avant 16 ans</h3>"
            "<p>Les traitements orthodontiques débutés <strong>avant le 16<sup>e</sup> anniversaire</strong> sont "
            "pris en charge par l’Assurance Maladie, sous réserve d’une demande d’entente préalable acceptée. "
            "La prise en charge s’effectue par semestres de traitement, dans la limite d’un nombre défini de "
            "semestres, suivis de séances de contention.</p>"
            "<h3>Après 16 ans</h3>"
            "<p>Les traitements orthodontiques ne sont pas remboursés par la Sécurité sociale. De nombreuses "
            "complémentaires santé prévoient toutefois un forfait spécifique pour l’orthodontie adulte : il est "
            "utile de leur transmettre le devis avant de commencer.</p>"
            "<h3>Dépassements et paiement</h3>"
            "<p>L’orthodontie relève d’honoraires à entente directe : le montant réellement facturé peut donc "
            "dépasser la base de remboursement. C’est précisément ce que détaille le devis. Un échelonnement des "
            "paiements sur la durée du traitement est possible.</p>" +
            avis("La grille tarifaire du cabinet sera publiée sur cette page selon ce que le cabinet souhaite rendre "
                 "public, dans le respect des obligations d’information sur les prix des professionnels de santé.")),
        modif="inverse"), variante="verre"),
    "Tarifs et remboursement", RUB_CABINET)

# ---- PAGE 22 : FAQ ----------------------------------------------------------
FAQ_THEMES = [
    ("Enfants", [
        ("À quel âge faut-il consulter un orthodontiste ?",
         "Le repère est 6–7 ans, à l’arrivée des premières dents définitives. Une consultation plus tardive reste utile, mais certaines corrections liées à la croissance sont plus simples à cet âge."),
        ("Mon enfant suce encore son pouce, est-ce un problème ?",
         "Au-delà de l’âge habituel, une succion prolongée peut modifier la position des dents et la forme du palais. C’est un des points examinés lors du bilan."),
        ("Un traitement précoce est-il toujours suivi d’un second ?",
         "Pas systématiquement, mais c’est fréquent. La première phase vise un objectif précis lié à la croissance ; l’alignement final se termine souvent à l’adolescence."),
    ]),
    ("Adolescents", [
        ("Faut-il attendre que toutes les dents définitives soient sorties ?",
         "Pas nécessairement. Certains traitements sont plus efficaces avant la fin de la croissance. Le moment optimal se détermine au bilan."),
        ("Mon adolescent fait du sport de contact, est-ce compatible ?",
         "Oui. Les aligneurs se retirent et un protège-dents peut être porté. Avec un appareil fixe, une protection adaptée est recommandée."),
    ]),
    ("Adultes", [
        ("Y a-t-il un âge limite ?",
         "Non. Ce qui compte est l’état de l’os et de la gencive, pas l’âge. Un bilan parodontal précède le traitement."),
        ("J’ai des couronnes et un implant, est-ce possible ?",
         "Souvent oui, en tenant compte du fait qu’un implant ne se déplace pas. Cela s’intègre dans la planification."),
    ]),
    ("Aligneurs", [
        ("Combien d’heures par jour ?",
         "Environ 22 heures : tout le temps, sauf pour manger et se brosser les dents."),
        ("Peut-on manger avec ses aligneurs ?",
         "Non. On les retire pour chaque repas, puis on se brosse les dents avant de les remettre."),
        ("Comment nettoyer ses gouttières ?",
         "À l’eau froide ou tiède, avec une brosse souple. Ni eau chaude, qui déforme le matériau, ni dentifrice abrasif, qui le raye et le rend opaque."),
        ("Les aligneurs font-ils mal ?",
         "Une pression est habituelle un à deux jours après chaque changement. Elle traduit le déplacement en cours et s’estompe ensuite."),
        ("Que faire si j’en perds un ?",
         "Prévenir le cabinet, remettre l’aligneur précédent et attendre les consignes. Ne jamais passer directement au suivant."),
    ]),
    ("Dental Monitoring", [
        ("Comment fonctionne le suivi à distance ?",
         "Vous êtes notifié, vous scannez vos arcades avec votre smartphone, les images sont analysées puis relues dans le cadre de votre suivi orthodontique."),
        ("Cela remplace-t-il les rendez-vous ?",
         "Non. Le suivi connecté complète les consultations et permet de réagir plus tôt entre deux visites."),
    ]),
    ("Ortho Mind", [
        ("Est-ce un diagnostic ?",
         "Non. Ortho Mind fournit une première orientation à partir de photographies. Un diagnostic nécessite un examen clinique et des radiographies."),
        ("Mes photos sont-elles protégées ?",
         "Ce sont des données de santé, traitées dans le cadre prévu par la réglementation applicable et conservées de manière sécurisée."),
    ]),
    ("Prix et remboursement", [
        ("Combien coûte un traitement ?",
         "Le montant dépend de l’étendue de la correction et de la durée. Un devis écrit et détaillé vous est remis après le bilan, avant tout engagement."),
        ("Qu’est-ce qui est remboursé ?",
         "Les traitements débutés avant 16 ans sont pris en charge par l’Assurance Maladie sous entente préalable. Au-delà, la prise en charge relève des complémentaires santé."),
    ]),
    ("Urgences", [
        ("Une gouttière fissurée, que faire ?",
         "Contactez le cabinet. Selon l’avancement de l’étape, il peut être possible de poursuivre, de revenir à l’aligneur précédent ou de refaire la pièce."),
        ("Un attachement s’est décollé.",
         "Ce n’est pas douloureux mais cela peut ralentir un déplacement. Signalez-le pour qu’il soit recollé lors du prochain contrôle, ou plus tôt si nécessaire."),
    ]),
    ("Contention", [
        ("À quoi sert la contention ?",
         "À stabiliser le résultat. Les dents gardent toute la vie une tendance à se déplacer : la contention s’oppose à cette récidive."),
        ("Combien de temps faut-il la porter ?",
         "Très longtemps, souvent avec un port nocturne au long cours. Les modalités sont définies en fin de traitement et réévaluées lors des contrôles."),
    ]),
]
TOUTES_QUESTIONS = [qr for _, lot in FAQ_THEMES for qr in lot]
corps_faq = "".join(
    bande('<div class="duo"><div data-reveler><h2>%s</h2></div>'
          '<div data-reveler data-reveler-delai="1">%s</div></div>' % (theme, faq(lot)),
          variante="verre" if i % 2 else "")
    for i, (theme, lot) in enumerate(FAQ_THEMES))
page(
    "faq.html",
    "Questions fréquentes sur l’orthodontie | Aix-en-Provence",
    "Les questions fréquentes sur l’orthodontie à Aix-en-Provence : enfants, adolescents, adultes, aligneurs, suivi connecté, prix, urgences et contention.",
    "Questions fréquentes",
    "Les réponses aux questions que les patients nous posent réellement, classées par thème. Si la vôtre n’y figure pas, posez-la nous en consultation.",
    corps_faq, "Questions fréquentes", schema=schema_faq(TOUTES_QUESTIONS))

# ---- PAGE 24 : Cabinet ------------------------------------------------------
page(
    "cabinet-aix-en-provence.html",
    "Cabinet d’orthodontie à Aix-en-Provence — Dr Renaud Desouches",
    "Cabinet d’orthodontie du Dr Renaud Desouches à Aix-en-Provence : adresse, téléphone, horaires, accès, parking, transports et prise de rendez-vous.",
    "Cabinet du Dr Renaud Desouches — Orthodontiste à Aix-en-Provence",
    "Toutes les informations pratiques pour venir au cabinet : adresse, horaires, accès et stationnement.",
    bande('<div class="duo"><div data-reveler>' +
          prose(
              "<h3>Adresse</h3><p>1422 route de Galice<br>13090 Aix-en-Provence</p>"
              "<h3>Téléphone</h3><p><a class=\"lien-souligne\" href=\"tel:+33442205043\">04 42 20 50 43</a></p>"
              "<h3>Horaires d’ouverture</h3><p>Du mardi au vendredi<br>9h30 – 12h et 14h – 19h</p>"
              "<h3>Prise de rendez-vous</h3><p>En ligne via Doctolib, ou par téléphone au <a class=\"lien-souligne\" href=\"tel:+33442205043\">04 42 20 50 43</a> aux heures d’ouverture.</p>" +
              boutons(btn("Prendre rendez-vous sur Doctolib", "https://www.doctolib.fr/orthodontiste/aix-en-provence/renaud-desouches", "primaire", True))) +
          '</div><div data-reveler data-reveler-delai="1">' +
          prose(
              "<h3>Stationnement</h3><p>Parking gratuit sur place.</p>"
              "<h3>Accessibilité</h3><p>Accès de plain-pied.</p>"
              "<h3>Équipement</h3><p>Scanner intra-oral 3D et radiologie sur place.</p>"
              "<h3>Transports</h3><p>Lignes de bus et arrêts les plus proches : à compléter.</p>") +
          '<div class="cadre" style="margin-top:1.5rem;background:var(--glace-clair);border:0;'
          'display:grid;place-items:center;min-height:16rem;text-align:center">'
          '<p style="margin:0;color:var(--marine-60);font-size:.9rem">Emplacement réservé à la carte Google Maps '
          '<br>(à intégrer après recueil du consentement cookies)</p></div>'
          '</div></div>') +
    bande('<div data-reveler style="max-width:42rem">' + avis(
        "Les coordonnées, horaires et informations d’accès seront complétés avec les éléments transmis par le "
        "cabinet avant la mise en ligne.") + '</div>', variante="verre"),
    "Cabinet et accès", RUB_CABINET,
    schema=json.dumps({
        "@context": "https://schema.org", "@type": "Dentist",
        "@id": DOMAINE + "/#cabinet",
        "name": "Dr Renaud Desouches — Orthodontiste",
        "medicalSpecialty": "Orthodontic",
        "url": DOMAINE + "/cabinet-aix-en-provence.html",
        "telephone": "+33442205043",
        "address": {"@type": "PostalAddress", "streetAddress": "1422 route de Galice",
                    "addressLocality": "Aix-en-Provence", "postalCode": "13090",
                    "addressRegion": "Provence-Alpes-Côte d’Azur", "addressCountry": "FR"},
        "openingHours": "Tu-Fr 09:30-12:00,14:00-19:00",
        "sameAs": ["https://www.doctolib.fr/orthodontiste/aix-en-provence/renaud-desouches", "https://www.instagram.com/dr.renauddesouches/", "https://www.tiktok.com/@dr.renauddesouches"]
    }, ensure_ascii=False, indent=2))

# ---- PAGE 25 : Rendez-vous --------------------------------------------------
page(
    "rendez-vous.html",
    "Prendre rendez-vous — Orthodontiste à Aix-en-Provence | Dr Desouches",
    "Prendre rendez-vous au cabinet d’orthodontie du Dr Renaud Desouches à Aix-en-Provence, ou commencer par une analyse en ligne de votre sourire avec Ortho Mind.",
    "Prendre rendez-vous",
    "Deux entrées possibles, selon l’étape où vous en êtes. Les deux mènent au même endroit : une réponse claire sur votre situation.",
    bande('<div class="duo duo--egal"><div data-reveler>'
          '<div class="cadre"><h2 style="font-size:var(--t-h3)">Je veux consulter au cabinet</h2>'
          '<p style="margin-top:.8rem;color:var(--marine-60)">Première consultation ou bilan orthodontique complet, '
          'pour un enfant, un adolescent ou un adulte. Prévoyez la carte Vitale et, si vous en avez, vos '
          'radiographies récentes.</p>' +
          boutons(btn("Prendre rendez-vous sur Doctolib", "https://www.doctolib.fr/orthodontiste/aix-en-provence/renaud-desouches", "primaire", True)) +
          '</div>'
          '</div><div data-reveler data-reveler-delai="1">'
          '<div class="cadre"><h2 style="font-size:var(--t-h3)">Je veux d’abord analyser mon sourire</h2>'
          '<p style="margin-top:.8rem;color:var(--marine-60)">Quelques photos prises avec votre téléphone et une '
          'première orientation, sans vous déplacer et sans engagement.</p>' +
          boutons(btn("Démarrer mon Évaluation Orthodontique", "ortho-mind.html")) +
          '</div></div></div>') +
    bande('<div class="duo"><div data-reveler>' +
          titre_bloc("Nous joindre", "Par téléphone, aux heures d’ouverture.") +
          '</div><div data-reveler data-reveler-delai="1">' +
          prose("<h3>Téléphone</h3><p><a class=\"lien-souligne\" href=\"tel:+33442205043\">04 42 20 50 43</a></p>"
                "<h3>Adresse</h3><p>1422 route de Galice<br>13090 Aix-en-Provence</p>"
                "<h3>Horaires</h3><p>Du mardi au vendredi, 9h30 – 12h et 14h – 19h</p>" +
                boutons(btn("Accès et plan", "cabinet-aix-en-provence.html"))) +
          '</div></div>', variante="verre"),
    "Prendre rendez-vous",
    actions=boutons(btn("Prendre rendez-vous sur Doctolib", "https://www.doctolib.fr/orthodontiste/aix-en-provence/renaud-desouches", "primaire", True)))

# ---- Pages légales ----------------------------------------------------------
for slug, titre, chapo, blocs in [
    ("mentions-legales.html", "Mentions légales",
     "Mentions légales du site du Dr Renaud Desouches, orthodontiste à Aix-en-Provence : éditeur, directeur de la publication, hébergeur et propriété intellectuelle.",
     [("Éditeur du site", "Identité du praticien, statut d’exercice, numéro RPPS, numéro d’inscription au tableau de l’Ordre national des chirurgiens-dentistes, adresse professionnelle et coordonnées : à compléter."),
      ("Directeur de la publication", "À compléter."),
      ("Hébergeur", "Raison sociale, adresse et coordonnées de l’hébergeur : à compléter. Pour les données de santé, l’hébergement doit être assuré par un hébergeur certifié HDS."),
      ("Ordre professionnel", "Praticien inscrit à l’Ordre national des chirurgiens-dentistes. Exercice soumis au code de la santé publique et au code de déontologie."),
      ("Propriété intellectuelle", "L’ensemble des contenus du site est protégé. Toute reproduction sans autorisation est interdite.")]),
    ("confidentialite.html", "Politique de confidentialité",
     "Comment les données personnelles collectées sur le site du Dr Renaud Desouches, orthodontiste à Aix-en-Provence, sont traitées, conservées et protégées.",
     [("Responsable de traitement", "À compléter."),
      ("Données collectées", "Données transmises via les formulaires de contact et de prise de rendez-vous, données de connexion, et le cas échéant photographies transmises dans le cadre d’Ortho Mind."),
      ("Finalités", "Répondre aux demandes, organiser les rendez-vous, assurer le suivi des patients."),
      ("Base légale", "Exécution de mesures précontractuelles, obligation légale liée au dossier médical, consentement pour les traitements facultatifs."),
      ("Durée de conservation", "Selon les durées légales applicables aux dossiers médicaux et aux données de contact."),
      ("Vos droits", "Accès, rectification, effacement, limitation, opposition et portabilité. Réclamation possible auprès de la CNIL."),
      ("Contact", "Coordonnées du responsable de traitement et, le cas échéant, du délégué à la protection des données : à compléter.")]),
    ("cookies.html", "Gestion des cookies",
     "Les cookies utilisés sur le site du Dr Renaud Desouches, orthodontiste à Aix-en-Provence, leur finalité et la manière de paramétrer vos choix à tout moment.",
     [("Cookies strictement nécessaires", "Indispensables au fonctionnement du site, déposés sans consentement."),
      ("Mesure d’audience", "Déposés uniquement après consentement, sauf configuration exemptée."),
      ("Contenus tiers", "Carte Google Maps, module de prise de rendez-vous, lecteurs vidéo : chargés uniquement après consentement."),
      ("Paramétrer vos choix", "Un module de gestion du consentement sera intégré avant la mise en ligne, permettant d’accepter, de refuser et de modifier vos choix à tout moment.")]),
    ("donnees-de-sante.html", "Données de santé",
     "Le traitement des photographies et informations médicales transmises sur ce site, notamment via Ortho Mind : nature, hébergement, consentement et sécurité.",
     [("Nature des données", "Les photographies intra-buccales et du visage, ainsi que les informations relatives à votre situation dentaire, constituent des données de santé au sens du RGPD."),
      ("Hébergement", "Ces données doivent être hébergées auprès d’un hébergeur certifié HDS. Références de l’hébergeur : à compléter."),
      ("Finalité", "Fournir une première orientation, préparer la consultation et, le cas échéant, alimenter votre dossier de patient."),
      ("Consentement", "Le dépôt de photographies suppose un consentement explicite, recueilli avant tout envoi."),
      ("Publication de cas cliniques", "Aucune image de patient n’est publiée sur ce site sans autorisation écrite préalable, révocable à tout moment."),
      ("Sécurité", "Accès restreint aux personnes habilitées, transmission chiffrée, durées de conservation encadrées.")]),
]:
    page(slug, "%s | Dr Renaud Desouches, Aix-en-Provence" % titre,
         chapo, titre, chapo,
         bande('<div data-reveler style="max-width:44rem">' +
               prose("".join("<h3>%s</h3><p>%s</p>" % (t, c) for t, c in blocs)) +
               avis("Ce contenu est un cadre de travail. Les mentions définitives doivent être validées avant la "
                    "mise en ligne du site.") + '</div>'),
         titre, actions="")


page("404.html",
     "Page introuvable | Dr Renaud Desouches, Aix-en-Provence",
     "Cette page n’existe pas ou a été déplacée. Retrouvez l’orthodontie par aligneurs à Aix-en-Provence depuis le menu ou la page d’accueil.",
     "Cette page n’existe pas",
     "Le lien que vous avez suivi est peut-être ancien, ou l’adresse comporte une erreur.",
     bande('<div data-reveler style="max-width:40rem">'
           + prose("<p>Voici les pages les plus consultées :</p>"
                   + liste(['<a class="lien-souligne" href="aligneurs.html">Le traitement par aligneurs</a>',
                            '<a class="lien-souligne" href="bilan-6-7-ans.html">Le bilan de 6–7 ans</a>',
                            '<a class="lien-souligne" href="ortho-mind.html">Ortho Mind</a>',
                            '<a class="lien-souligne" href="cabinet-aix-en-provence.html">Le cabinet et son accès</a>',
                            '<a class="lien-souligne" href="faq.html">Les questions fréquentes</a>']))
           + '</div>'),
     "Page introuvable",
     actions=boutons(btn("Retour à l’accueil", "index.html", "primaire", True)))


# --------------------------------------------------------------------------
# 5. Écriture
# --------------------------------------------------------------------------
def ecrire():
    for p in PAGES:
        v = VISUELS.get(p["slug"])
        if v:
            fichier, alt, legende, ratio, variante, fond = v
            p["corps"] += bande(
                '<div style="max-width:56rem;margin-inline:auto">%s</div>'
                % visuel(fichier, alt, legende, ratio, variante),
                variante=fond, serree=True)
        html = GABARIT.format(
            title=p["title"], description=p["description"], slug=p["slug"], domaine=DOMAINE,
            entete=marquer_actif(ENTETE, p["slug"]), h1=p["h1"], chapo=p["chapo"],
            actions=p["actions"], corps=p["corps"], appel=APPEL if p["actions"] else "",
            pied=PIED, schema=p["schema"], fil=p["fil"], rubrique=p["rubrique"],
            v_css=empreinte("assets/css/site.css"), v_js=empreinte("assets/js/site.js"))
        with open(os.path.join(RACINE, p["slug"]), "w", encoding="utf-8") as f:
            f.write(html)
    print("%d pages générées." % len(PAGES))

    # Sitemap
    aujourdhui = datetime.date.today().isoformat()
    urls = ["", ] + [p["slug"] for p in PAGES if p["slug"] != "404.html"]
    prio = {"": "1.0", "aligneurs.html": "0.9", "bilan-6-7-ans.html": "0.9",
            "ortho-mind.html": "0.9", "dental-monitoring.html": "0.8"}
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
                   % (DOMAINE, u, aujourdhui, prio.get(u, "0.7")))
    xml.append("</urlset>")
    with open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(xml))

    with open(os.path.join(RACINE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % DOMAINE)
    print("sitemap.xml et robots.txt générés.")


if __name__ == "__main__":
    ecrire()
