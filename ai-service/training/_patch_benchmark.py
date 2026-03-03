"""
Patch script: injects _BENCH_STATUS live update calls into run_question()
and creates get_bench_status() / start_bench_async() exports.
Run once then delete.
"""
import re

FILE = "real_benchmark.py"

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

# ── 1. Find and replace run_question ─────────────────────────────────────────
RQ_PATTERN = re.compile(
    r"(    def run_question\(self, question: dict\) -> dict:.*?return \{.*?\}(?:\n|$))",
    re.DOTALL
)

NEW_RQ = '''\
    def run_question(self, question: dict, q_index: int = 0) -> dict:
        """Full council pipeline for one question with live status tracking."""
        # Live: Round 1
        with _BENCH_LOCK:
            _BENCH_STATUS["current_q_index"] = q_index
            _BENCH_STATUS["current_q_text"]  = question["question"][:120]
            _BENCH_STATUS["current_round"]   = "round1"
            _BENCH_STATUS["current_doctors"] = [d["name"] for d in self.COUNCIL]

        print(f"  [Q{q_index+1}] {question['question'][:70]}...")
        print(f"  [Round 1 - Parallel] All doctors analyze simultaneously...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.COUNCIL)) as pool:
            futures = {pool.submit(self._ask_round1, doc, question): doc for doc in self.COUNCIL}
            round1_results = []
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                round1_results.append(res)
                marker = "V" if res["answer_r1"] == question["correct"] else "X"
                print(f"    {res['name']:12} -> {res['answer_r1']} {marker}")

        # Live: Debate
        with _BENCH_LOCK:
            _BENCH_STATUS["current_round"]   = "debate"
            _BENCH_STATUS["current_doctors"] = [d["name"] for d in self.COUNCIL]

        print(f"  [Round 2 - Debate] Cross-examination...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.COUNCIL)) as pool:
            futures = {pool.submit(self._ask_debate, doc, question, round1_results): doc for doc in self.COUNCIL}
            debate_results = []
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                debate_results.append(res)
                changed = " [revised!]" if res["answer_final"] != res.get("answer_r1") else ""
                marker = "V" if res["answer_final"] == question["correct"] else "X"
                print(f"    {res['name']:12} -> {res['answer_final']} {marker}{changed}")

        # Live: Consensus
        with _BENCH_LOCK:
            _BENCH_STATUS["current_round"]   = "consensus"
            _BENCH_STATUS["current_doctors"] = []

        council_ans, tally, agreed = self._weighted_consensus(debate_results)
        correct = (council_ans == question["correct"])
        votes_r1    = {r["name"]: r["answer_r1"]    for r in round1_results}
        votes_final = {r["name"]: r["answer_final"] for r in debate_results}

        print(f"  [Council] {'OK' if correct else 'WRONG'} Council={council_ans} Correct={question['correct']} Agreed={agreed}")

        return {
            "id": question["id"], "source": question["source"],
            "category": question["category"], "difficulty": question["difficulty"],
            "correct_ans": question["correct"], "votes_r1": votes_r1,
            "votes_final": votes_final, "council_ans": council_ans,
            "council_correct": correct, "agreed": agreed,
            "weight_tally": tally, "explanation": question["explanation"],
        }

'''

match = RQ_PATTERN.search(src)
if match:
    src = src[:match.start()] + NEW_RQ + src[match.end():]
    print(f"[1] Patched run_question() at char {match.start()}")
else:
    print("[1] WARNING: run_question pattern not found — patching by line number")
    lines = src.splitlines(keepends=True)
    # Find "def run_question" line
    start = next((i for i, l in enumerate(lines) if "def run_question" in l), None)
    if start is not None:
        # Find next def at 4-space indent
        end = start + 1
        while end < len(lines):
            if lines[end].startswith("    def ") and end > start + 3:
                break
            end += 1
        lines[start:end] = [NEW_RQ]
        src = "".join(lines)
        print(f"[1] Patched run_question() via line {start}")
    else:
        print("[1] FATAL: can't find run_question")

# ── 2. Patch run() to pass q_index and update status after each question ────
# Find the loop line:  result = self.run_question(q)
OLD_CALL = "                result = self.run_question(q)"
NEW_CALL = "                result = self.run_question(q, q_index=results.__len__())"
if OLD_CALL in src:
    src = src.replace(OLD_CALL, NEW_CALL, 1)
    print("[2] Patched run() call to pass q_index")

# After "results.append(result)", update live status
OLD_APPEND = "                results.append(result)"
NEW_APPEND = '''\
                results.append(result)

                # Live status update after each question
                with _BENCH_LOCK:
                    if result["council_correct"]:
                        _BENCH_STATUS["council_correct"] += 1
                    done = len(results)
                    total = _BENCH_STATUS["total_questions"]
                    _BENCH_STATUS["council_score"] = round(
                        _BENCH_STATUS["council_correct"] / done * 100, 1) if done else 0
                    _BENCH_STATUS["results"].append({
                        "id": result["id"], "source": result["source"],
                        "correct_ans": result["correct_ans"],
                        "council_ans": result["council_ans"],
                        "council_correct": result["council_correct"],
                        "votes_r1": result["votes_r1"],
                        "votes_final": result["votes_final"],
                    })
'''
if OLD_APPEND in src:
    src = src.replace(OLD_APPEND, NEW_APPEND, 1)
    print("[3] Patched run() append with live status update")

# ── 3. Update _compile call / status on completion ───────────────────────────
OLD_COMPILE = "        report = self._compile(results, model_scores_r1, model_scores_final,"
NEW_COMPILE = '''\
        # Mark done in live status
        import datetime as _dt
        with _BENCH_LOCK:
            _BENCH_STATUS["current_round"]   = "done"
            _BENCH_STATUS["current_q_text"]  = "Benchmark complete!"
            _BENCH_STATUS["finished_at"]     = _dt.datetime.now().isoformat()

        report = self._compile(results, model_scores_r1, model_scores_final,
'''
if OLD_COMPILE in src:
    src = src.replace(OLD_COMPILE, NEW_COMPILE, 1)
    print("[4] Patched run() completion marker")

# ── After self._save_excel, store full report and set status=completed ───────
OLD_SAVE = '        self._save_excel(report, results)\n        print(f"\\n📊 Saved: benchmark_results.json + benchmark_report.xlsx\\n")'
NEW_SAVE = '''\
        self._save_excel(report, results)
        print(f"\\n Results saved: benchmark_results.json + benchmark_report.xlsx\\n")
        with _BENCH_LOCK:
            _BENCH_STATUS["status"] = "completed"
            _BENCH_STATUS["report"] = report
'''
if OLD_SAVE in src:
    src = src.replace(OLD_SAVE, NEW_SAVE, 1)
    print("[5] Patched run() final completed status")
else:
    print("[5] WARNING: save pattern not found")

# ── Write back ─────────────────────────────────────────────────────────────
with open(FILE, "w", encoding="utf-8") as f:
    f.write(src)

# Verify
import ast
try:
    ast.parse(src)
    print(f"\n✅ Syntax OK — {len(src.splitlines())} lines")
except SyntaxError as e:
    print(f"\n❌ Syntax error at line {e.lineno}: {e.msg}")
    print(f"   {e.text}")
