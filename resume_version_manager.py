#!/usr/bin/env python3
"""
简历版本管理器 - 多版本简历智能管理
"""

import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

@dataclass
class ResumeVersion:
    """简历版本"""
    id: str
    name: str
    base_resume_id: Optional[str]  # 基础版本ID
    target_company: str
    target_position: str
    target_jd_hash: str  # JD的哈希值，用于追踪变化
    content: Dict[str, Any]  # 简历内容
    optimization_applied: List[str]  # 应用的优化建议
    ats_score: float
    created_time: datetime
    last_modified: datetime
    version_notes: str
    is_active: bool

@dataclass
class VersionComparison:
    """版本对比结果"""
    version1_id: str
    version2_id: str
    differences: Dict[str, Any]
    similarity_score: float
    recommendation: str

@dataclass
class PerformanceMetrics:
    """版本性能指标"""
    version_id: str
    applications_sent: int
    interviews_received: int
    response_rate: float
    feedback_received: List[str]
    avg_ats_score: float
    last_updated: datetime

class ResumeVersionManager:
    """简历版本管理器"""
    
    def __init__(self, db_path: str = "data/resume_versions.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 简历版本表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_versions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_resume_id TEXT,
                target_company TEXT,
                target_position TEXT,
                target_jd_hash TEXT,
                content TEXT NOT NULL,
                optimization_applied TEXT,
                ats_score REAL DEFAULT 0.0,
                created_time TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                version_notes TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # 版本性能表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id TEXT NOT NULL,
                applications_sent INTEGER DEFAULT 0,
                interviews_received INTEGER DEFAULT 0,
                response_rate REAL DEFAULT 0.0,
                feedback_received TEXT,
                avg_ats_score REAL DEFAULT 0.0,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (version_id) REFERENCES resume_versions (id)
            )
        ''')
        
        # 版本对比历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version1_id TEXT NOT NULL,
                version2_id TEXT NOT NULL,
                differences TEXT NOT NULL,
                similarity_score REAL,
                comparison_time TEXT NOT NULL,
                FOREIGN KEY (version1_id) REFERENCES resume_versions (id),
                FOREIGN KEY (version2_id) REFERENCES resume_versions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_version(self, resume_content: Dict[str, Any], 
                      target_company: str, target_position: str,
                      target_jd: str, base_version_id: Optional[str] = None,
                      version_name: Optional[str] = None) -> str:
        """创建新版本"""
        
        # 生成版本ID和名称
        version_id = hashlib.md5(
            f"{target_company}_{target_position}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        if not version_name:
            version_name = f"{target_company}_{target_position}_版本"
        
        # 计算JD哈希值
        jd_hash = hashlib.md5(target_jd.encode()).hexdigest()
        
        version = ResumeVersion(
            id=version_id,
            name=version_name,
            base_resume_id=base_version_id,
            target_company=target_company,
            target_position=target_position,
            target_jd_hash=jd_hash,
            content=resume_content,
            optimization_applied=[],
            ats_score=0.0,
            created_time=datetime.now(),
            last_modified=datetime.now(),
            version_notes="",
            is_active=True
        )
        
        self._save_version(version)
        logger.info(f"✅ 创建简历版本: {version_name} ({version_id})")
        
        return version_id
    
    def _save_version(self, version: ResumeVersion):
        """保存版本到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO resume_versions 
            (id, name, base_resume_id, target_company, target_position, target_jd_hash,
             content, optimization_applied, ats_score, created_time, last_modified,
             version_notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version.id,
            version.name,
            version.base_resume_id,
            version.target_company,
            version.target_position,
            version.target_jd_hash,
            json.dumps(version.content, ensure_ascii=False),
            json.dumps(version.optimization_applied),
            version.ats_score,
            version.created_time.isoformat(),
            version.last_modified.isoformat(),
            version.version_notes,
            version.is_active
        ))
        
        conn.commit()
        conn.close()
    
    def get_version(self, version_id: str) -> Optional[ResumeVersion]:
        """获取指定版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM resume_versions WHERE id = ?', (version_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ResumeVersion(
                id=row[0],
                name=row[1],
                base_resume_id=row[2],
                target_company=row[3],
                target_position=row[4],
                target_jd_hash=row[5],
                content=json.loads(row[6]),
                optimization_applied=json.loads(row[7]) if row[7] else [],
                ats_score=row[8],
                created_time=datetime.fromisoformat(row[9]),
                last_modified=datetime.fromisoformat(row[10]),
                version_notes=row[11] or "",
                is_active=bool(row[12])
            )
        return None
    
    def list_versions(self, active_only: bool = True) -> List[ResumeVersion]:
        """列出所有版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute('SELECT * FROM resume_versions WHERE is_active = 1 ORDER BY created_time DESC')
        else:
            cursor.execute('SELECT * FROM resume_versions ORDER BY created_time DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        versions = []
        for row in rows:
            version = ResumeVersion(
                id=row[0],
                name=row[1],
                base_resume_id=row[2],
                target_company=row[3],
                target_position=row[4],
                target_jd_hash=row[5],
                content=json.loads(row[6]),
                optimization_applied=json.loads(row[7]) if row[7] else [],
                ats_score=row[8],
                created_time=datetime.fromisoformat(row[9]),
                last_modified=datetime.fromisoformat(row[10]),
                version_notes=row[11] or "",
                is_active=bool(row[12])
            )
            versions.append(version)
        
        return versions
    
    def update_version(self, version_id: str, updates: Dict[str, Any]) -> bool:
        """更新版本"""
        version = self.get_version(version_id)
        if not version:
            return False
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(version, key):
                setattr(version, key, value)
        
        version.last_modified = datetime.now()
        self._save_version(version)
        
        logger.info(f"✅ 更新简历版本: {version.name}")
        return True
    
    def delete_version(self, version_id: str) -> bool:
        """删除版本（软删除）"""
        return self.update_version(version_id, {'is_active': False})
    
    def compare_versions(self, version1_id: str, version2_id: str) -> VersionComparison:
        """对比两个版本"""
        version1 = self.get_version(version1_id)
        version2 = self.get_version(version2_id)
        
        if not version1 or not version2:
            raise ValueError("版本不存在")
        
        differences = self._calculate_differences(version1.content, version2.content)
        similarity_score = self._calculate_similarity(version1.content, version2.content)
        recommendation = self._generate_comparison_recommendation(differences, similarity_score)
        
        comparison = VersionComparison(
            version1_id=version1_id,
            version2_id=version2_id,
            differences=differences,
            similarity_score=similarity_score,
            recommendation=recommendation
        )
        
        # 保存对比历史
        self._save_comparison(comparison)
        
        return comparison
    
    def _calculate_differences(self, content1: Dict[str, Any], 
                             content2: Dict[str, Any]) -> Dict[str, Any]:
        """计算内容差异"""
        differences = {}
        
        # 比较个人信息
        personal1 = content1.get('personal_info', {})
        personal2 = content2.get('personal_info', {})
        personal_diff = {k: {'v1': personal1.get(k), 'v2': personal2.get(k)} 
                        for k in set(personal1.keys()) | set(personal2.keys()) 
                        if personal1.get(k) != personal2.get(k)}
        if personal_diff:
            differences['personal_info'] = personal_diff
        
        # 比较工作经验
        work1 = content1.get('work_experience', [])
        work2 = content2.get('work_experience', [])
        if work1 != work2:
            differences['work_experience'] = {
                'count_diff': len(work2) - len(work1),
                'content_changed': True
            }
        
        # 比较项目经验
        projects1 = content1.get('projects', [])
        projects2 = content2.get('projects', [])
        if projects1 != projects2:
            differences['projects'] = {
                'count_diff': len(projects2) - len(projects1),
                'content_changed': True
            }
        
        # 比较技能
        skills1 = set(content1.get('skills', []))
        skills2 = set(content2.get('skills', []))
        if skills1 != skills2:
            differences['skills'] = {
                'added': list(skills2 - skills1),
                'removed': list(skills1 - skills2)
            }
        
        return differences
    
    def _calculate_similarity(self, content1: Dict[str, Any], 
                            content2: Dict[str, Any]) -> float:
        """计算相似度"""
        # 简化的相似度计算
        total_fields = 0
        same_fields = 0
        
        all_keys = set(content1.keys()) | set(content2.keys())
        
        for key in all_keys:
            total_fields += 1
            if content1.get(key) == content2.get(key):
                same_fields += 1
        
        return same_fields / total_fields if total_fields > 0 else 0.0
    
    def _generate_comparison_recommendation(self, differences: Dict[str, Any], 
                                          similarity_score: float) -> str:
        """生成对比建议"""
        if similarity_score > 0.9:
            return "两个版本几乎相同，建议进一步差异化"
        elif similarity_score > 0.7:
            return "版本有适度差异，适合不同类型的职位申请"
        elif similarity_score > 0.5:
            return "版本差异较大，请确保针对性优化合理"
        else:
            return "版本差异很大，建议重新评估优化策略"
    
    def _save_comparison(self, comparison: VersionComparison):
        """保存对比记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO version_comparisons 
            (version1_id, version2_id, differences, similarity_score, comparison_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            comparison.version1_id,
            comparison.version2_id,
            json.dumps(comparison.differences, ensure_ascii=False),
            comparison.similarity_score,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def update_performance_metrics(self, version_id: str, 
                                 applications_sent: Optional[int] = None,
                                 interviews_received: Optional[int] = None,
                                 feedback: Optional[str] = None,
                                 ats_score: Optional[float] = None):
        """更新版本性能指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取现有记录
        cursor.execute('SELECT * FROM version_performance WHERE version_id = ?', (version_id,))
        row = cursor.fetchone()
        
        if row:
            # 更新现有记录
            current_apps = row[2]
            current_interviews = row[3]
            current_feedback = json.loads(row[5]) if row[5] else []
            current_ats = row[6]
            
            new_apps = applications_sent if applications_sent is not None else current_apps
            new_interviews = interviews_received if interviews_received is not None else current_interviews
            new_feedback = current_feedback
            if feedback:
                new_feedback.append(feedback)
            new_ats = ats_score if ats_score is not None else current_ats
            
            response_rate = new_interviews / new_apps if new_apps > 0 else 0.0
            
            cursor.execute('''
                UPDATE version_performance 
                SET applications_sent = ?, interviews_received = ?, response_rate = ?,
                    feedback_received = ?, avg_ats_score = ?, last_updated = ?
                WHERE version_id = ?
            ''', (new_apps, new_interviews, response_rate, 
                  json.dumps(new_feedback), new_ats, datetime.now().isoformat(), version_id))
        else:
            # 创建新记录
            apps = applications_sent or 0
            interviews = interviews_received or 0
            response_rate = interviews / apps if apps > 0 else 0.0
            feedback_list = [feedback] if feedback else []
            
            cursor.execute('''
                INSERT INTO version_performance 
                (version_id, applications_sent, interviews_received, response_rate,
                 feedback_received, avg_ats_score, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (version_id, apps, interviews, response_rate, 
                  json.dumps(feedback_list), ats_score or 0.0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 更新版本性能指标: {version_id}")
    
    def get_performance_metrics(self, version_id: str) -> Optional[PerformanceMetrics]:
        """获取版本性能指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM version_performance WHERE version_id = ?', (version_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return PerformanceMetrics(
                version_id=row[1],
                applications_sent=row[2],
                interviews_received=row[3],
                response_rate=row[4],
                feedback_received=json.loads(row[5]) if row[5] else [],
                avg_ats_score=row[6],
                last_updated=datetime.fromisoformat(row[7])
            )
        return None
    
    def get_best_performing_version(self) -> Optional[str]:
        """获取表现最佳的版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 基于回应率和ATS评分的综合评估
        cursor.execute('''
            SELECT version_id, (response_rate * 0.7 + avg_ats_score * 0.3) as score
            FROM version_performance 
            WHERE applications_sent > 0
            ORDER BY score DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def generate_version_report(self, version_id: str) -> Dict[str, Any]:
        """生成版本报告"""
        version = self.get_version(version_id)
        performance = self.get_performance_metrics(version_id)
        
        if not version:
            return {}
        
        report = {
            'version_info': {
                'id': version.id,
                'name': version.name,
                'target_company': version.target_company,
                'target_position': version.target_position,
                'ats_score': version.ats_score,
                'created_time': version.created_time.isoformat(),
                'optimizations': version.optimization_applied
            },
            'performance_metrics': {},
            'recommendations': []
        }
        
        if performance:
            report['performance_metrics'] = {
                'applications_sent': performance.applications_sent,
                'interviews_received': performance.interviews_received,
                'response_rate': performance.response_rate,
                'feedback_count': len(performance.feedback_received),
                'avg_ats_score': performance.avg_ats_score
            }
            
            # 生成建议
            if performance.response_rate < 0.1:
                report['recommendations'].append("回应率较低，建议优化简历内容或投递策略")
            
            if performance.avg_ats_score < 0.7:
                report['recommendations'].append("ATS评分偏低，建议增加关键词和优化格式")
            
            if performance.applications_sent > 10 and performance.interviews_received == 0:
                report['recommendations'].append("多次投递无回应，建议重新制作简历")
        
        return report
    
    def cleanup_old_versions(self, keep_days: int = 90):
        """清理旧版本"""
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE resume_versions 
            SET is_active = 0 
            WHERE created_time < ? AND is_active = 1
        ''', (datetime.fromtimestamp(cutoff_date).isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ 清理了 {deleted_count} 个旧版本")
        return deleted_count