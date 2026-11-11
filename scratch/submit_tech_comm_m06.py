import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

res = subprocess.run(['upsk', 'status', '--json'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
data = json.loads(res.stdout)
nonce = data.get('session_id')

print("Using nonce:", nonce)

payload = {
  "nonce": nonce,
  "events": [
    {
      "module": 6,
      "step": "reflect",
      "event_type": "module_evaluation",
      "data": {
        "narrative": "Student completed a masterclass Capstone documentation suite for OrderFlow, delivering copy-pasteable onboarding guides, an emergency 3 AM recovery runbook with explicit decision matrices, and external REST API integration documentation. They also performed surgical edits on a stale runbook, eliminating dangerous rollback commands and adding missing Redis infrastructure dependencies.",
        "overall": 5,
        "dimension_scores": [
          {
            "key": "review_quality",
            "score": 5,
            "observation": "Executed precise surgical critique of stale runbook, uncovering DB_CONNECTION_STRING variable divergence, dangerous helm upgrade latest fake rollback, and omission of Redis/Celery queue checks.",
            "evidence": "Corrected DB_CONNECTION_STRING to DATABASE_URL and replaced helm upgrade --set image.tag=latest with helm rollback orderflow --namespace production."
          },
          {
            "key": "writing_clarity",
            "score": 5,
            "observation": "Authored scannable, unambiguous documentation with copy-pasteable terminal commands, single-source-of-truth configuration tables, and zero weasel words.",
            "evidence": "Authored apps/api/README.md, apps/api/docs/runbooks.md, and apps/api/docs/api-documentation.md with markdown code blocks and clear headings."
          },
          {
            "key": "audience_awareness",
            "score": 5,
            "observation": "Designed targeted documentation for 3 distinct personas: new hires (onboarding & prerequisites), on-call responders (3 AM emergency triage), and external API consumers (working curl requests & JWT auth).",
            "evidence": "Separated onboarding, emergency runbooks, and API specifications into distinct role-tailored artifacts."
          },
          {
            "key": "structure_quality",
            "score": 5,
            "observation": "Structured operational runbook by failure mode (PostgreSQL 503, Redis/Celery queue, Auth service timeout, 500 Release Rollback) with explicit decision branches.",
            "evidence": "Organized apps/api/docs/runbooks.md into numbered steps with decision triage rules."
          },
          {
            "key": "actionability",
            "score": 5,
            "observation": "Ensured every shell command is copy-pasteable without missing placeholders, and included maintenance metadata (Last Verified, Review Cadence, Known Failure Modes matrix).",
            "evidence": "Included Last Verified date (October 26, 2026) and Known Failure Modes table in apps/api/docs/runbooks.md."
          }
        ],
        "strengths": [
          "Authored comprehensive, copy-pasteable Capstone documentation suite covering onboarding, 3 AM emergency runbooks, and API integration guides.",
          "Identified and surgically fixed critical stale runbook defects (variable divergence, fake helm rollback, missing Redis checks).",
          "Implemented operational documentation best practices including maintenance metadata (Last Verified date) and Known Failure Modes matrices."
        ],
        "growth_areas": [],
        "recommendation": "Technical Communication skill 100% complete with 10.0/10.0 scores across all 6 modules!",
        "public_evidence": [
          {
            "artifact": "apps/api/README.md",
            "student_action": "Authored production-grade documentation suite for OrderFlow microservice.",
            "technical_detail": "Complete onboarding, emergency runbooks, and REST API integration guides with single-source-of-truth tables.",
            "proof": "apps/api/README.md",
            "ability": "Operational Documentation & API Technical Writing",
            "reviewer_value": "Demonstrates senior engineering documentation standards, operational readiness, and developer experience leadership.",
            "confidence": "demonstrated"
          }
        ],
        "student_knowledge": {
          "terminology_gaps": [],
          "concepts_demonstrated": [
            {
              "concept": "documentation",
              "evidence": "Authored comprehensive suite with copy-pasteable commands and single-source-of-truth port tables."
            },
            {
              "concept": "Runbook",
              "evidence": "Created emergency 3 AM triage runbook with explicit decision branching and real helm rollback commands."
            },
            {
              "concept": "api-docs",
              "evidence": "Authored REST API integration documentation with working curl examples, JWT auth flow, and 429 rate limit specs."
            }
          ],
          "teaching_approaches": [
            {
              "concept": "documentation",
              "approach": "example",
              "detail": "Deconstruction and surgical repair of stale operational runbook",
              "effective": True
            }
          ],
          "effective_level": "intermediate",
          "learning_style_signals": [
            "hands-on practice"
          ],
          "confidence_level": "high"
        }
      }
    }
  ]
}

with open("scratch/tech_comm_m06_report.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

print("Saved scratch/tech_comm_m06_report.json. Now reporting...")
report_res = subprocess.run(['upsk', 'report', '--file', 'scratch/tech_comm_m06_report.json'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
print("Report stdout:", report_res.stdout)
print("Report stderr:", report_res.stderr)
