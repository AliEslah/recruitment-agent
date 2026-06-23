# Evaluation Quality Report

- Timestamp: 2026-06-23T11:12:50+00:00
- Model: qwen/qwen3-4b-2507
- Stages run: job_calibration, resume_parsing, candidate_scoring, interview_planning, interview_evaluation, final_scorecard
- Status: passed
- Finished at: 2026-06-23T11:18:27+00:00
- Runtime seconds: 337.0
- Summary score: 1.0
- Passed/failed: 42/0
- Fixture data policy: Synthetic fixtures only. Reports must not contain real candidate data, raw tokens, OTPs, secrets, or private local paths.

## LLM Call Usage
- Total calls: 49
- Cache hits: 35
- Uncached calls: 14

## Prompt Versions
- job_calibration: job-calibration-v2
- resume_parsing: resume-parsing-v3
- candidate_scoring: candidate-scoring-v6
- interview_planning: interview-planning-v2
- interview_evaluation: interview-evaluation-v7
- final_scorecard: final-scorecard-v2

## Role Results
- PASS backend_engineer / job_calibration
- PASS backend_engineer / engineering-candidate-001 / resume_parsing
- PASS backend_engineer / engineering-candidate-001 / candidate_scoring
  - warning: risks_empty - Risk list is empty.
- PASS backend_engineer / engineering-candidate-001 / interview_planning
- PASS backend_engineer / engineering-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'Python' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'FastAPI' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'PostgreSQL' was not validated in transcript.
- PASS backend_engineer / engineering-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'Python' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'FastAPI' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'PostgreSQL' was not validated in transcript.
- PASS customer_support_specialist / job_calibration
- PASS customer_support_specialist / support-candidate-001 / resume_parsing
- PASS customer_support_specialist / support-candidate-001 / candidate_scoring
  - warning: recommendation_score_mismatch - Recommendation 'POSSIBLE_MATCH' does not match score-based band 'STRONG_MATCH'.
  - warning: expected_recommendation_band_mismatch - Recommendation 'POSSIBLE_MATCH' differs from fixture expected band 'STRONG_MATCH'.
- PASS customer_support_specialist / support-candidate-001 / interview_planning
- PASS customer_support_specialist / support-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'Zendesk' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'help center documentation' was not validated in transcript.
- PASS customer_support_specialist / support-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'Zendesk' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'help center documentation' was not validated in transcript.
- PASS finance_analyst / job_calibration
- PASS finance_analyst / finance-candidate-001 / resume_parsing
- PASS finance_analyst / finance-candidate-001 / candidate_scoring
- PASS finance_analyst / finance-candidate-001 / interview_planning
- PASS finance_analyst / finance-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'Excel modeling' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'forecasting' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'stakeholder reporting' was not validated in transcript.
- PASS finance_analyst / finance-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'Excel modeling' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'forecasting' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'stakeholder reporting' was not validated in transcript.
- PASS hr_generalist / job_calibration
- PASS hr_generalist / hr-candidate-001 / resume_parsing
- PASS hr_generalist / hr-candidate-001 / candidate_scoring
  - warning: recommendation_score_mismatch - Recommendation 'POSSIBLE_MATCH' does not match score-based band 'STRONG_MATCH'.
- PASS hr_generalist / hr-candidate-001 / interview_planning
- PASS hr_generalist / hr-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'onboarding' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'benefits coordination' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'policy documentation' was not validated in transcript.
- PASS hr_generalist / hr-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'onboarding' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'benefits coordination' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'policy documentation' was not validated in transcript.
- PASS marketing_specialist / job_calibration
- PASS marketing_specialist / marketing-candidate-001 / resume_parsing
  - warning: unsupported_profile_claim - Parsed skills item has low source overlap: copywriting
- PASS marketing_specialist / marketing-candidate-001 / candidate_scoring
  - warning: risks_empty - Risk list is empty.
  - warning: expected_recommendation_band_mismatch - Recommendation 'STRONG_MATCH' differs from fixture expected band 'POSSIBLE_MATCH'.
- PASS marketing_specialist / marketing-candidate-001 / interview_planning
- PASS marketing_specialist / marketing-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'email campaigns' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'copywriting' was not validated in transcript.
- PASS marketing_specialist / marketing-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'email campaigns' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'copywriting' was not validated in transcript.
- PASS operations_manager / job_calibration
- PASS operations_manager / operations-candidate-001 / resume_parsing
- PASS operations_manager / operations-candidate-001 / candidate_scoring
  - warning: expected_recommendation_band_mismatch - Recommendation 'STRONG_MATCH' differs from fixture expected band 'POSSIBLE_MATCH'.
- PASS operations_manager / operations-candidate-001 / interview_planning
- PASS operations_manager / operations-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'team leadership' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'fulfillment operations' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'Excel reporting' was not validated in transcript.
- PASS operations_manager / operations-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'team leadership' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'fulfillment operations' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'Excel reporting' was not validated in transcript.
- PASS sales_account_executive / job_calibration
- PASS sales_account_executive / sales-candidate-001 / resume_parsing
- PASS sales_account_executive / sales-candidate-001 / candidate_scoring
- PASS sales_account_executive / sales-candidate-001 / interview_planning
- PASS sales_account_executive / sales-candidate-001 / interview_evaluation
  - consistency: needs_validation - Resume skill 'negotiation' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'pipeline generation' was not validated in transcript.
- PASS sales_account_executive / sales-candidate-001 / final_scorecard
  - consistency: needs_validation - Resume skill 'negotiation' was not validated in transcript.
  - consistency: needs_validation - Resume skill 'pipeline generation' was not validated in transcript.

## Quality Warnings
- Total warning/check items: 104

## Recommended Prompt/Schema Fixes
- Clarify score-to-band calibration thresholds in candidate scoring prompts.
