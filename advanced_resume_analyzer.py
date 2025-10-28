#!/usr/bin/env python3
"""
高级简历分析器 - 深度解析、ATS优化、STAR强化
"""

import asyncio
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from loguru import logger

@dataclass
class QuantifiedAchievement:
    """量化成就"""
    original_text: str
    metrics: List[str]  # 提取的数字指标
    impact_type: str    # efficiency, cost, revenue, performance, etc.
    suggested_rewrite: str

@dataclass
class SkillExtraction:
    """技能提取"""
    technical_skills: List[str]
    soft_skills: List[str]
    tools_and_platforms: List[str]
    certifications: List[str]
    programming_languages: List[str]
    frameworks: List[str]

@dataclass
class ExperienceAnalysis:
    """经验分析"""
    situation: str
    task: str
    action: str
    result: str
    star_completeness: float  # 0-1分数
    missing_elements: List[str]
    quantified_achievements: List[QuantifiedAchievement]
    relevant_keywords: List[str]

@dataclass
class ResumeAnalysisResult:
    """简历分析结果"""
    basic_info: Dict[str, Any]
    skill_extraction: SkillExtraction
    experience_analyses: List[ExperienceAnalysis]
    ats_score: float
    ats_feedback: List[str]
    optimization_suggestions: List[str]
    missing_keywords: List[str]
    confidence_scores: Dict[str, float]

class AdvancedResumeAnalyzer:
    """高级简历分析器"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        
        # 技能关键词库
        self.skill_patterns = {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql'
            ],
            'frameworks': [
                'react', 'vue', 'angular', 'django', 'flask', 'spring', 'nodejs',
                'express', 'fastapi', 'laravel', 'rails', 'asp.net'
            ],
            'tools': [
                'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'git',
                'jira', 'slack', 'figma', 'sketch', 'photoshop'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'oracle', 'sqlite', 'cassandra', 'dynamodb'
            ]
        }
        
        # 量化指标模式
        self.quantification_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',  # 百分比
            r'(\d+(?:,\d+)*)\s*(?:users?|customers?|clients?)',  # 用户数
            r'\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|k|thousand)?',  # 金额
            r'(\d+(?:,\d+)*)\s*(?:hours?|days?|weeks?|months?)',  # 时间
            r'(\d+(?:,\d+)*)\s*(?:projects?|tasks?|features?)',  # 项目数
        ]
    
    async def analyze_resume_comprehensive(self, resume_text: str, 
                                         target_jd: Optional[str] = None) -> ResumeAnalysisResult:
        """综合分析简历"""
        logger.info("🔍 开始综合简历分析...")
        
        # 1. 深度信息提取
        basic_info = await self._extract_detailed_info(resume_text)
        
        # 2. 技能深度分析
        skill_extraction = await self._analyze_skills_comprehensive(resume_text)
        
        # 3. 经验STAR分析
        experience_analyses = await self._analyze_experiences_star(resume_text)
        
        # 4. ATS评分
        ats_score, ats_feedback = await self._calculate_ats_score(
            resume_text, target_jd, skill_extraction
        )
        
        # 5. 优化建议
        optimization_suggestions = await self._generate_optimization_suggestions(
            resume_text, target_jd, experience_analyses, skill_extraction
        )
        
        # 6. 关键词缺失分析
        missing_keywords = await self._identify_missing_keywords(resume_text, target_jd)
        
        # 7. 置信度评分
        confidence_scores = self._calculate_confidence_scores(basic_info)
        
        result = ResumeAnalysisResult(
            basic_info=basic_info,
            skill_extraction=skill_extraction,
            experience_analyses=experience_analyses,
            ats_score=ats_score,
            ats_feedback=ats_feedback,
            optimization_suggestions=optimization_suggestions,
            missing_keywords=missing_keywords,
            confidence_scores=confidence_scores
        )
        
        logger.info(f"✅ 简历分析完成，ATS评分: {ats_score:.1f}")
        return result
    
    async def _extract_detailed_info(self, resume_text: str) -> Dict[str, Any]:
        """详细信息提取"""
        prompt = f"""
请从以下简历中提取详细的结构化信息：

{resume_text}

请提取以下信息并以JSON格式返回：
{{
    "personal_info": {{
        "name": "姓名",
        "email": "邮箱",
        "phone": "电话",
        "location": "地址",
        "linkedin": "LinkedIn链接",
        "github": "GitHub链接",
        "portfolio": "作品集链接"
    }},
    "education": [
        {{
            "institution": "学校名称",
            "degree": "学位",
            "major": "专业",
            "graduation_date": "毕业时间",
            "gpa": "GPA",
            "honors": "荣誉",
            "relevant_courses": ["相关课程"]
        }}
    ],
    "work_experience": [
        {{
            "company": "公司名称",
            "position": "职位",
            "start_date": "开始时间",
            "end_date": "结束时间",
            "location": "工作地点",
            "description": "工作描述",
            "achievements": ["具体成就"],
            "technologies": ["使用技术"],
            "quantified_results": ["量化结果"]
        }}
    ],
    "projects": [
        {{
            "name": "项目名称",
            "description": "项目描述",
            "role": "担任角色",
            "duration": "项目时长",
            "team_size": "团队规模",
            "technologies": ["技术栈"],
            "achievements": ["项目成果"],
            "github_url": "GitHub链接",
            "demo_url": "演示链接"
        }}
    ],
    "skills": {{
        "programming_languages": ["编程语言"],
        "frameworks": ["框架"],
        "tools": ["工具"],
        "databases": ["数据库"],
        "cloud_platforms": ["云平台"],
        "methodologies": ["方法论"]
    }},
    "certifications": [
        {{
            "name": "证书名称",
            "issuer": "颁发机构",
            "date": "获得日期",
            "expiry": "过期日期",
            "credential_id": "证书ID"
        }}
    ],
    "languages": [
        {{
            "language": "语言",
            "proficiency": "熟练度"
        }}
    ]
}}

注意：
1. 如果某些信息不存在，设为null或空数组
2. 尽可能提取量化数据和具体技术
3. 保持原文的准确性
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"详细信息提取失败: {e}")
            return {}
    
    async def _analyze_skills_comprehensive(self, resume_text: str) -> SkillExtraction:
        """综合技能分析"""
        # 使用正则和NLP结合的方法
        technical_skills = []
        soft_skills = []
        tools_and_platforms = []
        certifications = []
        programming_languages = []
        frameworks = []
        
        resume_lower = resume_text.lower()
        
        # 提取编程语言
        for lang in self.skill_patterns['programming']:
            if lang in resume_lower:
                programming_languages.append(lang.title())
        
        # 提取框架
        for framework in self.skill_patterns['frameworks']:
            if framework in resume_lower:
                frameworks.append(framework.title())
        
        # 提取工具
        for tool in self.skill_patterns['tools']:
            if tool in resume_lower:
                tools_and_platforms.append(tool.upper())
        
        # 使用AI提取软技能
        soft_skills = await self._extract_soft_skills(resume_text)
        
        # 提取证书
        cert_pattern = r'(?:certified|certification|certificate)\s+(?:in\s+)?([A-Za-z\s]+)'
        cert_matches = re.findall(cert_pattern, resume_text, re.IGNORECASE)
        certifications = [match.strip() for match in cert_matches]
        
        return SkillExtraction(
            technical_skills=list(set(programming_languages + frameworks)),
            soft_skills=soft_skills,
            tools_and_platforms=list(set(tools_and_platforms)),
            certifications=list(set(certifications)),
            programming_languages=programming_languages,
            frameworks=frameworks
        )
    
    async def _extract_soft_skills(self, resume_text: str) -> List[str]:
        """提取软技能"""
        prompt = f"""
从以下简历中识别软技能，包括但不限于：
- 领导能力
- 沟通能力
- 团队协作
- 问题解决
- 项目管理
- 创新思维
- 时间管理
- 适应能力

简历内容：
{resume_text}

请返回JSON格式的软技能列表：
{{"soft_skills": ["技能1", "技能2", ...]}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            data = json.loads(result)
            return data.get('soft_skills', [])
            
        except Exception as e:
            logger.error(f"软技能提取失败: {e}")
            return []
    
    async def _analyze_experiences_star(self, resume_text: str) -> List[ExperienceAnalysis]:
        """STAR方法分析经验"""
        prompt = f"""
请分析以下简历中的工作经验和项目经验，使用STAR方法评估：

{resume_text}

对每个经验进行STAR分析：
- Situation (情境): 背景情况
- Task (任务): 面临的任务或挑战
- Action (行动): 采取的具体行动
- Result (结果): 达成的结果

请返回JSON格式：
{{
    "experiences": [
        {{
            "title": "经验标题",
            "situation": "情境描述",
            "task": "任务描述", 
            "action": "行动描述",
            "result": "结果描述",
            "star_completeness": 0.8,
            "missing_elements": ["缺失的STAR元素"],
            "quantified_metrics": ["量化指标"],
            "improvement_suggestions": ["改进建议"]
        }}
    ]
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            data = json.loads(result)
            
            analyses = []
            for exp in data.get('experiences', []):
                # 提取量化成就
                quantified_achievements = self._extract_quantified_achievements(
                    exp.get('result', '') + ' ' + exp.get('action', '')
                )
                
                analysis = ExperienceAnalysis(
                    situation=exp.get('situation', ''),
                    task=exp.get('task', ''),
                    action=exp.get('action', ''),
                    result=exp.get('result', ''),
                    star_completeness=exp.get('star_completeness', 0.0),
                    missing_elements=exp.get('missing_elements', []),
                    quantified_achievements=quantified_achievements,
                    relevant_keywords=[]
                )
                analyses.append(analysis)
            
            return analyses
            
        except Exception as e:
            logger.error(f"STAR分析失败: {e}")
            return []
    
    def _extract_quantified_achievements(self, text: str) -> List[QuantifiedAchievement]:
        """提取量化成就"""
        achievements = []
        
        for pattern in self.quantification_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                metric = match.group(1) if match.groups() else match.group(0)
                
                # 确定影响类型
                impact_type = "performance"
                if any(word in text.lower() for word in ['cost', 'save', 'reduce']):
                    impact_type = "cost"
                elif any(word in text.lower() for word in ['revenue', 'sales', 'profit']):
                    impact_type = "revenue"
                elif any(word in text.lower() for word in ['efficiency', 'speed', 'time']):
                    impact_type = "efficiency"
                
                achievement = QuantifiedAchievement(
                    original_text=match.group(0),
                    metrics=[metric],
                    impact_type=impact_type,
                    suggested_rewrite=f"通过具体行动实现了{match.group(0)}的{impact_type}提升"
                )
                achievements.append(achievement)
        
        return achievements
    
    async def _calculate_ats_score(self, resume_text: str, target_jd: Optional[str],
                                 skills: SkillExtraction) -> Tuple[float, List[str]]:
        """计算ATS评分"""
        score = 0.0
        feedback = []
        
        # 基础格式评分 (30%)
        format_score = self._evaluate_format(resume_text)
        score += format_score * 0.3
        if format_score < 0.8:
            feedback.append("简历格式需要优化，建议使用标准章节标题")
        
        # 关键词密度评分 (40%)
        if target_jd:
            keyword_score = await self._evaluate_keyword_match(resume_text, target_jd)
            score += keyword_score * 0.4
            if keyword_score < 0.7:
                feedback.append("简历与职位描述的关键词匹配度较低")
        else:
            score += 0.3  # 无JD时给予默认分数
        
        # 技能完整性评分 (20%)
        skill_score = self._evaluate_skill_completeness(skills)
        score += skill_score * 0.2
        if skill_score < 0.6:
            feedback.append("技能描述不够全面，建议补充更多技术栈")
        
        # 量化结果评分 (10%)
        quantification_score = self._evaluate_quantification(resume_text)
        score += quantification_score * 0.1
        if quantification_score < 0.5:
            feedback.append("缺少量化的工作成果，建议增加具体数据")
        
        return min(score, 1.0), feedback
    
    def _evaluate_format(self, resume_text: str) -> float:
        """评估格式规范性"""
        score = 0.0
        
        # 检查标准章节
        sections = ['education', 'experience', 'skill', 'project']
        found_sections = sum(1 for section in sections 
                           if any(keyword in resume_text.lower() 
                                for keyword in [section, section + 's']))
        score += (found_sections / len(sections)) * 0.5
        
        # 检查联系信息
        has_email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text)
        has_phone = re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text)
        contact_score = (bool(has_email) + bool(has_phone)) / 2
        score += contact_score * 0.3
        
        # 检查结构化信息
        has_dates = len(re.findall(r'\b\d{4}\b', resume_text)) >= 2
        has_companies = len(re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', resume_text)) >= 1
        structure_score = (bool(has_dates) + bool(has_companies)) / 2
        score += structure_score * 0.2
        
        return min(score, 1.0)
    
    async def _evaluate_keyword_match(self, resume_text: str, jd_text: str) -> float:
        """评估关键词匹配度"""
        prompt = f"""
分析简历和职位描述的关键词匹配度：

职位描述：
{jd_text}

简历：
{resume_text[:2000]}

请返回0-1之间的匹配度分数和分析：
{{"keyword_match_score": 0.8, "analysis": "分析说明"}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            data = json.loads(result)
            return data.get('keyword_match_score', 0.5)
            
        except Exception as e:
            logger.error(f"关键词匹配评估失败: {e}")
            return 0.5
    
    def _evaluate_skill_completeness(self, skills: SkillExtraction) -> float:
        """评估技能完整性"""
        score = 0.0
        
        # 技术技能数量
        tech_count = len(skills.technical_skills)
        score += min(tech_count / 10, 0.4)  # 最多0.4分
        
        # 工具平台数量
        tool_count = len(skills.tools_and_platforms)
        score += min(tool_count / 8, 0.3)   # 最多0.3分
        
        # 软技能数量
        soft_count = len(skills.soft_skills)
        score += min(soft_count / 6, 0.2)   # 最多0.2分
        
        # 证书数量
        cert_count = len(skills.certifications)
        score += min(cert_count / 3, 0.1)   # 最多0.1分
        
        return min(score, 1.0)
    
    def _evaluate_quantification(self, resume_text: str) -> float:
        """评估量化程度"""
        total_patterns = 0
        for pattern in self.quantification_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            total_patterns += len(matches)
        
        # 根据量化指标数量评分
        if total_patterns >= 8:
            return 1.0
        elif total_patterns >= 5:
            return 0.8
        elif total_patterns >= 3:
            return 0.6
        elif total_patterns >= 1:
            return 0.4
        else:
            return 0.0
    
    async def _generate_optimization_suggestions(self, resume_text: str, target_jd: Optional[str],
                                               experiences: List[ExperienceAnalysis],
                                               skills: SkillExtraction) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # STAR完整性建议
        incomplete_experiences = [exp for exp in experiences if exp.star_completeness < 0.8]
        if incomplete_experiences:
            suggestions.append(f"有{len(incomplete_experiences)}个经验描述不够完整，建议补充STAR要素")
        
        # 量化建议
        unquantified_count = sum(1 for exp in experiences if not exp.quantified_achievements)
        if unquantified_count > 0:
            suggestions.append("建议为工作成果添加具体的量化数据（如百分比、金额、时间等）")
        
        # 技能建议
        if len(skills.technical_skills) < 5:
            suggestions.append("技术技能偏少，建议补充更多相关技术栈")
        
        if len(skills.soft_skills) < 3:
            suggestions.append("软技能描述不足，建议增加团队协作、沟通等能力描述")
        
        # JD匹配建议
        if target_jd:
            jd_suggestions = await self._generate_jd_specific_suggestions(resume_text, target_jd)
            suggestions.extend(jd_suggestions)
        
        return suggestions
    
    async def _generate_jd_specific_suggestions(self, resume_text: str, jd_text: str) -> List[str]:
        """生成针对JD的具体建议"""
        prompt = f"""
基于职位描述分析简历，提供具体的优化建议：

职位描述：
{jd_text}

简历：
{resume_text[:2000]}

请提供5个具体的优化建议：
{{"suggestions": ["建议1", "建议2", "建议3", "建议4", "建议5"]}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            data = json.loads(result)
            return data.get('suggestions', [])
            
        except Exception as e:
            logger.error(f"JD建议生成失败: {e}")
            return []
    
    async def _identify_missing_keywords(self, resume_text: str, target_jd: Optional[str]) -> List[str]:
        """识别缺失的关键词"""
        if not target_jd:
            return []
        
        prompt = f"""
对比职位描述和简历，找出简历中缺失的重要关键词：

职位描述：
{target_jd}

简历：
{resume_text[:2000]}

请返回简历中缺失但在职位描述中重要的关键词：
{{"missing_keywords": ["关键词1", "关键词2", ...]}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            data = json.loads(result)
            return data.get('missing_keywords', [])
            
        except Exception as e:
            logger.error(f"缺失关键词识别失败: {e}")
            return []
    
    def _calculate_confidence_scores(self, basic_info: Dict[str, Any]) -> Dict[str, float]:
        """计算各部分解析的置信度"""
        scores = {}
        
        # 个人信息置信度
        personal = basic_info.get('personal_info', {})
        personal_score = sum(1 for key in ['name', 'email', 'phone'] 
                           if personal.get(key)) / 3
        scores['personal_info'] = personal_score
        
        # 工作经验置信度
        work_exp = basic_info.get('work_experience', [])
        if work_exp:
            work_score = sum(1 for exp in work_exp 
                           if all(exp.get(key) for key in ['company', 'position'])) / len(work_exp)
        else:
            work_score = 0.0
        scores['work_experience'] = work_score
        
        # 教育背景置信度
        education = basic_info.get('education', [])
        if education:
            edu_score = sum(1 for edu in education 
                          if all(edu.get(key) for key in ['institution', 'degree'])) / len(education)
        else:
            edu_score = 0.0
        scores['education'] = edu_score
        
        # 技能置信度
        skills = basic_info.get('skills', {})
        skill_categories = ['programming_languages', 'frameworks', 'tools']
        skill_score = sum(1 for cat in skill_categories 
                        if skills.get(cat)) / len(skill_categories)
        scores['skills'] = skill_score
        
        return scores

class ResumeOptimizer:
    """简历优化器"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def optimize_for_ats(self, resume_analysis: ResumeAnalysisResult, 
                             target_jd: str) -> Dict[str, Any]:
        """ATS优化"""
        prompt = f"""
基于以下简历分析结果和目标职位，生成ATS优化版本：

当前ATS评分: {resume_analysis.ats_score:.2f}
缺失关键词: {resume_analysis.missing_keywords}
优化建议: {resume_analysis.optimization_suggestions}

目标职位描述：
{target_jd}

请提供：
1. 优化后的工作经验描述
2. 技能部分建议
3. 关键词整合建议
4. 预期ATS评分提升

返回JSON格式：
{{
    "optimized_sections": {{
        "work_experience": ["优化后的经验描述"],
        "skills": ["建议的技能列表"],
        "keywords_integration": ["关键词整合建议"]
    }},
    "expected_score_improvement": 0.2,
    "optimization_rationale": "优化理由说明"
}}
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"ATS优化失败: {e}")
            return {}
    
    async def rewrite_experience_star(self, experience: str, target_role: str) -> str:
        """使用STAR方法重写经验"""
        prompt = f"""
请使用STAR方法重写以下工作经验，使其更适合{target_role}职位：

原始经验：
{experience}

目标职位：{target_role}

请按STAR格式重写：
- Situation (情境): 明确的背景和环境
- Task (任务): 具体的任务或挑战
- Action (行动): 详细的行动步骤
- Result (结果): 量化的结果和影响

返回重写后的经验描述，要求：
1. 突出与{target_role}相关的技能
2. 包含量化的结果
3. 使用行业关键词
4. 保持真实性
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"STAR重写失败: {e}")
            return experience