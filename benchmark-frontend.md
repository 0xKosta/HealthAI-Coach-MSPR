# Benchmark Frontend — Choix du framework pour HealthAI Coach

## Contexte du projet

HealthAI Coach est une plateforme de coaching santé personnalisé construite autour d'une API REST FastAPI.
Le frontend est une **Progressive Web App (PWA)** — un choix délibéré de l'équipe — consommant des données biométriques, nutritionnelles et sportives via des endpoints REST.

L'équipe est resserrée, le périmètre fonctionnel est clairement défini, et les priorités techniques sont : **lisibilité du code, maintenabilité à moyen terme et vélocité de livraison**. Ce sont ces critères qui guident le choix du framework, pas des conventions imposées.

---

## 1. Les trois candidats

| Framework | Éditeur | Première release | Paradigme |
|-----------|---------|-----------------|-----------|
| **Angular** | Google | 2016 (réécriture complète) | Framework full-stack, orienté entreprise |
| **React** | Meta | 2013 | Bibliothèque UI, écosystème à assembler |
| **Vue** | Communauté open-source (Evan You) | 2014 | Framework progressif, cohérent et équilibré |

---

## 2. Critères de comparaison

| Critère | Angular | React | Vue |
|---------|---------|-------|-----|
| **Courbe d'apprentissage** | Élevée — DI, décorateurs, RxJS, NgModules | Moyenne — JSX, hooks, gestion d'état externe | Faible — SFC lisibles, Composition API progressive |
| **Structure du projet** | Très cadrée — modules, services, composants imposés | Très libre — chaque équipe définit ses propres conventions | Claire par défaut, sans rigidité excessive |
| **TypeScript** | Natif, pratiquement obligatoire | Très répandu, pas imposé | Bien supporté, totalement optionnel |
| **Formulaires** | Complet nativement (Reactive / Template Forms) | Via librairies tierces (React Hook Form, Formik…) | Simple et efficace (`v-model`, Vuelidate) |
| **Tests** | Outils intégrés (Jasmine, Karma, TestBed) | Écosystème très riche (Jest, RTL, Vitest) | Solide (Vitest, Vue Test Utils) |
| **Maintenabilité** | Excellente sur grands projets d'entreprise | Variable selon les conventions adoptées | Bonne sur des projets de taille intermédiaire |
| **Écosystème** | Monolithique et complet | Très vaste, mais très fragmenté | Cohérent et suffisant |
| **Adéquation projet** | Surdimensionné | Puissant mais trop permissif | Précisément adapté |

---

## 3. Analyse par framework

### Angular — Puissant, mais disproportionné

Angular embarque une architecture d'entreprise complète : injection de dépendances, décorateurs, observables RxJS, routing typé, NgModules… Ces mécanismes ont une vraie valeur sur des projets à plusieurs dizaines de développeurs avec des exigences de scalabilité strictes.

Sur HealthAI Coach, cette lourdeur architecturale devient contre-productive. Le temps investi à configurer l'infrastructure Angular dépasse largement le bénéfice obtenu. Le runtime seul pèse ~130 ko gzippé, et la courbe d'apprentissage impose un onboarding coûteux pour un périmètre fonctionnel qui ne le justifie pas.

> **Verdict** : Outil de référence pour les grandes structures IT. Inadapté à l'échelle et à la nature de ce projet.

---

### React — Populaire, mais structurellement fragmenté

React domine le marché et son écosystème est exceptionnel. Mais cette popularité masque un problème fondamental : **React seul ne fait quasiment rien**. Chaque besoin standard impose un choix externe supplémentaire :

- Routing → React Router, TanStack Router…
- État global → Redux, Zustand, Jotai, Recoil…
- Formulaires → React Hook Form, Formik…
- Requêtes HTTP → React Query, SWR, Axios…

Chaque décision prise indépendamment fragmente la cohérence du projet et alourdit la base de code sans valeur fonctionnelle ajoutée.

#### L'argument "PWA → React (→ React Native)" ne tient pas

Un raccourci fréquemment entendu : *"Autant partir sur React, ça facilitera le passage à React Native si on veut une app mobile."*

Ce raisonnement est techniquement inexact pour deux raisons :

**1. React Native est un framework complètement distinct de React web.**
Les composants natifs (`View`, `Text`, `FlatList`…), le système de navigation, les APIs plateforme — rien n'est directement transposable depuis une app React web. Le partage de code entre les deux est marginal. Partir sur React web "en prévision de React Native" n'offre aucun avantage concret.

**2. Le choix d'une PWA n'impose aucun framework.**
Une PWA est une application web enrichie d'un Service Worker et d'un manifeste JSON. Vue 3 + Vite + `vite-plugin-pwa` produisent une PWA complète, installable, avec cache hors-ligne et notifications push — sans la moindre concession fonctionnelle par rapport à React.

Si un portage mobile natif devient pertinent, la réponse adaptée est **Capacitor** — qui encapsule n'importe quelle app web (Vue, React, Angular) en app iOS/Android — ou une application native séparée avec les outils appropriés.

> **Verdict** : Choix solide pour une équipe mature sur une grande application. Ici, la liberté qu'il offre est un vecteur d'incohérence, pas un avantage.

---

### Vue — Le bon outil pour le bon problème

Vue 3 avec la Composition API et `<script setup>` offre le meilleur ratio **puissance / complexité / lisibilité** pour HealthAI Coach :

- **Single File Components (SFC)** : template, logique et styles coexistent dans un fichier `.vue` unique, cohérent et immédiatement lisible.
- **Réactivité native** : `ref()`, `computed()`, `watch()` — aucune bibliothèque externe pour couvrir 95 % des besoins.
- **Pinia** : gestionnaire d'état officiel, typé, sans boilerplate superflu.
- **Vue Router** : solution officielle, intégrée, complète.
- **Vite** : build instantané, Hot Module Replacement ultra-rapide, configuration PWA en quelques lignes.
- **Légèreté** : runtime Vue 3 ~22 ko gzippé, contre ~42 ko pour React + ReactDOM.

HealthAI Coach consomme des endpoints REST pour restituer des dashboards, des conseils IA et des formulaires. Vue 3 couvre l'intégralité de ces besoins **sans friction architecturale**.

> **Verdict** : Framework progressif, léger, cohérent — le choix le plus pertinent au regard des contraintes réelles du projet.

---

## 4. Synthèse

```
Complexité fonctionnelle du projet :  ████████░░░░░░░░  (intermédiaire)

Angular :  ████████████████████████  (surdimensionné)
React   :  ██████████████░░░░░░░░░░  (surdimensionné + fragmentation)
Vue     :  ████████░░░░░░░░░░░░░░░░  (aligné avec le besoin réel)
```

---

## 5. Décision

**Vue 3 est retenu comme framework frontend de HealthAI Coach.**

Les raisons de ce choix :

- **Légèreté** — runtime ~22 ko gzippé, impact minimal sur les performances perçues
- **Cohérence** — écosystème officiel intégré (Pinia, Vue Router, Vite), aucune décision d'assemblage à arbitrer
- **Lisibilité** — SFC et Composition API produisent un code immédiatement compréhensible et maintenable
- **Adéquation PWA** — support natif via `vite-plugin-pwa`, sans contrainte liée au choix du framework
- **Scalabilité maîtrisée** — suffisamment structurant pour garantir la cohérence, sans imposer une architecture disproportionnée

Angular et React sont des outils de qualité — dans leurs contextes respectifs. Le choix d'un framework se justifie par l'adéquation au problème posé, pas par sa notoriété. Vue 3 répond précisément aux exigences de HealthAI Coach.
