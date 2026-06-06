import re
import string

# ~50 common English stopwords
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "i", "we", "you",
    "he", "she", "they", "it", "this", "that", "these", "those", "and",
    "or", "but", "if", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "as",
}

# ---------------------------------------------------------------------------
# Skills are grouped by domain for maintainability.
# All sets are merged into TECH_SKILLS at the bottom of this section.
# ---------------------------------------------------------------------------

# ── Programming languages ────────────────────────────────────────────────────
LANG_SKILLS: set[str] = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#",
    "go", "rust", "swift", "kotlin", "scala", "ruby", "php", "perl",
    "r", "matlab", "julia", "elixir", "erlang", "haskell", "clojure",
    "lua", "dart", "groovy", "objective-c", "assembly", "cobol", "fortran",
    "bash", "powershell", "shell scripting", "awk", "sed",
    "solidity", "move", "vyper",                        # blockchain
    "mojo", "nim", "zig",                               # emerging
}

# ── Web & frontend ───────────────────────────────────────────────────────────
WEB_SKILLS: set[str] = {
    "html", "css", "html5", "css3", "sass", "scss", "less",
    "react", "angular", "vue", "svelte", "nextjs", "nuxtjs", "remix",
    "gatsby", "astro", "qwik",
    "jquery", "bootstrap", "tailwind", "tailwindcss", "material ui",
    "chakra ui", "shadcn", "radix ui", "storybook",
    "webpack", "vite", "rollup", "parcel", "esbuild", "babel",
    "redux", "zustand", "mobx", "recoil", "jotai", "react query",
    "graphql", "rest", "grpc", "websocket", "webrtc",
    "pwa", "web components", "web assembly", "wasm",
    "d3", "three.js", "visx", "recharts", "echarts",
    "cypress", "playwright", "selenium", "puppeteer",
    "jest", "vitest", "testing library",
    "figma", "sketch", "adobe xd", "zeplin", "invision",
    "accessibility", "wcag", "aria",
}

# ── Backend & APIs ───────────────────────────────────────────────────────────
BACKEND_SKILLS: set[str] = {
    "nodejs", "express", "fastapi", "flask", "django", "fastify",
    "nestjs", "spring", "spring boot", "quarkus", "micronaut",
    "rails", "sinatra", "laravel", "symfony", "codeigniter",
    "asp.net", "dotnet", ".net core", "blazor",
    "gin", "fiber", "echo",                             # Go frameworks
    "actix", "axum", "rocket",                          # Rust frameworks
    "phoenix", "plug",                                  # Elixir
    "graphql", "rest api", "openapi", "swagger",
    "grpc", "protobuf", "thrift", "avro",
    "oauth", "jwt", "openid connect", "saml",
    "microservices", "service mesh", "api gateway",
    "event driven", "cqrs", "event sourcing",
    "hexagonal architecture", "domain driven design", "ddd",
    "serverless", "lambda", "cloud functions",
    "celery", "dramatiq", "bull", "sidekiq", "resque",
}

# ── Databases ────────────────────────────────────────────────────────────────
DB_SKILLS: set[str] = {
    "sql", "nosql", "postgresql", "mysql", "sqlite", "mariadb",
    "mssql", "sql server", "oracle", "db2",
    "mongodb", "couchdb", "firestore", "dynamodb", "cosmosdb",
    "redis", "memcached", "valkey",
    "elasticsearch", "opensearch", "solr",
    "cassandra", "scylladb", "hbase",
    "neo4j", "arangodb", "tigergraph",                  # graph
    "influxdb", "timescaledb", "questdb",               # time-series
    "clickhouse", "druid", "pinot",                     # olap
    "snowflake", "bigquery", "redshift", "synapse",     # cloud DW
    "dbt", "airbyte", "fivetran", "stitch",             # ELT/ETL tools
    "prisma", "sqlalchemy", "sequelize", "typeorm", "hibernate",
    "vector database", "pgvector", "faiss", "pinecone", "weaviate",
    "chroma", "qdrant", "milvus", "zilliz",
}

# ── Cloud & infrastructure ───────────────────────────────────────────────────
CLOUD_SKILLS: set[str] = {
    "aws", "azure", "gcp", "google cloud",
    "ec2", "s3", "lambda", "ecs", "eks", "fargate",
    "rds", "aurora", "cloudfront", "route53", "cloudwatch",
    "azure devops", "azure functions", "aks",
    "cloud run", "cloud build", "gke",
    "terraform", "pulumi", "cdk", "cloudformation",
    "ansible", "puppet", "chef", "salt",
    "docker", "kubernetes", "helm", "kustomize",
    "istio", "linkerd", "envoy",
    "nginx", "apache", "caddy", "traefik",
    "linux", "ubuntu", "debian", "centos", "rhel",
    "virtualbox", "vmware", "vagrant",
    "openstack", "proxmox",
    "cloudflare", "fastly", "akamai",
    "vercel", "netlify", "heroku", "fly.io", "render",
}

# ── DevOps & CI/CD ───────────────────────────────────────────────────────────
DEVOPS_SKILLS: set[str] = {
    "devops", "ci/cd", "gitops", "devsecops", "platform engineering",
    "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
    "teamcity", "bamboo", "argo cd", "flux",
    "git", "github", "gitlab", "bitbucket", "mercurial",
    "prometheus", "grafana", "alertmanager", "loki", "tempo",
    "datadog", "new relic", "dynatrace", "splunk", "elk stack",
    "sentry", "pagerduty", "opsgenie",
    "chaos engineering", "site reliability engineering", "sre",
    "observability", "distributed tracing", "opentelemetry",
    "vault", "consul",
    "sast", "dast", "sonarqube", "snyk", "trivy",
    "feature flags", "launchdarkly", "split.io",
}

# ── Data engineering & analytics ─────────────────────────────────────────────
DATA_SKILLS: set[str] = {
    "data engineering", "data analysis", "data analytics",
    "data warehousing", "data modeling", "data governance",
    "data quality", "data catalog", "data mesh",
    "etl", "elt", "data pipeline",
    "apache spark", "pyspark", "spark streaming",
    "hadoop", "hive", "pig", "impala", "presto", "trino",
    "kafka", "confluent", "apache flink", "apache beam",
    "rabbitmq", "activemq", "pulsar", "nats",
    "airflow", "prefect", "dagster", "luigi", "mage",
    "dbt", "great expectations", "soda",
    "tableau", "power bi", "looker", "metabase", "superset",
    "qlik", "microstrategy",
    "excel", "google sheets", "spreadsheet",
    "pandas", "numpy", "scipy", "statsmodels", "polars",
    "r", "sas", "spss", "stata",
    "jupyter", "colab", "databricks", "zeppelin",
    "dask", "vaex", "cudf",
    "snowflake", "bigquery", "redshift",
}

# ── ML & AI ──────────────────────────────────────────────────────────────────
ML_SKILLS: set[str] = {
    # Frameworks & libraries
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn",
    "jax", "flax", "paddle", "mxnet", "caffe",
    "xgboost", "lightgbm", "catboost", "h2o",
    "hugging face", "transformers", "diffusers", "accelerate",
    "langchain", "llamaindex", "llama index", "haystack", "semantic kernel",
    "openai", "anthropic", "cohere", "mistral",
    "stable diffusion", "controlnet", "comfyui",
    # ML concepts & techniques
    "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision",
    "reinforcement learning", "self-supervised learning",
    "transfer learning", "few-shot learning", "zero-shot learning",
    "generative ai", "generative models",
    "large language models", "llm", "slm",
    "fine-tuning", "lora", "qlora", "rlhf", "dpo",
    "rag", "retrieval augmented generation",
    "prompt engineering", "chain of thought", "agents", "agentic",
    "embeddings", "semantic search", "reranking",
    # MLOps & deployment
    "mlops", "model deployment", "model serving", "model monitoring",
    "mlflow", "weights and biases", "wandb", "neptune", "comet ml",
    "kubeflow", "bentoml", "torchserve", "triton", "onnx",
    "ray", "ray serve", "ray tune",
    "feature store", "feast",
    "data versioning", "dvc",
    # CV tasks
    "object detection", "image classification", "image segmentation",
    "pose estimation", "ocr", "face recognition",
    "yolo", "detectron", "mmdetection", "segment anything",
    # NLP tasks
    "text classification", "sentiment analysis", "named entity recognition",
    "question answering", "text summarization", "machine translation",
    "speech recognition", "text to speech", "speaker diarization",
    # Other ML
    "recommendation systems", "collaborative filtering",
    "a/b testing", "statistical modeling", "statistical analysis",
    "time series", "forecasting", "anomaly detection",
    "feature engineering", "hyperparameter tuning",
    "model evaluation", "evaluation", "benchmarking",
    # Tooling
    "jupyter", "colab", "cuda", "tensorrt",
    "faiss", "weaviate", "pinecone", "chroma", "qdrant", "milvus",
    "vector database",
    "apache spark", "pyspark", "dask",
    "airflow", "prefect", "dagster",
}

# ── Security & networking ─────────────────────────────────────────────────────
SEC_SKILLS: set[str] = {
    "cybersecurity", "information security", "appsec", "cloud security",
    "network security", "zero trust", "devsecops",
    "penetration testing", "pen testing", "red team", "blue team",
    "vulnerability assessment", "threat modeling",
    "siem", "soc", "edr", "xdr", "ndr",
    "firewalls", "ids", "ips", "waf", "vpn",
    "oauth", "jwt", "ssl", "tls", "pki", "kerberos",
    "owasp", "cve", "cvss",
    "burp suite", "metasploit", "nmap", "wireshark", "nessus",
    "encryption", "cryptography", "hashing", "hmac",
    "iam", "rbac", "abac", "privilege access management", "pam",
    "compliance", "gdpr", "hipaa", "sox", "pci dss", "iso 27001",
    "nist", "cis benchmarks",
    "tcp/ip", "dns", "dhcp", "bgp", "ospf", "mpls", "sd-wan",
    "802.1x", "vlan", "sdn",
}

# ── Mobile development ───────────────────────────────────────────────────────
MOBILE_SKILLS: set[str] = {
    "ios", "android", "react native", "flutter", "swift", "kotlin",
    "objective-c", "xamarin", "ionic", "capacitor", "cordova",
    "swiftui", "jetpack compose", "expo",
    "app store", "google play",
    "push notifications", "firebase",
    "mobile testing", "xctest", "espresso", "detox",
    "mobile ci/cd", "fastlane", "bitrise",
    "arkit", "arcore", "visionos", "watchos",
}

# ── Blockchain & Web3 ────────────────────────────────────────────────────────
WEB3_SKILLS: set[str] = {
    "blockchain", "ethereum", "solidity", "web3", "defi",
    "smart contracts", "nft", "ipfs", "hardhat", "foundry",
    "truffle", "ganache", "metamask", "walletconnect",
    "polkadot", "solana", "rust", "cosmos", "hyperledger",
    "layer 2", "polygon", "arbitrum", "optimism",
    "zero knowledge", "zk proof", "zk rollup",
    "tokenomics", "dao", "governance",
}

# ── Embedded & hardware ──────────────────────────────────────────────────────
EMBEDDED_SKILLS: set[str] = {
    "embedded systems", "firmware", "rtos", "bare metal",
    "c", "c++", "assembly", "fpga", "vhdl", "verilog",
    "arduino", "raspberry pi", "esp32", "stm32",
    "iot", "mqtt", "modbus", "can bus", "i2c", "spi", "uart",
    "linux kernel", "device drivers", "bsp",
    "ble", "zigbee", "lora", "lorawan", "nb-iot",
    "edge computing", "tinyml",
    "pcb design", "altium", "kicad",
    "automotive", "iso 26262", "autosar", "can", "lin",
    "plc", "scada", "industrial automation",
}

# ── Testing & QA ─────────────────────────────────────────────────────────────
QA_SKILLS: set[str] = {
    "testing", "quality assurance", "test automation",
    "unit testing", "integration testing", "end-to-end testing",
    "tdd", "bdd", "acceptance testing", "regression testing",
    "performance testing", "load testing", "stress testing",
    "jest", "vitest", "mocha", "chai", "jasmine",
    "pytest", "unittest", "nose2",
    "junit", "testng", "mockito", "spock",
    "rspec", "capybara",
    "cypress", "playwright", "selenium", "puppeteer", "webdriver",
    "postman", "insomnia", "newman",
    "k6", "gatling", "jmeter", "locust",
    "testflight", "firebase test lab",
    "mutation testing", "fuzz testing", "property based testing",
    "allure", "extent reports",
}

# ── Architecture & design ────────────────────────────────────────────────────
ARCH_SKILLS: set[str] = {
    "system design", "software architecture", "solution architecture",
    "microservices", "monolith", "serverless", "event driven",
    "domain driven design", "ddd", "cqrs", "event sourcing",
    "hexagonal architecture", "clean architecture", "onion architecture",
    "solid principles", "design patterns", "gang of four",
    "api design", "rest", "graphql", "grpc",
    "distributed systems", "consensus", "raft", "paxos",
    "cap theorem", "eventual consistency", "saga pattern",
    "circuit breaker", "bulkhead", "retry pattern",
    "high availability", "fault tolerance", "disaster recovery",
    "scalability", "performance optimization", "caching",
    "technical debt", "refactoring", "code review",
    "uml", "c4 model", "arc42",
}

# ── Soft skills & practices ──────────────────────────────────────────────────
SOFT_SKILLS: set[str] = {
    "agile", "scrum", "kanban", "lean", "xp",
    "product management", "project management", "program management",
    "leadership", "team lead", "mentoring", "coaching",
    "communication", "presentation", "stakeholder management",
    "problem solving", "critical thinking", "analytical",
    "teamwork", "collaboration", "cross-functional",
    "research", "documentation", "technical writing",
    "customer success", "client management", "consulting",
    "hiring", "recruiting", "interviewing",
    "budgeting", "forecasting", "roadmap",
}

# ── Game development ─────────────────────────────────────────────────────────
GAME_SKILLS: set[str] = {
    "unity", "unreal engine", "godot", "cocos2d",
    "c#", "c++", "blueprints",
    "game physics", "shaders", "hlsl", "glsl",
    "opengl", "directx", "vulkan", "metal",
    "multiplayer", "networking", "steam sdk",
    "game design", "level design", "procedural generation",
    "photon", "mirror", "netcode for gameobjects",
}

# ── Design & UX ──────────────────────────────────────────────────────────────
DESIGN_SKILLS: set[str] = {
    "ui design", "ux design", "product design",
    "user research", "usability testing", "a/b testing",
    "figma", "sketch", "adobe xd", "invision", "zeplin",
    "adobe photoshop", "adobe illustrator", "adobe after effects",
    "motion design", "animation", "lottie",
    "design system", "atomic design",
    "information architecture", "wireframing", "prototyping",
    "accessibility", "wcag", "inclusive design",
    "branding", "typography", "color theory",
}

# ── Business & finance tools ─────────────────────────────────────────────────
BIZ_SKILLS: set[str] = {
    "excel", "google sheets", "vba",
    "tableau", "power bi", "looker", "metabase",
    "salesforce", "hubspot", "zendesk", "intercom",
    "jira", "confluence", "notion", "asana", "linear",
    "slack", "microsoft teams",
    "sap", "oracle erp", "netsuite", "workday",
    "quickbooks", "xero",
    "sql", "business intelligence", "bi",
    "data visualization", "reporting",
    "erp", "crm", "hrms",
}

# ---------------------------------------------------------------------------
# Merged public set
# ---------------------------------------------------------------------------
TECH_SKILLS: set[str] = (
    LANG_SKILLS | WEB_SKILLS | BACKEND_SKILLS | DB_SKILLS |
    CLOUD_SKILLS | DEVOPS_SKILLS | DATA_SKILLS | ML_SKILLS |
    SEC_SKILLS | MOBILE_SKILLS | WEB3_SKILLS | EMBEDDED_SKILLS |
    QA_SKILLS | ARCH_SKILLS | SOFT_SKILLS | GAME_SKILLS |
    DESIGN_SKILLS | BIZ_SKILLS
)

# ---------------------------------------------------------------------------
# Skills ambiguous enough to require whole-word boundary matching.
# Pure substring would false-match these inside longer words:
#   "r"   → inside "pytorch", "kubernetes", "docker"
#   "go"  → inside "mongodb", "django", "cargo"
#   "c"   → inside almost everything
#   "ray" → inside "array", "spray"
#   "dbt" → inside "debug"
#   "sas" → inside "kubernetes" (no, but kept for safety)
#   "lin" → inside "kubernetes", "berlin"
# ---------------------------------------------------------------------------
_WORD_BOUNDARY_SKILLS: frozenset[str] = frozenset({
    # Single letters / very short tokens — match inside longer words everywhere
    "r", "c", "go", "c#", "c++",
    # Short tokens that are common substrings in unrelated words
    "ray",    # inside "array", "spray", "library"
    "dbt",    # inside "debug"
    "sas",    # safety
    "lin",    # inside "kubernetes", "berlin", "pipeline"
    "gin",    # inside "rankings", "engine", "beginning"
    "xp",     # inside "experience", "export"
    "can",    # inside "kubernetes", "scan", "canonical"
    "lua",    # inside "value", "formula"
    "nim",    # inside "minimum", "dynamic"
    "zig",    # inside "blazing"
    "elk",    # inside "welk" — rare but safe
    "ion",    # inside "version", "function"
    "sol",    # inside "isolation", "console"
    "rust",   # "rust" is fine as substring but keep boundary for "trust", "robust"
})


def tokenize(text: str) -> list[str]:
    """
    Lowercase, remove punctuation, split on whitespace, strip stopwords,
    and return tokens with length > 2.
    """
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


def extract_years_from_text(text: str) -> float | None:
    """
    Find patterns like '5 years', '3+ years', '2-4 years' using regex.
    Returns the minimum numeric value found, or None if nothing matches.
    """
    # Order matters: range pattern first, then plus pattern, then plain
    patterns = [
        r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*\+?\s*years?",  # 2-4 years
        r"(\d+(?:\.\d+)?)\s*\+\s*years?",                              # 3+ years
        r"(\d+(?:\.\d+)?)\s*years?",                                   # 5 years
    ]

    found: list[float] = []

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # group(1) is always the lower/first number
            found.append(float(match.group(1)))

    return min(found) if found else None


def extract_skills_from_text(text: str) -> set[str]:
    """
    Case-insensitive match of TECH_SKILLS (including ML_SKILLS) against text.

    Strategy
    --------
    - Multi-word skills and most single-word skills: pure substring match.
      Fast and handles compound terms like "machine learning" naturally.
    - A small set of ambiguous short tokens (_WORD_BOUNDARY_SKILLS like "r",
      "go", "ray") use whole-word \\b regex to avoid false positives
      (e.g. "r" inside "pytorch", "go" inside "mongodb").

    Returns the set of matched canonical skill strings.
    """
    text_lower = text.lower()
    matched: set[str] = set()

    for skill in TECH_SKILLS:
        if skill in _WORD_BOUNDARY_SKILLS:
            # Whole-word boundary match for ambiguous short tokens
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                matched.add(skill)
        else:
            # Substring match — correct for multi-word and unambiguous skills
            if skill in text_lower:
                matched.add(skill)

    return matched


def compute_seniority_level(years: float, title: str) -> int:
    """
    Returns seniority as an integer:
        1 = Junior / Intern / Associate
        2 = Mid-level
        3 = Senior
        4 = Lead / Principal / Staff / Director / Head / Chief

    Title keywords take precedence; years are used as a tiebreaker /
    fallback when no strong title signal is found.
    """
    title_lower = title.lower()

    # Level-4 signals
    if any(kw in title_lower for kw in ("lead", "principal", "staff", "director", "head", "chief", "vp")):
        return 4

    # Level-3 signals
    if "senior" in title_lower or "sr." in title_lower or "sr " in title_lower:
        return 3

    # Level-1 signals
    if any(kw in title_lower for kw in ("junior", "jr.", "jr ", "intern", "associate", "entry")):
        return 1

    # No clear title signal — fall back to years of experience
    if years is None:
        return 2  # default to mid when no information available

    if years < 2:
        return 1
    if years < 5:
        return 2
    if years < 9:
        return 3
    return 4
