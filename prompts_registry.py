#!/usr/bin/env python3
from shared.logging_config import get_logger

logger = get_logger(__name__)

"""
Prompts Registry with MLflow Integration
Centralized prompt management with versioning and tracking
"""

import mlflow
from typing import Dict, Optional
from datetime import datetime
from country_config import get_country_config, get_special_instructions
from config import MLFLOW_PROD_EXPERIMENT_PATH


class PromptsRegistry:
    """
    Centralized registry for all prompts used in the SuperAdvisor Agent.
    Supports MLflow prompt logging and versioning.
    """
    
    def __init__(self, experiment_name: Optional[str] = None, enable_mlflow: bool = True):
        """
        Initialize prompts registry with optional MLflow tracking.
        
        Args:
            experiment_name: MLflow experiment name for prompt tracking
            enable_mlflow: Enable/disable MLflow integration
        """
        self.enable_mlflow = enable_mlflow
        # ✅ Use MLFLOW_PROD_EXPERIMENT_PATH from config.py instead of hardcoded default
        self.experiment_name = experiment_name or MLFLOW_PROD_EXPERIMENT_PATH
        self.prompt_version = "1.0.0"
        self.last_registered = None
        
        if self.enable_mlflow:
            try:
                mlflow.set_experiment(self.experiment_name)
                logger.info(f"✅ MLflow prompts registry initialized: {self.experiment_name}")
            except Exception as e:
                logger.info(f"⚠️ MLflow initialization warning: {e}")
                self.enable_mlflow = False
    
    def get_system_prompt(self, country: str) -> str:
        """
        Get the main system prompt for response synthesis.
        
        Args:
            country: Country code (AU, US, UK, IN)
            
        Returns:
            Complete system prompt string
        """
        # Get country-specific configuration
        config = get_country_config(country)
        special_instructions = get_special_instructions(country) or ""
        
        prompt = f"""You are {config.advisor_title}, an expert retirement advisor.

{config.regulatory_context}

INSTRUCTIONS:
1. Answer the user's question directly and clearly
2. Use specific numbers from the member profile AND tool results
3. Refer to retirement accounts as "{config.retirement_account_term}"
4. Refer to balances as "{config.balance_term}"
5. Use simple language - no emoji or special characters
6. Format with clear sections separated by blank lines
7. Keep recommendations practical and easy to understand
8. Discuss all monetary values in {config.currency_symbol}{config.currency}

{special_instructions}

RESPONSE FORMAT:
Start with a direct answer to their question.
Then explain key considerations.
End with a clear recommendation.

Use this structure for your response:

- Direct Answer: [answer their specific question]
- Key Considerations: [list 2-3 important points]
- Recommendation: [actionable advice]

IMPORTANT RULES:
- Do NOT use emoji (no emojis)
- Do NOT use special characters or symbols
- Do NOT use asterisks for emphasis
- DO separate numbers and words with spaces
- DO use simple, clear English
- DO keep sentences short
- If the user asked "How much can I withdraw?" WITHOUT specifying an amount:
  Answer generally about withdrawal rules, not specific calculations
- Only calculate specific amounts if user gave a specific amount
- Don't make up withdrawal amounts the user didn't ask about
- CRITICAL FOR AUSTRALIA: When asked about "unrestricted access" or "access without restrictions":
  Answer: "preservation age (60) upon retirement" NOT "age 65"
  Age 65 is the unrestricted non-preserved age, but unrestricted access begins at preservation age (60) upon retirement

Example format:

Answer: You can withdraw up to 100,000 {config.currency}.

Key Considerations:
- Your balance needs to last your retirement
- You have dependents to consider  
- Your other assets provide financial buffer

Recommendation: Consider withdrawing only what you need now.
"""
        return prompt
    
    def get_country_specific_note(self, country: str) -> str:
        """
        Get country-specific notes (if any).
        
        DEPRECATED: Use country_config.get_special_instructions() instead.
        Kept for backward compatibility.
        """
        return get_special_instructions(country) or ""
    
    def get_off_topic_decline_message(self, real_name: str, classification: str) -> str:
        """
        Get the off-topic decline message.
        
        Args:
            real_name: Member's real name
            classification: Classification result from ai_classify
            
        Returns:
            Polite decline message
        """
        return f"""Hi {real_name},

Thank you for reaching out! I noticed your question appears to be outside my expertise as it is {classification.replace("_", " ")}. I'm a Superannuation Advisor, and I specialize exclusively in retirement and superannuation planning.

I can help you with:
• Retirement savings (EPF, NPS, Superannuation, 401(k), Pensions)
• Withdrawal rules and eligibility
• Tax implications on retirement withdrawals
• Retirement benefit calculations
• Long-term retirement projections

Is there anything about your retirement planning I can help you with today?"""
    
    def get_retirement_keywords(self) -> list:
        """
        Get comprehensive list of retirement keywords for fast-path classification.
        
        Returns:
            List of retirement-related keywords
        """
        return [
            # US retirement accounts
            '401k', '401(k)', 'ira', 'roth', 'roth ira', 'traditional ira', 
            'tsp', 'thrift savings', 'simple ira', 'sep ira',
            
            # Australia retirement
            'super', 'superannuation', 'smsf', 'concessional', 'non-concessional',
            'preservation age', 'transition to retirement', 'ttr', 
            'self-managed super', 'industry super',
            
            # India retirement
            'epf', 'pf', 'ppf', 'nps', 'eps', 'vpf', 'provident fund',
            'national pension', 'employees provident', 'voluntary provident',
            
            # UK retirement - Pensions
            'sipp', 'lgps', 'workplace pension', 'occupational pension', 
            'state pension', 'personal pension', 'defined benefit', 
            'defined contribution', 'final salary', 'db pension', 'dc pension',
            
            # UK retirement - Savings accounts
            'lisa', 'lifetime isa', 'pension pot', 'pension drawdown',
            'stocks and shares isa', 'pension commencement lump sum', 'pcls',
            
            # UK regulatory/tax terms
            'salary sacrifice', 'auto-enrolment', 'auto enrolment',
            'annual allowance', 'lifetime allowance', 'tax relief',
            'higher rate tax relief', 'pension credit',
            
            # Universal retirement terms
            'retirement', 'retire', 'retiring', 'pension', 'pensioner',
            'contribution', 'contributions', 'withdraw', 'withdrawal',
            'early access', 'hardship', 'social security', 'centrelink',
            'age pension', 'retirement age', 'retirement income',
            'retirement planning', 'retirement savings', 'retirement benefit'
        ]
    
    def get_retirement_archetypes(self) -> list:
        """
        Get archetype retirement queries for embedding-based classification.
        These represent canonical examples of on-topic queries.
        
        Returns:
            List of retirement query archetypes
        """
        return [
            # Withdrawal queries
            "Can I withdraw money from my superannuation account?",
            "How do I access my 401k early?",
            "What are the rules for EPF withdrawal?",
            "Am I allowed to take money out of my pension?",
            
            # Tax queries
            "How much tax will I pay on my retirement withdrawal?",
            "What are the tax implications of accessing my super?",
            "Will I be taxed on my 401k distribution?",
            "What is the tax rate on NPS withdrawals?",
            
            # Benefit queries
            "What pension benefits am I entitled to?",
            "How much will I receive from Social Security?",
            "What is my Centrelink age pension payment?",
            "How is my EPS monthly pension calculated?",
            
            # Projection queries
            "How much will my retirement savings grow over 10 years?",
            "What will my superannuation balance be at retirement?",
            "Can you project my 401k balance at age 65?",
            "How much will my EPF corpus be after 20 years?",
            
            # Contribution queries
            "How much can I contribute to my IRA this year?",
            "What are the superannuation contribution limits?",
            "Can I make voluntary contributions to EPF?",
            "What is the maximum SIPP contribution?",
            
            # Eligibility queries
            "When can I access my retirement savings?",
            "What is my preservation age for superannuation?",
            "Am I eligible for early retirement withdrawal?",
            "Can I access my pension at age 55?",
            
            # Planning queries
            "What should I do with my retirement savings?",
            "Is it a good time to access my superannuation?",
            "Should I consolidate my retirement accounts?",
            "How can I maximize my retirement income?",
        ]
    
    def get_off_topic_archetypes(self) -> list:
        """
        Get archetype off-topic queries for embedding-based classification.
        These represent canonical examples of off-topic queries.
        
        Returns:
            List of off-topic query archetypes
        """
        return [
            # General knowledge
            "What is the weather like today?",
            "What is the capital of France?",
            "Who won the game last night?",
            "Tell me about the history of Rome",
            
            # Entertainment
            "Tell me a joke",
            "What movies are playing?",
            "Who is your favorite singer?",
            "What TV shows should I watch?",
            
            # Cooking and food
            "How do I cook pasta?",
            "What is a good recipe for soup?",
            "Where can I find a restaurant?",
            "What should I eat for dinner?",
            
            # Technical support
            "I forgot my password, can you help?",
            "How do I reset my login?",
            "My account is locked",
            "I can't access the website",
            
            # Social events (NOT financial)
            "What should I get for a retirement party gift?",
            "How to plan a retirement party?",
            "Retirement party decoration ideas",
            "Funny retirement party games",
            
            # General finance (non-retirement)
            "How do I apply for a mortgage?",
            "What credit card should I get?",
            "How do I save for a vacation?",
            "Should I invest in cryptocurrency?",
            
            # Other topics
            "How do I fix my car?",
            "What is the best phone to buy?",
            "How do I book a flight?",
            "What exercises should I do?",
        ]
    
    def get_ai_classify_query_template(self, user_query: str) -> str:
        """
        Get the SQL query template for ai_classify.
        
        Args:
            user_query: User's query (will be escaped)
            
        Returns:
            SQL query string
        """
        escaped_query = user_query.replace("'", "''")
        
        return f"""
        SELECT ai_classify(
            '{escaped_query}',
            ARRAY(
                'retirement_planning', 'superannuation_withdrawal', 'pension_benefits',
                'contribution_rules', 'tax_questions', 'early_access', 'early_withdrawal',
                'hardship_withdrawal', 'account_access',
                '401k', '401(k)', 'IRA', 'Roth', 'TSP',
                'EPF', 'PF', 'VPF', 'EPS', 'NPS', 'PPF',
                'SIPP', 'LGPS', 'LISA',
                'off_topic'
            )
        ) AS topic_classification
        """
    
    def get_validation_prompt_template(self) -> str:
        """
        Get the validation prompt template for LLM Judge.
        
        Returns:
            Validation prompt template with placeholders
        """
        return """FAIR VALIDATION TASK: Analyze this retirement advice response thoroughly.

USER'S EXACT QUESTION: "{user_query}"

{member_info}

{tool_info}

{tool_status}

AI GENERATED RESPONSE (FULL {response_length} CHARACTERS - REVIEW ENTIRE RESPONSE BELOW):
{response_text}

SYSTEM NOTE:
- Off-topic queries (vacation, food, general life advice) are filtered BEFORE reaching validation using ai_classify
- If you see a polite decline for non-retirement topics, this is CORRECT behavior and should PASS
- Only retirement-related queries should have tool calculations and detailed answers

VALIDATION CRITERIA (BE FAIR - REVIEW ENTIRE RESPONSE):

0. **TOOL EXECUTION**: If ANY tools failed (see above), response MUST fail validation with CRITICAL severity

0.5. **SCOPE ADHERENCE**: 
   - If question is about retirement/pensions/superannuation → response must answer it
   - If question is OFF-TOPIC (vacation, food, general advice) → politely declining is CORRECT
   - A polite decline that redirects to retirement topics should PASS validation
   - Only fail if response answers off-topic questions OR ignores in-scope retirement questions

1. **QUESTION ANSWERING**: Does the response adequately address the user's retirement question (IF in scope)?

2. **SPECIFICITY**: Does it provide specific numbers where appropriate?

3. **DATA USAGE**: Does it reference member data appropriately? (IMPORTANT: Using member's profile data is CORRECT, not an error)

4. **COMPLETENESS**: Does it address main aspects of the question?

5. **ACCURACY**: Are statements consistent with retirement rules?

IMPORTANT CLARIFICATIONS:
- The member profile ABOVE contains the member's actual data (age, balance, country, etc)
- The tool calculations ABOVE show the actual results from regulatory calculators
- Using this data in the response is CORRECT and EXPECTED
- If response says "you are age 52" and profile shows age=52, that's DATA USAGE, NOT INVENTION
- If response says "your balance is $X" and profile shows balance=$X, that's CORRECT, NOT MADE UP
- If response uses numbers from tool calculations, that's CORRECT, NOT INVENTED
- Only flag as "invented data" if response contains numbers/facts NOT in the member profile OR tool results

SEVERITY GUIDELINES - BE FAIR:
- CRITICAL: Only if major factual error that contradicts member's actual data OR if tools failed
- HIGH: If main retirement question completely unanswered (when it should be)
- MODERATE: If some details missing but main answer is there
- LOW: Minor style or formatting issues

RESPONSE PASSES if:
✓ All tools executed successfully (no errors)
✓ Answers the main retirement question asked (if in scope) OR politely declines if off-topic
✓ Uses member's provided profile data appropriately
✓ Uses tool calculation results appropriately
✓ Provides accurate information about retirement rules
✓ References member's age/balance when relevant
✓ Stays within retirement advisory scope

RESPONSE FAILS only if:
✗ Any calculation tools failed to execute
✗ Completely misses answering an IN-SCOPE retirement question
✗ Answers off-topic questions outside the retirement domain
✗ Contains major factual errors about retirement rules
✗ Uses data that contradicts the provided member profile or tool results

CRITICAL: If the response passes all criteria, the "violations" array MUST be empty [].
Only include violations if the response actually FAILS validation.
Keep violations to a MAXIMUM of 2-3 significant issues.

JSON FORMAT REQUIREMENTS - KEEP CONCISE:
- Each violation "detail" must be ONE SENTENCE MAX
- Each violation "evidence" must be ONE SHORT QUOTE MAX
- "reasoning" must be ONE SENTENCE MAX
- If passed=true, violations MUST be an empty array []

Respond with ONLY VALID, COMPLETE JSON (no other text):
{{
  "passed": true/false,
  "confidence": 0.0-1.0,
  "violations": [
    {{
      "code": "SHORTCODE",
      "severity": "CRITICAL/HIGH/MODERATE/LOW",
      "detail": "One sentence.",
      "evidence": "Short quote."
    }}
  ],
  "reasoning": "One sentence explanation."
}}"""
    
    def get_member_profile_format(self, member_profile: dict) -> str:
        """
        Format member profile for validation prompt.
        
        Args:
            member_profile: Member profile dictionary
            
        Returns:
            Formatted member profile string
        """
        if not member_profile:
            return "NO MEMBER PROFILE PROVIDED"
        
        return f"""
MEMBER PROFILE (for reference):
- Member ID: {member_profile.get('member_id', 'N/A')}
- Name: {member_profile.get('name', 'N/A')} (anonymized during processing)
- Age: {member_profile.get('age', 'N/A')}
- Country: {member_profile.get('country', 'N/A')}
- Preservation Age: {member_profile.get('preservation_age', 'N/A')}
- Employment Status: {member_profile.get('employment_status', 'N/A')}
- Super Balance: {member_profile.get('super_balance', 'N/A')}
- Other Assets: {member_profile.get('other_assets', 'N/A')}
- Dependents: {member_profile.get('dependents', 'N/A')}
"""
    
    def get_tool_output_format(self, tool_output: dict) -> tuple:
        """
        Format tool output for validation prompt.
        
        Args:
            tool_output: Tool output dictionary
            
        Returns:
            Tuple of (tool_info_string, tool_status_string, tool_failures_list)
        """
        if not tool_output:
            return "NO TOOL CALCULATIONS PERFORMED", "✅ No tools were required", []
        
        tool_lines = ["TOOL CALCULATIONS & RESULTS (what the planning LLM received):"]
        tool_failures = []
        
        for tool_name, tool_result in tool_output.items():
            if "error" in tool_result:
                tool_lines.append(f"\n❌ Tool '{tool_name}' failed: {tool_result['error']}")
                tool_failures.append(f"- {tool_name}: {tool_result['error']}")
            else:
                tool_lines.append(f"\n✓ Tool: {tool_result.get('tool_name', tool_name)}")
                tool_lines.append(f"  UC Function: {tool_result.get('uc_function', 'N/A')}")
                tool_lines.append(f"  Authority: {tool_result.get('authority', 'N/A')}")
                tool_lines.append(f"  Calculation Result: {tool_result.get('calculation', 'N/A')}")
                if tool_result.get('citations'):
                    tool_lines.append(f"  Citations: {len(tool_result['citations'])} regulatory references")
        
        tool_info = "\n".join(tool_lines)
        
        # Tool status indicator
        if tool_failures:
            tool_status = f"❌ TOOL FAILURES DETECTED:\n" + "\n".join(tool_failures)
        else:
            tool_status = "✅ All tools executed successfully"
        
        return tool_info, tool_status, tool_failures
    
    def get_citation_query_template(self, country: str, tools_used: list) -> str:
        """
        Get the SQL query template for fetching citations.
        
        Args:
            country: Country code (uppercase)
            tools_used: List of tools used in query processing
            
        Returns:
            SQL query string
        """
        tool_conditions = [f"tool_type = '{tool}'" for tool in tools_used]
        where_clause = " OR ".join(tool_conditions)
        
        return f"""SELECT DISTINCT
  citation_id, country, authority, regulation_name,
  regulation_code, source_url, description
FROM super_advisory_demo.member_data.citation_registry
WHERE country = '{country}'
  AND ({where_clause})
ORDER BY citation_id"""
    
    def register_prompts_with_mlflow(self, run_name: Optional[str] = None):
        """
        Register all prompts with MLflow for versioning and tracking.
        
        Args:
            run_name: Optional name for the MLflow run
        """
        if not self.enable_mlflow:
            logger.info("⚠️ MLflow disabled, skipping prompt registration")
            return
        
        try:
            run_name = run_name or f"prompts_v{self.prompt_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name) as run:
                # Log prompt metadata
                mlflow.log_param("prompt_version", self.prompt_version)
                mlflow.log_param("registration_time", datetime.now().isoformat())
                
                # Log all prompts as artifacts
                prompts_dict = {
                    "system_prompt_template": self.get_system_prompt(country="{country}"),
                    "off_topic_decline_template": self.get_off_topic_decline_message(
                        real_name="{real_name}", 
                        classification="{classification}"
                    ),
                    "retirement_keywords": self.get_retirement_keywords(),
                    "ai_classify_template": self.get_ai_classify_query_template(user_query="{user_query}"),
                    "citation_query_template": self.get_citation_query_template(
                        country="{country}", 
                        tools_used=["{tool1}", "{tool2}"]
                    )
                }
                
                # Add validation prompts
                prompts_dict["validation_prompt_template"] = self.get_validation_prompt_template()
                
                # Log each prompt as a parameter
                for prompt_name, prompt_content in prompts_dict.items():
                    if isinstance(prompt_content, str):
                        # Log as text artifact
                        mlflow.log_text(prompt_content, f"prompts/{prompt_name}.txt")
                    else:
                        # Log as JSON for lists/dicts
                        import json
                        mlflow.log_text(json.dumps(prompt_content, indent=2), 
                                       f"prompts/{prompt_name}.json")
                
                # Log metrics
                mlflow.log_metric("total_prompts", len(prompts_dict))
                mlflow.log_metric("retirement_keywords_count", len(self.get_retirement_keywords()))
                
                self.last_registered = run.info.run_id
                logger.info(f"✅ Prompts registered with MLflow - Run ID: {run.info.run_id}")
                logger.info(f"   Version: {self.prompt_version}")
                logger.info(f"   Total prompts: {len(prompts_dict)}")
                
                return run.info.run_id
                
        except Exception as e:
            logger.info(f"❌ Error registering prompts with MLflow: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_prompt_metadata(self) -> Dict:
        """Get metadata about registered prompts."""
        return {
            "version": self.prompt_version,
            "last_registered": self.last_registered,
            "mlflow_enabled": self.enable_mlflow,
            "experiment_name": self.experiment_name,
            "total_keywords": len(self.get_retirement_keywords())
        }


# Singleton instance for global access
_global_registry = None

def get_prompts_registry(experiment_name: Optional[str] = None, 
                        enable_mlflow: bool = True) -> PromptsRegistry:
    """
    Get or create the global prompts registry instance.
    
    Args:
        experiment_name: MLflow experiment name
        enable_mlflow: Enable/disable MLflow integration
        
    Returns:
        PromptsRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = PromptsRegistry(experiment_name=experiment_name, 
                                          enable_mlflow=enable_mlflow)
    
    return _global_registry


# Convenience function for immediate registration
def register_prompts_now(experiment_name: Optional[str] = None, 
                        run_name: Optional[str] = None):
    """
    Convenience function to immediately register prompts with MLflow.
    
    Args:
        experiment_name: MLflow experiment name
        run_name: MLflow run name
    """
    registry = get_prompts_registry(experiment_name=experiment_name)
    return registry.register_prompts_with_mlflow(run_name=run_name)


if __name__ == "__main__":
    # Test registration when run directly
    logger.info("=" * 70)
    logger.info("Prompts Registry - MLflow Registration")
    logger.info("=" * 70)
    
    registry = PromptsRegistry(enable_mlflow=True)
    
    logger.info("\n📋 Prompt Metadata:")
    metadata = registry.get_prompt_metadata()
    for key, value in metadata.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n🚀 Registering prompts with MLflow...")
    run_id = registry.register_prompts_with_mlflow()
    
    if run_id:
        logger.info(f"\n✅ Success! Run ID: {run_id}")
    else:
        logger.info("\n⚠️ Registration completed with warnings")
    
    logger.info("\n" + "=" * 70)

