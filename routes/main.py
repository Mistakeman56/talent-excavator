"""
routes/main.py — 主页和报告展示路由模块

本模块实现了系统的主要页面路由，包括：
1. 首页 — 系统入口页面，展示功能模块和AI访谈入口
2. 报告展示页 — 展示AI生成的天赋诊断报告
3. 报告分享 — 生成分享链接，支持无需登录查看报告
4. 报告导出 — 导出报告为Markdown文件
5. 天赋类型学页面入口 — 渲染测评页面
6. 天赋类型学结果页 — 展示测评结果

路由清单：
- GET  /                        — 首页
- GET  /report                  — 报告展示页（需要登录）
- POST /api/report/share        — 生成分享链接（需要登录）
- GET  /report/shared/<token>   — 通过分享链接查看报告（无需登录）
- GET  /api/report/export-markdown — 导出报告为Markdown（需要登录）
- GET  /talent-type             — 天赋类型学测评页
- GET  /talent-type/result/<id> — 天赋类型学结果页

安全设计：
- 报告页面需要登录才能访问
- 分享链接使用随机token，难以猜测
- 分享页面无需登录即可查看，方便分享给他人
"""

from flask import Blueprint, render_template, redirect, url_for, jsonify, request, make_response
from flask_login import current_user, login_required
from datetime import datetime
from models import db, InterviewSession
import uuid

# 创建主页模块的 Blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    系统首页

    路由: GET /
    需要登录: 否

    说明:
        首页是系统的入口页面，展示以下内容：
        1. Hero区域：系统标题、副标题、核心功能入口按钮
        2. AI访谈模块：介绍AI深度访谈功能
        3. 量表模块：介绍天赋维度筛查量表
        4. 类型学模块：介绍天赋类型学测评
        5. 72种人格图鉴：展示四种大类型的入口
        6. Human词典：词典功能入口

        首页还会检测用户是否有未完成的访谈，如果有则显示"继续上次访谈"按钮。

    返回:
        渲染 index.html 模板
    """
    return render_template('index.html', current_user=current_user)


@main_bp.route('/report')
@login_required
def report():
    """
    报告展示页面

    路由: GET /report
    需要登录: 是

    说明:
        展示AI生成的天赋诊断报告。
        报告内容为Markdown格式，前端使用marked.js渲染，
        使用DOMPurify进行XSS消毒。

        报告包含14个章节：
        1. 用户真正的底层天赋是什么
        2. 为什么这些天赋过去被遮蔽了
        3. 用户的缺点、怪癖、嫉妒、痛苦分别透露了什么
        4. 用户的能量来源与能量黑洞
        5. 用户的高能场景与伪擅长场景
        6. 用户最适合的角色类型
        7. 用户最不该再走的路
        8. 用户如何把天赋映射到职业、事业、产品
        9. 用户在认知/身体/精神/职业四象限的现状判断
        10. 用户当前更像哪种生活方式原型
        11. 当前最核心的问题是什么
        12. 未来30天/90天/6-12个月的演进建议
        13. AI使用建议
        14. 一段真正打到用户心里的结语

    返回:
        渲染 report.html 模板，传入报告内容和生成时间

    错误处理:
        如果用户没有生成过报告，重定向到首页
    """
    # 查询当前用户最近一次的访谈报告
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).order_by(InterviewSession.id.desc()).first()

    report_content = interview.report_content if interview else ''
    if not report_content:
        return redirect(url_for('main.index'))

    return render_template('report.html', report=report_content,
                           now=datetime.now().strftime('%Y年%m月%d日 %H:%M'))


@main_bp.route('/api/report/share', methods=['POST'])
@login_required
def share_report():
    """
    生成报告分享链接

    路由: POST /api/report/share
    需要登录: 是

    说明:
        为当前用户的最新报告生成一个分享链接。
        分享链接使用随机token，无需登录即可查看报告。

        如果报告已经有share_token，则复用现有的token。
        如果没有，则生成一个新的token。

    返回数据:
    {
        "success": true,
        "url": "https://example.com/report/shared/abc123def456",
        "token": "abc123def456"
    }

    错误情况:
        - 没有可分享的报告时返回错误
    """
    # 查询当前用户最近一次有报告的访谈
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).filter(
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.id.desc()).first()

    if not interview:
        return jsonify({"success": False, "error": "没有可分享的报告"})

    # 如果没有share_token，生成一个新的
    if not interview.share_token:
        interview.share_token = uuid.uuid4().hex[:16]
        db.session.commit()

    # 生成完整的分享URL
    share_url = url_for('main.shared_report', token=interview.share_token, _external=True)
    return jsonify({"success": True, "url": share_url, "token": interview.share_token})


@main_bp.route('/report/shared/<token>')
def shared_report(token):
    """
    通过分享链接查看报告（无需登录）

    路由: GET /report/shared/<token>
    需要登录: 否

    参数:
        token — 分享链接的随机token

    说明:
        允许未登录用户通过分享链接查看报告。
        token是随机生成的16位十六进制字符串，难以猜测。

    返回:
        渲染 report.html 模板，传入报告内容

    错误处理:
        - token无效或报告不存在时返回404页面
    """
    # 根据token查询对应的访谈记录
    interview = InterviewSession.query.filter_by(share_token=token).first()
    if not interview or not interview.report_content:
        return render_template('errors/404.html'), 404

    return render_template('report.html', report=interview.report_content,
                           now=interview.created_at.strftime('%Y年%m月%d日 %H:%M') if interview.created_at else '',
                           is_shared=True)


@main_bp.route('/api/report/export-markdown')
@login_required
def export_markdown():
    """
    导出报告为Markdown文件

    路由: GET /api/report/export-markdown
    需要登录: 是

    说明:
        将当前用户的最新报告导出为Markdown格式文件。
        浏览器会自动下载文件，文件名为 talent_report.md。

    返回:
        Markdown文件下载响应

    响应头:
        - Content-Type: text/markdown; charset=utf-8
        - Content-Disposition: attachment; filename=talent_report.md

    错误情况:
        - 没有可导出的报告时返回错误JSON
    """
    # 查询当前用户最近一次有报告的访谈
    interview = InterviewSession.query.filter_by(
        user_id=current_user.id
    ).filter(
        InterviewSession.report_content.isnot(None)
    ).order_by(InterviewSession.id.desc()).first()

    if not interview:
        return jsonify({"success": False, "error": "没有可导出的报告"})

    # 创建文件下载响应
    response = make_response(interview.report_content)
    response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=talent_report.md'
    return response


@main_bp.route('/talent-type')
def talent_type():
    """
    天赋类型学测评页面

    路由: GET /talent-type
    需要登录: 否（但提交答案需要登录）

    说明:
        渲染天赋类型学测评页面，包含：
        1. 欢迎页面：介绍测评功能和开始按钮
        2. 答题页面：40道情境迫选题
        3. 结果页面：4字母类型代码和解读报告

        40道题分4个模组：
        - Module I (t1-t12)：决定第1位字母（天赋形态 C/R/B/S）
        - Module II (t13-t22)：决定第2位字母（能量模式 D/R/V）
        - Module III (t23-t30)：决定第3位字母（驱动来源 A/H）
        - Module IV (t31-t40)：决定第4位字母（兴趣指向 M/C/P）

        总组合 = 4 × 3 × 2 × 3 = 72种天赋类型
    """
    return render_template('talent_type.html')


@main_bp.route('/talent-type/result/<session_id>')
@login_required
def talent_type_result(session_id):
    """
    天赋类型学测评结果页

    路由: GET /talent-type/result/<session_id>
    需要登录: 是

    参数:
        session_id — 测评会话的UUID标识

    说明:
        展示天赋类型学测评的结果，包含：
        1. 4字母类型代码（如 CDAM）
        2. 类型名称和标语
        3. 四维度详情
        4. 完整的解读报告

        结果页支持通过session_id查询历史结果，
        用户可以收藏或分享结果页链接。
    """
    return render_template('talent_type_result.html', session_id=session_id)
