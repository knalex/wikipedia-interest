"""Еталонні запити, спільні для запису відповідей і офлайн-тестів."""

IF_MSG = ("Порівняй зростання інтересу до інтервального голодування в польськомовній "
          "та чеськомовній Wikipedia за останні два роки.")
EN_MSG = ("Ми створюємо застосунок для вивчення мов. Порівняй інтерес до вивчення англійської у "
          "вибраних нами мовних розділах та підготуй короткий звіт: які аудиторії варто дослідити "
          "наступними й чому?")
EV_MSG = "Порівняй \"електромобілі\" в англійській, німецькій, французькій та японській Wikipedia."


def msg(*texts):
    args = []
    for text in texts:
        args += ["--user-message", text]
    return args


CASES = {
    "if_pl_cs": ["--query", "uk:інтервальне голодування", "--query", "en:intermittent fasting",
                 "--targets", "pl,cs"] + msg(IF_MSG),
    "if_pl_phrase": ["--query", "uk:інтервальне голодування", "--query", "en:intermittent fasting",
                     "--query", "pl:post przerywany", "--targets", "pl,cs"] + msg(IF_MSG, "post przerywany"),
    "if_include_broader": ["--query", "uk:інтервальне голодування", "--targets", "pl,cs",
                           "--include", "Q44602"] + msg(IF_MSG),
    "if_entity_cs": ["--entity", "Q1666254", "--targets", "cs"],
    "astronomy_uk": ["--query", "uk:астрономія", "--targets", "uk"]
                    + msg("Чи зростає інтерес до астрономії в українській Wikipedia?"),
    "english_learning": ["--query", "uk:вивчення англійської мови",
                         "--query", "en:English as a second or foreign language",
                         "--targets", "uk,pl,cs,de,es"]
                        + msg("Порівняй інтерес до вивчення англійської мови в різних мовних розділах Wikipedia."),
    # агент замінив слова користувача ширшим поняттям на повторному ході
    "english_substituted": ["--query", "uk:англійська мова",
                            "--query", "en:English as a second or foreign language",
                            "--targets", "uk,pl,de,es"]
                           + msg(EN_MSG, "Українська, польська, німецька та іспанська."),
    "mercury_ambiguous": ["--query", "en:Mercury", "--targets", "pl,cs"]
                         + msg("Compare interest in Mercury in the Polish and Czech Wikipedia."),
    # уточнення, яке дописав агент, не повинно мовчки знімати неоднозначність слів користувача
    "mercury_agent_qualifier": ["--query", "ru:Меркурий", "--query", "en:Mercury (planet)",
                                "--targets", "pl,cs"]
                               + msg("Сравни интерес к Меркурию в польской и чешской Википедии за последний год."),
    "unknown_edition": ["--query", "ru:биткоин", "--targets", "pl,tlh"]
                       + msg("Сравни интерес к биткоину в польской и клингонской Википедии."),
    # агент переклав «електромобілі» ширшим поняттям (electric vehicle = електротранспорт)
    "ev_broad_translation": ["--query", "uk:електромобілі", "--query", "en:electric vehicle",
                             "--targets", "en,de"] + msg(EV_MSG),
    "ev_exact_translation": ["--query", "uk:електромобіль", "--query", "en:electric car",
                             "--targets", "en,de"] + msg(EV_MSG),
    # назва латиницею в україномовному запиті
    "bitcoin_latin": ["--query", "uk:Bitcoin", "--query", "en:Bitcoin", "--targets", "en"]
                     + msg("Покажи тренд переглядів статті \"Bitcoin\" з 2010 по 2015 рік.", "Англійська Wikipedia."),
    "nonsense": ["--query", "uk:квантовий борщ Бородіна", "--query", "en:quantum borscht Borodin",
                 "--targets", "uk,cs"]
                + msg("Перевір, чи росте інтерес до квантового борщу Бородіна в українській і чеській Wikipedia."),
    "surname_only": ["--query", "ru:Шевченко", "--query", "en:Taras Shevchenko", "--targets", "pl,cs"]
                    + msg("Сравни интерес к Шевченко в польской и чешской Википедии."),
}

# Етап 2: (запит етапу 1, з кошика якого беруться статті; аргументи fetch_pageviews.py).
# Дата «сьогодні» зафіксована, щоб період і записані відповіді не залежали від дня запуску.
STAGE2_TODAY = "2026-09-27"
STAGE2_CASES = {
    "pv_if_last24": ("if_pl_cs", ["--last", "24"]),
    "pv_bitcoin_before_2015": ("bitcoin_latin", ["--start", "2010-01", "--end", "2015-12"]),
}
