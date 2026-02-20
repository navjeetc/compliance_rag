#!/usr/bin/env python3
"""
Content Quality Analysis for Compliance Documents
==================================================

Uses LLM to systematically analyze compliance documents for:
- Information density and practical value
- Clarity and completeness
- Coverage of compliance topics
- Gaps in content
- Overall quality scoring

Adapted from RAG Accelerator course for compliance RAG project.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from tqdm import tqdm
import logging

# Try Google Gemini first, fallback to OpenAI
try:
    from google import genai
    from google.genai import types
    USE_GEMINI = True
except ImportError:
    from openai import AsyncOpenAI
    USE_GEMINI = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ComplianceContentAnalyzer:
    def __init__(self):
        if USE_GEMINI:
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
        else:
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        self.project_root = Path(__file__).resolve().parent.parent
        self.data_dir = self.project_root / "data" / "processed"
        self.output_dir = self.project_root / "analysis"
        self.output_dir.mkdir(exist_ok=True)
        
    async def analyze_file_content(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Analyze a single compliance document using LLM"""
        
        analysis_prompt = f"""
You are an expert compliance documentation analyst. Analyze this compliance document.

FILE: {file_path.name}
CONTENT LENGTH: {len(content)} characters

Analyze this file for:

1. **Information Density** (1-10): How much useful compliance information per section?
   - 10 = Every section provides critical compliance requirements
   - 5 = Mix of requirements and explanatory content
   - 1 = Mostly administrative or navigation content

2. **Practical Value** (1-10): How directly useful for compliance implementation?
   - 10 = Immediately actionable requirements with clear controls
   - 5 = Conceptual guidance that enables compliance
   - 1 = Pure theory or background information

3. **Clarity** (1-10): How well-written and understandable?
   - 10 = Crystal clear requirements, excellent structure
   - 5 = Generally clear but some ambiguous sections
   - 1 = Confusing, poorly structured, hard to interpret

4. **Completeness** (1-10): Does it fully cover its compliance domain?
   - 10 = Complete coverage with all controls and requirements
   - 5 = Covers basics but missing advanced requirements
   - 1 = Incomplete, leaves many compliance questions unanswered

5. **Redundancy** (1-10): How much does it duplicate other compliance content?
   - 10 = Highly redundant, mostly repeats other standards
   - 5 = Some overlap but adds unique requirements
   - 1 = Unique compliance content not found elsewhere

**CONTENT TO ANALYZE:**
{content[:4000]}{"..." if len(content) > 4000 else ""}

CRITICAL: Respond ONLY with valid JSON. Do not include any explanatory text before or after the JSON.
Do not use markdown code blocks. Output ONLY the raw JSON object in this exact format:
{{
  "analysis": {{
    "information_density": 8,
    "practical_value": 7,
    "clarity": 9,
    "completeness": 6,
    "redundancy": 3
  }},
  "key_compliance_areas": ["area1", "area2", "area3"],
  "valuable_sections": ["section1", "section2"],
  "missing_elements": ["missing1", "missing2"],
  "content_type": "policy|standard|guideline|framework|control_catalog",
  "target_audience": "auditor|security_engineer|compliance_analyst|all",
  "implementation_focus": true|false,
  "code_examples_present": true|false,
  "one_sentence_summary": "Brief summary of what this document covers"
}}
"""

        try:
            if USE_GEMINI:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=analysis_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=1000
                    )
                )
                result_text = response.text.strip()
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": analysis_prompt}],
                    temperature=0.1,
                    max_tokens=1000
                )
                result_text = response.choices[0].message.content.strip()
            
            # Clean up any markdown formatting and extract JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            # Try to find JSON object in the response
            result_text = result_text.strip()
            
            # Find the first { and last }
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                result_text = result_text[start_idx:end_idx+1]
            
            analysis = json.loads(result_text)
            
            # Calculate overall quality score
            scores = analysis["analysis"]
            # Redundancy is reverse scored (lower is better)
            redundancy_adjusted = 11 - scores["redundancy"]
            overall = (scores["information_density"] + scores["practical_value"] + 
                      scores["clarity"] + scores["completeness"] + redundancy_adjusted) / 5
            
            analysis["analysis"]["overall_quality"] = round(overall, 1)
            analysis["filename"] = file_path.name
            analysis["file_size"] = len(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path.name}: {str(e)}")
            return {
                "filename": file_path.name,
                "error": str(e),
                "analysis": {"overall_quality": 0}
            }

    async def analyze_all_files(self) -> List[Dict[str, Any]]:
        """Analyze all processed compliance documents"""
        
        all_analyses = []
        
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return all_analyses
        
        txt_files = list(self.data_dir.glob("*.txt"))
        logger.info(f"Found {len(txt_files)} processed compliance documents")
        
        for file_path in tqdm(txt_files, desc="Analyzing compliance documents"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if len(content.strip()) < 100:  # Skip very short files
                    logger.warning(f"Skipping {file_path.name} - too short")
                    continue
                    
                analysis = await self.analyze_file_content(file_path, content)
                analysis["source_directory"] = "processed"
                all_analyses.append(analysis)
                
                # Small delay to respect rate limits
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue
        
        return all_analyses

    def generate_analysis_report(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary report from all analyses"""
        
        valid_analyses = [a for a in analyses if "error" not in a]
        
        if not valid_analyses:
            return {"error": "No valid analyses generated"}
        
        # Calculate statistics
        quality_scores = [a["analysis"]["overall_quality"] for a in valid_analyses]
        
        # Group by quality tier
        high_quality = [a for a in valid_analyses if a["analysis"]["overall_quality"] >= 7.5]
        medium_quality = [a for a in valid_analyses if 5.0 <= a["analysis"]["overall_quality"] < 7.5]
        low_quality = [a for a in valid_analyses if a["analysis"]["overall_quality"] < 5.0]
        
        # Identify top files by category
        top_practical = sorted(valid_analyses, 
                             key=lambda x: x["analysis"]["practical_value"], reverse=True)
        top_complete = sorted(valid_analyses, 
                            key=lambda x: x["analysis"]["completeness"], reverse=True)
        
        # Content type distribution
        content_types = {}
        target_audiences = {}
        
        for analysis in valid_analyses:
            content_type = analysis.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
            audience = analysis.get("target_audience", "unknown")
            target_audiences[audience] = target_audiences.get(audience, 0) + 1
        
        report = {
            "summary": {
                "total_files_analyzed": len(valid_analyses),
                "average_quality_score": round(sum(quality_scores) / len(quality_scores), 2),
                "high_quality_files": len(high_quality),
                "medium_quality_files": len(medium_quality),
                "low_quality_files": len(low_quality)
            },
            "quality_tiers": {
                "high_quality": [{"filename": a["filename"], "score": a["analysis"]["overall_quality"]} 
                               for a in high_quality],
                "medium_quality": [{"filename": a["filename"], "score": a["analysis"]["overall_quality"]} 
                                 for a in medium_quality],
                "low_quality": [{"filename": a["filename"], "score": a["analysis"]["overall_quality"]} 
                              for a in low_quality]
            },
            "top_by_category": {
                "most_practical": [{"filename": a["filename"], "score": a["analysis"]["practical_value"]} 
                                 for a in top_practical],
                "most_complete": [{"filename": a["filename"], "score": a["analysis"]["completeness"]} 
                                for a in top_complete]
            },
            "content_distribution": {
                "by_type": content_types,
                "by_audience": target_audiences
            },
            "recommendations": {
                "files_to_prioritize": [a["filename"] for a in high_quality],
                "files_needing_review": [a["filename"] for a in low_quality if a["analysis"]["practical_value"] >= 6],
                "files_to_supplement": [a["filename"] for a in valid_analyses if len(a.get("missing_elements", [])) > 2]
            }
        }
        
        return report

    async def run_analysis(self):
        """Main analysis workflow"""
        
        logger.info("Starting comprehensive compliance content analysis...")
        logger.info(f"Using {'Google Gemini' if USE_GEMINI else 'OpenAI'} for analysis")
        
        # Analyze all files
        analyses = await self.analyze_all_files()
        
        # Generate report
        report = self.generate_analysis_report(analyses)
        
        # Save detailed results
        output_file = self.output_dir / "content_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(analyses, f, indent=2)
        
        logger.info(f"Detailed analysis saved to {output_file}")
        
        # Save summary report
        report_file = self.output_dir / "analysis_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Analysis report saved to {report_file}")
        
        # Print summary
        if "error" not in report:
            print(f"\n🎯 ANALYSIS COMPLETE")
            print(f"📊 Files analyzed: {report['summary']['total_files_analyzed']}")
            print(f"📈 Average quality: {report['summary']['average_quality_score']}/10")
            print(f"🟢 High quality: {report['summary']['high_quality_files']} files")
            print(f"🟡 Medium quality: {report['summary']['medium_quality_files']} files")
            print(f"🔴 Low quality: {report['summary']['low_quality_files']} files")
            print(f"\n✅ Results saved to {self.output_dir}/")
        
        return analyses, report

async def main():
    """Run the content analysis"""
    
    analyzer = ComplianceContentAnalyzer()
    await analyzer.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
