Plus de 135 000 tablettes cunéiformes. 2,19 millions de lignes. Moins de 5 minutes pour les transformer en une base SQL interrogeable.

Je publie aujourd'hui Nisaba, un moteur open source pour l'épigraphie sumérienne computationnelle. 🏛️

Le problème : le corpus de la Cuneiform Digital Library Initiative (CDLI) est distribué sous forme de fichiers texte ATF accumulés sur 30 ans, avec des conventions hétérogènes. Difficile d'y poser une question simple (« qui a livré combien de moutons, et quand ? ») sans écrire un parseur ad hoc.

L'approche : compiler l'intégralité du dump CDLI en Apache Parquet / DuckDB, sans perdre les marques de cassure ni les signes endommagés, puis construire des outils déterministes et traçables par-dessus (chaque résultat renvoie à un P-number et à une ligne).

Ce que contient le dépôt :
• Compilateur ATF en streaming → 135 253 tablettes, 6,9 M de signes, 35 M de 4-mers indexés en 292 s
• Grand livre Ur III : extraction des transactions (ki…-ta / i3-dab5 / ba-zi) et bilans par fonctionnaire (24 018 transactions sur un échantillon de 5 000 tablettes)
• Datation des tablettes à formule d'année cassée par recoupement des carrières des fonctionnaires
• Recherche de raccords de fragments par similarité de k-mers (Jaccard)
• Explorateur HTML hors ligne avec photos CDLI, et requêtes DuckDB en quelques millisecondes

Statut, en toute honnêteté : c'est un outil d'ingénierie de données, pas un assyriologue. Les attributions de scribes, les dates inférées et les candidats de raccord sont des hypothèses heuristiques, pas encore validées par des spécialistes, et la précision n'a pas été mesurée sur une vérité terrain experte. C'est précisément là que j'ai besoin d'aide.

👉 Code (licence MIT) : https://github.com/silveremartin-dev/Nisaba
Retours, critiques et contributions bienvenus, en particulier de la part d'assyriologues et de chercheurs en humanités numériques.

#HumanitésNumériques #Assyriologie #OpenSource #DuckDB #DataEngineering #Python #Cunéiforme
