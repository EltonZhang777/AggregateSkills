"""Focused behavior contracts retained from the retired prerequisite checks."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def skill_reference(name, filename):
    return (
        ROOT / "skills" / name / "references" / filename
    ).read_text(encoding="utf-8")


def section(text, heading):
    start = text.index(heading) + len(heading)
    end = text.find("\n## ", start)
    if heading.startswith("### "):
        same_level = text.find("\n### ", start)
        if same_level != -1 and (end == -1 or same_level < end):
            end = same_level
    return text[start:] if end == -1 else text[start:end]


class SkillPrerequisiteInvocationTests(unittest.TestCase):
    def test_all_entrypoints_put_the_bounded_invocation_rule_first(self):
        entrypoints = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(10, len(entrypoints))

        for path in entrypoints:
            with self.subTest(skill=path.parent.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("## Dependencies", text)
                dependencies = section(text, "## Dependencies")
                rule = " ".join(dependencies.strip().split("\n\n", 1)[0].split()).lower()

                required_concepts = (
                    "explicitly reaches a call",
                    "directly declared skill prerequisite",
                    "may proceed",
                    "disables implicit invocation",
                    "waives only",
                    "other prerequisite instructions",
                    "confirmation",
                    "authorization",
                    "security",
                    "safety",
                    "does not authorize transitive calls",
                    "new call steps",
                    "explicit prohibition",
                )
                missing = [phrase for phrase in required_concepts if phrase not in rule]
                self.assertEqual([], missing, f"{path}: incomplete or misplaced rule")

    def test_skill_scout_remains_plan_only(self):
        text = skill("skill-scout").lower()
        self.assertIn("return a selection plan to the caller", text)
        self.assertIn("does not invoke selected workflows", text)

    def test_user_only_workflows_keep_invocation_metadata(self):
        for name in ("requirements-to-spec-tickets", "spec-implement-loop"):
            with self.subTest(skill=name):
                frontmatter = skill(name).split("---", 2)[1]
                self.assertIn("disable-model-invocation: true", frontmatter)

    def test_implicit_discovery_remains_disabled_where_configured(self):
        for name in ("requirements-to-spec-tickets", "review-duo", "skill-scout", "spec-implement-loop"):
            with self.subTest(skill=name):
                policy = (ROOT / "skills" / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
                self.assertIn("allow_implicit_invocation: false", policy)
def mentions_concepts(text, *concepts):
    return all(any(term in text for term in alternatives) for alternatives in concepts)


def sentence_with_concepts(text, *concepts):
    return next((sentence for sentence in re.split(r"(?<=[.!?])\s+", text) if mentions_concepts(
        sentence, *concepts,
    )), "")


def independent_work_continuation(text):
    sentence = sentence_with_concepts(
        text, ("independent", "unrelated"), ("phase", "group", "work"),
        ("continue", "continues", "continuing", "proceed", "proceeds", "proceeding",
         "remain eligible", "remain available", "keep running", "running"),
    )
    if re.search(
        r"\b(?:does not|doesn't|did not|didn't|cannot|can't|must not|mustn't|"
        r"may not|will not|won't|would not|wouldn't|should not|shouldn't|"
        r"is not|isn't|are not|aren't|was not|wasn't|were not|weren't|never|unable to)\s+"
        r"(?:(?:be\s+)?(?:able|allowed|permitted|authorized|expected|guaranteed)\s+to\s+)?"
        r"(?:continue|proceed|remain|run)\b",
        sentence,
    ) or re.search(
        r"\b(?:is|are|was|were|will be|may be)\s+"
        r"(?:blocked|prevented|barred|stopped|paused|prohibited|forbidden|unable)\s+"
        r"from\s+(?:continu\w*|proceed\w*|remain\w*|run\w*)\b",
        sentence,
    ):
        return ""
    return sentence


def clauses(text):
    return [clause.strip() for clause in re.split(
        r"\b(?:however|although|though|while|yet|except|unless|rather than)\b"
        r"|\bbut\b(?!\s+(?:only\s+)?(?:with|after|unless|when|if)\s+(?:a\s+)?"
        r"(?:separate|additional|own)(?:\s+user)?\s+approval)"
        r"|\band(?=\s+(?:does not|doesn't|cannot|can't|must not|never)\b)"
        r"|\band(?=\s+(?:commit(?:s)?|push(?:es)?)\b"
        r"(?:(?!\band\b)[^.!?])*\b(?:requir\w*|need\w*)\b"
        r"(?:(?!\band\b)[^.!?])*\b(?:separate|additional)\s+approval\b)"
        r"|\band(?=\s+(?:(?:a|the)\s+)?(?:separate\s+)?user(?:'s)?\s+"
        r"(?:(?:separate|own)\s+)?(?:approval|authorization)\b)"
        r"|\band(?=\s+(?:(?:a|the)\s+)?(?:(?:separate|own)\s+)?"
        r"(?:approval|authorization)\s+(?:from|by)\s+(?:the\s+)?user\b)"
        r"|\band(?=\s+(?:issue creation|comments?|label changes|sub-issue links?|"
        r"pull request actions?|pr creation|merges?)\b[^.!?]*\b(?:is|are)\s+"
        r"(?:separately\s+)?(?:authorized|approved|permitted|allowed)\s+by\s+(?:the\s+)?user\b)"
        r"|\band(?=\s+(?:these|those|they)\s+(?:still\s+)?(?:requir\w*|need\w*)\b"
        r"[^.!?]*\b(?:separate|additional)\s+approval\b)"
        r"|\band(?=\s+(?:(?:the|a)\s+)?(?:user|group\s+b|b\b))|[;.!?]",
        text,
    ) if clause.strip()]


def authorization_grant_clause(text, *concepts):
    parts = clauses(text)
    for index, clause in enumerate(parts):
        match = TASK_AUTHORIZATION_GRANT.search(clause)
        if (
            match
            and not TASK_AUTHORIZATION_DENIAL.search(clause)
            and mentions_concepts(clause[match.end():], *concepts)
            and not (
                index + 1 < len(parts)
                and ANAPHORIC_SEPARATE_APPROVAL.search(parts[index + 1])
            )
        ):
            return clause
    return ""


def permission_clause(text, *concepts):
    for clause in clauses(text):
        clause = re.sub(
            r"\b(?:not|never|without|rather than)\s+under a's (?:approval|authorization)\b",
            "",
            clause,
        )
        if (
            mentions_concepts(clause, *concepts)
            and re.search(
                r"\b(?:may|can|allowed|permitted|authorized|authorizes?|permits?|"
                r"allows?|grants?|covers?)\b",
                clause,
            )
            and not TASK_ACTION_DENIAL.search(clause)
        ):
            return clause
    return ""


def status_sync_grant_clause(text, *concepts):
    for clause in clauses(text):
        direct_scope = STATUS_SYNC_CONDITIONALLY_APPROVED_WRITE.sub("", clause)
        match = STATUS_SYNC_GRANT.search(direct_scope)
        if match and mentions_concepts(direct_scope[match.start():], *concepts):
            return clause
    return ""


AUTO_INSTALL_PROHIBITION = re.compile(
    r"\b(?:do not|does not|don't|never|must not)\s+(?:automatically\s+)?install\b"
)
TASK_AUTHORIZATION_GRANT = re.compile(
    r"\b(?:approval|authorization)\b.*\b"
    r"(?:grant(?:s|ed)?|authoriz(?:e|es|ed)|permit(?:s|ted)?|"
    r"allow(?:s|ed)?|cover(?:s|ed)?|enable(?:s|d)?)\b"
)
TASK_AUTHORIZATION_DENIAL = re.compile(
    r"\b(?:approval|authorization)\s+"
    r"(?:does not|doesn't|cannot|can't|must not|never)\s+"
    r"(?:grant|authorize|permit|allow|cover)\b"
    r"|\b(?:approval|authorization)\s+(?:(?:is\s+)?alone\s+)?(?:is\s+)?"
    r"(?:insufficient|inadequate|not sufficient|not enough)\s+to\s+"
    r"(?:grant|authorize|permit|allow|cover)\b"
)
TASK_ACTION_DENIAL = re.compile(
    r"\b(?:does not|doesn't|cannot|can't|must not|never)\s+"
    r"(?:grant|authorize|permit|allow|cover)\b"
    r"|\b(?:may not|cannot|can't|must not|should not)\s+(?:write|commit|push)\b"
    r"|\b(?:never|isn't|is not|aren't|are not|not)\s+(?:permitted|authorized|allowed)\b"
)
ANAPHORIC_SEPARATE_APPROVAL = re.compile(
    r"\b(?:these|those|they)\s+(?:still\s+)?(?:requir\w*|need\w*)\b"
    r"[^.!?]*\b(?:separate|additional)\s+approval\b"
)
TASK_AUTHORIZATION_LIMIT = re.compile(
    r"\b(?:does not|doesn't|cannot|can't|must not)\s+(?:carry|transfer|extend|apply)\b"
)
STATUS_SYNC_GRANT = re.compile(
    r"\b(?:status-sync authorization|status synchronization|status sync)\s+"
    r"(?:(?:itself|also|may|can|still)\s+)*(?:authoriz(?:es|e)|permit(?:s)?|"
    r"allow(?:s)?|cover(?:s)?|grant(?:s)?|enable(?:s)?|creat(?:e|es)|"
    r"writ(?:e|es)|post(?:s)?|link(?:s)?|label(?:s)?|chang(?:e|es)|updat(?:e|s)|"
    r"merg(?:e|es)|delet(?:e|es)|edit(?:s)?|comment(?:s)?|add(?:s)?|"
    r"remov(?:e|es)|open(?:s)?|clos(?:e|es)|perform(?:s)?|"
    r"execut(?:e|es)|issue(?:s)?)\b"
)
STATUS_SYNC_CONDITIONALLY_APPROVED_WRITE = re.compile(
    r"\b(?:allow(?:s|ed)?|authoriz(?:e|es|ed)|permit(?:s|ted)?|grant(?:s|ed)?|"
    r"cover(?:s|ed)?|enable(?:s|d)?)\s+"
    r"(?:the\s+)?(?:issue creation|create an issue|new issue|comments?|labels?|"
    r"label changes|sub-issue links?|pull request actions?|pr creation|merges?|"
    r"other github writes?)\s*,?\s*(?:but\s+)?(?:only\s+)?"
    r"(?:with|after|unless|when|if)\s+(?:a\s+)?"
    r"(?:separate|additional|own)(?:\s+user)?\s+approval\b"
)
NON_STATUS_WRITES = (
    "issue creation", "create an issue", "new issue", "comment", "label", "sub-issue",
    "pull request", "pr creation", "merge", "other github write",
)


class SkillScoutBehaviorTests(unittest.TestCase):
    def test_general_inventory_and_selected_catalog_flow(self):
        text = skill("skill-scout").lower().replace(chr(96), "")
        general = section(text, "## general-host discovery")
        fallback = " ".join(section(text, "## skillroute local-catalog fallback").split())
        local_reference = skill_reference("skill-scout", "skillroute-local-catalog.md").lower().replace(chr(96), "")
        dependencies = section(local_reference, "## dependencies")
        local = section(local_reference, "## skillroute local-catalog mode")
        explicit = section(text, "### resolve an explicitly named skill")
        report = section(text, "## report")
        self.assertLess(text.index("## general-host discovery"), text.index("## skillroute local-catalog fallback"))
        self.assertIn("only after general-host discovery cannot retrieve a result", fallback)
        self.assertIn("only when the user selects the local-catalog mode", fallback)
        self.assertIn("skillroute-local-catalog.md", fallback)
        self.assertNotIn("## skillroute local-catalog mode", text)
        self.assertIn("start with an installed-skill inventory exposed by the host or supplied by the caller", general)
        self.assertIn("treat an inventory as complete only when its source identifies it as covering all installed skills", general)
        self.assertIn("a partial inventory never proves a skill is absent", general)
        self.assertIn("request a complete inventory or the user's choice to use skillroute local-catalog mode", general)
        self.assertIn("return unavailable", general)
        self.assertIn("if any dependency is missing, report all missing dependencies", dependencies)
        self.assertIn("skillroute cli", dependencies)
        self.assertIn("optional local-catalog mode", local)
        self.assertIn("reads the local catalog only", local)
        self.assertIn("does not use a network backend", local)
        self.assertIn("run the cli and backend checks before routing", local)
        self.assertIn("if the cli, local backend, or catalog is unavailable, return unavailable", local)
        self.assertIn("do not present the result as evidence that a skill is absent", local)
        self.assertIn("temporary resolver or backend errors", local)
        self.assertIn("return an unresolved prerequisite result", local)
        self.assertIn("exact failed check and recovery condition", local)
        self.assertIn("and stop", local)
        self.assertIn("do not fall back to another discovery source", local)
        self.assertIn("if a complete inventory does not contain it, return missing prerequisite", explicit)
        self.assertIn("if the inventory is partial, return unavailable", explicit)
        self.assertIn("unresolved prerequisite", report)
        self.assertIn("unavailable", report)

    def test_ambiguous_explicit_name_requires_source_choice(self):
        text = skill("skill-scout").lower().replace(chr(96), "")
        explicit = section(text, "### resolve an explicitly named skill")
        self.assertIn("treat a supplied source as part of the identity", explicit)
        self.assertIn("a same-name entry from another source is not a match", explicit)
        self.assertIn("if multiple entries match, return user decision required", explicit)
        self.assertIn("show each candidate and its declared or undeclared source", explicit)
        self.assertIn("do not choose by inventory order or rank", explicit)


class PrAndMergeBehaviorTests(unittest.TestCase):
    def test_multi_pr_requests_route_before_discovery_and_preserve_single_pr_flow(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        routing_heading = "## multi-pr request routing"
        self.assertIn(routing_heading, text)
        self.assertLess(text.index(routing_heading), text.index("## dependencies"))

        routing = section(text, routing_heading)
        self.assertIn("before discovery", routing)
        self.assertIn("references/multi-pr-batch.md", routing)
        self.assertIn("exactly one operation is resolved", routing)
        self.assertIn("no other outcome needs a batch report", routing)
        self.assertNotIn("eligible operation", routing)
        self.assertIn("single-pr flow", routing)
        self.assertIn("## resolve the source and target", text)

    def test_multi_pr_reference_covers_scope_plan_ordering_and_refresh_gates(self):
        reference_path = ROOT / "skills" / "pr-and-merge" / "references" / "multi-pr-batch.md"
        self.assertTrue(reference_path.is_file(), "the routed multi-PR reference must exist")
        text = skill_reference("pr-and-merge", "multi-pr-batch.md").lower().replace(chr(96), "")

        selectors = section(text, "## discover and deduplicate selectors")
        self.assertIn("inclusive pr ranges", selectors)
        self.assertIn("selector aliases", selectors)
        self.assertIn("same exact pr", selectors)
        self.assertIn("different bases stay separate operations", selectors)
        self.assertIn("explicit stack relationship", selectors)

        scope = section(text, "## report the complete scope")
        self.assertIn("one row per deduplicated operation", scope)
        self.assertIn("unmatched", scope)
        self.assertIn("ambiguous", scope)
        self.assertIn("missing base", scope)
        self.assertIn("draft", scope)
        self.assertIn("already-blocked prs", scope)
        self.assertIn("prospective pr operation", scope)
        self.assertIn("report-only", scope)
        self.assertIn("initial scope report", scope)
        self.assertIn("no planned writes", scope)
        self.assertIn("final outcome summary", scope)
        self.assertIn("verified exact merged match", scope)
        self.assertIn("closed unmerged pr remains report-only", scope)

        plan = section(text, "## present the exact plan and authorize the batch")
        for detail in ("source head sha", "dependencies", "planned pushes", "blockers"):
            self.assertIn(detail, plan)
        self.assertIn("one explicit authorization", plan)
        self.assertIn("no writes", plan)
        self.assertIn("head and base names and oids", plan)
        self.assertIn("satisfies", plan)
        self.assertIn("per-pr merge approval", plan)
        self.assertIn("base oid advancement alone does not revoke batch authorization", plan)
        self.assertIn("approved source head is unchanged", plan)
        self.assertIn("no new conflict-resolution work is required", plan)

        execution = section(text, "## execute the approved batch")
        self.assertIn("then merge them in that same order", execution)
        self.assertIn("do not ask again for that unchanged merge", execution)
        self.assertIn("do not ask again solely because the base oid advanced", execution)
        self.assertIn("live per-pr merge checks", execution)

        batch = section(skill("pr-and-merge").lower(), "## process a batch")
        self.assertNotIn("present a separate approval snapshot for each pr", batch)
        self.assertNotIn("finish preparing every eligible pr before merging any", batch)
        self.assertIn("never stash or clean a supplied worktree", batch)
        self.assertIn("stage its conflict-resolution files only after explicit approval of the exact diff", batch)

        source_resolution = section(skill("pr-and-merge").lower(), "## resolve the source and target")
        self.assertIn("already dirty at this initial source-resolution check", source_resolution)
        self.assertIn("if conflict resolution later makes the worktree dirty", source_resolution)

        preparation = section(skill("pr-and-merge").lower(), "## reuse or prepare the pr")
        self.assertIn("for a single-pr request", preparation)
        self.assertIn("for a batch request", preparation)
        self.assertIn("do not pause again for a merge already listed in the authorized batch", preparation)

        ordering = section(text, "## order dependencies and conflict candidates")
        self.assertIn("read every selected diff before ordering", ordering)
        self.assertIn("hard constraints", ordering)
        self.assertIn("conflict-free", ordering)
        self.assertIn("only to break ties within either group", ordering)
        self.assertIn("complete order cannot bypass this preference", ordering)
        self.assertIn("same base", ordering)

        conflicts = section(text, "## gate conflict resolution")
        self.assertIn(".wt", conflicts)
        self.assertIn("dirty worktree", conflicts)
        self.assertIn("exact repository", conflicts)
        self.assertIn("exact source branch", conflicts)
        self.assertIn("owner/repo", conflicts)
        self.assertIn("git rev-parse --show-toplevel", conflicts)
        self.assertIn("git remote -v", conflicts)
        self.assertIn("git status --porcelain=v1 --untracked-files=all", conflicts)
        self.assertIn("never stage, commit, stash, discard, or push automatically", conflicts)
        self.assertIn("complete unstaged conflict-resolution diff", conflicts)
        self.assertIn("before staging or any other write", conflicts)
        self.assertIn("stage only the approved files", conflicts)
        self.assertIn("staged diff differs from the approved diff", conflicts)

        refresh = section(text, "## refresh after source or base changes")
        self.assertIn("head and base oids", refresh)
        self.assertIn("reviews", refresh)
        self.assertIn("checks", refresh)
        self.assertIn("base oid advancement alone does not revoke batch authorization", refresh)
        self.assertIn("commits between them", refresh)
        self.assertIn("current diff against the approved source snapshot", refresh)
        self.assertIn("unrelated operations continue", refresh)
        self.assertIn("../skill.md#process-a-batch", text)
        self.assertIn("../skill.md#merge-after-approval", text)

        merge = skill_reference("pr-and-merge", "merge-after-approval.md").lower()
        self.assertIn("multi-pr-batch.md#refresh-after-source-or-base-changes", merge)
        self.assertIn("retain the batch-plan order through merging", merge)
        self.assertIn("conflict-free entries before conflict candidates", merge)
        self.assertIn("only to break ties within either group", merge)
        self.assertIn("before staging or any other write", merge)
        self.assertIn("stage only the approved files", merge)
        self.assertIn("if it differs from the approved diff", merge)

    def test_pr_text_gate_follows_push_classification_and_precedes_writes(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        reuse = section(text, "## reuse or prepare the pr")
        prepare_heading = "### prepare or reuse pr text"
        preflight_heading = "### pr-text preflight before the first source push"
        prepare_start = reuse.index(prepare_heading)
        preflight_start = reuse.index(preflight_heading)
        first_fetch = reuse.index("git fetch remote head_branch")
        second_fetch = reuse.index("git fetch remote head_branch", first_fetch + 1)
        third_fetch = reuse.index("git fetch remote head_branch", second_fetch + 1)
        branch_check = reuse.index("git branch --show-current", preflight_start)
        head_check = reuse.index("git rev-parse head", preflight_start)
        push = reuse.index("git push remote head:refs/heads/head_branch")
        create_pr = reuse.index("gh pr create")
        edit_pr = reuse.index("gh pr edit")

        self.assertLess(first_fetch, prepare_start)
        self.assertLess(prepare_start, preflight_start)
        self.assertLess(preflight_start, branch_check)
        self.assertLess(preflight_start, head_check)
        self.assertLess(branch_check, second_fetch)
        self.assertLess(head_check, second_fetch)
        self.assertLess(second_fetch, push)
        self.assertLess(push, third_fetch)
        self.assertLess(third_fetch, create_pr)
        self.assertLess(third_fetch, edit_pr)
        self.assertLess(prepare_start, create_pr)
        self.assertLess(prepare_start, edit_pr)

    def test_github_scope_and_subskill_steps_remain_explicit(self):
        text = skill("pr-and-merge").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        reuse = section(text, "## reuse or prepare the pr")
        merge_route = section(text, "## merge after approval")
        merge = skill_reference("pr-and-merge", "merge-after-approval.md").lower().replace(chr(96), "")
        self.assertIn("it handles github only", activation)
        drafting_rule = sentence_with_concepts(
            reuse, ("before drafting",), ("materially updating",), ("pr title",), ("body",),
            ("language rule",), ("root agents.md",), ("conventional-git-messages",),
        )
        self.assertTrue(drafting_rule)
        self.assertRegex(drafting_rule, r"\b(?:pass|read|follow|apply|use|provide)\b")
        self.assertNotRegex(
            drafting_rule,
            r"\b(?:do not|don't|does not|doesn't|never|must not|mustn't|"
            r"may not|will not|won't|would not|wouldn't|should not|shouldn't|"
            r"cannot|can't|is not|isn't|are not|aren't)\s+"
            r"(?:pass|read|follow|apply|use|provide)\b",
        )
        self.assertIn("delegate the title and body or only the necessary correction to /conventional-git-messages", reuse)
        self.assertIn("only when the user requests a merge", merge_route)
        self.assertIn("explicitly approves that exact pr", merge_route)
        self.assertIn("references/merge-after-approval.md", merge_route)
        self.assertIn("merge each pr only after the user explicitly approves that exact pr", merge)
        self.assertIn("immediately before each merge, recheck that pr's head and base", merge)
        self.assertIn("when an approved merge encounters a conflict, use /resolving-merge-conflicts", merge)


class PruneWorktreesBehaviorTests(unittest.TestCase):
    def test_unavailable_evidence_never_produces_safe_to_clean(self):
        text = skill("prune-worktrees-and-branches").lower().replace("*", "")
        self.assertIn("if a required github check is unavailable, do not mark the affected branch safe to clean", text)
        self.assertIn("unknown, failed, incomplete, or out-of-date evidence must never produce safe to clean", text)

    def test_cleanup_references_follow_their_separate_approval_gates(self):
        text = skill("prune-worktrees-and-branches").lower().replace("*", "")
        local_gate = section(text, "## apply approved local cleanup")
        remote_gate = section(text, "## apply separately approved remote cleanup")
        local = skill_reference("prune-worktrees-and-branches", "approved-local-cleanup.md").lower().replace("*", "").replace(chr(96), "")
        remote = skill_reference("prune-worktrees-and-branches", "approved-remote-branch-deletion.md").lower().replace("*", "").replace(chr(96), "")
        self.assertIn("ask for explicit approval of that local set", local_gate)
        self.assertIn("after approval of the exact local cleanup set", local_gate)
        self.assertIn("references/approved-local-cleanup.md", local_gate)
        self.assertIn("require an explicit pass for every item", remote_gate)
        self.assertIn("ask for explicit remote-deletion approval in a separate question", remote_gate)
        self.assertIn("after approval for exactly the reviewed remote, branch names, and oids", remote_gate)
        self.assertIn("references/approved-remote-branch-deletion.md", remote_gate)
        self.assertIn("git worktree remove <path>", local)
        self.assertIn("git branch -d -- <branch>", local)
        self.assertIn("git push <remote> --delete refs/heads/<branch>", remote)
        self.assertIn("never use --force", remote)


class GrillDuoBehaviorTests(unittest.TestCase):
    def test_summary_fields_and_reviewer_fallback_remain(self):
        text = skill("grill-duo").lower()
        self.assertIn("summarize the goal, confirmed decisions, constraints, and material risks", text)
        roles = section(text, "## roles and continuity")
        self.assertIn("only reviewer unavailability uses solo mode", roles)


class GrillDuoWithDocsBehaviorTests(unittest.TestCase):
    def test_delegates_protocol_and_keeps_host_as_document_writer(self):
        text = skill("grill-duo-with-docs").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        self.assertIn("use /grill-duo for the grilling protocol", activation)
        self.assertIn("use /domain-modeling for glossary and decision discipline", activation)
        self.assertIn("do not copy either skill's body into this entrypoint", activation)


class SkillRoutePrerequisiteTests(unittest.TestCase):
    def test_cli_identity_and_callability_are_clear_across_affected_skills(self):
        for name in (
            "grill-duo",
            "grill-duo-with-docs",
            "pr-and-merge",
            "requirements-to-spec-tickets",
            "review-duo",
        ):
            with self.subTest(skill=name):
                dependencies = section(
                    skill(name).lower().replace(chr(96), ""), "## dependencies"
                )
                self.assertIn("skillroute cli executable (skillroute)", dependencies)
                self.assertIn("before starting the workflow", dependencies)
                self.assertIn("callable", dependencies)
                self.assertIn("https://github.com/erichare/skillroute", dependencies)


class RequirementsToSpecTicketsBehaviorTests(unittest.TestCase):
    def test_child_prompt_template_is_referenced_and_contains_the_handoff_contract(self):
        parent = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        filename = "child-session-initial-prompt.md"
        reference = f"references/{filename}"
        self.assertIn(reference, parent)

        template = skill_reference("requirements-to-spec-tickets", filename).lower().replace(chr(96), "")
        fill_instructions = section(template, "## fill instructions")
        copy_ready = template[template.index("# copy-ready prompt (below):"):]
        group = section(template, "## approved group")
        startup = section(template, "## first response and grilling gate")
        workflow = section(template, "## workflow gates")
        linking = section(template, "### native ticket linking")
        boundaries = section(template, "## boundaries and completion")

        for placeholder in (
            "[group title]", "[approved outcome]", "[approved scope]", "[non-goals]",
            "[acceptance intent]", "[target repository]", "[workspace path and branch]",
            "[required dependencies]", "[known group dependencies]",
            "[target repository root agents.md language rule]",
            "[shared workspace and write-authorization rules]",
        ):
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, group)

        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("placeholder",), ("fill", "replace"), ("before",), ("handoff", "start"),
        ))
        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("confirmed information", "confirmed facts"), ("do not", "never"), ("invent",),
        ))
        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("sibling requirements",), ("exclude", "omit", "leave out"),
        ))
        self.assertTrue(sentence_with_concepts(
            fill_instructions, ("unrelated parent history",), ("exclude", "omit", "leave out"),
        ))
        self.assertNotIn("example", copy_ready)

        self.assertTrue(sentence_with_concepts(
            startup, ("first response",), ("restate",), ("outcome",), ("scope",), ("non-goals",),
            ("workflow constraints",),
        ))
        self.assertTrue(sentence_with_concepts(
            startup, ("complete-grouping approval",), ("already",), ("authorizes",),
            ("workflow",), ("do not", "don't", "never"), ("opt-in",),
        ))
        self.assertTrue(sentence_with_concepts(
            startup, ("grill-duo-with-docs",), ("answerable frontier",), ("wait",), ("user",),
        ))
        self.assertTrue(sentence_with_concepts(
            startup, ("no answerable questions", "frontier is empty"), ("shared-understanding summary",),
            ("wait",), ("confirmation",),
        ))

        phases = ("/grill-duo-with-docs", "/to-spec", "/to-tickets")
        for phase in phases:
            self.assertIn(phase, workflow)
        self.assertLess(workflow.index(phases[0]), workflow.index(phases[1]))
        self.assertLess(workflow.index(phases[1]), workflow.index(phases[2]))
        self.assertTrue(sentence_with_concepts(
            workflow, ("re-read", "reread"), ("source",), ("each phase",), ("before",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("phase source",), ("unavailable",), ("report",), ("pause",), ("phase",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("phase source",), ("independent",), ("eligible",), ("in-scope work",),
            ("continue",), ("phase order",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("global prerequisite",), ("missing",), ("report",), ("all",),
            ("dependencies",), ("tell the user",), ("install them",), ("stop",),
            ("entire workflow",), ("automatically",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("grill-duo-with-docs",), ("confirmation",),
            ("shared project-document changes",), ("before",),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("to-spec",), ("seam",), ("confirmation", "gate"),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("to-tickets",), ("ticket-granularity", "granularity"),
            ("blocking-edge", "blocking edge"), ("publication",), ("gate", "confirmation"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("after all planned tickets exist",), ("publication gates",), ("pass",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("required permissions are unavailable",), ("report the blocker",), ("stop",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("before each write", "before each link"), ("ticket exists",),
            ("current parent", "parent endpoint"), ("fully paginate",), ("spec",), ("sub-issues",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("already complete", "already linked"), ("both reads", "both endpoints"),
            ("same spec",), ("skip",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("404",), ("ticket exists",), ("spec",), ("sub-issues read succeeds",),
            ("must not contain", "does not contain"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("different parent",), ("disagree", "cannot establish"), ("pause",),
            ("never reparent",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("failed or ambiguous",), ("re-read", "reread"), ("both relationships",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("clearly transient",), ("three total", "at most three"),
            ("write attempts",), ("per link",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("record", "count"), ("attempt",), ("before each write", "before every retry"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("preserve",), ("ticket and spec issue titles",), ("bodies",), ("labels",),
            ("states",), ("blocker edges", "blocking edges"), ("record",),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("before linking, record",), ("after linking, verify",),
            ("ticket and spec issue titles",), ("bodies",), ("labels",), ("states",),
            ("blocker edges", "blocking edges"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("verify",), ("native parent relationship",),
            ("re-read", "reread"), ("spec sub-issues list", "spec's sub-issues list"),
            ("paginate", "paginating"),
        ))
        self.assertTrue(sentence_with_concepts(
            linking, ("report links",), ("succeeded",), ("remain pending",),
        ))
        language_rule = sentence_with_concepts(
            workflow, ("target repository",), ("root agents.md",), ("language rule",), ("pass",),
        )
        self.assertTrue(language_rule)
        for phase in (*phases, "/conventional-git-messages"):
            self.assertIn(phase, language_rule)
        self.assertTrue(sentence_with_concepts(
            workflow, ("shared workspace",), ("write-authorization rules", "write authorization rules"),
            ("preserve", "follow", "carry"),
        ))
        self.assertTrue(sentence_with_concepts(
            workflow, ("conventional-git-messages",), ("re-read", "reread"), ("original",), ("before",),
        ))

        self.assertTrue(sentence_with_concepts(
            boundaries, ("user-facing questions",), ("must not", "do not", "never"),
            ("answer",), ("user",),
        ))
        self.assertTrue(sentence_with_concepts(
            boundaries, ("parent",), ("readiness",), ("handoff",), ("retry",), ("resumption",),
        ))
        self.assertTrue(sentence_with_concepts(
            boundaries, ("prompt", "child-session identifier"), ("alone",), ("readiness",),
            ("does not establish", "not evidence", "does not prove"),
        ))
        self.assertTrue(sentence_with_concepts(
            boundaries, ("completion report",), ("actual status",), ("completed phases",),
            ("artifacts", "outputs"), ("blockers",),
        ))

    def test_complete_group_approval_starts_documentation_phase(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        grouping = section(text, "## 2. turn the request into groups")
        protocol = section(text, "## 4. child-session protocol")
        git = section(text, "## 5. task branches and git publication")
        documents = section(text, "## 6. shared workspace and document writes")
        self.assertTrue(sentence_with_concepts(
            grouping, ("complete", "entire", "whole"), ("grouping", "groups"),
            ("approval", "approved"), ("wait", "pause"),
        ))
        self.assertTrue(sentence_with_concepts(
            grouping, ("approval",), ("group",), ("start", "begin"), ("grill-duo-with-docs",),
        ))
        self.assertTrue(sentence_with_concepts(
            grouping, ("group", "grouping"), ("no", "without", "not"), ("opt-in", "opt in"),
        ))
        self.assertTrue(sentence_with_concepts(
            protocol, ("group",), ("grill-duo-with-docs",), ("invoke", "run"),
        ))
        self.assertTrue(sentence_with_concepts(
            protocol, ("frontier",), ("empty", "no answerable questions"),
            ("shared-understanding", "summary"), ("wait", "pause"), ("confirmation", "confirm"),
        ))
        sequence = sentence_with_concepts(
            protocol, ("grill-duo-with-docs",), ("to-spec",), ("to-tickets",),
            ("first", "before", "prior"), ("then", "next", "order"),
        )
        self.assertTrue(sequence)
        self.assertLess(sequence.index("grill-duo-with-docs"), sequence.index("to-spec"))
        self.assertLess(sequence.index("to-spec"), sequence.index("to-tickets"))
        self.assertTrue(sentence_with_concepts(git, ("approval", "authorize"), ("group",), ("commit",)))
        self.assertTrue(sentence_with_concepts(documents, ("user-confirmed",), ("project documents",)))

    def test_phase_sources_and_global_prerequisites_have_distinct_failure_scopes(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        dependencies = section(text, "## dependencies")
        protocol = section(text, "## 4. child-session protocol")
        phase_rules = protocol.split("the first response must", 1)[0]

        self.assertTrue(mentions_concepts(dependencies, ("skill",), ("tool",)))
        self.assertTrue(sentence_with_concepts(
            dependencies, ("missing",), ("report",), ("stop", "halt"),
        ))
        no_auto_install = sentence_with_concepts(
            dependencies, ("install",), ("not", "never", "without"), ("automatic", "automatically"),
        )
        self.assertTrue(no_auto_install)
        self.assertRegex(no_auto_install, AUTO_INSTALL_PROHIBITION)
        self.assertTrue(sentence_with_concepts(
            phase_rules, ("source",), ("phase",), ("pause", "hold"),
        ))
        self.assertTrue(independent_work_continuation(phase_rules))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase and also pauses every independent eligible phase."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase and the independent eligible phase is not allowed to continue."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase, but the unrelated eligible phase will not proceed."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase, but the unrelated eligible phase is blocked from continuing."
        ))
        self.assertFalse(independent_work_continuation(
            "A missing source pauses its phase, but the unrelated eligible phase is unable to continue."
        ))
        self.assertTrue(sentence_with_concepts(
            phase_rules, ("source",), ("resume", "resuming"), ("re-read", "reread", "check again"),
        ))
        global_rule = sentence_with_concepts(
            phase_rules, ("global", "prerequisite"), ("stop", "halt"), ("install",),
            ("not", "never", "without"),
        )
        self.assertTrue(global_rule)
        self.assertRegex(global_rule, AUTO_INSTALL_PROHIBITION)

        manual = (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md").read_text(encoding="utf-8").lower()
        phase_scenario = section(manual, "## phase-scoped source failure")
        global_scenario = section(manual, "## missing global dependencies")
        self.assertTrue(sentence_with_concepts(
            phase_scenario, ("source",), ("phase",), ("pause", "hold"),
        ))
        self.assertTrue(independent_work_continuation(phase_scenario))
        self.assertTrue(sentence_with_concepts(
            phase_scenario, ("source",), ("resume", "resuming"), ("re-read", "reread", "check again"),
        ))
        phase_install_rule = sentence_with_concepts(
            phase_scenario, ("install",), ("automatic", "automatically"), ("not", "never", "without"),
        )
        self.assertTrue(phase_install_rule)
        self.assertRegex(phase_install_rule, AUTO_INSTALL_PROHIBITION)
        self.assertTrue(sentence_with_concepts(
            global_scenario, ("skill",), ("tool",), ("preflight",),
        ))
        global_install_rule = sentence_with_concepts(
            global_scenario, ("report", "identify"), ("stop", "halt"), ("install",),
            ("not", "never", "without"), ("automatic", "automatically"),
        )
        self.assertTrue(global_install_rule)
        self.assertRegex(global_install_rule, AUTO_INSTALL_PROHIBITION)

    def test_task_publication_authorization_is_scoped_and_preserves_other_gates(self):
        text = skill("requirements-to-spec-tickets").lower().replace(chr(96), "")
        protocol = section(text, "## 4. child-session protocol")
        git = section(text, "## 5. task branches and git publication")
        target_policy = section(text, "## 3. create interactive child sessions")

        self.assertTrue(sentence_with_concepts(
            protocol, ("missing", "unavailable"), ("dependency", "prerequisite"),
            ("install",), ("stop", "halt"),
        ))
        self.assertTrue(sentence_with_concepts(
            target_policy, ("normative", "policy"), ("root",), ("agents.md",),
            ("repository",), ("receiving", "target"),
        ))
        self.assertTrue(sentence_with_concepts(
            target_policy, ("source", "installation"), ("agents.md",), ("substitute", "replace"),
        ))

        decision = (
            ROOT / "docs" / "adr" / "0003-task-scoped-write-authorization.md"
        ).read_text(encoding="utf-8").lower()
        self.assertTrue(sentence_with_concepts(
            decision, ("status",), ("root",), ("repository",), ("ticket",), ("checkpoint",),
        ))
        self.assertTrue(sentence_with_concepts(
            decision, ("every other",), ("git",), ("github",), ("write",),
            ("existing",), ("approval gate",),
        ))
        self.assertTrue(permission_clause(
            "Existing group authorization permits force-pushes to other branches.".lower(),
            ("existing",), ("group",), ("authorization",), ("force-push", "force push"),
            ("other branch",),
        ))
        self.assertFalse(permission_clause(
            "Force-pushes require separate approval, but a user may separately authorize them.".lower(),
            ("existing", "current"), ("group",), ("authorization",), ("force-push", "force push"),
            ("other branch",),
        ))

        allowed = authorization_grant_clause(
            git, ("group",), ("commit",), ("push",), ("branch",),
            ("ordinary", "normal", "non-force", "routine"),
            ("initial", "first"), ("remote ref", "remote branch"),
        )
        self.assertTrue(allowed)
        self.assertTrue(mentions_concepts(
            allowed, ("ordinary", "normal", "non-force", "routine"), ("initial", "first"),
            ("remote ref", "remote branch"),
        ))
        scope = sentence_with_concepts(
            git, ("authorization",), ("limited", "only", "restricted", "confined"),
            ("group",), ("branch",), ("unrelated", "other groups"), ("task",),
        )
        self.assertTrue(scope)
        self.assertTrue(mentions_concepts(
            scope, ("unrelated", "other groups"), ("task",),
        ))
        self.assertRegex(scope, TASK_AUTHORIZATION_LIMIT)

        denied = sentence_with_concepts(
            git, ("force-push", "force push"), ("remote-ref", "remote ref", "remote reference"),
            ("delete", "deletion", "remove"), ("other branch", "different branch"), ("pull request", "pull-request"),
            ("issue",), ("status",), ("sub-issue", "sub issue"), ("github",), ("write",),
            ("separate approval",), ("retain", "require", "need", "necessary", "must"),
        )
        self.assertTrue(denied)
        self.assertRegex(
            denied,
            (
                r"\b(?:retain(?:s)?|require(?:s)?|need(?:s)?|must have|must retain)\b"
                r".*\b(?:separate|additional|own)\s+approval\b"
            ),
        )
        self.assertFalse(permission_clause(
            denied, ("current", "same", "approved", "existing"),
            ("group", "task", "branch"), ("authorization", "approval"),
            ("force-push", "force push", "remote-ref deletion", "remote ref deletion",
             "other branch", "pull request", "issue creation", "status change", "comment",
             "label", "sub-issue", "github write"),
        ))

    def test_authorization_contract_accepts_paraphrases_and_rejects_broadening(self):
        grant = (
            "Full-group approval permits routine commits and normal pushes on the group's "
            "dedicated task branch, including the initial remote ref."
        )
        self.assertTrue(sentence_with_concepts(
            grant, ("approval", "authorization"), ("grant", "authorize", "permit", "allow"),
            ("group",), ("commit",), ("push",), ("task branch", "dedicated branch"),
            ("ordinary", "normal", "routine"), ("initial", "first"), ("remote ref", "remote branch"),
        ))
        self.assertTrue(authorization_grant_clause(
            grant, ("group",), ("commit",), ("push",), ("task branch", "dedicated branch"),
            ("ordinary", "normal", "routine"), ("initial", "first"), ("remote ref", "remote branch"),
        ))

        combined_boundary = (
            "Group approval permits routine commits and ordinary pushes on the dedicated task branch, "
            "but does not permit pushes to another branch."
        )
        self.assertTrue(authorization_grant_clause(
            combined_boundary, ("routine",), ("commit",), ("push",), ("task branch",),
        ))
        self.assertTrue(authorization_grant_clause(
            "Group approval permits routine commits and ordinary pushes on its task branch, "
            "and force-pushes require separate approval.",
            ("routine",), ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes review, while commits and pushes on the task branch need separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes review, and commits and pushes on the task branch require separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes document work, with commits and pushes on its task branch "
            "requiring separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Group approval authorizes document work, with routine commits and pushes on its task branch, "
            "and these require separate approval.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Approval is insufficient to authorize focused group commits and normal pushes on the dedicated task branch, "
            "including the initial remote ref.",
            ("commit",), ("push",), ("task branch",), ("initial",), ("remote ref",),
        ))
        self.assertFalse(authorization_grant_clause(
            "Approval alone is insufficient to authorize focused group commits and normal pushes on the dedicated task branch.",
            ("commit",), ("push",), ("task branch",),
        ))
        self.assertTrue(authorization_grant_clause(
            "After group B receives its own approval, that approval permits B to write files, commit, "
            "and push only on B's dedicated task branch.".lower(),
            ("write",), ("commit",), ("push",),
            ("only",), ("dedicated task branch",),
        ))
        paraphrased_denial = (
            "Before separate approval, group B is never authorized to write files, commit, or push "
            "under A's approval."
        ).lower()
        self.assertTrue(sentence_with_concepts(
            paraphrased_denial, ("group b",), ("before",), ("separate approval",),
            ("write",), ("commit",), ("push",), ("under a's approval",),
        ))
        self.assertRegex(paraphrased_denial, TASK_ACTION_DENIAL)

        removed_branch = "Group approval permits routine commits and normal pushes, including the initial push."
        self.assertFalse(sentence_with_concepts(
            removed_branch, ("approval",), ("commit",), ("push",), ("task branch", "dedicated branch"),
        ))

        limited = (
            "Authorization is confined to this group's task branch and cannot transfer to other groups "
            "or later tasks."
        ).lower()
        self.assertTrue(sentence_with_concepts(
            limited, ("authorization",), ("limited", "restricted", "confined"),
            ("group",), ("branch",), ("other groups", "unrelated"), ("task",),
        ))
        self.assertRegex(limited, TASK_AUTHORIZATION_LIMIT)

        broadened = "Authorization extends to every group, task, and branch.".lower()
        self.assertFalse(sentence_with_concepts(
            broadened, ("limited", "restricted", "confined"), ("other groups", "unrelated"),
            ("task",),
        ))
        self.assertNotRegex(broadened, TASK_AUTHORIZATION_LIMIT)

    def test_manual_multiple_groups_covers_authorization_non_carryover(self):
        manual = (ROOT / "tests" / "manual" / "requirements-to-spec-tickets.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## multiple groups in a shared checkout")
        self.assertTrue(sentence_with_concepts(
            scenario, ("group a",), ("only",), ("a's task branch", "group a's branch"),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("group b",), ("only",), ("b's dedicated task branch", "group b's branch"),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("group b",), ("unapproved", "not approved", "without approval"),
        ))
        b_grant = authorization_grant_clause(
            scenario, ("write",), ("commit",), ("push",),
            ("b's dedicated task branch", "group b's branch"),
        )
        self.assertTrue(b_grant)
        self.assertTrue(mentions_concepts(
            b_grant, ("group b", "b's"), ("separate approval", "own approval"), ("only",),
        ))
        no_carry_rule = sentence_with_concepts(
            scenario, ("group b",), ("before", "until"), ("separate approval",),
            ("cannot", "can't", "must not", "may not", "prohibited", "never authorized",
             "isn't authorized", "is not authorized", "not permitted"),
            ("write", "writing", "files"),
            ("commit",), ("push",), ("under a's approval", "under a's authorization"),
            ("separate approval", "own approval"),
        )
        self.assertTrue(no_carry_rule)
        self.assertRegex(
            no_carry_rule,
            (
                r"\b(?:cannot|can't|must not|may not)\s+(?:write|writing|commit|push)\b"
                r"|\b(?:does not|doesn't|cannot|can't|must not)\s+(?:authorize|permit|allow|cover)\b"
                r"|\b(?:never|isn't|is not|aren't|are not|not)\s+"
                r"(?:authorized|permitted|allowed)\b"
            ),
        )
        self.assertNotRegex(
            no_carry_rule,
            r"\b(?:cannot|can't)\s+be\s+(?:blocked|prevented|stopped|prohibited|barred)\b",
        )
        self.assertFalse(permission_clause(
            scenario, ("group b",), ("under a's approval", "under a's authorization"),
            ("write", "writing", "commit", "push"),
        ))
        self.assertFalse(permission_clause(
            "Group B may write under its own approval, not under A's approval.".lower(),
            ("group b",), ("under a's approval",), ("write",),
        ))
        self.assertFalse(permission_clause(
            "Group B may not write under A's approval.".lower(),
            ("group b",), ("under a's approval",), ("write",),
        ))
        for denial in (
            "Group B is never authorized to write under A's approval.",
            "Group B isn't authorized to write under A's approval.",
        ):
            self.assertFalse(permission_clause(
                denial.lower(), ("group b",), ("under a's approval",), ("write",),
            ))
        self.assertTrue(permission_clause(
            "Group B may write under A's approval.".lower(),
            ("group b",), ("under a's approval",), ("write",),
        ))


class SpecImplementLoopBehaviorTests(unittest.TestCase):
    def test_target_language_rule_is_passed_to_documentation_skills(self):
        text = skill("spec-implement-loop").replace(chr(96), "")
        self.assertIn("Pass the target rule to /grill-duo-with-docs", text)
        self.assertNotIn("/grill-with-docs", text)

    def test_multi_root_reference_is_selected_only_after_read_only_deduplication(self):
        intake = section(skill("spec-implement-loop").lower(), "## intake and frontier")

        self.assertIn("after read-only intake and deduplication", intake)
        self.assertIn("if more than one distinct root remains", intake)
        self.assertIn(
            "follow the [multi-root coordination reference](references/multi-root-coordination.md)",
            intake,
        )
        self.assertIn("with one root, continue the single-root workflow below", intake)
        self.assertIn("this skill remains authoritative for procedures shared by both paths", intake)
        self.assertIn("prioritizing dependency order and then root order or issue number", intake)

    def test_multi_root_scope_is_mapped_and_validated_before_selection(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower()
        listing = section(reference, "## 1. list and validate roots")
        selection = section(reference, "## 2. select and freeze the batch")

        self.assertIn(
            "proposed root-to-ticket mapping with root entries in issue-number order",
            listing,
        )
        self.assertIn(
            "within each root, list explicitly referenced child tickets in issue-number order",
            listing,
        )
        self.assertIn("show blocker edges separately", listing)
        steps = [
            listing.index("detect child tickets listed under multiple roots"),
            listing.index("do not link an overlapping ticket until ownership or decomposition is resolved"),
            listing.index("mark each ticket described as a child task"),
            listing.index("ask once whether to link all missing cases in the validated roots"),
            listing.index("create only approved links"),
            listing.index("verify the resulting native links"),
            listing.index("return to the complete root-to-ticket listing"),
        ]
        self.assertEqual(steps, sorted(steps))
        self.assertIn("choose one owning root or decompose the ticket", listing)
        self.assertIn("pause only affected roots", listing)
        self.assertIn("unaffected roots may continue under their existing authorizations", listing)
        self.assertIn("if a link points to another root", listing)
        self.assertIn("ask for explicit approval for that exact relationship change", listing)
        self.assertIn("approval for missing links does not authorize moving or removing an existing link", listing)
        self.assertIn("if supported github tooling cannot apply and verify the exact change", listing)
        self.assertIn("do not substitute another operation", listing)
        self.assertIn("resume only after a read-only authoritative check confirms the chosen parent", listing)
        self.assertIn("if it cannot be verified, keep the affected roots paused", listing)
        self.assertIn("complete, validated listing", selection)
        self.assertIn("single-root flow", selection)

    def test_multi_root_batch_scope_stays_frozen_through_root_completion(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower().replace(chr(96), "")
        listing = section(reference, "## 1. list and validate roots")
        selection = section(reference, "## 2. select and freeze the batch")
        tracking = section(reference, "## 5. track acceptance, closure, and rework")
        completion = section(reference, "## 6. complete the batch")

        self.assertIn("if the documents or skill instructions conflict, explain the conflict to the user and pause only affected roots", reference)
        self.assertIn("the caller must not edit skill documents during the run", reference)
        self.assertIn("freeze the selected set for task-start authorization", selection)
        self.assertIn("a newly discovered root stays out of the batch until the user approves the scope change and renewed task-start authorization", selection)
        self.assertIn("pause the affected root with the evidence and resume condition", listing)
        self.assertIn("continue safe independent roots", listing)
        self.assertIn("in-scope acceptance rework returns to the current batch and the same parallel limit", tracking)
        self.assertIn("pause out-of-scope rework and scope expansion; present the proposed scope change to the user and resume only after renewed scope and task-start authorization are approved", tracking)
        self.assertIn("if a newly found root blocks only some selected roots, pause those roots and continue unaffected roots", tracking)
        self.assertIn("the batch stays open until every selected root has reached its completion checkpoint and root close", completion)

    def test_multi_root_task_start_authorization_scopes_cross_root_operations(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower()
        preparation = section(reference, "## 3. prepare and authorize the batch")
        adr_text = " ".join((
            ROOT / "docs" / "adr" / "0003-task-scoped-write-authorization.md"
        ).read_text(encoding="utf-8").lower().split())

        self.assertTrue(sentence_with_concepts(
            preparation, ("cross-root dependency",),
            ("source-root-to-dependent-root", "source root to dependent root"),
        ))
        operation = sentence_with_concepts(
            preparation, ("source root", "source-root"),
            ("dependent root", "dependent-root"), ("destination",),
            ("creates", "merges"),
        )
        self.assertTrue(operation)
        self.assertTrue(mentions_concepts(
            operation, ("branch",), ("worktree", "branch"),
            ("ticket branch", "integration branch"),
        ))
        self.assertTrue(sentence_with_concepts(
            preparation, ("ambiguous",), ("ask", "clarify"),
            ("pause",), ("dependent root",),
        ))

        worktree_prep = sentence_with_concepts(
            preparation, ("worktrees",), ("cross-root operations",),
        )
        authorization = sentence_with_concepts(
            preparation, ("single", "one"), ("task-start authorization",),
            ("frozen batch",),
        )
        authorized_operations = sentence_with_concepts(
            preparation, ("after approval",), ("only",), ("listed",),
            ("cross-root operations",),
        )
        dispatch = sentence_with_concepts(
            preparation, ("dispatch",), ("limit",), ("operations",),
            ("succeeded", "success"),
        )
        self.assertTrue(worktree_prep)
        self.assertTrue(authorization)
        self.assertTrue(authorized_operations)
        self.assertTrue(dispatch)
        self.assertLess(preparation.index(worktree_prep), preparation.index(authorization))
        self.assertLess(preparation.index(authorization), preparation.index(authorized_operations))
        self.assertLess(preparation.index(authorization), preparation.index(dispatch))
        self.assertTrue(sentence_with_concepts(
            preparation, ("per-root",), ("do not", "not request"),
            ("authorization", "grant"),
        ))

        batch_grant = sentence_with_concepts(
            adr_text, ("grant",), ("only",), ("listed resources", "listed"),
            ("categories", "actions"), ("batch",),
        )
        cross_root_scope = sentence_with_concepts(
            adr_text, ("cross-root",), ("source root",), ("dependent root",),
            ("destination",), ("operation", "branch"),
        )
        self.assertTrue(batch_grant)
        self.assertTrue(cross_root_scope)
        self.assertTrue(sentence_with_concepts(
            adr_text, ("authorization",), ("only",),
            ("listed cross-root operations",), ("batch",),
        ))
        self.assertTrue(sentence_with_concepts(
            adr_text, ("per-root",), ("replaces", "one"),
            ("authorization",), ("batch",),
        ))

    def test_task_start_authorization_covers_frozen_scope_before_dispatch(self):
        plan = section(skill("spec-implement-loop").lower(), "## plan the graph and reusable worktree pool")
        task_start = next(line for line in plan.splitlines() if line.strip().startswith("7."))

        self.assertTrue(mentions_concepts(
            task_start, ("freeze", "frozen"), ("batch",), ("authorization",),
            ("before",), ("dispatch",),
        ))
        self.assertTrue(mentions_concepts(
            task_start, ("root",), ("repository",), ("integration branch",),
            ("worktree",), ("ticket assignment",), ("action categories",),
            ("issue targets",), ("cross-root operation",),
        ))
        gate = sentence_with_concepts(
            task_start, ("grant",), ("required scope",), ("dispatch",),
        )
        self.assertTrue(gate)
        self.assertRegex(gate, r"\b(?:until|only after|after)\b")
        self.assertTrue(sentence_with_concepts(
            task_start, ("pending",), ("declined",), ("incomplete",),
            ("dispatch",), ("implementation conversation",),
        ))
        self.assertTrue(sentence_with_concepts(
            task_start, ("worker",), ("only",), ("grant", "authorization"),
            ("ticket",), ("resources",), ("actions", "categories"),
        ))
        self.assertTrue(sentence_with_concepts(
            task_start, ("worker",), ("another ticket", "sibling ticket"),
            ("authorization", "grant"), ("must not", "cannot"),
        ))
        self.assertTrue(sentence_with_concepts(
            task_start, ("unlisted",), ("gated", "blocked"),
            ("actions", "resources"),
        ))

    def test_multi_root_scheduler_shares_limit_and_releases_safe_slots(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower().replace(chr(96), "")
        preparation = section(reference, "## 3. prepare and authorize the batch")
        scheduling = section(reference, "## 4. schedule queues and gate prerequisites")
        acceptance = section(reference, "## 5. track acceptance, closure, and rework")

        self.assertIn("before the first implementation conversation, ask once for a single batch-wide parallel limit", preparation)
        self.assertIn("apply that cap across roots to every dispatch and refill throughout the batch", preparation)
        self.assertIn("unlimited still cannot exceed the clean, available worker slots", preparation)
        self.assertTrue(sentence_with_concepts(
            scheduling, ("worker",), ("only",), ("grant", "authorization"),
            ("ticket",),
        ))
        self.assertTrue(sentence_with_concepts(
            scheduling, ("worker",), ("another ticket", "sibling ticket"),
            ("authorization", "grant"), ("must not", "cannot"),
        ))
        self.assertLess(
            preparation.index("before the first implementation conversation"),
            preparation.index("dispatch planned work only after this limit is set"),
        )
        self.assertIn("count active implementation conversations across all selected roots against the same limit", scheduling)
        self.assertIn("refill capacity as work completes without exceeding the shared limit or available slots", scheduling)
        self.assertIn("check for newly eligible work on the agreed 15-minute cadence", scheduling)
        self.assertIn("stop checking once every selected root has an implementation conversation", scheduling)
        self.assertIn("do not interrupt an active worker when newly eligible work changes queue order", scheduling)
        self.assertIn("reuse an idle slot only when it is safe and its workspace is clean", scheduling)
        self.assertIn("release its worker slot at root_checkpoint", acceptance)
        self.assertIn("lightweight wait for final user acceptance or closure does not consume an implementation slot", acceptance)

    def test_manual_authorization_acceptance_covers_worker_scope_and_dispatch_gates(self):
        manual = (ROOT / "tests" / "manual" / "spec-implement-loop.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## graph planning and reusable worktree pool")

        self.assertTrue(sentence_with_concepts(
            scenario, ("ticket a",), ("ticket b",), ("worker",), ("only",),
            ("grant", "authorization"), ("resources",), ("actions",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("another ticket", "sibling ticket"), ("resources",),
            ("actions",), ("blocked",),
        ))
        self.assertTrue(sentence_with_concepts(
            scenario, ("pending",), ("declined",), ("incomplete",),
            ("no worker", "no implementation conversation"), ("starts", "dispatch"),
        ))

    def test_cross_root_prerequisites_are_resolved_and_integrated_before_dispatch(self):
        reference = skill_reference("spec-implement-loop", "multi-root-coordination.md").lower().replace(chr(96), "")
        preparation = section(reference, "## 3. prepare and authorize the batch")
        scheduling = section(reference, "## 4. schedule queues and gate prerequisites")

        self.assertIn("if the required base or source branch is ambiguous, ask which existing branch to use or which source branch to merge", preparation)
        self.assertIn("pause only the affected dependent root until resolved", preparation)
        self.assertIn("do not infer a branch or merge operation", preparation)
        self.assertIn("the plan and task-start authorization must explicitly name the source root branch and its merge into the dependent integration branch", preparation)
        self.assertIn("creating a dependent ticket branch from the source does not substitute for or authorize that merge", preparation)
        self.assertIn("merge that branch into the dependent root as authorized; dispatch the dependent ticket only after the merge succeeds", scheduling)
        self.assertIn("do not wait for the source root's full queue or final acceptance", scheduling)
        self.assertIn("a blocked prerequisite or merge conflict pauses only the affected dependent root", scheduling)
        self.assertIn("continue other roots with ready tickets", scheduling)
        self.assertLess(
            preparation.index("if the required base or source branch is ambiguous"),
            preparation.index("request the single task-start authorization defined by the main skill"),
        )

    def test_remediation_routes_only_when_final_review_finds_issues(self):
        text = skill("spec-implement-loop").lower()
        final_review = section(text, "## final review")
        remediation = skill_reference("spec-implement-loop", "final-review-remediation.md").lower().replace(chr(96), "")
        self.assertIn("when no non-deferred ready ticket remains, review the complete target diff", final_review)
        self.assertIn("if the reports contain no findings", final_review)
        self.assertIn("if findings exist", final_review)
        self.assertIn("references/final-review-remediation.md", final_review)
        self.assertNotIn("## final review and remediation", text)
        self.assertIn("preserve its seam-confirmation gate before publication", remediation)
        self.assertIn("preserve its granularity, blocking-edge, and publication approval gates", remediation)
        self.assertIn("**deferred:** yes", remediation)
        self.assertIn("show the complete p0/p1 batch and ask the user for approval", remediation)
        self.assertIn("allow at most three rounds", remediation)

    def test_status_sync_authorization_is_repository_and_checkpoint_scoped(self):
        text = skill("spec-implement-loop").lower().replace(chr(96), "")
        authorization = section(text, "## plan the graph and reusable worktree pool")
        lifecycle = section(text, "## root-run lifecycle")
        issue_loop = section(text, "## issue loop")
        status_retry_rule = next(
            line for line in text.splitlines() if line.startswith("ticket and root status-sync writes")
        )

        for detail in (
            "reconcile an uncertain outcome before retrying",
            "retry only transient failures up to three total attempts",
            "do not retry permanent failures",
            "preserve confirmed independent status updates if a later status sync fails",
        ):
            self.assertIn(detail, status_retry_rule)

        self.assertFalse("issue #143" in text, "Issue #143 cannot provide reusable status authorization.")
        self.assertTrue(sentence_with_concepts(
            authorization, ("root",), ("repository", "repo"), ("ticket",), ("status",),
            ("limited", "only", "scoped"),
        ))
        self.assertTrue(sentence_with_concepts(
            authorization, ("status",), ("only", "limited"), ("ticket",), ("root",), ("checkpoint",),
        ))
        denied = sentence_with_concepts(
            authorization, ("status-sync authorization", "status synchronization"),
            ("not", "cannot", "prohibited", "outside"),
            ("issue",), ("comment",), ("label",), ("sub-issue", "sub issue"),
            ("pull request", "pull-request"), ("merge",), ("github",), ("write",),
            ("authorize", "permit"),
        )
        self.assertTrue(denied, "The status-sync scope must distinguish status changes from other writes.")
        self.assertRegex(
            denied,
            r"\b(?:does not|doesn't|cannot|can't|must not|never)\s+(?:authorize|permit|allow|cover)\b",
        )
        self.assertFalse(status_sync_grant_clause(
            authorization, NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization is status-only, but a separate user approval authorizes a comment.".lower(),
            ("comment",),
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and the user separately authorizes issue creation.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and a separate approval from the user "
            "authorizes a comment.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and a separate approval by the user "
            "authorizes a comment.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes, and issue creation is separately "
            "authorized by the user.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync permits status changes and allows comments only with separate user approval.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync allows issue creation only after separate user approval.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync may allow issue creation, but only after a separate approval.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync may allow issue creation, but only if separate approval is granted.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status sync may allow issue creation, but only when a separate approval is in place.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertFalse(status_sync_grant_clause(
            "Status-sync authorization permits status changes on the supplied root issue.".lower(),
            NON_STATUS_WRITES,
        ))
        self.assertTrue(status_sync_grant_clause(
            "Status sync can create an issue.".lower(), NON_STATUS_WRITES,
        ))
        self.assertTrue(status_sync_grant_clause(
            "Status sync may label an issue.".lower(), NON_STATUS_WRITES,
        ))
        self.assertTrue(status_sync_grant_clause(
            "Status-sync authorization only permits status changes. Status-sync authorization also permits issue creation.".lower(),
            ("issue creation",),
        ))

        ticket_checkpoint = lifecycle.index("| ticket_checkpoint")
        ticket_sync = lifecycle.index("| status_sync")
        root_sync = lifecycle.index("| root_status_sync")
        root_checkpoint = lifecycle.index("| root_checkpoint")
        self.assertLess(ticket_checkpoint, ticket_sync)
        self.assertLess(ticket_sync, root_sync)
        self.assertLess(root_sync, root_checkpoint)
        ticket_checkpoint_rule = next(
            line for line in lifecycle.splitlines() if "| ticket_checkpoint |" in line
        )
        self.assertTrue(mentions_concepts(
            ticket_checkpoint_rule, ("review",), ("internally",), ("does not wait for human approval",), ("status_sync",),
        ))
        root_status_rule = next(line for line in lifecycle.splitlines() if "| root_status_sync |" in line)
        self.assertTrue(mentions_concepts(
            root_status_rule, ("final verification",), ("review",), ("completed",),
            ("without a separate approval", "approval pause"),
        ))
        root_checkpoint_rule = next(line for line in lifecycle.splitlines() if "| root_checkpoint |" in line)
        self.assertTrue(mentions_concepts(
            root_checkpoint_rule, ("explicit approval", "approval"), ("complete",),
        ))
        self.assertTrue(sentence_with_concepts(
            lifecycle, ("status synchronization", "status_sync"), ("never", "does not"),
            ("approval",), ("root",), ("complete",),
        ))

        ticket_sync_rule = next(line for line in issue_loop.splitlines() if line.lstrip().startswith("6."))
        self.assertTrue(mentions_concepts(
            ticket_sync_rule, ("internal ticket review", "review checkpoint"),
            ("confirmed authorized push", "confirmed push"), ("ticket's status", "ticket status"),
            ("task-start grant", "batch grant"), ("does not wait for human approval",),
        ))
        self.assertIn("apply the shared bounded retry rules to status sync", ticket_sync_rule)
        root_sync_rule = next(line for line in issue_loop.splitlines() if line.lstrip().startswith("7."))
        self.assertTrue(mentions_concepts(
            root_sync_rule, ("final verification",), ("root status",), ("before",),
            ("root completion checkpoint", "completion checkpoint"),
        ))

        interruption = sentence_with_concepts(
            lifecycle, ("restart", "interruption", "resume"), ("reconcile", "re-read"),
            ("root",), ("ticket",), ("repository",), ("status",), ("write",),
        )
        self.assertTrue(interruption)

    def test_manual_status_scenario_covers_repository_and_operation_boundaries(self):
        manual = (ROOT / "tests" / "manual" / "spec-implement-loop.md").read_text(encoding="utf-8").lower()
        scenario = section(manual, "## task-scoped commits and pushes")
        status_scenario = sentence_with_concepts(
            scenario, ("repository a", "repo a"), ("repository b", "repo b"),
            ("root",), ("ticket",), ("status",), ("checkpoint",),
            ("unchanged", "unmodified"),
        )
        self.assertTrue(status_scenario)
        self.assertTrue(sentence_with_concepts(
            scenario, ("repository a", "repo a"), ("in-repository ticket",),
            ("cross-repository ticket",), ("repository b", "repo b"),
        ))
        self.assertFalse("issue #143" in status_scenario, "Manual scenario must not rely on Issue #143.")

        denial = sentence_with_concepts(
            scenario, ("status-sync authorization", "status sync authorization"),
            ("not", "cannot", "outside", "prohibited"),
            ("issue",), ("comment",), ("label",), ("sub-issue", "sub issue"),
            ("pr", "pull request"), ("merge",), ("github",), ("write",),
        )
        self.assertTrue(denial)
        self.assertRegex(
            denial,
            r"\b(?:does not|doesn't|cannot|can't|must not|never)\s+(?:authorize|permit|allow|cover)\b",
        )
        self.assertFalse(status_sync_grant_clause(
            scenario, NON_STATUS_WRITES + ("pr action",),
        ))


class ConventionalGitMessagesBehaviorTests(unittest.TestCase):
    def test_each_output_type_routes_to_an_existing_reference(self):
        text = skill("conventional-git-messages").lower()
        routes = section(text, "## guidance routes")
        self.assertIn("follow its links only for rules", routes)
        self.assertIn("it reuses.", routes)
        references = (
            ("commit message", "commit-messages.md", ("## commit subject", "## commit body")),
            (
                "pull request title, description, or comment",
                "pull-request-text.md",
                (
                    "## pull request titles",
                    "## pull request descriptions",
                    "## pull request comments",
                    "## optional diagrams",
                ),
            ),
            (
                "issue title, description, or comment",
                "issue-text.md",
                ("## issue titles", "## issue descriptions", "## issue comments"),
            ),
        )
        for trigger, filename, headings in references:
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, routes)
                self.assertIn(f"(references/{filename})", routes)
                reference_path = (
                    ROOT / "skills" / "conventional-git-messages" / "references" / filename
                )
                self.assertTrue(reference_path.is_file())
                reference_text = reference_path.read_text(encoding="utf-8").lower()
                for heading in headings:
                    self.assertIn(heading, reference_text)

    def test_shared_operation_boundary_stays_in_the_entrypoint(self):
        text = skill("conventional-git-messages").lower().replace(chr(96), "")
        activation = section(text, "## activation criteria & objective")
        self.assertIn("never perform a git operation", activation)
        self.assertIn("create or modify an issue", activation)
        self.assertIn("open or edit a pull request", activation)
        self.assertIn("post a comment", activation)

    def test_optional_diagrams_use_user_selected_skill_scout_flow(self):
        text = skill_reference("conventional-git-messages", "pull-request-text.md").lower().replace(chr(96), "")
        diagrams = section(text, "## optional diagrams")
        self.assertIn("follow /skill-scout's general-host flow", diagrams)
        self.assertIn("use its skillroute local-catalog mode only when the user selects it", diagrams)
        self.assertIn("do not install, index, copy, or silently substitute a skill", diagrams)


class ReadmeBehaviorTests(unittest.TestCase):
    def test_generic_skill_install_command_remains(self):
        self.assertIn("npx skills@latest add EltonZhang777/AggregateSkills", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
