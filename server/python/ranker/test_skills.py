import sys
sys.path.insert(0, ".")

from utils.text_utils import (
    TECH_SKILLS, ML_SKILLS, LANG_SKILLS, WEB_SKILLS,
    BACKEND_SKILLS, DB_SKILLS, CLOUD_SKILLS, DEVOPS_SKILLS, DATA_SKILLS,
    SEC_SKILLS, MOBILE_SKILLS, WEB3_SKILLS, EMBEDDED_SKILLS, QA_SKILLS,
    ARCH_SKILLS, SOFT_SKILLS, GAME_SKILLS, DESIGN_SKILLS, BIZ_SKILLS,
    extract_skills_from_text,
)

# ── Category counts ──────────────────────────────────────────────────────────
cats = [
    ("Languages",   LANG_SKILLS),    ("Web/Frontend", WEB_SKILLS),
    ("Backend",     BACKEND_SKILLS), ("Databases",    DB_SKILLS),
    ("Cloud/Infra", CLOUD_SKILLS),   ("DevOps",       DEVOPS_SKILLS),
    ("Data Eng",    DATA_SKILLS),    ("ML/AI",        ML_SKILLS),
    ("Security",    SEC_SKILLS),     ("Mobile",       MOBILE_SKILLS),
    ("Web3",        WEB3_SKILLS),    ("Embedded",     EMBEDDED_SKILLS),
    ("Testing/QA",  QA_SKILLS),      ("Architecture", ARCH_SKILLS),
    ("Soft Skills", SOFT_SKILLS),    ("Game Dev",     GAME_SKILLS),
    ("Design/UX",   DESIGN_SKILLS),  ("Business",     BIZ_SKILLS),
]
print("Skill category breakdown:")
for name, s in cats:
    print(f"  {name:<18} {len(s):>3} skills")
print(f"  {'TOTAL':<18} {len(TECH_SKILLS):>3} unique skills")
print()

# ── Extraction correctness ───────────────────────────────────────────────────
tests = [
    ("pytorch found",        "Experience with PyTorch and TensorFlow",                    "pytorch"),
    ("langchain found",      "Built RAG pipelines using LangChain",                       "langchain"),
    ("rag found",            "Built RAG pipelines and rag-based retrieval",               "rag"),
    ("kubernetes found",     "k8s and Kubernetes cluster management",                     "kubernetes"),
    ("fine-tuning found",    "LLM fine-tuning with LoRA and QLoRA",                       "fine-tuning"),
    ("swift ios found",      "iOS development with Swift and SwiftUI",                    "swift"),
    ("solidity found",       "Ethereum smart contracts in Solidity",                      "solidity"),
    ("embedded/rtos found",  "RTOS firmware for STM32 microcontrollers",                  "rtos"),
    ("jest found",           "Unit testing with Jest and React Testing Library",          "jest"),
    ("system design found",  "System design and distributed systems",                     "system design"),
    ("r standalone",         "Statistical analysis using R and Python",                   "r"),
    ("go standalone",        "Golang and Go developer with Go experience",                "go"),
    # False-positive guards
    ("r not in pytorch",     "Expert in PyTorch and Docker and Kubernetes",               "__no_r__"),
    ("go not in mongodb",    "MongoDB and PostgreSQL and Django databases",               "__no_go__"),
    ("c not in docker",      "Docker containers and microservices architecture",          "__no_c__"),
]

all_ok = True
for label, text, expected in tests:
    found = extract_skills_from_text(text)
    if expected == "__no_r__":
        if "r" in found:
            print(f"  FAIL [{label}]: 'r' false-matched in: {text!r}")
            all_ok = False
        else:
            print(f"  PASS [{label}]")
    elif expected == "__no_go__":
        if "go" in found:
            print(f"  FAIL [{label}]: 'go' false-matched in: {text!r}")
            all_ok = False
        else:
            print(f"  PASS [{label}]")
    elif expected == "__no_c__":
        if "c" in found:
            print(f"  FAIL [{label}]: 'c' false-matched in: {text!r}")
            all_ok = False
        else:
            print(f"  PASS [{label}]")
    else:
        if expected not in found:
            print(f"  FAIL [{label}]: {expected!r} not found  (got={sorted(found)[:8]})")
            all_ok = False
        else:
            print(f"  PASS [{label}]")

print()
print("All checks passed." if all_ok else "SOME CHECKS FAILED.")
