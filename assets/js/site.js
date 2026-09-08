/* =========================================================================
   Dr Renaud Desouches — interactions du site
   ========================================================================= */
(function () {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';
  var MOINS_DE_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ----------------------------------------------------------------------
     1. Moteur d'arcade dentaire
     Dessine une arcade maxillaire schématique interpolée entre
     un état encombré (t = 0) et un état aligné (t = 1).
     ---------------------------------------------------------------------- */

  // De la molaire gauche à la molaire droite.
  var DENTS = [
    { l: 10.5, h: 9.5 }, { l: 7.2, h: 8.6 }, { l: 7.2, h: 8.8 },
    { l: 7.8, h: 11.2 }, { l: 7.0, h: 9.4 }, { l: 8.6, h: 11.6 },
    { l: 8.6, h: 11.6 }, { l: 7.0, h: 9.4 }, { l: 7.8, h: 11.2 },
    { l: 7.2, h: 8.8 }, { l: 7.2, h: 8.6 }, { l: 10.5, h: 9.5 }
  ];

  // Déplacements de l'état initial : rotation (°), glissement le long de
  // l'arcade (px) et écart vestibulo-lingual (px). Encombrement antérieur.
  var DESORDRES = {
    encombrement: [
      { r: 2, s: 1, n: 1 }, { r: -4, s: 2, n: -2 }, { r: 6, s: 3, n: 3 },
      { r: -13, s: 7, n: -7 }, { r: 17, s: 9, n: 9 }, { r: -12, s: 7, n: -8 },
      { r: 14, s: -8, n: 8 }, { r: -16, s: -10, n: -9 }, { r: 11, s: -6, n: 7 },
      { r: -6, s: -3, n: -3 }, { r: 5, s: -2, n: 2 }, { r: -2, s: -1, n: -1 }
    ],
    diasteme: [
      { r: 0, s: -3, n: 0 }, { r: 0, s: -3, n: 0 }, { r: 1, s: -3, n: 0 },
      { r: -2, s: -5, n: 0 }, { r: 3, s: -7, n: 1 }, { r: -4, s: -9, n: 0 },
      { r: 4, s: 9, n: 0 }, { r: -3, s: 7, n: 1 }, { r: 2, s: 5, n: 0 },
      { r: -1, s: 3, n: 0 }, { r: 0, s: 3, n: 0 }, { r: 0, s: 3, n: 0 }
    ],
    proalveolie: [
      { r: 0, s: 0, n: 0 }, { r: -1, s: 0, n: 1 }, { r: 2, s: 1, n: 2 },
      { r: 5, s: 2, n: 6 }, { r: 8, s: 2, n: 10 }, { r: 11, s: 2, n: 13 },
      { r: -11, s: -2, n: 13 }, { r: -8, s: -2, n: 10 }, { r: -5, s: -2, n: 6 },
      { r: -2, s: -1, n: 2 }, { r: 1, s: 0, n: 1 }, { r: 0, s: 0, n: 0 }
    ],
    croise: [
      { r: 3, s: 0, n: -9 }, { r: 2, s: 0, n: -11 }, { r: 1, s: 0, n: -10 },
      { r: -6, s: 3, n: -4 }, { r: 9, s: 3, n: 4 }, { r: -5, s: 2, n: -3 },
      { r: 6, s: -2, n: 3 }, { r: -8, s: -3, n: -4 }, { r: 5, s: -3, n: 4 },
      { r: -1, s: 0, n: 2 }, { r: -2, s: 0, n: 2 }, { r: -3, s: 0, n: 1 }
    ]
  };

  var K = 4.3;      // unités -> pixels
  var RX = 196, RY = 220, CX = 300, CY = 46, RS = 182;

  function creer(nom, attrs) {
    var el = document.createElementNS(NS, nom);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  function positionsDeBase() {
    var total = 0, i;
    for (i = 0; i < DENTS.length; i++) total += DENTS[i].l * K;
    var curseur = -total / 2, pos = [];
    for (i = 0; i < DENTS.length; i++) {
      var larg = DENTS[i].l * K;
      pos.push(curseur + larg / 2);
      curseur += larg;
    }
    return pos;
  }

  var BASE = positionsDeBase();

  function construireArcade(svg, options) {
    options = options || {};
    svg.setAttribute('viewBox', '50 -8 500 268');
    svg.setAttribute('role', 'img');
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Gencive : arc discret placé derrière les dents.
    var gencive = creer('path', {
      d: arcPath(RX - 30, RY - 30, -1.30, 1.30),
      fill: 'none', stroke: 'var(--glace-clair)', 'stroke-width': 26,
      'stroke-linecap': 'round', opacity: '.9'
    });
    svg.appendChild(gencive);

    // Coque de l'aligneur.
    var coque = creer('path', {
      d: arcPath(RX + 2, RY + 2, -1.34, 1.34),
      fill: 'none', stroke: 'var(--glace)', 'stroke-width': 58,
      'stroke-linecap': 'round', opacity: '0', class: 'coque'
    });
    svg.appendChild(coque);

    var groupe = creer('g', {});
    svg.appendChild(groupe);

    var dents = [];
    for (var i = 0; i < DENTS.length; i++) {
      var d = DENTS[i];
      var forme = creer('rect', {
        x: (-d.l * K / 2).toFixed(2),
        y: (-d.h * K * 0.62).toFixed(2),
        width: (d.l * K - 1.6).toFixed(2),
        height: (d.h * K * 1.24).toFixed(2),
        rx: (d.l * K * 0.30).toFixed(2),
        fill: 'var(--verre)',
        stroke: 'var(--marine)',
        'stroke-width': 1.4,
        'stroke-opacity': .55,
        class: 'dent'
      });
      groupe.appendChild(forme);
      dents.push(forme);
    }

    var etat = {
      svg: svg, dents: dents, coque: coque,
      desordre: DESORDRES[options.desordre] || DESORDRES.encombrement
    };
    placer(etat, typeof options.t === 'number' ? options.t : 1);
    return etat;
  }

  function arcPath(rx, ry, a0, a1) {
    var pts = [], n = 26;
    for (var i = 0; i <= n; i++) {
      var a = a0 + (a1 - a0) * (i / n);
      pts.push(
        (CX + rx * Math.sin(a)).toFixed(1) + ' ' +
        (CY + ry * (1 - Math.cos(a))).toFixed(1)
      );
    }
    return 'M' + pts.join(' L');
  }

  function placer(etat, t) {
    var e = 1 - t;
    for (var i = 0; i < etat.dents.length; i++) {
      var dz = etat.desordre[i];
      var s = BASE[i] + dz.s * e;
      var a = s / RS;
      var n = dz.n * e;
      var x = CX + (RX + n) * Math.sin(a);
      var y = CY + (RY + n) * (1 - Math.cos(a));
      var rot = a * 180 / Math.PI + dz.r * e;
      etat.dents[i].setAttribute(
        'transform',
        'translate(' + x.toFixed(2) + ' ' + y.toFixed(2) + ') rotate(' + rot.toFixed(2) + ')'
      );
    }
    if (etat.coque) {
      etat.coque.setAttribute('opacity', (0.10 + t * 0.30).toFixed(3));
    }
  }

  /* ----------------------------------------------------------------------
     2. Arcade interactive du hero
     ---------------------------------------------------------------------- */
  function heroArcade() {
    var svg = document.getElementById('arcade-scene');
    if (!svg) return;
    var piste = document.getElementById('arcade-piste');
    var compteur = document.getElementById('arcade-compteur');
    var aide = document.getElementById('arcade-aide');
    var TOTAL = 34;

    var etat = construireArcade(svg, { t: 0, desordre: 'encombrement' });
    svg.setAttribute('aria-label',
      'Schéma d’une arcade dentaire passant d’un encombrement à un alignement, à faire varier avec le curseur.');

    function rendre(t) {
      placer(etat, t);
      var no = Math.round(1 + t * (TOTAL - 1));
      compteur.innerHTML = 'Aligneur ' + pad(no) + ' <em>/ ' + TOTAL + '</em>';
    }
    function pad(n) { return n < 10 ? '0' + n : '' + n; }

    piste.addEventListener('input', function () {
      rendre(this.value / 100);
      if (aide) aide.setAttribute('data-visible', 'false');
    });

    rendre(0);

    if (MOINS_DE_MOTION) {
      piste.value = 100; rendre(1);
      return;
    }

    // Séquence d'ouverture : l'arcade s'aligne une fois, puis la main prend le relais.
    var demarrage = null, DUREE = 2600, joue = true;
    function pas(ts) {
      if (!joue) return;
      if (demarrage === null) demarrage = ts;
      var p = Math.min(1, (ts - demarrage) / DUREE);
      var eased = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
      piste.value = eased * 100;
      rendre(eased);
      if (p < 1) requestAnimationFrame(pas);
      else if (aide) aide.setAttribute('data-visible', 'true');
    }
    piste.addEventListener('pointerdown', function () { joue = false; });
    setTimeout(function () { requestAnimationFrame(pas); }, 900);
  }

  /* ----------------------------------------------------------------------
     3. Comparateurs avant / après
     ---------------------------------------------------------------------- */
  function duels() {
    var liste = document.querySelectorAll('[data-duel]');
    Array.prototype.forEach.call(liste, function (duel) {
      var avant = duel.querySelector('[data-duel-avant]');
      var apres = duel.querySelector('[data-duel-apres]');
      var poignee = duel.querySelector('.duel__poignee');
      var faceApres = duel.querySelector('.duel__face--apres');
      var type = duel.getAttribute('data-duel') || 'encombrement';

      construireArcade(avant, { t: 0, desordre: type });
      construireArcade(apres, { t: 1, desordre: type });
      avant.setAttribute('aria-label', 'Schéma de la situation initiale');
      apres.setAttribute('aria-label', 'Schéma du résultat obtenu');

      function positionner(pc) {
        pc = Math.max(2, Math.min(98, pc));
        faceApres.style.clipPath = 'inset(0 0 0 ' + pc + '%)';
        poignee.style.left = pc + '%';
      }
      function depuisEvenement(ev) {
        var r = duel.getBoundingClientRect();
        positionner(((ev.clientX - r.left) / r.width) * 100);
      }
      var actif = false;
      duel.addEventListener('pointerdown', function (ev) {
        actif = true; duel.setPointerCapture(ev.pointerId); depuisEvenement(ev);
      });
      duel.addEventListener('pointermove', function (ev) { if (actif) depuisEvenement(ev); });
      duel.addEventListener('pointerup', function () { actif = false; });
      duel.addEventListener('pointercancel', function () { actif = false; });
      positionner(50);
    });
  }

  /* ----------------------------------------------------------------------
     4. En-tête, navigation, tiroir
     ---------------------------------------------------------------------- */
  function entete() {
    var barre = document.querySelector('.entete');
    if (!barre) return;
    var seuil = 8;
    function surDefilement() {
      barre.classList.toggle('est-detache', window.scrollY > seuil);
    }
    surDefilement();
    window.addEventListener('scroll', surDefilement, { passive: true });

    // Menus déroulants : survol + clavier.
    var items = document.querySelectorAll('.nav__item--menu');
    Array.prototype.forEach.call(items, function (item) {
      var bouton = item.querySelector('.nav__lien');
      var fermeture;
      function ouvrir() {
        clearTimeout(fermeture);
        Array.prototype.forEach.call(items, function (a) {
          if (a !== item) { a.setAttribute('data-ouvert', 'false'); a.querySelector('.nav__lien').setAttribute('aria-expanded', 'false'); }
        });
        item.setAttribute('data-ouvert', 'true');
        bouton.setAttribute('aria-expanded', 'true');
      }
      function fermer(delai) {
        fermeture = setTimeout(function () {
          item.setAttribute('data-ouvert', 'false');
          bouton.setAttribute('aria-expanded', 'false');
        }, delai || 0);
      }
      item.addEventListener('mouseenter', ouvrir);
      item.addEventListener('mouseleave', function () { fermer(120); });
      bouton.addEventListener('click', function (ev) {
        ev.preventDefault();
        if (item.getAttribute('data-ouvert') === 'true') fermer(0); else ouvrir();
      });
      item.addEventListener('focusin', ouvrir);
      item.addEventListener('focusout', function (ev) {
        if (!item.contains(ev.relatedTarget)) fermer(0);
      });
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Escape') return;
      Array.prototype.forEach.call(items, function (a) {
        a.setAttribute('data-ouvert', 'false');
        a.querySelector('.nav__lien').setAttribute('aria-expanded', 'false');
      });
    });

    // Tiroir mobile.
    var bascule = document.querySelector('.bascule');
    var tiroir = document.getElementById('tiroir');
    if (bascule && tiroir) {
      bascule.addEventListener('click', function () {
        var ouvert = bascule.getAttribute('aria-expanded') === 'true';
        bascule.setAttribute('aria-expanded', ouvert ? 'false' : 'true');
        tiroir.setAttribute('data-ouvert', ouvert ? 'false' : 'true');
        document.body.style.overflow = ouvert ? '' : 'hidden';
      });
      Array.prototype.forEach.call(tiroir.querySelectorAll('.tiroir__tete[aria-expanded]'), function (tete) {
        tete.addEventListener('click', function () {
          var ouvert = tete.getAttribute('aria-expanded') === 'true';
          tete.setAttribute('aria-expanded', ouvert ? 'false' : 'true');
          tete.nextElementSibling.setAttribute('data-ouvert', ouvert ? 'false' : 'true');
        });
      });
    }
  }

  /* ----------------------------------------------------------------------
     5. Révélations au défilement
     ---------------------------------------------------------------------- */
  function revelations() {
    var cibles = document.querySelectorAll('[data-reveler]');
    if (!cibles.length) return;
    if (MOINS_DE_MOTION || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(cibles, function (c) { c.classList.add('est-visible'); });
      return;
    }
    var obs = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('est-visible'); obs.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
    Array.prototype.forEach.call(cibles, function (c) { obs.observe(c); });
  }

  /* ----------------------------------------------------------------------
     6. Séquences numérotées : jauge de progression
     ---------------------------------------------------------------------- */
  function sequences() {
    var blocs = document.querySelectorAll('.sequence');
    if (!blocs.length) return;
    function maj() {
      Array.prototype.forEach.call(blocs, function (bloc) {
        var jauge = bloc.querySelector('.sequence__jauge');
        var etapes = bloc.querySelectorAll('.etape');
        var r = bloc.getBoundingClientRect();
        var ancre = window.innerHeight * 0.58;
        var p = (ancre - r.top) / r.height;
        p = Math.max(0, Math.min(1, p));
        if (jauge) jauge.style.height = (p * 100).toFixed(2) + '%';
        Array.prototype.forEach.call(etapes, function (et) {
          var pr = et.querySelector('.etape__puce').getBoundingClientRect();
          et.classList.toggle('est-atteinte', pr.top < ancre);
        });
      });
    }
    maj();
    window.addEventListener('scroll', maj, { passive: true });
    window.addEventListener('resize', maj);
  }

  /* ----------------------------------------------------------------------
     7. FAQ
     ---------------------------------------------------------------------- */
  function faq() {
    Array.prototype.forEach.call(document.querySelectorAll('.faq__q'), function (q) {
      q.addEventListener('click', function () {
        var ouvert = q.getAttribute('aria-expanded') === 'true';
        q.setAttribute('aria-expanded', ouvert ? 'false' : 'true');
        q.nextElementSibling.setAttribute('data-ouvert', ouvert ? 'false' : 'true');
      });
    });
  }

  /* ----------------------------------------------------------------------
     8. Filtres de la galerie
     ---------------------------------------------------------------------- */
  function filtres() {
    var barre = document.querySelector('.filtres');
    if (!barre) return;
    var boutons = barre.querySelectorAll('.filtre');
    var cas = document.querySelectorAll('.cas');
    var compte = document.getElementById('galerie-compte');

    barre.addEventListener('click', function (ev) {
      var b = ev.target.closest('.filtre');
      if (!b) return;
      Array.prototype.forEach.call(boutons, function (x) { x.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      var cat = b.getAttribute('data-filtre');
      var n = 0;
      Array.prototype.forEach.call(cas, function (c) {
        var ok = cat === 'tous' || (c.getAttribute('data-cat') || '').split(' ').indexOf(cat) !== -1;
        c.hidden = !ok;
        if (ok) n++;
      });
      if (compte) compte.textContent = n + (n > 1 ? ' cas affichés' : ' cas affiché');
    });
  }

  /* ----------------------------------------------------------------------
     9. Divers
     ---------------------------------------------------------------------- */
  function divers() {
    var an = document.getElementById('annee');
    if (an) an.textContent = new Date().getFullYear();

    var hero = document.querySelector('.hero');
    if (hero) requestAnimationFrame(function () { hero.classList.add('est-pret'); });
  }

  /* ---------------------------------------------------------------------- */
  /* --- Modale « évaluation à venir » --------------------------------------
     Les CTA d'évaluation ouvrent la modale plutôt que de mener à une page.
     Sans JavaScript, leur href reste valide : la modale est une surcouche. */
  function modaleEval() {
    var modale = document.getElementById('modale-eval');
    if (!modale) return;
    var declencheur = null;

    function focalisables() {
      return modale.querySelectorAll('a[href], button:not([disabled])');
    }

    function ouvrir(e) {
      e.preventDefault();
      declencheur = e.currentTarget;
      modale.hidden = false;
      document.body.style.overflow = 'hidden';
      var f = focalisables();
      if (f.length) f[f.length - 1].focus();
    }

    function fermer() {
      modale.hidden = true;
      document.body.style.overflow = '';
      if (declencheur) declencheur.focus();
    }

    [].forEach.call(document.querySelectorAll('[data-eval]'), function (el) {
      el.addEventListener('click', ouvrir);
    });
    [].forEach.call(modale.querySelectorAll('[data-fermer]'), function (el) {
      el.addEventListener('click', fermer);
    });

    document.addEventListener('keydown', function (e) {
      if (modale.hidden) return;
      if (e.key === 'Escape') { fermer(); return; }
      if (e.key !== 'Tab') return;
      var f = focalisables();
      if (!f.length) return;
      var premier = f[0], dernier = f[f.length - 1];
      if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus(); }
      else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus(); }
    });
  }

  function demarrer() {
    entete();
    revelations();
    heroArcade();
    duels();
    sequences();
    faq();
    filtres();
    divers();
    modaleEval();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
