"""个人天赋档案页 — 整合三种测评结果，生成统一的个人天赋画像"""

import json
import re
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, InterviewSession, ScaleResult, TalentTypeResult

profile_bp = Blueprint('profile', __name__)


def safe_json_loads(text, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(text) if text else default
    except (json.JSONDecodeError, TypeError):
        return default


def extract_talent_keywords(report_content):
    """从AI访谈报告中提取天赋关键词"""
    if not report_content:
        return []

    keywords = []
    patterns = [
        r'底层天赋[是为：:]\s*(.+?)(?:\n|$)',
        r'核心天赋[是为：:]\s*(.+?)(?:\n|$)',
        r'天赋[包括有：:]\s*(.+?)(?:\n|$)',
        r'你的天赋[是为：:]\s*(.+?)(?:\n|$)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, report_content)
        for m in matches:
            parts = re.split(r'[、，,；;]', m)
            for p in parts:
                p = p.strip().strip('*').strip('。').strip()
                if 2 <= len(p) <= 20:
                    keywords.append(p)

    return list(dict.fromkeys(keywords))[:10]


def cross_validate(interview_keywords, scale_dims, type_dims):
    """跨测评交叉分析"""
    confirmed = []
    conflicts = []

    dim_mapping = {
        '认知洞察型': ['认知运算', '逻辑分析', '模式识别', '系统思维', '抽象思考'],
        '创造表达型': ['创造', '表达', '创新', '原创', '想象力', '叙事'],
        '社交协同型': ['社交', '协同', '共情', '沟通', '关系', '连接', '同理'],
        '系统推动型': ['系统', '推动', '执行', '组织', '规划', '领导'],
        '身体感知型': ['身体', '感知', '直觉', '动手', '感官', '运动'],
    }

    scale_top = scale_dims[0]['name'] if scale_dims else ''
    type_code = type_dims.get('code', '') if type_dims else ''

    type_to_dim = {
        'C': '认知洞察型',
        'R': '社交协同型',
        'B': '身体感知型',
        'S': '系统推动型',
    }

    type_dim_name = type_to_dim.get(type_code[0], '') if type_code else ''

    if scale_top and type_dim_name:
        if scale_top == type_dim_name:
            confirmed.append(f'量表（{scale_top}）与类型学（{type_dim_name}）互相验证')
        else:
            conflicts.append(f'量表指向「{scale_top}」，类型学指向「{type_dim_name}」')

    for kw in interview_keywords:
        for dim_name, dim_keywords in dim_mapping.items():
            for dk in dim_keywords:
                if dk in kw:
                    if scale_top == dim_name or type_dim_name == dim_name:
                        confirmed.append(f'访谈关键词「{kw}」与{dim_name}维度吻合')
                    break

    return {
        'confirmed': list(dict.fromkeys(confirmed))[:5],
        'conflicts': list(dict.fromkeys(conflicts))[:3]
    }


@profile_bp.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')


@profile_bp.route('/api/profile/summary')
@login_required
def get_profile_summary():
    user_id = current_user.id

    interview = InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.created_at.desc()).first()

    interview_data = None
    interview_keywords = []
    if interview:
        interview_keywords = extract_talent_keywords(interview.report_content)
        interview_data = {
            'has': True,
            'keywords': interview_keywords,
            'report_preview': interview.report_content[:500] + '...' if len(interview.report_content) > 500 else interview.report_content,
            'created_at': interview.created_at.isoformat() if interview.created_at else None
        }
    else:
        interview_data = {'has': False}

    primary_scale = ScaleResult.query.filter_by(
        user_id=user_id, scale_type='primary'
    ).order_by(ScaleResult.created_at.desc()).first()

    secondary_scale = ScaleResult.query.filter_by(
        user_id=user_id, scale_type='secondary'
    ).order_by(ScaleResult.created_at.desc()).first()

    scale_data = {'primary': None, 'secondary': None}
    scale_top_dims = []

    if primary_scale:
        scores = safe_json_loads(primary_scale.scores)
        top_dims = safe_json_loads(primary_scale.top_dimensions, [])
        scale_top_dims = top_dims
        scale_data['primary'] = {
            'scores': scores,
            'top_dimensions': top_dims,
            'created_at': primary_scale.created_at.isoformat() if primary_scale.created_at else None
        }

    if secondary_scale:
        scale_data['secondary'] = {
            'talent_type': secondary_scale.talent_type,
            'scores': safe_json_loads(secondary_scale.scores),
            'created_at': secondary_scale.created_at.isoformat() if secondary_scale.created_at else None
        }

    talent_type = TalentTypeResult.query.filter_by(
        user_id=user_id
    ).order_by(TalentTypeResult.created_at.desc()).first()

    tt_data = None
    tt_dims = {}
    if talent_type:
        report = safe_json_loads(talent_type.report)
        tt_dims = {
            'code': talent_type.type_code,
            'name': report.get('name', ''),
            'tagline': report.get('tagline', ''),
            'dimensions': safe_json_loads(talent_type.dimensions),
            'scores': safe_json_loads(talent_type.scores)
        }
        tt_data = {
            'has': True,
            'type_code': talent_type.type_code,
            'name': report.get('name', ''),
            'tagline': report.get('tagline', ''),
            'dimensions': safe_json_loads(talent_type.dimensions),
            'scores': safe_json_loads(talent_type.scores),
            'created_at': talent_type.created_at.isoformat() if talent_type.created_at else None
        }
    else:
        tt_data = {'has': False}

    validation = cross_validate(interview_keywords, scale_top_dims, tt_dims)

    has_any = interview_data['has'] or scale_data['primary'] or tt_data['has']

    return jsonify({
        'success': True,
        'has_data': has_any,
        'interview': interview_data,
        'scale': scale_data,
        'talent_type': tt_data,
        'cross_validation': validation
    })
