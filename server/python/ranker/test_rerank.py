import sys
sys.path.insert(0, ".")
from pipeline.rank_aggregator import rerank_top10

# Build 12 fake results with a tiny score gap so boosts/penalties can flip ranks
results = []
for i in range(12):
    results.append({
        "_rank": i + 1,
        "_score": round(0.80 - i * 0.005, 4),   # only 0.005 gap so boosts matter
        "_semantic_score": 0.5,
        "_behavioral_score": 0.5,
        "signals": {
            "open_to_work_flag":         (i % 3 == 0),
            "recruiter_response_rate":   0.9 if i < 3 else 0.2,
            "notice_period_days":        14  if i == 5 else 90,
            "github_activity_score":     85  if i == 4 else 30,
            "verified_email":            True,
            "verified_phone":            (i % 2 == 0),
            "interview_completion_rate": 0.1 if i == 1 else 0.8,   # rank-2 penalised
            "offer_acceptance_rate":     0.2 if i == 2 else 0.7,   # rank-3 penalised
        },
    })

jd = {"required_skills": set(), "min_years": 3, "seniority_level": 2}

print("Before rerank (top 6):")
for r in results[:6]:
    s = r["signals"]
    print(
        f"  rank={r['_rank']}  score={r['_score']}"
        f"  rr={s['recruiter_response_rate']}"
        f"  icr={s['interview_completion_rate']}"
        f"  oar={s['offer_acceptance_rate']}"
        f"  notice={s['notice_period_days']}"
        f"  gh={s['github_activity_score']}"
    )

reranked = rerank_top10(results, jd)

print("\nAfter rerank (top 6):")
for r in reranked[:6]:
    s = r["signals"]
    print(
        f"  rank={r['_rank']}  score={r['_score']}"
        f"  rr={s['recruiter_response_rate']}"
        f"  icr={s['interview_completion_rate']}"
    )

# --- assertions ---
all_ranks = [r["_rank"] for r in reranked]
assert all_ranks == list(range(1, 13)), f"Ranks not sequential: {all_ranks}"
print("\nAll ranks sequential: OK")

# Positions 11-12 must be unchanged (rerank_top10 only touches 1-10)
assert reranked[10]["_score"] == results[10]["_score"], "Position 11 should be unchanged"
assert reranked[11]["_score"] == results[11]["_score"], "Position 12 should be unchanged"
print("Positions 11-12 unchanged: OK")

# Original rank-2 had icr=0.1 (penalty -0.03) and rr=0.9 (boost +0.03)
# net delta = 0, but original rank-5 (notice=14, +0.02) should beat some peers
# Just verify the reranked top-10 set is a permutation of the original top-10
original_top10_scores = {r["_score"] for r in results[:10]}
reranked_top10_scores  = {r["_score"] for r in reranked[:10]}
assert original_top10_scores == reranked_top10_scores, \
    "Reranked top-10 should contain the same candidates, just reordered"
print("Top-10 identity preserved (same candidates, reordered): OK")

# The low-ICR candidate (orig rank 2, icr=0.1) gets net penalty of -0.03+0.03=0
# because rr=0.9 offsets it. But rank-3 (rr=0.9, oar=0.2) gets net +0.03-0.02=+0.01
# and rank-6 (notice=14) gets +0.02. Verify the reranked top-3 are the 3 strongest
# by boosted score — the key guarantee is that the ICR-penalised candidate dropped.
new_rank_low_icr = next(r["_rank"] for r in reranked if r["signals"]["interview_completion_rate"] == 0.1)
print(f"Low-ICR candidate (orig rank 2) now at rank: {new_rank_low_icr}  (should be > 2)")
assert new_rank_low_icr > 2, f"Low-ICR candidate should have dropped from rank 2, got {new_rank_low_icr}"

# Rank-1 should stay rank-1 (highest base score + clean signals)
assert reranked[0]["_score"] == results[0]["_score"], "Rank-1 should remain unchanged"
print("Rank-1 unchanged: OK")

print("\nAll assertions passed. rerank_top10 is working correctly.")
