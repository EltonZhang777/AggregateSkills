import json
import re
import sys
import unicodedata


PROJECT_SKILLS = {
    "conventional-git-messages",
    "grill-duo-with-docs",
    "pr-and-merge",
    "requirements-to-spec-tickets",
    "spec-implement-loop",
}
PRESERVED_CHINESE = "已有说明：保留这段中文。"
CHINESE_MARKERS = (
    "账户", "账号", "中文", "英文", "请问", "哪种", "语言", "保留", "目标", "已", "未", "缓存", "恢复",
    "设置", "拒绝", "暂停", "停用", "系统", "服务", "请求", "操作", "驳回", "混合", "报告", "写入",
)
JAPANESE_HAN_MARKERS = ("対応", "実施", "確認", "変更", "対象", "現在", "開始", "停止", "仕様", "読込")
ENGLISH_MARKERS = {
    "an", "and", "after", "ask", "are", "before", "body", "by", "candidate", "complete", "completed",
    "criteria", "documentation", "draft", "english", "existing", "for", "from", "guide", "guidance", "has",
    "have", "if", "in", "including", "is", "issue", "it", "labels", "language", "map", "new", "not", "of",
    "on", "or", "policy", "preserve", "project", "pull", "ready", "reject", "rejects", "repository", "request",
    "root", "rule", "saving", "sentences", "service", "shortened", "status", "stores", "summary", "suspended",
    "target", "text", "the", "this", "ticket", "to", "untouched", "user-visible", "verbatim", "when", "which",
    "with", "work", "write", "written", "while", "therefore", "thus", "consequently", "hence", "so", "were",
    "preserving", "original", "meaning", "files", "changed",
}
ENGLISH_FUNCTION_WORDS = {
    "an", "and", "after", "are", "before", "by", "for", "from", "has", "have", "if", "in", "including", "not",
    "is", "it", "of", "on", "or", "the", "this", "to", "when", "which", "with", "while", "therefore",
    "thus", "consequently", "hence", "so", "were",
}
FOREIGN_WORDS = {
    "avec", "bonjour", "ce", "ces", "cette", "dans", "de", "des", "du", "et", "est", "français", "la",
    "el", "bien", "funciona", "il", "jouer", "langue", "le", "les", "par", "permis", "pour", "projet",
    "que", "qui", "sistema", "sont", "sur", "texte", "un", "une", "dépôt",
}
ENGLISH_RESULT_CONNECTORS = (
    "as a result", "therefore", "thus", "consequently", "so", "hence", "as such", "for that reason",
    "this causes", "this means", "that is why", "accordingly",
)
CHINESE_RESULT_CONNECTORS = ("因此", "所以", "于是", "因而", "从而", "由此", "结果")


def has_han(text):
    return re.search(r"[\u3400-\u9fff]", text) is not None


def has_kana(text):
    return re.search(r"[\u3040-\u30ff]", text) is not None


def has_non_han_letter(text):
    return any(
        unicodedata.category(character).startswith("L")
        and not "\u3400" <= character <= "\u9fff"
        for character in text
    )


def has_non_ascii_letter(text):
    return any(
        unicodedata.category(character).startswith("L") and ord(character) > 127
        for character in text
    )


def is_chinese(text):
    without_common_acronyms = re.sub(r"\bPR\b", "", text, flags=re.IGNORECASE)
    return (
        has_han(text)
        and not has_non_han_letter(without_common_acronyms)
        and not any(marker in text for marker in JAPANESE_HAN_MARKERS)
        and any(marker in text for marker in CHINESE_MARKERS)
    )


def is_english(text):
    if has_han(text) or has_kana(text) or has_non_ascii_letter(text):
        return False
    words = re.findall(r"[a-z]+(?:-[a-z]+)?", text.lower())
    if not words or any(word in FOREIGN_WORDS for word in words):
        return False
    return (
        sum(word in ENGLISH_MARKERS for word in words) / len(words) >= 0.25
        and any(word in ENGLISH_MARKERS - ENGLISH_FUNCTION_WORDS for word in words)
    )


def has_english_status_check_before_saving(text):
    lower = text.lower()
    check = re.search(r"\b(?:check|verify|confirm|validate)\w*\b", lower)
    if not check:
        return False
    before_check = lower[max(0, check.start() - 40):check.start()]
    after_check = lower[check.end():check.end() + 12]
    return (
        re.search(r"\baccount\w*\b", lower)
        and re.search(r"\b(?:status|state|standing)\b", lower)
        and re.search(r"\b(?:sav\w*|stor\w*|writ\w*)\b", lower)
        and re.search(r"\bbefore\b", lower)
        and not re.search(r"\b(?:not|never|no|without|skip\w*|fail\w*|avoid\w*|doesn't|don't|didn't|can't|cannot|won't|wouldn't|isn't)\b", before_check)
        and not re.match(r"\s+(?:no|none|neither)\b", after_check)
    )


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def has_english_rejection(text):
    if re.search(r"\bnot\s+accept\w*\b", text, re.IGNORECASE):
        return True
    negations = re.compile(
        r"\bnot\b(?!\s+only\b)|\b(?:never|no|cannot|can't|won't|wouldn't|doesn't|don't|didn't|isn't|aren't|wasn't|weren't)\b",
        re.IGNORECASE,
    )
    for match in re.finditer(r"\b(?:reject\w*|deny\w*|refus\w*|declin\w*|block\w*|turn\s+down)\b", text, re.IGNORECASE):
        prefix = text[:match.start()]
        prefix = re.split(r"\b(?:but|however|yet)\b|[.!?;]", prefix, flags=re.IGNORECASE)[-1]
        if not negations.search(prefix):
            return True
    return False


def has_english_rejection_causes_suspension(text):
    return re.search(
        r"\b(?:reject\w*|deny\w*|refus\w*|declin\w*|block\w*|turn\s+down|not\s+accept\w*)\b"
        r".{0,80}\b(?:caus\w*|lead\w*\s+to|result\w*\s+in)\b"
        r".{0,80}\baccounts?\b.{0,30}\b(?:suspend\w*|inactiv\w*|disabl\w*|paus\w*)\b",
        text,
        re.IGNORECASE,
    ) is not None


def chinese_rejection_position(text):
    positions = [text.find(term) for term in ("不接受", "不予受理") if term in text]
    for term in ("拒绝", "驳回", "拒收"):
        start = text.find(term)
        while start >= 0:
            prefix = text[:start]
            prefix = re.split(r"[，,；;。！？]|但是|然而|不过|\bbut\b|\bhowever\b", prefix)[-1]
            if not re.search(r"不会|不能|并不会|并不|并未|没有|无法|未被|不再|不予|无须|无需|不|未|没", prefix):
                positions.append(start)
                break
            start = text.find(term, start + len(term))
    return min(positions) if positions else None


def has_chinese_rejection_causes_suspension(text):
    return re.search(
        r"(?:拒绝|驳回|拒收|不接受|不予受理).{0,30}(?:导致|造成|引起|使|令)"
        r".{0,30}(?:账户|账号).{0,20}(?:暂停|停用|冻结|禁用)",
        text,
    ) is not None


def has_chinese_rejection(text):
    return chinese_rejection_position(text) is not None


def has_chinese_positive_account_suspension(text):
    if not any(word in text for word in ("账户", "账号")):
        return False
    states = list(re.finditer(r"暂停|停用|冻结|禁用", text))
    if not states:
        return False
    state = states[-1]
    preceding = text[max(0, state.start() - 10):state.start()]
    following = text[state.end():state.end() + 16]
    state_qualifier = re.split(r"[，,；;。！？：:]|时|后|导致|造成|引起|使|令", following, maxsplit=1)[0]
    return not re.search(r"并未|尚未|没有|未曾|未|没|不再|不", preceding + state_qualifier)


def has_chinese_account_rejection_relation(text):
    account_ends = [text.find(word) + len(word) for word in ("账户", "账号") if word in text]
    pause_ends = [text.find(word) + len(word) for word in ("暂停", "停用", "冻结", "禁用") if word in text]
    rejection = chinese_rejection_position(text)
    if not account_ends or not pause_ends or rejection is None or not has_chinese_positive_account_suspension(text):
        return False
    cause_end = max(max(account_ends), max(pause_ends))
    if cause_end >= rejection:
        return False
    bridge = text[cause_end:rejection]
    return any(marker in bridge for marker in (
        "时", "后", "期间", "情况下", "导致", "使", "造成", "引起", "因此", "所以", "于是", "从而",
    "因而", "则", "就", "会", "将", "便", "一旦", "如果", "当",
    ))


def has_english_causal_link(lines):
    for cause, effect in zip(lines, lines[1:]):
        cause_line = cause.lower()
        effect_line = effect.lower()
        account_state = re.search(
            r"\b(?:suspend\w*|inactiv\w*|disabl\w*|paus\w*)\b", cause_line
        )
        state_context = cause_line[max(0, account_state.start() - 35):account_state.start()] if account_state else ""
        caused_by_account = (
            re.search(r"\baccounts?\b", cause_line)
            and account_state
            and not re.search(r"\b(?:not|never|no longer|isn't|wasn't|aren't|weren't)\b", state_context)
            and not has_english_rejection(cause_line)
        )
        connector = next(
            (
                re.match(rf"\s*{re.escape(word)}\b\s*[,;:]?\s*", effect, re.IGNORECASE)
                for word in ENGLISH_RESULT_CONNECTORS
                if re.match(rf"\s*{re.escape(word)}\b\s*[,;:]?\s*", effect, re.IGNORECASE)
            ),
            None,
        )
        if (
            caused_by_account
            and connector
            and has_english_rejection(effect[connector.end():])
            and not has_english_rejection_causes_suspension(effect[connector.end():])
            and is_english(cause)
            and is_english(effect)
        ):
            return True
    return False


def has_chinese_causal_link(lines):
    for cause, effect in zip(lines, lines[1:]):
        caused_by_account = has_chinese_positive_account_suspension(cause) and not has_chinese_rejection(cause)
        connector = next((word for word in CHINESE_RESULT_CONNECTORS if effect.startswith(word)), None)
        outcome = effect[len(connector or ""):].lstrip(" ，,：:；;")
        rejected = has_chinese_rejection(outcome)
        if (
            caused_by_account
            and connector
            and rejected
            and not has_chinese_rejection_causes_suspension(outcome)
            and is_chinese(cause)
            and is_chinese(effect)
        ):
            return True
    return False


def artifact_text(value):
    if isinstance(value, dict):
        return "\n\n".join(str(part) for part in value.values())
    return str(value)


def has_same_fixture_heading_and_code_lines(source, candidate):
    def protected_lines(text):
        return [
            (index, line)
            for index, line in enumerate(text.splitlines())
            if line.startswith("#") or line.strip().startswith("`")
        ]

    return protected_lines(source) == protected_lines(candidate)


def has_source_authority_claim(sentences):
    for sentence in sentences:
        lower = sentence.lower()
        mentions_source_root = "aggregateskills" in lower or re.search(
            r"\b(?:source|installation|upstream|skill[- ]bundled)\b.{0,60}\bagents\.md\b|"
            r"\bagents\.md\b.{0,60}\b(?:source|installation|upstream|skill[- ]bundled)\b",
            lower,
        )
        if "agents.md" not in lower or not mentions_source_root:
            continue
        precedence_claim = re.search(r"\b(?:takes?|has)\s+precedence\b", lower)
        negated_precedence = re.search(
            r"\b(?:does\s+not|doesn't|never|not)\s+(?:take|takes|have|has)\s+precedence\b",
            lower,
        )
        if precedence_claim and not negated_precedence:
            return True
        if any(term in lower for term in ("authoritative", "source of truth", "authority")):
            negated_authority = re.search(
                r"\b(?:not|never)\s+(?:(?:an?|the)\s+)?(?:authoritative|authority|source of truth)\b|"
                r"\bsource of truth\b.{0,12}\b(?:is|are)\s+not\b|"
                r"\b(?:do not|don't|never|should not|must not)\s+(?:treat|consider|regard)\b"
                r".{0,100}\b(?:as|to be)\s+(?:(?:an?|the)\s+)?(?:authoritative|authority|source of truth)\b|"
                r"\b(?:(?:must|should|may|can|will)\s+)?not\s+be\s+(?:treated|considered|regarded)\b"
                r".{0,100}\b(?:as|to be)\s+(?:(?:an?|the)\s+)?(?:authoritative|authority|source of truth)\b|"
                r"不是权威|不作为权威",
                lower,
            )
            if not negated_authority:
                return True
        for match in re.finditer(
            r"\b(?:follow|use|apply|obey|trust|respect\w*|rely\s+on|govern\w*|control\w*|determin\w*)\b",
            lower,
        ):
            prefix = lower[max(0, match.start() - 40):match.start()]
            negated = re.search(
                r"\b(?:do not|don't|never|should not|must not|cannot|can't)\b(?:\W+[\w'-]+){0,4}\W*$|"
                r"(?:不要|不得|不应)(?:读取|遵循|使用|依赖)",
                prefix,
            )
            if not negated:
                return True
    return False


def asks_language_choice(question):
    cleaned = re.sub(r"(?<![A-Za-z])(?:PR|issue|English|[A-C])(?![A-Za-z])", "", question, flags=re.IGNORECASE)
    asks_which = any(
        phrase in cleaned
        for phrase in (
            "用哪种语言", "使用哪种语言", "用哪一种语言", "使用哪一种语言", "以何种语言", "采用何种语言",
            "用什么语言", "使用什么语言", "采用什么语言", "选择哪种语言",
        )
    )
    offers_choices = (
        any(term in cleaned for term in ("英文", "英语"))
        and any(term in cleaned for term in ("中文", "简体中文"))
        and any(term in cleaned for term in ("还是", "或", "双语"))
    )
    asks_for_text = any(term in question for term in (
        "撰写", "起草", "写入", "标题", "正文", "文档", "评论", "工单", "陈述", "文本", "项目", "草稿", "内容", "记录", "回复",
    )) or re.search(r"\b(?:PR|issue)\b", question, re.IGNORECASE)
    asks_to_write = any(term in question for term in ("用", "使用", "采用", "撰写", "起草", "写入", "写成", "希望", "需要", "想"))
    asks_preference = any(term in question for term in ("希望", "想要", "打算", "计划", "要用", "需要用", "应该", "应当", "应使用"))
    asks_to_classify_existing = (
        any(term in question for term in ("现有", "当前", "目前", "已写", "已经写", "已完成"))
        and any(term in question for term in ("标题", "正文", "文档", "评论", "文本", "内容"))
        and not asks_preference
    )
    return (
        not asks_to_classify_existing
        and
        is_chinese(cleaned)
        and (asks_which or offers_choices)
        and asks_for_text
        and asks_to_write
        and ("?" in question or "？" in question)
    )


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as result_file:
            results = json.load(result_file)
    else:
        results = json.load(sys.stdin)
    require(
        set(results) == {"compression_mixed", "compression_report", "compression_nonproject", "project_text", "ambiguous_policy", "same_repo"},
        "acceptance response set is incomplete",
    )
    require(not is_english("Le service rejette la demande."), "English check accepts a French sentence")
    require(not is_english("Il a un role a jouer."), "English check accepts a French sentence with shared short words")
    require(not is_english("Il a un permis."), "English check accepts a French sentence with a shared article")
    require(not is_english("The service rejects it. これはテストです。"), "English check accepts Japanese mixed into an English candidate")
    require(not is_chinese("Le rapport est français, 中文标记已保留。"), "Chinese check accepts a report led by French")
    require(not is_chinese("対応完了"), "Chinese check accepts a Kanji-only Japanese report")
    require(is_chinese("已拟好 PR 标题与正文。"), "Chinese check rejects a report containing the common PR acronym")
    require(is_english("The repository’s policy — when clear — uses English."), "English check rejects ordinary punctuation")
    require(not is_english("el sistema funciona bien and"), "English check accepts mostly Spanish text")
    require(not is_english("the and of the"), "English check accepts text made only of function words")
    require(not is_english("not"), "English check accepts a lone function word")
    require(not asks_language_choice("请问语言政策为什么没有统一？"), "generic language-policy question passed as a language choice")
    require(not asks_language_choice("请问哪种语言更好学？"), "unrelated which-language question passed as a language choice")
    require(not asks_language_choice("请问英文还是中文更好学？"), "unrelated language-choice options passed without a project-text context")
    require(not asks_language_choice("请问 PR 正文当前是英文还是中文？"), "existing text classification passed as a drafting preference")
    require(not asks_language_choice("请问现有PR正文当前使用哪种语言？"), "existing text language was treated as a drafting preference")
    require(asks_language_choice("请问 issue 草稿应使用哪种语言？"), "direct language-choice question was rejected")
    require(asks_language_choice("请问 PR 标题用英文还是中文？"), "language-choice question with ordinary acronyms was rejected")
    require(asks_language_choice("请问PR标题用英文还是中文？"), "language-choice question with an acronym beside Chinese was rejected")
    require(has_source_authority_claim(["The AggregateSkills source AGENTS.md is authoritative; do not rely on it."]), "source-root authority claim was not detected")
    require(has_source_authority_claim(["Follow the AggregateSkills source AGENTS.md for language policy."]), "source-root instruction was not detected when the repository name followed the verb")
    require(has_source_authority_claim(["Respect the AggregateSkills source AGENTS.md policy for target text."]), "source-root instruction was not detected with 'respect'")
    require(not has_source_authority_claim(["Do not read or rely on the AggregateSkills source repository's AGENTS.md."]), "source-root exclusion was misread as authority")
    require(not has_source_authority_claim(["The AggregateSkills source AGENTS.md is not authoritative."]), "negated source-root authority was misread as authority")
    require(has_source_authority_claim(["The source repository's AGENTS.md is authoritative."]), "source-root authority without the repository name was missed")
    require(has_source_authority_claim(["The source AGENTS.md takes precedence over the target root rule."]), "source-root precedence claim was not detected")
    require(not has_source_authority_claim(["The source AGENTS.md does not take precedence over the target root rule."]), "negated source-root precedence was treated as authority")
    require(not has_source_authority_claim(["The source AGENTS.md is not an authority."]), "'not an authority' was misread as a positive authority claim")
    require(not has_source_authority_claim(["Do not treat the source repository's AGENTS.md as authoritative."]), "negated 'treat as authoritative' was misread as a positive claim")
    require(has_source_authority_claim(["The skill-bundled AGENTS.md is authoritative for target text."]), "skill-bundled source-root authority was missed")
    require(has_source_authority_claim(["The upstream AGENTS.md governs language policy."]), "upstream source-root authority was missed")
    require(not has_source_authority_claim(["The source repository's AGENTS.md must not be treated as authoritative."]), "passive authority negation was misread as a positive claim")
    require(
        not has_same_fixture_heading_and_code_lines("# Notes\n`Service.check()`", "# Notes\n`Inserted.check()`\n`Service.check()`"),
        "protected structure check accepts an inserted code line",
    )
    require(
        not has_same_fixture_heading_and_code_lines("# Notes\nsource\n`Service.check()`", "# Notes\n`Service.check()`\nsource"),
        "protected code line can move relative to source prose",
    )
    require(has_english_causal_link(["The account is suspended.", "Therefore, the service refuses the request."]), "English causal paraphrase was rejected")
    require(has_english_causal_link(["The account is suspended.", "Accordingly, the service refuses the request."]), "equivalent English causal connector was rejected")
    require(not has_english_causal_link(["The account is not suspended.", "As a result, the service rejects the request."]), "negated account state was accepted as the cause")
    require(has_english_status_check_before_saving("The service checks the current account status before it saves the request."), "valid pre-save account-status check was rejected")
    require(not has_english_status_check_before_saving("Before saving, the service does not check account status."), "negated pre-save account-status check was accepted")
    require(not has_english_status_check_before_saving("Before saving, the service skips checking account status."), "skipped pre-save account-status check was accepted")
    require(not has_english_status_check_before_saving("Before saving, the service fails to check account status."), "failed pre-save account-status check was accepted")
    require(not has_english_causal_link(["The service rejects the request.", "So the account is suspended."]), "causal direction was reversed")
    require(not has_english_causal_link(["The service rejects requests, causing the account to be suspended.", "Therefore, the service refuses the request."]), "reversed cause embedded in the cause line was accepted")
    require(not has_english_rejection("The service does not reject the request."), "English negation was treated as rejection")
    require(has_english_rejection("The service not only rejects the request."), "'not only rejects' was mistaken for a negation")
    require(not has_english_rejection("The service does not under any circumstances, even after the full validation and processing of every related request, reject this request."), "long English negation was treated as rejection")
    require(not has_english_causal_link(["The account is suspended.", "Therefore, the service does not reject the request."]), "negated English outcome was accepted as causal")
    require(not has_english_causal_link(["The account is suspended.", "Therefore, the service does not under any circumstances reject the request."]), "long English negation was accepted as causal")
    require(not has_english_causal_link(["The account is suspended.", "Therefore, the service refuses the request, which in turn causes the account to be suspended."]), "reverse causation in the English result line was accepted")
    require(not has_english_causal_link(["The account is suspended.", "The service also rejects the request."]), "non-causal 'also' was treated as a connector")
    require(is_chinese("账号停用导致操作被驳回。"), "Chinese check rejected a valid synonym-rich sentence")
    require(has_chinese_account_rejection_relation("账号停用导致操作被驳回。"), "valid Chinese account-to-rejection wording was rejected")
    require(not has_chinese_account_rejection_relation("系统拒绝请求时，账户暂停。"), "reversed Chinese cause and effect was accepted")
    require(not has_chinese_account_rejection_relation("账户未暂停时，系统会拒绝该请求。"), "negated Chinese suspension was accepted as the source cause")
    require(not has_chinese_causal_link(["账户未暂停。", "因此服务拒绝请求。"]), "negated Chinese suspension was accepted as the causal state")
    require(not has_chinese_positive_account_suspension("账户暂停状态尚未生效。"), "post-state Chinese negation was treated as a positive suspension")
    require(not has_chinese_causal_link(["账户暂停状态尚未生效。", "因此服务拒绝请求。"]), "post-state Chinese negation was accepted as the causal state")
    require(not has_chinese_positive_account_suspension("账户暂停后，账户仍未处于暂停状态。"), "a later negated account state was masked by an earlier positive state")
    require(not has_chinese_causal_link(["账户暂停后，账户仍未处于暂停状态。", "因此服务拒绝请求。"]), "a later negated account state was accepted as causal")
    require(not has_chinese_rejection("账户暂停时，系统不会拒绝请求。"), "Chinese negation was treated as rejection")
    require(not has_chinese_rejection("服务不会在任何情况下根据账户状态、本次请求及处理流程完成校验后拒绝该请求。"), "long Chinese negation was treated as rejection")
    require(not has_chinese_causal_link(["账户暂停。", "因此服务不会拒绝请求。"]), "negated Chinese outcome was accepted as causal")
    require(not has_chinese_causal_link(["账户暂停。", "因此，服务不会轻易拒绝请求。"]), "long Chinese negation was accepted as causal")
    require(has_chinese_causal_link(["账号停用。", "所以操作被驳回。"]), "compressed Chinese causal paraphrase was rejected")
    require(not has_chinese_causal_link(["服务拒绝请求。", "因此账户暂停。"]), "Chinese causal direction was reversed")
    require(not has_chinese_causal_link(["服务拒绝请求，导致账户暂停。", "因此服务拒绝请求。"]), "reversed cause embedded in the cause line was accepted")
    require(not has_chinese_causal_link(["账户暂停。", "因此服务拒绝请求，进而导致账户暂停。"]), "reverse causation in the Chinese result line was accepted")
    mixed = results["compression_mixed"]
    source = (
        "# Language notes\n"
        "The service checks the current account status before it saves the request.\n"
        "The account is suspended.\n"
        "As a result, the service rejects the request.\n"
        "账户暂停时，系统会拒绝该请求。\n"
        "账户已暂停。\n"
        "因此，服务拒绝该请求。\n"
        "The transition is unclear. 这句附近缺少语言线索。\n"
        "`Service.validate()`\n"
    )
    candidate = mixed["candidate"]
    require(
        len(candidate.encode("utf-8")) < len(source.encode("utf-8")),
        "mixed-language candidate is not shorter",
    )
    unclear_mixed = "The transition is unclear. 这句附近缺少语言线索。"
    require(has_same_fixture_heading_and_code_lines(source, candidate), "candidate changed, inserted, or reordered the fixture heading or code line")
    require(unclear_mixed in candidate.splitlines(), "an unclear mixed-language sentence was changed or spliced")
    source_ordered_lines = [
        line for line in candidate.splitlines()
        if line.strip() and not line.startswith("#") and not line.strip().startswith("`") and line != unclear_mixed
    ]
    require(len(source_ordered_lines) == 6, "candidate changed the number or order of source sentences")
    english_lines, chinese_lines = source_ordered_lines[:3], source_ordered_lines[3:]
    require(all(is_english(line) for line in english_lines), "rewritten English source sentences changed language")
    require(all(is_chinese(line) for line in chinese_lines), "rewritten Chinese source sentences changed language")
    require(
        has_english_status_check_before_saving(english_lines[0]),
        "first English source sentence lost or negated its account-status check before saving",
    )
    require(
        re.search(r"\baccount\w*\b", english_lines[1], re.IGNORECASE)
        and re.search(r"\b(?:suspend\w*|inactiv\w*|disabl\w*|paus\w*)\b", english_lines[1], re.IGNORECASE),
        "second English source sentence lost the suspended-account state",
    )
    require(
        any(re.match(rf"\s*{re.escape(word)}\b", english_lines[2], re.IGNORECASE) for word in ENGLISH_RESULT_CONNECTORS)
        and has_english_rejection(english_lines[2]),
        "third English source sentence lost its result connector or rejection",
    )
    require(has_chinese_account_rejection_relation(chinese_lines[0]), "first Chinese source sentence lost or reversed the suspension and rejection relationship")
    require(
        has_chinese_positive_account_suspension(chinese_lines[1]),
        "second Chinese source sentence lost or negated the suspended-account state",
    )
    require(
        any(chinese_lines[2].startswith(word) for word in CHINESE_RESULT_CONNECTORS)
        and has_chinese_rejection(chinese_lines[2]),
        "third Chinese source sentence lost its result connector or rejection",
    )
    require(has_english_causal_link(english_lines), "English causal direction or source-language context changed")
    require(has_chinese_causal_link(chinese_lines), "Chinese causal link lost its source-language context")
    require(is_chinese(mixed["report"]), "compression report does not use Chinese")
    require(
        "英文" in mixed["report"] and "中文" in mixed["report"]
        and any(term in mixed["report"] for term in ("混合", "兼有", "同时包含")),
        "compression report omitted the resulting English/Chinese mixture",
    )

    report_case = results["compression_report"]
    require(
        report_case["languages"] == {"target": "Japanese", "source": "English", "conversation": "Chinese"},
        "compression report scenario does not use three distinct languages",
    )
    english_source = "The guide stores all user-visible labels in a central map."
    report_candidate = report_case["candidate"]
    require(
        len(report_candidate.encode("utf-8")) < len(english_source.encode("utf-8")),
        "report-language candidate is not shorter",
    )
    require(is_english(report_candidate), "English source content was not compressed in English")
    require(is_chinese(report_case["report"]), "conversation-facing report does not use Chinese only")

    nonproject = results["compression_nonproject"]
    nonproject_source = "缓存失效后，应按顺序恢复各项设置。该文件面向独立用户，不应翻译。"
    nonproject_candidate = nonproject["candidate"].strip()
    require(
        has_han(nonproject_candidate)
        and not has_non_han_letter(nonproject_candidate)
        and is_chinese(nonproject_candidate)
        and all(term in nonproject_candidate for term in ("缓存", "恢复", "设置")),
        "non-project source content was not compressed in Chinese",
    )
    require(
        len(nonproject_candidate.encode("utf-8")) < len(nonproject_source.encode("utf-8")),
        "non-project candidate is not shorter",
    )
    require(is_english(nonproject["report"]), "non-project report does not use English")

    project_text = results["project_text"]
    require(set(project_text) == PROJECT_SKILLS, "the five required skill cases are incomplete")
    for skill, output in project_text.items():
        artifact = artifact_text(output["artifact"])
        require(artifact.count(PRESERVED_CHINESE) == 1, f"{skill} changed, omitted, or duplicated untouched Chinese text")
        new_text = artifact.replace(PRESERVED_CHINESE, "")
        require(new_text.strip(), f"{skill} produced no new project text")
        require(is_english(new_text), f"{skill} did not follow the English target policy")
        require(is_chinese(output["report"]), f"{skill} report does not use Chinese only")
        if skill == "requirements-to-spec-tickets":
            prompt = output["child_prompt"]
            sentences = re.split(r"(?<=[.!?])\s+", prompt)
            target_rule = any(
                "AGENTS.md" in sentence
                and any(term in sentence.lower() for term in ("target repository", "different target repository", "another repository", "that repository", "destination repository"))
                and "read" in sentence.lower()
                and "follow" in sentence.lower()
                and not re.search(r"\b(?:do not|don't|never)\s+(?:read|follow|use|apply)\b|(?:不要|不得|不应)(?:读取|遵循|使用)", sentence, re.IGNORECASE)
                for sentence in sentences
            )
            source_rule = any(
                "AggregateSkills" in sentence
                and "AGENTS.md" in sentence
                and any(term in sentence.lower() for term in ("source", "installation", "source repository"))
                and bool(re.search(r"\b(?:do not|don't|never)\s+(?:read|follow|use|rely|apply)\b|(?:不要|不得|不应)(?:读取|遵循|使用|依赖)", sentence, re.IGNORECASE))
                for sentence in sentences
            )
            require(target_rule, "child prompt did not direct the child to read and follow the target root rule")
            require(
                any(term in prompt for term in ("English", "英文", "英语"))
                and any(term in prompt.lower() for term in ("project text", "project prose", "项目文本", "项目文字"))
                and any(term in prompt.lower() for term in ("preserve", "保留"))
                and any(term in prompt.lower() for term in ("ask before", "unclear", "不明确", "不清楚")),
                "child prompt did not carry the target language rule",
            )
            require(source_rule, "child prompt did not exclude the source root as language authority")
            require(not has_source_authority_claim(sentences), "child prompt treated the source-root policy as authoritative")
        if skill == "grill-duo-with-docs":
            require(
                output["languages"] == {"target_root": "English", "nested": "Chinese", "conversation": "Chinese"},
                "nested-policy scenario does not conflict with the target root language",
            )

    same_repo = results["same_repo"]
    require(
        same_repo["languages"] == {"target": "English", "skill_source": "English", "conversation": "Chinese"},
        "same-repository scenario does not make the skill source and target repository identical",
    )
    same_repo_artifact = artifact_text(same_repo["artifact"])
    require(same_repo_artifact.count(PRESERVED_CHINESE) == 1, "same-repository case changed or omitted the untouched Chinese passage")
    require(
        is_english(same_repo_artifact.replace(PRESERVED_CHINESE, ""))
        and is_chinese(same_repo["report"]),
        "same-repository case did not follow its shared target-root rule and conversation language",
    )

    ambiguous = results["ambiguous_policy"]
    require(set(ambiguous) == PROJECT_SKILLS, "ambiguity case did not cover all five project-text skills")
    for skill, response in ambiguous.items():
        require(not response["artifact"].strip(), f"{skill} drafted before resolving ambiguous language")
        question = response["question"]
        require(
            asks_language_choice(question),
            f"{skill} did not ask in Chinese before drafting",
        )
    print("Language-policy agent acceptance passed.")


if __name__ == "__main__":
    main()
