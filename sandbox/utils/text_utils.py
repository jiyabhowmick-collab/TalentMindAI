"""
Text processing utilities for the TalentMind AI ranking pipeline.

Provides skill extraction, tokenization, seniority-level inference, and
years-of-experience parsing.  All functions are fully offline and rely only
on regex / set-based matching — no external APIs or ML models.

Key exports:
    TECH_SKILLS          – canonical set of ~400+ recognised tech skills
    STOPWORDS            – common English stopwords
    tokenize()           – lowercase, clean, remove stopwords
    extract_skills_from_text()  – substring / regex skill extraction
    extract_years_from_text()   – "5+ years" → 5.0
    compute_seniority_level()   – title + years → 1-4
"""

from __future__ import annotations

import re
from typing import List, Optional, Set

# ──────────────────────────────────────────────────────────────────────
# TECH_SKILLS — ~400+ skills grouped by domain
# ──────────────────────────────────────────────────────────────────────

_LANG = {
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "ruby", "php", "swift", "kotlin", "scala", "perl", "haskell",
    "elixir", "clojure", "erlang", "fortran", "cobol", "assembly",
    "objective-c", "dart", "julia", "r", "matlab", "groovy", "lua",
    "nim", "zig", "v", "go", "rust", "bash", "shell", "powershell",
    "sql", "plsql", "tsql", "vba", "f#", "ocaml", "racket", "lisp",
    "prolog", "solidity", "vyper", "move",
}

_WEB = {
    "react", "angular", "vue", "svelte", "nextjs", "next.js", "nuxt",
    "gatsby", "remix", "astro", "html", "css", "sass", "less",
    "tailwind", "tailwindcss", "bootstrap", "material-ui", "mui",
    "chakra-ui", "ant-design", "webpack", "vite", "rollup", "parcel",
    "babel", "eslint", "prettier", "storybook", "jest", "cypress",
    "playwright", "puppeteer", "selenium", "jquery", "backbone",
    "ember", "alpine.js", "htmx", "webassembly", "wasm", "pwa",
    "graphql", "rest", "restful", "websocket", "ajax", "json",
    "xml", "yaml", "markdown", "handlebars", "ejs", "pug", "jinja",
}

_BACKEND = {
    "node.js", "nodejs", "express", "fastify", "nestjs", "koa",
    "django", "flask", "fastapi", "tornado", "bottle", "pyramid",
    "spring", "spring-boot", "springboot", "quarkus", "micronaut",
    "rails", "sinatra", "laravel", "symfony", "codeigniter", "lumen",
    "gin", "echo", "fiber", "gorilla", "chi", "actix", "rocket",
    "axum", "warp", "asp.net", "blazor", "grpc", "thrift",
    "rabbitmq", "kafka", "celery", "sidekiq", "bull", "zeromq",
    "nats", "mqtt", "redis", "memcached",
}

_DB = {
    "postgresql", "postgres", "mysql", "mariadb", "sqlite", "oracle",
    "sql-server", "mssql", "mongodb", "dynamodb", "cassandra",
    "couchdb", "couchbase", "neo4j", "arangodb", "dgraph", "fauna",
    "cockroachdb", "tidb", "clickhouse", "timescaledb", "influxdb",
    "elasticsearch", "opensearch", "solr", "supabase", "firebase",
    "firestore", "prisma", "sequelize", "sqlalchemy", "typeorm",
    "knex", "drizzle", "mongoose", "redis", "etcd",
}

_CLOUD = {
    "aws", "azure", "gcp", "google-cloud", "heroku", "vercel",
    "netlify", "digitalocean", "linode", "vultr", "cloudflare",
    "ec2", "s3", "lambda", "fargate", "ecs", "eks", "rds",
    "aurora", "redshift", "sagemaker", "bedrock", "step-functions",
    "cloudformation", "cdk", "sam", "amplify", "cognito", "iam",
    "vpc", "route53", "cloudfront", "api-gateway", "sns", "sqs",
    "kinesis", "eventbridge", "glue", "athena", "emr",
    "azure-devops", "azure-functions", "cosmos-db", "blob-storage",
    "bigquery", "cloud-run", "cloud-functions", "gke", "pubsub",
}

_DEVOPS = {
    "docker", "kubernetes", "k8s", "helm", "istio", "envoy",
    "terraform", "pulumi", "ansible", "chef", "puppet", "vagrant",
    "packer", "jenkins", "github-actions", "gitlab-ci", "circleci",
    "travis-ci", "argo-cd", "argocd", "flux", "spinnaker",
    "prometheus", "grafana", "datadog", "new-relic", "splunk",
    "elk", "logstash", "kibana", "fluentd", "jaeger", "zipkin",
    "nginx", "apache", "caddy", "traefik", "haproxy", "consul",
    "vault", "nomad", "ci/cd", "cicd", "devops", "sre", "gitops",
    "linux", "unix", "systemd", "cron",
}

_DATA = {
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "bokeh", "dash", "streamlit", "gradio", "jupyter", "notebook",
    "databricks", "snowflake", "dbt", "airflow", "prefect",
    "dagster", "luigi", "spark", "pyspark", "flink", "beam",
    "hadoop", "hive", "pig", "presto", "trino", "dask", "vaex",
    "polars", "arrow", "parquet", "avro", "delta-lake", "iceberg",
    "hudi", "lakehouse", "data-warehouse", "data-lake", "etl",
    "elt", "data-pipeline", "data-engineering", "data-science",
    "data-analysis", "data-visualization", "tableau", "power-bi",
    "looker", "metabase", "superset", "great-expectations",
}

_ML = {
    "machine-learning", "machine learning", "deep-learning",
    "deep learning", "neural-network", "neural network",
    "tensorflow", "pytorch", "keras", "jax", "flax", "scikit-learn",
    "sklearn", "xgboost", "lightgbm", "catboost", "random-forest",
    "gradient-boosting", "svm", "knn", "decision-tree",
    "linear-regression", "logistic-regression", "naive-bayes",
    "clustering", "k-means", "dbscan", "pca", "t-sne", "umap",
    "automl", "hyperparameter-tuning", "feature-engineering",
    "feature-store", "model-serving", "model-monitoring",
    "mlops", "mlflow", "kubeflow", "wandb", "dvc", "bentoml",
    "seldon", "triton", "onnx", "tensorrt", "openvino",
    "hugging-face", "huggingface", "transformers", "bert", "gpt",
    "llm", "llms", "rag", "langchain", "llamaindex", "openai",
    "anthropic", "gemini", "nlp", "natural-language-processing",
    "computer-vision", "cv", "opencv", "yolo", "detectron",
    "image-classification", "object-detection", "segmentation",
    "ocr", "speech-recognition", "tts", "asr",
    "reinforcement-learning", "rl", "gan", "vae", "diffusion",
    "stable-diffusion", "fine-tuning", "transfer-learning",
    "embedding", "vector-database", "pinecone", "weaviate",
    "milvus", "chroma", "qdrant", "faiss",
    "recommendation-system", "time-series", "anomaly-detection",
    "distributed training", "distributed-training",
}

_SEC = {
    "cybersecurity", "security", "penetration-testing", "pentest",
    "owasp", "soc", "siem", "ids", "ips", "firewall", "waf",
    "encryption", "ssl", "tls", "oauth", "oauth2", "jwt", "saml",
    "ldap", "active-directory", "kerberos", "zero-trust",
    "vulnerability-assessment", "threat-modeling", "devsecops",
    "compliance", "gdpr", "hipaa", "pci-dss", "soc2", "iso-27001",
}

_MOBILE = {
    "ios", "android", "react-native", "flutter", "xamarin",
    "ionic", "cordova", "capacitor", "swiftui", "uikit",
    "jetpack-compose", "kotlin-multiplatform", "expo",
    "mobile-development", "app-development",
}

_WEB3 = {
    "blockchain", "ethereum", "bitcoin", "web3", "defi", "nft",
    "smart-contract", "dapp", "solana", "polygon", "avalanche",
    "cosmos", "polkadot", "near", "cardano", "tezos", "algorand",
    "hardhat", "truffle", "foundry", "ethers.js", "web3.js",
    "ipfs", "the-graph", "chainlink", "openzeppelin",
}

_EMBEDDED = {
    "embedded", "embedded-systems", "rtos", "firmware", "fpga",
    "vhdl", "verilog", "systemverilog", "arduino", "raspberry-pi",
    "stm32", "esp32", "arm", "risc-v", "iot", "mqtt", "can-bus",
    "modbus", "plc", "scada",
}

_QA = {
    "testing", "unit-testing", "integration-testing", "e2e-testing",
    "tdd", "bdd", "pytest", "unittest", "mocha", "chai", "jasmine",
    "karma", "protractor", "testng", "junit", "rspec", "minitest",
    "selenium", "appium", "robot-framework", "cucumber", "postman",
    "insomnia", "k6", "locust", "gatling", "jmeter",
    "load-testing", "performance-testing", "qa", "quality-assurance",
    "test-automation", "manual-testing",
}

_ARCH = {
    "microservices", "monolith", "serverless", "event-driven",
    "cqrs", "event-sourcing", "domain-driven-design", "ddd",
    "clean-architecture", "hexagonal-architecture", "mvc", "mvvm",
    "design-patterns", "solid", "dry", "kiss", "api-design",
    "system-design", "distributed-systems", "high-availability",
    "scalability", "fault-tolerance", "load-balancing",
    "caching", "sharding", "replication", "consensus",
    "cap-theorem", "eventual-consistency",
}

_SOFT = {
    "agile", "scrum", "kanban", "lean", "waterfall", "jira",
    "confluence", "notion", "asana", "trello", "monday",
    "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
    "code-review", "pair-programming", "mob-programming",
    "technical-writing", "documentation", "mentoring",
    "leadership", "communication", "teamwork", "problem-solving",
    "critical-thinking", "time-management", "project-management",
}

_GAME = {
    "unity", "unreal-engine", "godot", "pygame", "phaser",
    "three.js", "babylon.js", "webgl", "opengl", "vulkan",
    "directx", "metal", "game-development", "game-design",
    "level-design", "3d-modeling", "blender", "maya",
}

_DESIGN = {
    "figma", "sketch", "adobe-xd", "photoshop", "illustrator",
    "after-effects", "premiere-pro", "canva", "invision",
    "zeplin", "abstract", "ui-design", "ux-design", "ui/ux",
    "user-research", "usability-testing", "wireframing",
    "prototyping", "responsive-design", "accessibility", "a11y",
    "wcag", "aria", "design-system", "atomic-design",
}

_BIZ = {
    "product-management", "product-owner", "business-analysis",
    "requirements-gathering", "stakeholder-management",
    "roadmap", "okr", "kpi", "a/b-testing", "analytics",
    "google-analytics", "mixpanel", "amplitude", "segment",
    "salesforce", "hubspot", "crm", "erp", "sap",
    "fintech", "healthtech", "edtech", "legaltech", "proptech",
}

TECH_SKILLS: frozenset[str] = frozenset(
    _LANG | _WEB | _BACKEND | _DB | _CLOUD | _DEVOPS | _DATA
    | _ML | _SEC | _MOBILE | _WEB3 | _EMBEDDED | _QA | _ARCH
    | _SOFT | _GAME | _DESIGN | _BIZ
)

# ──────────────────────────────────────────────────────────────────────
# Stopwords
# ──────────────────────────────────────────────────────────────────────

STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "is", "it", "its",
    "was", "are", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "shall", "can", "not", "no", "nor", "so", "if", "then",
    "than", "too", "very", "just", "about", "up", "out", "all",
    "also", "into", "over", "such", "we", "our", "you", "your",
    "they", "their", "this", "that", "these", "those", "which",
    "who", "whom", "what", "when", "where", "how", "each", "every",
    "both", "few", "more", "most", "other", "some", "any", "only",
    "own", "same", "here", "there",
})

# ──────────────────────────────────────────────────────────────────────
# Ambiguous short tokens that need word-boundary regex matching
# ──────────────────────────────────────────────────────────────────────

_WORD_BOUNDARY_SKILLS: frozenset[str] = frozenset({
    "r", "c", "go", "v", "ray", "dbt", "gin", "xp", "lua",
    "nim", "zig", "elk", "rust", "dart", "hive", "pig", "beam",
    "flux", "helm", "vault", "consul", "echo", "chi", "pug",
    "dash", "nats", "sam", "cdk", "ion", "move", "near",
    "can", "soc", "waf", "qa", "rl", "cv", "ocr", "tts", "asr",
    "ddd", "mvc", "mvvm", "dry", "kiss", "git", "svn", "lean",
    "arm", "iot", "plc", "k6", "ios",
})

# Compiled regex cache for boundary skills
_BOUNDARY_RE: dict[str, re.Pattern[str]] = {
    skill: re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE)
    for skill in _WORD_BOUNDARY_SKILLS
}

# Non-boundary skills (safe for substring matching)
_SUBSTRING_SKILLS: frozenset[str] = TECH_SKILLS - _WORD_BOUNDARY_SKILLS


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, remove stopwords, keep tokens len > 2."""
    if not text:
        return []
    # Replace common punctuation with space, keep hyphens inside words
    cleaned = re.sub(r"[^a-zA-Z0-9\-/#+.]", " ", text.lower())
    tokens = cleaned.split()
    return [
        t for t in tokens
        if len(t) > 2 and t not in STOPWORDS
    ]


def extract_years_from_text(text: str) -> Optional[float]:
    """
    Extract years of experience from text.

    Handles patterns like:
        "5 years"  →  5.0
        "3+ years" →  3.0
        "2-4 years" → 3.0 (midpoint)
        "10+ yrs"  → 10.0
    """
    if not text:
        return None

    # Range pattern: "2-4 years"
    m = re.search(r"(\d+)\s*[-–—to]+\s*(\d+)\s*\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return (lo + hi) / 2.0

    # Simple pattern: "5+ years" or "5 years"
    m = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if m:
        return float(m.group(1))

    return None


def extract_skills_from_text(text: str) -> Set[str]:
    """
    Extract recognised tech skills from free-form text.

    Uses substring matching for most skills and word-boundary regex
    for ambiguous short tokens (e.g. 'go', 'r', 'c').
    """
    if not text:
        return set()

    lower = text.lower()
    found: Set[str] = set()

    # Substring match for unambiguous skills
    for skill in _SUBSTRING_SKILLS:
        if skill in lower:
            found.add(skill)

    # Word-boundary regex for ambiguous short tokens
    for skill, pattern in _BOUNDARY_RE.items():
        if pattern.search(lower):
            found.add(skill)

    return found


def compute_seniority_level(years: Optional[float], title: str = "") -> int:
    """
    Compute seniority level 1-4 from years of experience and title.

    4 = Lead / Principal / Staff / Director / Head / Chief / VP
    3 = Senior / Sr.
    1 = Junior / Jr. / Intern / Associate / Entry
    Fallback by years: <2→1, <5→2, <9→3, else→4
    """
    title_lower = (title or "").lower()

    # Title-based overrides
    if any(kw in title_lower for kw in
           ("lead", "principal", "staff", "director", "head", "chief", "vp",
            "vice president", "fellow", "distinguished", "architect")):
        return 4

    if any(kw in title_lower for kw in ("senior", "sr.", "sr ")):
        return 3

    if any(kw in title_lower for kw in
           ("junior", "jr.", "jr ", "intern", "associate", "entry", "trainee",
            "apprentice", "graduate")):
        return 1

    # Fallback by years
    if years is None:
        return 2  # default mid-level
    if years < 2:
        return 1
    if years < 5:
        return 2
    if years < 9:
        return 3
    return 4
