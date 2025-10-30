#!/usr/bin/env python3
"""
智能简历优化系统
配置路径: resume_optimizer.py (项目根目录)
"""

import asyncio
import re
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import openai
from loguru import logger
import sqlite3
import uuid

@dataclass
class KeywordAnalysis:
    """关键词分析结果"""
    technical_skills: List[str]
    soft_skills: List[str]
    industry_keywords: List[str]
    missing_keywords: List[str]
    match_score: float
    recommendations: List[str]

@dataclass
class ATSScore:
    """ATS评分"""
    overall_score: int  # 0-100
    keyword_score: int
    format_score: int
    structure_score: int
    quantification_score: int
    issues: List[str]
    improvements: List[str]

@dataclass
class STARSuggestion:
    """STAR法则建议"""
    experience_id: str
    missing_elements: List[str]  # S, T, A, R
    suggestions: Dict[str, str]
    improved_description: str
    quantification_tips: List[str]

@dataclass
class OptimizationSuggestion:
    """优化建议"""
    section: str  # personal_info, work_experience, projects, skills
    priority: str  # high, medium, low
    type: str  # keyword_missing, quantification_needed, star_incomplete, format_issue
    current_text: str
    suggested_text: str
    reason: str

@dataclass
class ResumeVersion:
    """简历版本 - 增强版"""
    version_id: str
    name: str
    target_company: str
    target_position: str
    description: str              # 新增：版本描述
    resume_data: Dict[str, Any]
    ats_score: Dict[str, Any]     # 修改：存储完整ATS评分对象
    created_time: datetime
    is_active: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        return {
            'version_id': self.version_id,
            'name': self.name,
            'target_company': self.target_company,
            'target_position': self.target_position,
            'description': self.description,
            'resume_data': self.resume_data,
            'ats_score': self.ats_score,
            'created_time': self.created_time.isoformat(),
            'is_active': self.is_active
        }

class ResumeOptimizer:
    """智能简历优化器"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        
        # 常用量化指标
        self.quantification_patterns = {
            'performance': ['提升', '提高', '增长', '增加', '优化', '改善'],
            'efficiency': ['效率', '速度', '时间', '成本', '资源'],
            'scale': ['用户', '数据', '系统', '团队', '项目'],
            'impact': ['影响', '收益', '价值', '收入', '利润']
        }
        
        # ATS友好格式规则
        self.ats_format_rules = {
            'font_keywords': ['Arial', 'Calibri', 'Times New Roman', 'Helvetica'],
            'avoid_elements': ['图表', '图片', '表格', '特殊符号'],
            'preferred_sections': ['个人信息', '工作经验', '教育背景', '技能', '项目经验']
        }
    
    async def analyze_resume_vs_jd(self, resume_data: Dict[str, Any], 
                                 jd_data: Dict[str, Any]) -> KeywordAnalysis:
        """分析简历与JD的匹配度"""
        try:
            # 提取JD关键词
            jd_keywords = await self._extract_jd_keywords(jd_data)
            
            # 提取简历关键词
            resume_keywords = self._extract_resume_keywords(resume_data)
            
            # 计算匹配度
            match_score = self._calculate_match_score(resume_keywords, jd_keywords)
            
            # 生成建议
            recommendations = await self._generate_keyword_recommendations(
                resume_keywords, jd_keywords, jd_data
            )
            
            return KeywordAnalysis(
                technical_skills=jd_keywords.get('technical', []),
                soft_skills=jd_keywords.get('soft', []),
                industry_keywords=jd_keywords.get('industry', []),
                missing_keywords=jd_keywords.get('missing', []),
                match_score=match_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"关键词分析失败: {e}")
            return KeywordAnalysis([], [], [], [], 0.0, [])
    
    async def _extract_jd_keywords(self, jd_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """提取JD关键词"""
        prompt = f"""
分析以下职位描述，提取关键词并分类：

职位：{jd_data.get('title', '')}
公司：{jd_data.get('company', '')}
要求：{' '.join(jd_data.get('requirements', []))}
职责：{' '.join(jd_data.get('responsibilities', []))}
技能：{' '.join(jd_data.get('skills_required', []))}

请分类提取关键词，返回JSON格式：
{{
    "technical": ["Python", "Docker", "AWS"],
    "soft": ["团队合作", "沟通能力", "解决问题"],
    "industry": ["互联网", "金融科技", "电商"],
    "experience_level": ["3年", "高级", "资深"],
    "certifications": ["AWS认证", "PMP"],
    "tools": ["Git", "Jenkins", "Kubernetes"]
}}

只返回JSON，不要其他解释。
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"JD关键词提取失败: {e}")
            return {"technical": [], "soft": [], "industry": []}
    
    def _extract_resume_keywords(self, resume_data: Dict[str, Any]) -> List[str]:
        """提取简历关键词"""
        keywords = []
        
        # 从技能中提取
        keywords.extend(resume_data.get('skills', []))
        
        # 从工作经验中提取
        for work in resume_data.get('work_experience', []):
            keywords.extend(work.get('responsibilities', []))
            keywords.extend(work.get('achievements', []))
        
        # 从项目经验中提取
        for project in resume_data.get('projects', []):
            keywords.extend(project.get('technologies', []))
            keywords.extend(project.get('achievements', []))
        
        # 去重并转为小写
        return list(set([kw.lower().strip() for kw in keywords if kw.strip()]))
    
    def _calculate_match_score(self, resume_keywords: List[str], 
                              jd_keywords: Dict[str, List[str]]) -> float:
        """计算匹配度分数"""
        all_jd_keywords = []
        for category_keywords in jd_keywords.values():
            all_jd_keywords.extend([kw.lower() for kw in category_keywords])
        
        if not all_jd_keywords:
            return 0.0
        
        matched = 0
        for jd_kw in all_jd_keywords:
            for resume_kw in resume_keywords:
                if jd_kw in resume_kw or resume_kw in jd_kw:
                    matched += 1
                    break
        
        return (matched / len(all_jd_keywords)) * 100
    
    async def _generate_keyword_recommendations(self, resume_keywords: List[str],
                                              jd_keywords: Dict[str, List[str]],
                                              jd_data: Dict[str, Any]) -> List[str]:
        """生成关键词建议"""
        prompt = f"""
基于以下分析，生成简历优化建议：

JD要求的关键词：{jd_keywords}
简历现有关键词：{resume_keywords[:20]}  # 限制长度
目标职位：{jd_data.get('title', '')}

请生成5-8条具体的关键词优化建议，每条建议要具体可操作：

要求：
1. 指出缺失的重要关键词
2. 建议在简历的哪个部分添加
3. 给出具体的表达方式

返回JSON数组格式：["建议1", "建议2", ...]
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"生成关键词建议失败: {e}")
            return ["无法生成关键词建议，请手动检查关键词匹配度"]
    
    async def calculate_ats_score(self, resume_data: Dict[str, Any], 
                                jd_data: Dict[str, Any]) -> ATSScore:
        """计算ATS评分"""
        try:
            # 关键词匹配分数
            keyword_analysis = await self.analyze_resume_vs_jd(resume_data, jd_data)
            keyword_score = int(keyword_analysis.match_score)
            
            # 格式分数
            format_score = self._calculate_format_score(resume_data)
            
            # 结构分数
            structure_score = self._calculate_structure_score(resume_data)
            
            # 量化分数
            quantification_score = self._calculate_quantification_score(resume_data)
            
            # 总分
            overall_score = int((keyword_score * 0.4 + format_score * 0.2 + 
                               structure_score * 0.2 + quantification_score * 0.2))
            
            # 生成问题和改进建议
            issues, improvements = self._generate_ats_feedback(
                keyword_score, format_score, structure_score, quantification_score
            )
            
            return ATSScore(
                overall_score=overall_score,
                keyword_score=keyword_score,
                format_score=format_score,
                structure_score=structure_score,
                quantification_score=quantification_score,
                issues=issues,
                improvements=improvements
            )
            
        except Exception as e:
            logger.error(f"ATS评分计算失败: {e}")
            return ATSScore(0, 0, 0, 0, 0, ["评分计算失败"], [])
    
    def _calculate_format_score(self, resume_data: Dict[str, Any]) -> int:
        """计算格式分数"""
        score = 100
        
        # 检查必要部分
        required_sections = ['personal_info', 'work_experience', 'education']
        for section in required_sections:
            if not resume_data.get(section):
                score -= 20
        
        # 检查联系信息
        personal_info = resume_data.get('personal_info', {})
        if not personal_info.get('email'):
            score -= 15
        if not personal_info.get('phone'):
            score -= 10
        
        return max(0, score)
    
    def _calculate_structure_score(self, resume_data: Dict[str, Any]) -> int:
        """计算结构分数"""
        score = 100
        
        # 检查工作经验结构
        work_exp = resume_data.get('work_experience', [])
        if not work_exp:
            score -= 30
        else:
            for work in work_exp:
                if not work.get('company'):
                    score -= 10
                if not work.get('position'):
                    score -= 10
                if not work.get('responsibilities') and not work.get('achievements'):
                    score -= 15
        
        # 检查技能部分
        if not resume_data.get('skills'):
            score -= 20
        
        return max(0, score)
    
    def _calculate_quantification_score(self, resume_data: Dict[str, Any]) -> int:
        """计算量化分数"""
        score = 0
        total_descriptions = 0
        quantified_descriptions = 0
        
        # 检查工作经验中的量化
        for work in resume_data.get('work_experience', []):
            for achievement in work.get('achievements', []):
                total_descriptions += 1
                if self._has_quantification(achievement):
                    quantified_descriptions += 1
        
        # 检查项目经验中的量化
        for project in resume_data.get('projects', []):
            for achievement in project.get('achievements', []):
                total_descriptions += 1
                if self._has_quantification(achievement):
                    quantified_descriptions += 1
        
        if total_descriptions > 0:
            score = int((quantified_descriptions / total_descriptions) * 100)
        
        return score
    
    def _has_quantification(self, text: str) -> bool:
        """检查文本是否包含量化数据"""
        # 检查数字和百分比
        number_pattern = r'\d+%|\d+\w*|\d+\.\d+'
        if re.search(number_pattern, text):
            return True
        
        # 检查量化关键词
        quantification_keywords = ['提升', '提高', '增长', '减少', '节省', '优化']
        return any(keyword in text for keyword in quantification_keywords)
    
    def _generate_ats_feedback(self, keyword_score: int, format_score: int,
                              structure_score: int, quantification_score: int
                              ) -> Tuple[List[str], List[str]]:
        """生成ATS反馈"""
        issues = []
        improvements = []
        
        if keyword_score < 70:
            issues.append(f"关键词匹配度较低 ({keyword_score}%)")
            improvements.append("增加与目标职位相关的技能关键词")
        
        if format_score < 80:
            issues.append(f"简历格式需要改进 ({format_score}%)")
            improvements.append("完善个人信息，确保联系方式完整")
        
        if structure_score < 80:
            issues.append(f"简历结构不够完整 ({structure_score}%)")
            improvements.append("补充缺失的工作经验或项目描述")
        
        if quantification_score < 60:
            issues.append(f"缺乏量化数据 ({quantification_score}%)")
            improvements.append("在成就描述中添加具体的数字和百分比")
        
        return issues, improvements
    
    async def generate_star_suggestions(self, resume_data: Dict[str, Any],
                                       jd_data: Dict[str, Any]) -> List[STARSuggestion]:
        """生成STAR法则建议"""
        suggestions = []
        
        # 分析工作经验
        for i, work in enumerate(resume_data.get('work_experience', [])):
            suggestion = await self._analyze_experience_star(
                f"work_{i}", work, jd_data, "work_experience"
            )
            if suggestion:
                suggestions.append(suggestion)
        
        # 分析项目经验
        for i, project in enumerate(resume_data.get('projects', [])):
            suggestion = await self._analyze_experience_star(
                f"project_{i}", project, jd_data, "project"
            )
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    async def _analyze_experience_star(self, exp_id: str, experience: Dict[str, Any],
                                     jd_data: Dict[str, Any], exp_type: str) -> Optional[STARSuggestion]:
        """分析单个经验的STAR完整性"""
        try:
            # 构建经验描述
            if exp_type == "work_experience":
                description = f"公司: {experience.get('company', '')}\n"
                description += f"职位: {experience.get('position', '')}\n"
                description += f"职责: {'; '.join(experience.get('responsibilities', []))}\n"
                description += f"成就: {'; '.join(experience.get('achievements', []))}"
            else:  # project
                description = f"项目: {experience.get('name', '')}\n"
                description += f"角色: {experience.get('role', '')}\n"
                description += f"描述: {experience.get('description', '')}\n"
                description += f"成就: {'; '.join(experience.get('achievements', []))}"
            
            prompt = f"""
分析以下{exp_type}经验，基于STAR法则(Situation-Task-Action-Result)给出改进建议：

目标职位：{jd_data.get('title', '')}
经验描述：
{description}

请分析：
1. 缺失的STAR元素
2. 每个缺失元素的具体建议
3. 重写后的完整描述
4. 量化建议

返回JSON格式：
{{
    "missing_elements": ["S", "T", "A", "R"],
    "suggestions": {{
        "S": "情境建议",
        "T": "任务建议", 
        "A": "行动建议",
        "R": "结果建议"
    }},
    "improved_description": "改进后的描述",
    "quantification_tips": ["量化建议1", "量化建议2"]
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('```json'):
                result = result[7:-3]
            elif result.startswith('```'):
                result = result[3:-3]
            
            data = json.loads(result)
            
            return STARSuggestion(
                experience_id=exp_id,
                missing_elements=data.get('missing_elements', []),
                suggestions=data.get('suggestions', {}),
                improved_description=data.get('improved_description', ''),
                quantification_tips=data.get('quantification_tips', [])
            )
            
        except Exception as e:
            logger.error(f"STAR分析失败 {exp_id}: {e}")
            return None
    
    async def generate_optimization_suggestions(self, resume_data: Dict[str, Any],
                                              jd_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """生成综合优化建议"""
        suggestions = []
        
        # 关键词优化建议
        keyword_analysis = await self.analyze_resume_vs_jd(resume_data, jd_data)
        for recommendation in keyword_analysis.recommendations:
            suggestions.append(OptimizationSuggestion(
                section="skills",
                priority="high",
                type="keyword_missing",
                current_text="",
                suggested_text=recommendation,
                reason="提高关键词匹配度"
            ))
        
        # STAR法则建议
        star_suggestions = await self.generate_star_suggestions(resume_data, jd_data)
        for star_suggestion in star_suggestions:
            if star_suggestion.missing_elements:
                suggestions.append(OptimizationSuggestion(
                    section="work_experience",
                    priority="medium",
                    type="star_incomplete",
                    current_text="",
                    suggested_text=star_suggestion.improved_description,
                    reason=f"完善STAR法则，缺失: {', '.join(star_suggestion.missing_elements)}"
                ))
        
        # 量化建议
        quantification_suggestions = self._generate_quantification_suggestions(resume_data)
        suggestions.extend(quantification_suggestions)
        
        return suggestions
    
    def _generate_quantification_suggestions(self, resume_data: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """生成量化建议"""
        suggestions = []
        
        # 检查工作经验
        for i, work in enumerate(resume_data.get('work_experience', [])):
            for j, achievement in enumerate(work.get('achievements', [])):
                if not self._has_quantification(achievement):
                    suggestions.append(OptimizationSuggestion(
                        section=f"work_experience[{i}].achievements[{j}]",
                        priority="medium",
                        type="quantification_needed",
                        current_text=achievement,
                        suggested_text=f"建议添加具体数据：{achievement} (增加百分比、数量等)",
                        reason="缺乏量化数据，影响说服力"
                    ))
        
        return suggestions

class ResumeVersionManager:
    """简历版本管理器 - 带数据库持久化"""
    
    def __init__(self, db_path: str = "data/templates.db"):
        self.db_path = db_path
        self._init_version_tables()
    
    def _init_version_tables(self):
        """初始化版本管理数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 简历版本表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_versions (
                version_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target_company TEXT,
                target_position TEXT,
                description TEXT,
                resume_data TEXT NOT NULL,
                ats_score_data TEXT,
                created_time TEXT NOT NULL,
                is_active BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # 版本对比缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_comparisons (
                id TEXT PRIMARY KEY,
                version1_id TEXT NOT NULL,
                version2_id TEXT NOT NULL,
                comparison_result TEXT NOT NULL,
                created_time TEXT NOT NULL,
                FOREIGN KEY (version1_id) REFERENCES resume_versions (version_id),
                FOREIGN KEY (version2_id) REFERENCES resume_versions (version_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_version(self, name: str, target_company: str, target_position: str,
                      resume_data: Dict[str, Any], ats_score: Dict[str, Any],
                      description: str = "") -> str:
        """创建新版本（带用户隔离）"""
        try:
            import interview_assistant_system
            from flask import request
            user = getattr(request, 'current_user', None)
            user_id = user.user_id if user else None
        except:
            user_id = None
        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO resume_versions
                (version_id, name, target_company, target_position, description,
                resume_data, ats_score_data, created_time, is_active, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                version_id,
                name,
                target_company,
                target_position,
                description,
                json.dumps(resume_data, ensure_ascii=False),
                json.dumps(ats_score, ensure_ascii=False),
                datetime.now().isoformat(),
                False,
                user_id
            ))
            conn.commit()
            logger.info(f"创建简历版本: {name} ({version_id}) 用户: {user_id or 'guest'}")
            return version_id
        except Exception as e:
            conn.rollback()
            logger.error(f"创建版本失败: {e}")
            raise
        finally:
            conn.close()
    
    def get_version(self, version_id: str) -> Optional[ResumeVersion]:
        """获取版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT version_id, name, target_company, target_position, description,
                       resume_data, ats_score_data, created_time, is_active
                FROM resume_versions 
                WHERE version_id = ?
            ''', (version_id,))
            
            row = cursor.fetchone()
            if row:
                return ResumeVersion(
                    version_id=row[0],
                    name=row[1],
                    target_company=row[2] or '',
                    target_position=row[3] or '',
                    description=row[4] or '',
                    resume_data=json.loads(row[5]),
                    ats_score=json.loads(row[6]) if row[6] else {},
                    created_time=datetime.fromisoformat(row[7]),
                    is_active=bool(row[8])
                )
            return None
            
        except Exception as e:
            logger.error(f"获取版本失败: {e}")
            return None
        finally:
            conn.close()
    
    def list_versions(self) -> List[ResumeVersion]:
        """列出所有版本（按用户过滤）"""
        from user_auth import get_current_user
        
        user = get_current_user()
        user_id = user.user_id if user else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('''
                    SELECT version_id, name, target_company, target_position, description,
                        resume_data, ats_score_data, created_time, is_active
                    FROM resume_versions 
                    WHERE user_id = ? OR user_id IS NULL
                    ORDER BY created_time DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT version_id, name, target_company, target_position, description,
                        resume_data, ats_score_data, created_time, is_active
                    FROM resume_versions 
                    WHERE user_id IS NULL
                    ORDER BY created_time DESC
                ''')
            
            versions = []
            for row in cursor.fetchall():
                version = ResumeVersion(
                    version_id=row[0],
                    name=row[1],
                    target_company=row[2] or '',
                    target_position=row[3] or '',
                    description=row[4] or '',
                    resume_data=json.loads(row[5]),
                    ats_score=json.loads(row[6]) if row[6] else {},
                    created_time=datetime.fromisoformat(row[7]),
                    is_active=bool(row[8])
                )
                versions.append(version)
            
            return versions
            
        except Exception as e:
            logger.error(f"列出版本失败: {e}")
            return []
        finally:
            conn.close()
    
    def set_active_version(self, version_id: str):
        """设置活跃版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 先将所有版本设为非活跃
            cursor.execute('UPDATE resume_versions SET is_active = FALSE')
            
            # 设置指定版本为活跃
            cursor.execute('''
                UPDATE resume_versions 
                SET is_active = TRUE 
                WHERE version_id = ?
            ''', (version_id,))
            
            conn.commit()
            logger.info(f"设置活跃版本: {version_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"设置活跃版本失败: {e}")
            raise
        finally:
            conn.close()
    
    def delete_version(self, version_id: str) -> bool:
        """删除版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 删除相关的对比缓存
            cursor.execute('''
                DELETE FROM version_comparisons 
                WHERE version1_id = ? OR version2_id = ?
            ''', (version_id, version_id))
            
            # 删除版本
            cursor.execute('''
                DELETE FROM resume_versions 
                WHERE version_id = ?
            ''', (version_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"删除版本: {version_id}")
                return True
            else:
                return False
                
        except Exception as e:
            conn.rollback()
            logger.error(f"删除版本失败: {e}")
            return False
        finally:
            conn.close()
    
    def update_version(self, version_id: str, updates: Dict[str, Any]) -> bool:
        """更新版本信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 构建更新语句
            set_clause = []
            values = []
            
            for key, value in updates.items():
                if key in ['name', 'target_company', 'target_position', 'description']:
                    set_clause.append(f"{key} = ?")
                    values.append(value)
                elif key == 'resume_data':
                    set_clause.append("resume_data = ?")
                    values.append(json.dumps(value, ensure_ascii=False))
                elif key == 'ats_score':
                    set_clause.append("ats_score_data = ?")
                    values.append(json.dumps(value, ensure_ascii=False))
            
            if not set_clause:
                return False
            
            values.append(version_id)
            
            cursor.execute(f'''
                UPDATE resume_versions 
                SET {", ".join(set_clause)}
                WHERE version_id = ?
            ''', values)
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"更新版本: {version_id}")
                return True
            else:
                return False
                
        except Exception as e:
            conn.rollback()
            logger.error(f"更新版本失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_active_version(self) -> Optional[ResumeVersion]:
        """获取当前活跃版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT version_id, name, target_company, target_position, description,
                       resume_data, ats_score_data, created_time, is_active
                FROM resume_versions 
                WHERE is_active = TRUE
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                return ResumeVersion(
                    version_id=row[0],
                    name=row[1],
                    target_company=row[2],
                    target_position=row[3],
                    description=row[4],
                    resume_data=json.loads(row[5]),
                    ats_score=json.loads(row[6]) if row[6] else {},
                    created_time=datetime.fromisoformat(row[7]),
                    is_active=bool(row[8])
                )
            return None
            
        except Exception as e:
            logger.error(f"获取活跃版本失败: {e}")
            return None
        finally:
            conn.close()
    
    def cache_comparison(self, version1_id: str, version2_id: str, 
                        comparison_result: Dict[str, Any]) -> str:
        """缓存对比结果"""
        comparison_id = f"cmp_{uuid.uuid4().hex[:16]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO version_comparisons 
                (id, version1_id, version2_id, comparison_result, created_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                comparison_id,
                version1_id,
                version2_id,
                json.dumps(comparison_result, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return comparison_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"缓存对比结果失败: {e}")
            return ""
        finally:
            conn.close()
    
    def get_cached_comparison(self, version1_id: str, version2_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的对比结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 尝试正向和反向查找
            cursor.execute('''
                SELECT comparison_result, created_time 
                FROM version_comparisons 
                WHERE (version1_id = ? AND version2_id = ?) 
                   OR (version1_id = ? AND version2_id = ?)
                ORDER BY created_time DESC
                LIMIT 1
            ''', (version1_id, version2_id, version2_id, version1_id))
            
            row = cursor.fetchone()
            if row:
                # 检查缓存是否还有效（24小时内）
                cached_time = datetime.fromisoformat(row[1])
                if datetime.now() - cached_time < timedelta(hours=24):
                    return json.loads(row[0])
            
            return None
            
        except Exception as e:
            logger.error(f"获取缓存对比失败: {e}")
            return None
        finally:
            conn.close()
    
    def cleanup_old_comparisons(self, days: int = 7):
        """清理旧的对比缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cursor.execute('''
                DELETE FROM version_comparisons 
                WHERE created_time < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个旧的对比缓存")
            
        except Exception as e:
            logger.error(f"清理对比缓存失败: {e}")
        finally:
            conn.close()